# AutoPrice AI — setup & documentation index

This file is a **short index** of how setup and docs fit together. For always-current behavior, prefer **`README.md`**, **`PROJECT_EXPLANATION.md`**, and **`PROJECT_DOCUMENTATION.md`**.

## Primary documentation

| File | Contents |
|------|----------|
| **`README.md`** | Quick start, Windows/macOS scripts, configuration table, troubleshooting, high-level tree |
| **`PROJECT_EXPLANATION.md`** | Narrative workflow, LangChain vs Semantic Kernel vs `tools/` matrix |
| **`PROJECT_DOCUMENTATION.md`** | System architecture, every agent, tools catalog, **repository file reference** (backend + frontend), WebSocket events, DB schema, deployment, env vars |
| **`QUICK_REFERENCE.md`** | URLs, common commands, doc map |
| **`SETUP_INSTRUCTIONS.md`** | Detailed first-time setup and run instructions |

## Automation scripts

- **`run-windows.bat`** — Creates `backend/venv` if needed, installs deps with `venv\Scripts\python.exe -m pip`, starts backend + frontend.
- **`run-mac-linux.sh`** — Same idea for Unix shells.

## Backend template environment

- **`backend/.env.example`** — Lists `GROQ_*`, loop interval, `USE_LANGGRAPH_PIPELINE`, `USE_MARKET_SEMANTIC_KERNEL`, `USE_AGENT_SEMANTIC_KERNEL`, `SEMANTIC_KERNEL_CHAT_ENABLED`, SMTP, etc. Copy to **`backend/.env`** (never commit secrets).

## After setup

1. Backend: `http://localhost:8000` (API docs at `/docs`).
2. Frontend: `http://localhost:3000` (or the port CRA prints).
3. If something fails: **`QUICK_REFERENCE.md`** troubleshooting → **`README.md`** → **`PROJECT_DOCUMENTATION.md`**.

---

*Legacy “files created” checklists from early setup iterations have been folded into the docs above; use those three markdown files as the source of truth.*
