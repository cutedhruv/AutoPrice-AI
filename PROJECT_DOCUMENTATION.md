# AutoPrice AI – Project Documentation

## 1. System Architecture

### 1.1 Overview

AutoPrice AI is an autonomous pricing intelligence system built with a multi-agent architecture. The system operates continuously without human intervention, making intelligent pricing decisions based on market conditions, demand patterns, and business rules.

### 1.2 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React 18 + Tailwind CSS + CRA | Dashboard, products, charts, notifications |
| Charts | Recharts | Price and analytics visualization |
| Real-time | WebSocket + REST polling | Live agent status; 10s refresh fallback in `useDashboardData` |
| Backend | FastAPI (Python) | REST API, WebSocket, app lifespan (DB init, agent loop) |
| Agents | Modular Python classes | Market, Data, Pricing, Risk, Execution, Memory |
| Orchestration | **LangGraph** (toggle) | `USE_LANGGRAPH_PIPELINE` — compiled graph in `pricing_graph.py`; sequential fallback in orchestrator |
| LLM | **Groq** (OpenAI-compatible chat) | `PricingAgent`: LangChain `pricing_llm_decide` then `tools/llm_client.get_pricing_decision` |
| Rules fallback | `pricing_tools.calculate_optimal_price` | Via `agent_operations_bridge.fetch_optimal_price_rule_based` (LC → SK? → tools) |
| Trends | **pytrends** | Google Trends in `tools/trends_tools.py`; Market Agent reaches it through `market_framework_bridge` |
| SK / LC | **Semantic Kernel**, **LangChain** | `agent_framework/`: tools + plugins for all pipeline agents; optional SK Groq chat service |
| Database | SQLite + SQLAlchemy | Products, history, decisions, logs, notifications |
| Loop | asyncio | `OrchestratorAgent.start_loop` interval from `AGENT_LOOP_INTERVAL` |

### 1.3 Design Principles

1. **Autonomy** — System runs without manual triggers
2. **Explainability** — Every decision has a clear reason
3. **Modularity** — Each agent/tool is independent and reusable
4. **Safety** — Risk validation before any price change
5. **Transparency** — Live visibility into agent operations

---

## 2. Agent System Design

### 2.1 Agent Pipeline

```
Orchestrator → Market Agent → Data Agent → Pricing Agent → Risk Agent → Execution Agent → Memory Agent
```

Per-product execution is implemented as:

1. **LangGraph** — When `USE_LANGGRAPH_PIPELINE=true` (default in `config.py`), `agent_framework/pricing_graph.py` compiles a linear `StateGraph` that calls the same agent methods as the sequential path.
2. **Sequential** — `OrchestratorAgent.process_product` uses the same agent instances step-by-step when LangGraph is disabled, compilation fails, or `ainvoke` raises (fallback).

### 2.2 Agent Descriptions

#### Orchestrator Agent
- **Role**: Pipeline coordinator
- **Responsibilities**: 
  - Manages the autonomous loop timer
  - Sequences agent execution for each product (LangGraph or sequential)
  - Attaches WebSocket broadcast callback for live UI updates
  - Invokes `MemoryAgent` at end of each cycle

#### Market Agent
- **Role**: External intelligence
- **Responsibilities**:
  - **Competitor prices** — `fetch_competitor_data` in **`market_framework_bridge.py`**: LangChain `competitor_snapshot` → optional SK `MarketIntelligence.competitor_snapshot` (`USE_MARKET_SEMANTIC_KERNEL`) → `tools.competitor_tools.get_competitor_price`
  - **Google Trends** — `fetch_google_trends`: LangChain `google_trends_research` → optional SK `google_trends_research` → `tools.trends_tools.get_google_trends`
  - **Demand snapshot** — `fetch_simulated_demand`: LangChain `simulate_market_demand` → optional SK `simulate_market_demand` → `simulate_demand_change`
  - Nudges `demand_data` from Trends when `trends_data.available` (logic unchanged in `market_agent.py`)

#### Data Agent
- **Role**: Internal analytics
- **Responsibilities**:
  - Loads product rows via **`fetch_internal_product_rows`** (`agent_operations_bridge.py`): LangChain `internal_product_rows` → optional SK `PipelineAgents.internal_product_rows` (`USE_AGENT_SEMANTIC_KERNEL`) → `get_product_data`
  - Loads history via **`fetch_internal_price_history`**: LangChain `internal_price_history` → optional SK → `get_price_history`
  - Derives short-term price trend, margin, stock, demand from that data (unchanged aggregation in `data_agent.py`)

