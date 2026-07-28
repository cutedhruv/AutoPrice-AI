# 🚀 AutoPrice AI - Setup & Run Instructions

## ⏱️ Quick Summary
- **First time setup:** ~5 minutes
- **Subsequent runs:** ~2 minutes
- **No complex configuration needed** (everything works out of the box)
- **Framework toggles** — Copy `backend/.env.example` to `backend/.env`; see `README.md` and `PROJECT_DOCUMENTATION.md` §8 for `USE_LANGGRAPH_PIPELINE`, `USE_MARKET_SEMANTIC_KERNEL`, `USE_AGENT_SEMANTIC_KERNEL`, and Groq/SMTP keys.

---

## 📋 One-Time Setup (Do This First)

### 1️⃣ Verify Prerequisites
```bash
# Check Python version (should be 3.9 or higher)
python --version

# Check Node.js version (should be 16 or higher)
node --version

# Check npm version (should be 7 or higher)
npm --version
```

### 2️⃣ Backend Setup
```bash
# Navigate to backend
cd autoprice-ai/backend

# Create virtual environment
python -m venv venv

# Activate it (Windows)
venv\Scripts\activate

# Activate it (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**✅ Backend ready!**

### 3️⃣ Frontend Setup
```bash
# Open a NEW terminal

# Navigate to frontend
cd autoprice-ai/frontend

# Install dependencies
npm install
```

**✅ Frontend ready!**

---

## ▶️ Running the Project (Every Time)

### 🎯 Two Terminals Required

**Terminal 1 - Backend Server:**
```bash
# Navigate to backend
cd autoprice-ai/backend

# Activate virtual environment (Windows)
venv\Scripts\activate

# Activate virtual environment (Mac/Linux)
source venv/bin/activate

# Start the server
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
2026-05-08 09:12:36,558 - agents.orchestrator - INFO - Autonomous pricing loop started (interval: 15s)
```

**Terminal 2 - Frontend Server:**
```bash
# Navigate to frontend
cd autoprice-ai/frontend

# Start React
npm start
```

**You should see:**
```
Compiled successfully!
Local:            http://localhost:3000
```

---

## 🌐 Access the Application

Once both servers are running:

1. **Open your browser:** http://localhost:3000
2. **See the dashboard** with:
   - Product listings
   - Live price updates
   - Agent activity feed
   - Decision explanations

3. **Optional - API Documentation:** http://localhost:8000/docs

---

## ❌ Troubleshooting

| Problem | Solution |
|---------|----------|
| `python: command not found` | Install Python 3.9+ from python.org |
| `ModuleNotFoundError` in backend | Make sure `(venv)` shows in terminal, then run `pip install -r requirements.txt` |
| `npm: command not found` | Install Node.js from nodejs.org |
| Port 3000/8000 already in use | Close other apps or restart your computer |
| Virtual environment won't activate | Delete `venv` folder and recreate it |
| `CTRL+C` doesn't stop server | Press `CTRL+C` again or close the terminal |

---

## 🔄 Workflow for Next Time

```
1. Open Terminal 1 → cd backend → venv\Scripts\activate → python -m uvicorn main:app --reload
2. Open Terminal 2 → cd frontend → npm start
3. Open browser → http://localhost:3000
4. Done! 🎉
```

---

## 📱 What You'll See

✅ **Dashboard** - Product grid with current prices  
✅ **Agent Activity** - Real-time pricing decisions (updates every 15 seconds)  
✅ **Explanations** - Why each price changed  
✅ **Charts** - Price history over time  
✅ **Notifications** - System alerts and updates  

---

## 🛑 Stopping the Project

Simply press `CTRL+C` in each terminal:

```bash
# In Terminal 1 (Backend)
CTRL+C
# Server stopped

# In Terminal 2 (Frontend)
CTRL+C
# Development server stopped
```

---

## 🎓 Next Steps

- Read [README.md](README.md) for detailed documentation
- Check [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) for architecture details
- Explore the agents in `backend/agents/`
- Modify products in `backend/database/seed.py`

---

**Happy pricing! 🚀**
