# AutoPrice AI – Autonomous Pricing Analyst Agent

A fully autonomous, AI-assisted e-commerce pricing platform that monitors competitors, blends market signals (including search trends), and updates prices with explainability—while keeping deterministic guardrails and safe fallbacks.

![Architecture](https://img.shields.io/badge/Architecture-Agentic_AI-blue)
![Backend](https://img.shields.io/badge/Backend-FastAPI-green)
![Frontend](https://img.shields.io/badge/Frontend-React-blue)
![Database](https://img.shields.io/badge/Database-SQLite-orange)
![Orchestration](https://img.shields.io/badge/Orchestration-LangGraph-purple)
![LLM](https://img.shields.io/badge/LLM-Groq-orange)
<p align="center">
  <img src="Screenshot 2026-07-28 170532.png" alt="AutoPrice AI Banner" width="100%">
</p>

## Project Demo

<p align="center">
  <a href="https://youtu.be/_uW1iH3ccuo">
    <img src="https://img.youtube.com/vi/_uW1iH3ccuo/maxresdefault.jpg" alt="Project Demo" width="800">
  </a>
</p>

<p align="center">
  <b>▶️ Watch the Full Project Demo on YouTube</b>
</p>
## What this project does today

- **Autonomous loop** — On backend startup, an asyncio loop runs every `AGENT_LOOP_INTERVAL` seconds (default **15s**) and processes each active product.
- **Multi-agent pipeline** — **Market → Data → Pricing → Risk → Execution** (same business logic whether orchestrated by LangGraph or the legacy sequential path).
- **LLM-assisted pricing** — **Groq** (`tools/llm_client.py`) powers the **Pricing Agent** when `GROQ_API_KEY` is set; otherwise the system uses **rule-based** pricing (`calculate_optimal_price`).
- **Google Trends** — **pytrends** (`tools/trends_tools.py`) enriches market analysis; failures are non-fatal (cached / graceful).
- **LangChain everywhere (agents)** — Each agent reaches `tools/` through **LangChain tools first**: **Market** (competitor, trends, demand) via `market_framework_bridge.py`; **Data, rule-based pricing, Risk, Execution** via `agent_operations_bridge.py`. **Groq pricing** uses a LangChain **async** tool then the same `get_pricing_decision` as before (Semantic Kernel is not layered on that async path).
- **Semantic Kernel (optional second step)** — **`USE_MARKET_SEMANTIC_KERNEL`** gates SK plugins under `MarketIntelligence`; **`USE_AGENT_SEMANTIC_KERNEL`** gates SK under `PipelineAgents` for sync operations. **Memory** `get_system_stats` uses LangChain **sync** `invoke` then direct tools (no SK) to stay safe under FastAPI’s sync status endpoint.
- **LangGraph** — When `USE_LANGGRAPH_PIPELINE=true` (default), `agent_framework/pricing_graph.py` runs the same agent methods in graph form; set `false` for sequential-only orchestration.
- **Semantic Kernel chat** — Optional Groq-backed SK chat service on the shared kernel: `SEMANTIC_KERNEL_CHAT_ENABLED=true` (see `config.py`).
- **Explainability** — Decisions, agent logs, price history, and rich HTML email bodies (`tools/email_builder.py`) describe *why* a price changed.
- **Notifications** — In-app notifications plus optional **SMTP** email; `NOTIFICATION_EMAIL` supports **comma-separated** recipients.

## Quick start

| Step | Action |
|------|--------|
| 1 | **Python 3.9+**, **Node 16+**, **npm** |
| 2 | Backend: `cd backend` → `python -m venv venv` → install deps (see below) |
| 3 | Frontend: `cd frontend` → `npm install` |
| 4 | Copy `backend/.env.example` to `backend/.env` and set keys (optional Groq/SMTP) |
| 5 | Run backend **8000** + frontend (**3000**, or **3001** if CRA picks another port) |

### Windows (recommended)

Use **`run-windows.bat`** at the repo root: it creates `backend/venv` if missing, installs dependencies with **`venv\Scripts\python.exe -m pip`** (avoids broken `pip.exe` launchers after moving the project), and starts servers.

Or manually:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
```

```powershell
cd frontend
npm start
```

- **Dashboard:** [http://localhost:3000](http://localhost:3000) (or the URL printed by CRA, e.g. **3001**)
- **API docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **WebSocket:** `ws://localhost:8000/ws`

### macOS / Linux

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

Use `./run-mac-linux.sh` if you prefer a scripted start.

> **Dev tip:** Avoid `uvicorn --reload` while heavy installs write into `backend/venv` (file watchers can thrash). For day-to-day dev, reload is fine once dependencies are stable.

## Architecture (high level)

```
┌──────────────────────────────┐
│   React 18 + Tailwind UI   │
│   REST + WebSocket (8000)  │
└──────────────┬─────────────┘
               │
┌──────────────▼─────────────┐
│      FastAPI (main.py)      │
│  REST │ WebSocket │ lifespan│
└──────────────┬─────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│  OrchestratorAgent — autonomous loop + per-product flow  │
│  LangGraph (default) OR sequential fallback              │
│    Market → Data → Pricing → Risk → Execution            │
└──────────────┬────────────────────────────────────────────┘
               │
┌──────────────▼─────────────┐
│  SQLite (products, history, │
│  decisions, logs, notifs)  │
└────────────────────────────┘
```

## Agent roles

| Agent | Role |
|--------|------|
| **Orchestrator** | Cycle scheduling, per-product pipeline, WebSocket broadcasts |
| **Market** | Competitor snapshot, demand simulation, **Google Trends** context |
| **Data** | Internal product metrics, margin, stock, short price-history trend |
| **Pricing** | **Groq LLM** decision + enforced post-processing, or **rules** fallback |
| **Risk** | Margin floors, max single-step change, above-cost checks |
| **Execution** | DB price update, decision log, notifications / **rich email** |
| **Memory** | Cycle stats and system-level summaries |

## Strategy (how pricing behaves)

1. **Competitive anchor** — Competitor price anchors positioning; system aims to stay **below** competitor while protecting margin (see `tools/llm_client.py` prompts and `tools/pricing_tools.py` rules).
2. **Demand & stock** — Higher demand / tighter stock → smaller undercut; lower demand / excess stock → deeper discount logic in rules; LLM prompt encodes similar tradeoffs.
3. **Trends signal** — When Trends data is available, demand score can be nudged and LLM context includes interest / related queries (`agents/market_agent.py`).
4. **Safety** — Risk agent rejects unsafe proposals; execution only runs when approved and decision is not `no_change`.
5. **Observability** — Agent logs, decisions table, notifications, and optional email give a full trail.

## Configuration (`backend/.env`)

| Variable | Purpose |
|----------|---------|
| `GROQ_API_KEY` | Enables LLM pricing via Groq |
| `GROQ_MODEL` | Model id (default in `config.py`) |
| `GROQ_BASE_URL` | OpenAI-compatible base URL for Groq (used by optional Semantic Kernel chat) |
| `DATABASE_URL` | SQLite path (default `sqlite:///./autoprice.db`) |
| `AGENT_LOOP_INTERVAL` | Seconds between full cycles |
| `USE_LANGGRAPH_PIPELINE` | `true`/`false` — LangGraph per-product graph vs sequential orchestrator |
| `USE_MARKET_SEMANTIC_KERNEL` | `true`/`false` — After LangChain on Market paths, try SK `MarketIntelligence` before direct `tools/` |
| `USE_AGENT_SEMANTIC_KERNEL` | `true`/`false` — After LangChain on Data / rules / risk / execution, try SK `PipelineAgents` before direct `tools/` |
| `SEMANTIC_KERNEL_CHAT_ENABLED` | `true` to register Groq chat on the shared Semantic Kernel |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD` | Gmail (or other) SMTP |
| `NOTIFICATION_EMAIL` | Recipient(s); **comma-separated** for multiple inboxes |

**Gmail:** use an **App Password** (2-Step Verification on) for `SMTP_PASSWORD`. If you see `535 BadCredentials`, regenerate the app password and restart the backend.

**Security:** never commit real `.env` secrets; rotate keys if they were ever shared.

## Project structure (key paths)

```
autoprice-ai/
├── backend/
│   ├── main.py                 # FastAPI app + lifespan (DB seed, agent loop)
│   ├── config.py               # Env-driven settings
│   ├── agents/                 # Market, Data, Pricing, Risk, Execution, Memory, Orchestrator
│   ├── agent_framework/        # LangGraph, LangChain tools, SK plugins, kernel, market + agent_operations bridges
│   ├── tools/
│   │   ├── llm_client.py       # Groq chat completions for pricing
│   │   ├── trends_tools.py     # Google Trends (pytrends)
│   │   ├── notification_tools.py  # DB notifications + SMTP
│   │   ├── email_builder.py    # Rich explainable price-update emails
│   │   └── ...
│   ├── database/
│   └── requirements.txt        # Includes langgraph, langchain, semantic-kernel, pytrends, …
├── frontend/                   # CRA + React 18 + Tailwind + Recharts
├── run-windows.bat
├── run-mac-linux.sh
├── README.md                   # This file
├── PROJECT_EXPLANATION.md      # Short workflow + framework matrix
└── PROJECT_DOCUMENTATION.md    # Architecture, file map, deployment
```

## Dependencies (backend highlights)

Core: **FastAPI**, **Uvicorn**, **SQLAlchemy**, **Pydantic**, **httpx**, **websockets**, …  
AI / orchestration: **langgraph**, **langchain**, **langchain-core**, **semantic-kernel**, **pytrends**, **groq** (package present; primary LLM path uses httpx to Groq API).

## Troubleshooting

| Issue | What to try |
|--------|-------------|
| `pip` “cannot find python.exe” after moving repo | Remove `backend/venv`, recreate, use `venv\Scripts\python.exe -m pip install -r requirements.txt` |
| PowerShell blocks `Activate.ps1` | Use `venv\Scripts\python.exe` directly (as in `run-windows.bat`) |
| Port **8000** in use | Stop other uvicorn / `Get-NetTCPConnection -LocalPort 8000` |
| Frontend on **3001** | CRA picked alternate port; open the URL it prints. API base is `http://localhost:8000` in `frontend/src/services/api.js` |
| No emails | Check SMTP app password, `NOTIFICATION_EMAIL`, spam/quarantine; logs show `Rich email sent` vs `Rich email send failed` |
| LLM not used | Empty `GROQ_API_KEY` → automatic **rule-based** pricing still runs |

## License

MIT License — demonstration / learning project; extend for production with auth, real data feeds, and hardened secrets management.
