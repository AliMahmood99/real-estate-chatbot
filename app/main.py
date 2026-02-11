"""FastAPI application entry point with lifespan management."""

import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import check_db_connection, create_tables
from app.routers import admin, health, webhook

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown events."""
    # Startup
    logger.info("Starting Real Estate AI Chatbot...")
    db_ok = await check_db_connection()
    if not db_ok:
        logger.warning("Database connection failed — app starting without DB")
    else:
        logger.info("Database connection verified")
        # Create tables if they don't exist
        try:
            await create_tables()
            logger.info("Database tables ensured")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
    yield
    # Shutdown
    logger.info("Shutting down Real Estate AI Chatbot...")


app = FastAPI(
    title="Real Estate AI Chatbot",
    description="Multi-platform AI chatbot for Egyptian real estate companies",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware — allow admin panel
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(webhook.router)
app.include_router(admin.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler returning consistent JSON format."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "data": None,
            "error": "Internal server error",
        },
    )
