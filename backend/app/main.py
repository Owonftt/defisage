"""DeFiSage — AI-Powered DeFi Protocol Intelligence Platform.

FastAPI backend orchestrating a Xiaomi MiMo multi-agent pipeline that produces
institutional-grade research memos for live DeFi protocols.
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.core.config import settings
from app.core.token_tracker import TokenTracker
from app.services.mimo_client import MiMoClient

load_dotenv()

token_tracker = TokenTracker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    print("🧭 DeFiSage starting...")
    print(f"   Model: {settings.MIMO_MODEL}")
    print(f"   Token budget: {settings.DAILY_TOKEN_BUDGET:,}/day")
    yield
    print("🧭 DeFiSage shutting down...")


app = FastAPI(
    title="DeFiSage",
    description=(
        "AI-Powered DeFi Protocol Intelligence Platform — multi-agent risk, "
        "tokenomics, and governance analysis powered by Xiaomi MiMo."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.token_tracker = token_tracker
app.state.mimo_client = MiMoClient(
    settings.MIMO_API_KEY, settings.MIMO_BASE_URL, settings.MIMO_MODEL
)

app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "DeFiSage",
        "version": "1.0.0",
        "status": "running",
        "model": settings.MIMO_MODEL,
        "endpoints": {
            "docs": "/docs",
            "health": "/api/health",
            "analyze": "/api/analyze",
            "batch": "/api/batch-analyze",
            "scaffold": "/api/scaffold",
            "chat": "/api/chat",
            "stats": "/api/stats",
            "agents": "/api/agents",
        },
    }


@app.get("/api/health")
async def health():
    stats = token_tracker.get_stats()
    return {
        "status": "healthy",
        "uptime": stats["uptime_seconds"],
        "tokens_used_today": stats["total_tokens_today"],
        "analyses_completed": stats["analyses_completed"],
        "model": settings.MIMO_MODEL,
    }
