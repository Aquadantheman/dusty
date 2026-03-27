"""
Dusty API - Vintage & Antique Shop Finder
FastAPI backend for shop discovery and sale tracking
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from core.config import settings
from core.database import init_db
from routers import shops, sales, discovery, neighborhoods


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    await init_db()
    print("🏪 Dusty API starting up...")
    yield
    # Shutdown
    print("👋 Dusty API shutting down...")


app = FastAPI(
    title="Dusty API",
    description="Discover vintage, antique, and thrift shops with sale tracking",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(shops.router, prefix="/api/v1", tags=["shops"])
app.include_router(sales.router, prefix="/api/v1", tags=["sales"])
app.include_router(discovery.router, prefix="/api/v1", tags=["discovery"])
app.include_router(neighborhoods.router, prefix="/api/v1", tags=["neighborhoods"])


@app.get("/")
async def root():
    return {
        "name": "Dusty API",
        "version": "0.1.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
