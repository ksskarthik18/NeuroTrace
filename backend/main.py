"""
NeuroTrace - Main Application Entry Point
FastAPI server with CORS, lifespan events, and route mounting.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.database import init_db
from backend.api.routes import router


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup, clean up on shutdown."""
    print(f"[NeuroTrace] v{settings.app_version} starting...")
    print(f"   Environment : {settings.app_env}")
    print(f"   LLM Provider: {settings.llm_provider} ({settings.llm_model})")
    print(f"   Database    : {settings.database_url}")

    await init_db()
    print("   [OK] Database initialized")

    yield

    print("[NeuroTrace] shutting down...")


app = FastAPI(
    title="NeuroTrace",
    description=(
        "Autonomous AI System for Bug Localization, "
        "Root Cause Analysis, and Patch Verification"
    ),
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "name": "NeuroTrace",
        "version": settings.app_version,
        "description": "Autonomous AI Debugging Framework",
        "docs": "/docs",
    }
