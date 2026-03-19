"""FastAPI application for taxi bot REST API."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot.api.routes import shifts, stats, predictions

app = FastAPI(
    title="Taxi Driver Bot API",
    description="REST API for taxi driver bot integrations",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(shifts.router, prefix="/api/v1", tags=["shifts"])
app.include_router(stats.router, prefix="/api/v1", tags=["stats"])
app.include_router(predictions.router, prefix="/api/v1", tags=["predictions"])


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0"}