#### Pricing Agent
- **Role**: Decision maker
- **Responsibilities**:
  - **Primary (Groq):** **`fetch_llm_pricing_decision`** — LangChain async `pricing_llm_decide` (wraps the same inputs as before) then **`get_pricing_decision`** in `llm_client.py`.behavior matches the previous direct await).
  - **Fallback (rules):** **`fetch_optimal_price_rule_based`** — LangChain `rule_based_optimal_price` → optional SK `rule_based_optimal_price` → `calculate_optimal_price`, plus `generate_explanation` as before
  - Emits the same structured pricing dict (`source`: `llm` vs `rule_based`)

#### Risk Agent
- **Role**: Validator/Guardian
- **Responsibilities**:
  - When decision is not `no_change`, runs **`fetch_validate_price`**: LangChain `validate_proposed_price_tool` → optional SK `validate_proposed_price` → `validate_price` (same rules: margin floor ~4%, max step change 25%, cost floor, competitor band warnings)
  - Short-circuits approval for `no_change` (unchanged)

#### Execution Agent
- **Role**: Action executor
- **Responsibilities**:
  - Persists price via **`fetch_update_price`**: LangChain `execute_price_update_tool` → optional SK `execute_price_update` → `update_price`
  - Logs decisions (`log_decision`), notifications, rich email (`build_price_update_email` + `send_rich_notification`), WebSocket broadcasts (unchanged after DB write)

#### Memory Agent
- **Role**: System memory
- **Responsibilities**:
  - **`record_cycle`** — Increments counters and summaries from `cycle_results` (unchanged)
  - **`get_system_stats`** — Recent decisions and agent lines via **`fetch_recent_decisions_sync`** / **`fetch_agent_activity_sync`**: LangChain sync `invoke` then direct `get_recent_decisions` / `get_agent_activity` (Semantic Kernel omitted on this synchronous API path)

### 2.3 AI orchestration (`backend/agent_framework/`)

| Component | File(s) | Purpose |
|-----------|---------|---------|
| LangGraph pipeline | `pricing_graph.py` | Linear `StateGraph`: market → data → pricing → risk → execution → finalize; calls the same `OrchestratorAgent` agent instances |
| LangChain tools | `langchain_tools.py` | `@tool` / async tools for market, demand, DB reads, Groq pricing, rules, validate, execute, memory reads; `list_market_intelligence_tools()`, `list_pipeline_agent_tools()` |
| Semantic Kernel plugins | `semantic_plugins.py` | **`MarketIntelligence`**: trends, competitor, bulk trends, `simulate_market_demand`. **`PipelineAgents`**: product rows, history, rule price, validate, execute, recent decisions/activity |
| Shared kernel | `kernel_factory.py` | Singleton: both plugins + optional Groq chat service when `SEMANTIC_KERNEL_CHAT_ENABLED=true` |
| Market bridge | `market_framework_bridge.py` | `fetch_competitor_data`, `fetch_google_trends`, `fetch_simulated_demand` — LangChain → `USE_MARKET_SEMANTIC_KERNEL` SK → `tools/` |
| Pipeline bridge | `agent_operations_bridge.py` | Data, pricing (LLM + rules), risk, execution async paths; sync helpers for Memory stats |
| Package exports | `__init__.py` | Re-exports graph builder, kernel, bridges, tool list helpers |

Business rules and DB side effects remain in **`tools/`**; bridges add ordering and observability without changing return shapes.

---

## 3. Tools System

### 3.1 Tool Design Philosophy

Each tool is:
- A pure function with structured input/output
- Error-handled with graceful fallbacks
- Database-aware but session-independent
- Reusable across multiple agents

### 3.2 Tool Catalog

#### `get_product_data(product_id: Optional[int])`
- Returns complete product information with computed metrics
- Calculates real-time profit margins and price differences

#### `get_competitor_price(product_id: int)`
- Simulates multi-competitor price monitoring
- Returns lowest price, average market price, price gap analysis
- Updates competitor price in database for realistic simulation

#### `calculate_optimal_price(...)`
- Multi-factor pricing algorithm
- Factors: competitor price, demand score, stock level, cost price
- Returns: optimal price, confidence, decision type, reasoning

#### `validate_price(...)`
- Business rule enforcement (`pricing_tools.py`)
- Rules include: minimum margin threshold (~**4%**), max single-step change (**25%**), above-cost, sanity vs competitor band (warnings)
- Returns: approval status, risk level, issues/warnings

#### `get_google_trends(...)` / `get_market_trends_summary(...)`
- Cached **pytrends** calls; optional `geo` parameter
- Used by Market Agent and exposed via LangChain / Semantic Kernel wrappers

