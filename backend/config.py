"""Configuration for AutoPrice AI Backend"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-8b-8192")

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autoprice.db")

# Agent Loop
AGENT_LOOP_INTERVAL = int(os.getenv("AGENT_LOOP_INTERVAL", "15"))  # seconds

# Pipeline orchestration — LangGraph wraps the existing agents (sequential fallback if false)
USE_LANGGRAPH_PIPELINE = os.getenv("USE_LANGGRAPH_PIPELINE", "true").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Semantic Kernel: optional Groq-compatible endpoint for plugin orchestration helpers
SEMANTIC_KERNEL_CHAT_ENABLED = os.getenv("SEMANTIC_KERNEL_CHAT_ENABLED", "false").strip().lower() in (
    "1",
    "true",
    "yes",
)
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")

# Market Agent — LangChain tools are always used first (see market_framework_bridge.py).
# Semantic Kernel plugins are optional (fallback chain continues to direct tools/).
USE_MARKET_SEMANTIC_KERNEL = os.getenv("USE_MARKET_SEMANTIC_KERNEL", "true").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Data / Pricing / Risk / Execution / Memory — Semantic Kernel second step after LangChain (fallback to tools/)
USE_AGENT_SEMANTIC_KERNEL = os.getenv("USE_AGENT_SEMANTIC_KERNEL", "true").strip().lower() in (
    "1",
    "true",
    "yes",
)

# Notification
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
NOTIFICATION_EMAIL = os.getenv("NOTIFICATION_EMAIL", "")

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
