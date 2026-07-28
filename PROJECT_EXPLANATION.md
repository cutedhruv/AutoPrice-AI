# AutoPrice AI – Project Explanation & Workflow

## 1. Project overview

AutoPrice AI is an autonomous, agentic e-commerce pricing demo. It runs a loop over active products, pulls market and internal data, proposes prices (Groq LLM or rules), validates them, executes approved updates, and streams status to a React dashboard. The same business rules live in `backend/tools/`; LangChain and Semantic Kernel wrap those calls for consistency and future planners.

## 2. High-level workflow

1. **Agent loop** — `OrchestratorAgent` runs every `AGENT_LOOP_INTERVAL` seconds (default **15**), loads active products, and runs the per-product pipeline for each.
2. **Per-product pipeline** (order is always **Market → Data → Pricing → Risk → Execution**):
   - **Orchestrator** — Schedules work, optional **LangGraph** graph vs sequential path, broadcasts WebSocket updates, calls **Memory** at end of cycle.
   - **Market** — Competitor snapshot, simulated demand, Google Trends; each external step goes **LangChain → optional Semantic Kernel → direct `tools/`** (see `market_framework_bridge.py`).
   - **Data** — Product row and price history from SQLite via **`agent_operations_bridge.py`** (same triple path).
   - **Pricing** — LLM path: **LangChain async tool** then **`tools/llm_client.get_pricing_decision`** (Semantic Kernel is not used here because the call is async). Rule fallback: **LangChain → optional SK → `calculate_optimal_price`**.
   - **Risk** — Validates proposed price via **`agent_operations_bridge.fetch_validate_price`**.
   - **Execution** — Persists price via **`fetch_update_price`**, logs decision, sends notifications / rich email.
   - **Memory** — Increments cycle counters; **`get_system_stats`** loads recent decisions and agent activity via **LangChain sync `invoke`** then direct tools (Semantic Kernel is skipped on this sync path to avoid nested event loops under FastAPI).
3. **Frontend** — REST + WebSocket (`main.py`, `websocket_manager.py`) drive live agent status, charts, and notifications.



## 4. Integration of major components

- **Backend (FastAPI)** — `backend/main.py`: REST, WebSocket, lifespan (DB init, seed, agent loop task).
- **Agents** — `backend/agents/*.py`: thin orchestration, logging, broadcasts; heavy logic delegated to `tools/` and bridges.
- **Agent framework** — `backend/agent_framework/`: LangChain `@tool` definitions, Semantic Kernel plugins, shared kernel, `market_framework_bridge.py`, `agent_operations_bridge.py`, optional LangGraph graph.
- **Database** — SQLite + SQLAlchemy (`database/models.py`, `db.py`, `seed.py`).
- **Frontend** — React 18 + Tailwind + Recharts; `src/services/api.js`, hooks, dashboard components.

## 5. Where to read more

- **`PROJECT_DOCUMENTATION.md`** — Architecture, agents, tools catalog, env vars, WebSocket events, DB schema, frontend map, **repository file reference**.
- **`README.md`** — Quick start, configuration table, troubleshooting, high-level structure.
- **`backend/config.py`** — Authoritative defaults for all feature flags and URLs.

## 6. Summary

AutoPrice AI keeps **deterministic pricing and validation** in `tools/` while routing **every agent** through **LangChain first** and **Semantic Kernel second** where enabled and safe, so the app stays reliable if frameworks fail and remains easy to extend with planners or SK-native agents later.