#### `get_pricing_decision(...)` / `call_llm(...)`
- Groq chat completions for JSON structured pricing output
- Post-processing enforces business constraints before returning to `PricingAgent`

#### `build_price_update_email(...)`
- Builds short DB message, subject, plain text, and rich HTML for execution-time emails

#### LangChain / SK entry points
- `list_market_intelligence_tools()` — LangChain tools used on the Market path
- `list_pipeline_agent_tools()` — LangChain tools for Data, Pricing, Risk, Execution, Memory reads
- `get_shared_kernel()` — singleton Semantic Kernel with `MarketIntelligence` + `PipelineAgents` plugins (and optional Groq chat)

#### `update_price(...)`
- Executes database update
- Creates price history record
- Returns confirmation with change metrics

#### `send_notification(...)` / `send_rich_notification(...)`
- Persists rows in `notifications` table
- Sends **SMTP** email when `SMTP_USER`, `SMTP_PASSWORD`, and `NOTIFICATION_EMAIL` are set
- `NOTIFICATION_EMAIL` may be **comma-separated** for multiple recipients
- Rich path uses `_send_rich_email` for HTML price-update templates

#### `generate_explanation(...)`
- Creates human-readable reasoning
- Incorporates all decision factors
- Suitable for customer/stakeholder communication

#### `log_decision(...)`
- Permanent decision record
- Includes full agent chain, confidence, profit impact
- Enables audit trail

Agents typically reach the catalog above through **`agent_operations_bridge`** or **`market_framework_bridge`** (LangChain → optional Semantic Kernel → these functions).

---

## 4. Repository layout and key files

### 4.1 Root (repository)

| Item | Purpose |
|------|---------|
| `README.md` | Quick start, config table, troubleshooting, repo map |
| `PROJECT_EXPLANATION.md` | Short narrative: workflow, LangChain/SK matrix, pointers |
| `PROJECT_DOCUMENTATION.md` | This document: architecture, agents, tools, files, deployment |
| `QUICK_REFERENCE.md` | Commands, URLs, common fixes |
| `SETUP_INSTRUCTIONS.md` | First-time and daily run steps |
| `SETUP_COMPLETE.md` | Meta checklist of setup artifacts (historical) |
| `run-windows.bat` / `run-mac-linux.sh` | One-command dev startup |

### 4.2 `backend/` — API, agents, framework

| Path | Purpose |
|------|---------|
| `main.py` | FastAPI: REST, WebSocket `/ws`, lifespan (DB init, seed, agent loop), `OrchestratorAgent` |
| `config.py` | Env flags: `GROQ_*`, `DATABASE_URL`, `AGENT_LOOP_INTERVAL`, `USE_LANGGRAPH_PIPELINE`, `USE_MARKET_SEMANTIC_KERNEL`, `USE_AGENT_SEMANTIC_KERNEL`, `SEMANTIC_KERNEL_CHAT_ENABLED`, SMTP |
| `websocket_manager.py` | Connection registry and broadcast |
| `agents/orchestrator.py` | Loop, per-product flow, LangGraph app or sequential branch |
| `agents/market_agent.py` | Competitor, demand, trends via `market_framework_bridge` |
| `agents/data_agent.py` | Product + history via `agent_operations_bridge` |
| `agents/pricing_agent.py` | `fetch_llm_pricing_decision` + `fetch_optimal_price_rule_based` |
| `agents/risk_agent.py` | `fetch_validate_price` |
| `agents/execution_agent.py` | `fetch_update_price` + notifications / email |
| `agents/memory_agent.py` | Counters; stats lists via sync LangChain helpers in bridge |
| `agent_framework/pricing_graph.py` | LangGraph linear graph over existing agents |
| `agent_framework/langchain_tools.py` | All `@tool` / async tools wrapping `tools/*` |
| `agent_framework/semantic_plugins.py` | SK plugins: `MarketIntelligence`, `PipelineAgents` |
| `agent_framework/kernel_factory.py` | Singleton kernel + optional Groq chat service |
| `agent_framework/market_framework_bridge.py` | Market path: LC → SK? → tools |
| `agent_framework/agent_operations_bridge.py` | Non-market pipeline: LC → SK? → tools; sync memory helpers |
| `agent_framework/__init__.py` | Re-exports for imports and notebooks |
| `tools/llm_client.py` | Groq structured pricing |
| `tools/pricing_tools.py` | Rules, validate, update |
| `tools/product_tools.py` | SQLite product and history reads |
| `tools/competitor_tools.py` | Competitor snapshot, demand simulation |
| `tools/trends_tools.py` | Google Trends (pytrends) |
| `tools/explanation_tools.py` | Logging, decisions, explanations, activity feeds |
| `tools/notification_tools.py` | Notifications + SMTP |
| `tools/email_builder.py`, `email_service.py`, `explainable_email.py` | Email composition and delivery |
| `database/db.py`, `models.py`, `seed.py` | SQLAlchemy session, ORM, demo data |
| `.env.example` | Template env including framework toggles |
| `requirements.txt` | Locked / listed Python dependencies |

