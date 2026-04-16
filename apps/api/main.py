"""
FastAPI main application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import analyze, insurers, parse, report


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: nothing needed — Alembic handles migrations separately
    yield
    # Shutdown


app = FastAPI(
    title="ClaimSmart Intelligence API",
    description="OCR, rule engine, and GPT-4o powered insurance claim analysis for India.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — only allow requests from Next.js BFF (internal)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://claimsmart.in",  # Production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(analyze.router)
app.include_router(insurers.router)
app.include_router(parse.router)
app.include_router(report.router)


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
