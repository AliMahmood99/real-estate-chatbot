"""Async database engine and session management."""

import logging
import ssl
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

# Build connect args — Railway PostgreSQL may need SSL for external connections
connect_args: dict = {}
db_url = settings.async_database_url

# Remove sslmode from URL if present (asyncpg handles SSL differently)
if "sslmode=" in db_url or "ssl=" in db_url:
    # Strip sslmode/ssl params from URL — we handle SSL via connect_args
    import re
    db_url = re.sub(r'[\?&](sslmode|ssl)=[^&]*', '', db_url)
    # Clean up leftover ? or &
    db_url = db_url.replace('?&', '?').rstrip('?')

engine = create_async_engine(
    db_url,
    echo=settings.APP_ENV == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args=connect_args,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that provides an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connection() -> bool:
    """Check if database connection is healthy."""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def create_tables() -> None:
    """Create all tables (for development only)."""
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
