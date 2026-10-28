"""Main FastAPI application entry point for OrchardIQ."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.ask import router as ask_router
from src.api.routes.sessions import router as sessions_router
from src.api.routes.trace import router as trace_router
from src.api.routes.catalog import router as catalog_router
from src.api.routes.forecast import router as forecast_router
from src.api.routes.quality import router as quality_router
from src.api.routes.audit import router as audit_router
from src.api.routes.health import router as health_router
from src.api.routes.metrics import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup initialization and graceful shutdown."""
    # Warmup subsystems
    yield


app = FastAPI(
    title="OrchardIQ Enterprise Analytics API",
    description="Agentic Enterprise Analytics Platform for Orchard Inc. (Data Warehouse, RAG, Governance, ML)",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure permissive CORS for Next.js frontend and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(health_router)
app.include_router(ask_router)
app.include_router(sessions_router)
app.include_router(trace_router)
app.include_router(catalog_router)
app.include_router(forecast_router)
app.include_router(quality_router)
app.include_router(audit_router)
app.include_router(metrics_router)


@app.get("/")
def root():
    return {
        "platform": "OrchardIQ",
        "tagline": "Agentic Enterprise Analytics & Lakehouse Intelligence",
        "version": "0.1.0",
        "docs_url": "/docs",
        "health_url": "/health",
    }
