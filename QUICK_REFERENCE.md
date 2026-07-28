# 📌 AutoPrice AI - Quick Reference Card

## 🎯 First Time Setup (5 minutes)

```bash
# 1. Backend Setup
cd autoprice-ai/backend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux
pip install -r requirements.txt

# 2. Frontend Setup (NEW TERMINAL)
cd autoprice-ai/frontend
npm install
```

---

## ▶️ Running the Project (Every Time)

### Option 1: Automatic Scripts (Easiest)

**Windows:**
```bash
double-click: run-windows.bat
# Or from terminal:
run-windows.bat
```

**Mac/Linux:**
```bash
chmod +x run-mac-linux.sh
./run-mac-linux.sh
```

### Option 2: Manual (Two Terminals)

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate                                    # Windows
source venv/bin/activate                               # Mac/Linux
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

---

## 🌐 Access URLs

| Component | URL |
|-----------|-----|
| **Dashboard** | http://localhost:3000 |
| **API Docs** | http://localhost:8000/docs |
| **WebSocket** | ws://localhost:8000/ws |

---

## 🛠️ Common Commands

| Task | Command |
|------|---------|
| Activate backend venv | `venv\Scripts\activate` (Win) or `source venv/bin/activate` (Mac/Linux) |
| Deactivate venv | `deactivate` |
| Reset database | Delete `backend/autoprice.db` |
| Clear frontend cache | Delete `frontend/node_modules`, then `npm install` |
| Stop servers | Press `CTRL+C` in each terminal |

---

## ⚠️ Common Errors & Fixes

| Error | Fix |
|-------|-----|
| `python: command not found` | Install Python 3.9+ from python.org |
| `ModuleNotFoundError` | Activate venv and run `pip install -r requirements.txt` |
| `npm: command not found` | Install Node.js from nodejs.org |
| Port already in use | Close other apps or restart computer |
| Virtual env won't activate | Delete venv folder and recreate |

---

## 📱 What You'll See

After opening http://localhost:3000:

✅ **Product Grid** - Shows all e-commerce products  
✅ **Current Prices** - Real-time pricing  
✅ **Agent Activity** - Live pricing decisions (every 15 seconds)  
✅ **Decision Log** - Why prices changed  
✅ **Price Charts** - Historical trends  

---

## 📖 Documentation map

| Doc | Use when |
|-----|----------|
| `README.md` | First-time setup, env vars, troubleshooting |
| `PROJECT_EXPLANATION.md` | Quick mental model of the agent loop and LangChain / SK |
| `PROJECT_DOCUMENTATION.md` | Full architecture, every major file, WebSocket + DB reference |
| `SETUP_INSTRUCTIONS.md` | Step-by-step install and run |

---

## 🚀 That's It!

You now have a fully functional autonomous pricing AI system running! 

**Enjoy! 🎉**