### 4.3 `frontend/src/` — dashboard UI

| Path | Purpose |
|------|---------|
| `index.js`, `App.js` | React entry and app shell |
| `pages/DashboardPage.js` | Main dashboard route |
| `components/Header.js`, `StatsBar.js`, `layout/TopNavBar.js` | Header, KPI strip, navigation |
| `components/ProductGrid.js` | Product cards |
| `components/AgentActivityPanel.js`, `DecisionLog.js` | Live agents and decision history |
| `components/PriceCharts.js`, `NotificationPanel.js` | Charts and alert list |
| `components/AgentsUpdatePage.js`, `AgentUpdatesPage.js`, `DemoPage.js` | Extra pages / demos |
| `hooks/useDashboardData.js` | WebSocket + REST with polling fallback |
| `services/api.js` | `fetch` helpers and API base URL |

---

## 5. Real-Time Communication

### 5.1 WebSocket Events

| Event Type | Direction | Description |
|-----------|-----------|-------------|
| `agent_status` | Server → Client | Agent step updates |
| `price_update` | Server → Client | Price change notification |
| `cycle_start` | Server → Client | New cycle begins |
| `cycle_complete` | Server → Client | Cycle summary |

### 5.2 Polling Fallback

REST API polling every 10 seconds ensures data freshness even if WebSocket disconnects.

---

## 6. Database Schema

### Products
- Product catalog with pricing, stock, demand metrics

### Price History
- Complete audit trail of all price changes
- Includes reason, agent, margin at time of change

### Agent Logs
- Full activity log for all agents
- Status tracking (running/completed/error)

### Decisions
- Structured decision records
- Includes confidence, profit impact, agent chain

### Notifications
- User-facing alerts
- Read/unread status

---

## 7. Frontend Architecture

### 7.1 Component Structure

- **Header** — Brand, agent status indicator, connection status
- **StatsBar** — Key metrics overview
- **ProductGrid** — Flipkart-inspired product cards
- **AgentActivityPanel** — Live agent status feed
- **DecisionLog** — Detailed decision explanations
- **PriceCharts** — Recharts visualizations
- **NotificationPanel** — Alert feed

### 7.2 Design Decisions

- **Flipkart-inspired** but not a clone — focus on data display
- **Card-based layout** for products with key metrics visible
- **Color-coded** status indicators throughout
- **Real-time animations** for live updates
- **Responsive** grid layout for all screen sizes

---

## 8. Deployment Notes

### Environment variables (`backend/.env`)

Copy **`backend/.env.example`** to **`.env`**. Commonly used keys:

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Enables LLM pricing (`llm_client` / LangChain `pricing_llm_decide` chain) |
| `GROQ_MODEL` | Groq model id |
| `GROQ_BASE_URL` | OpenAI-compatible base URL (Groq); also used if SK chat is enabled |
| `DATABASE_URL` | SQLAlchemy URL (default SQLite file in `backend/`) |
| `AGENT_LOOP_INTERVAL` | Seconds between full pricing cycles |
| `USE_LANGGRAPH_PIPELINE` | `true`: LangGraph per-product graph; `false`: sequential only |
| `USE_MARKET_SEMANTIC_KERNEL` | After LangChain on Market paths, call SK `MarketIntelligence` before direct tools |
| `USE_AGENT_SEMANTIC_KERNEL` | After LangChain on Data / rules / risk / execution, call SK `PipelineAgents` before direct tools |
| `SEMANTIC_KERNEL_CHAT_ENABLED` | Registers Groq as SK chat completion service on the shared kernel |
| `SMTP_*`, `NOTIFICATION_EMAIL` | Optional email notifications |

### Development
```bash
# Backend (from backend/ with venv activated, or use venv python directly on Windows)
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend && npm start
```

Use **`run-windows.bat`** or **`run-mac-linux.sh`** for a consistent first-time setup.

### Production Considerations
- Replace SQLite with PostgreSQL (or another managed DB)
- Add authentication/authorization on REST + WebSocket
- Deploy with Docker / process manager; secrets via vault, not `.env` in images
- Use Redis or similar if scaling WebSocket fan-out
- Rate limiting and observability (structured logs, metrics) for LLM and Trends calls
- Review **Gmail / workspace** deliverability (SPF/DKIM) if sending high volume from SMTP

