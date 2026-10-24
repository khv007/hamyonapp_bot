import logging
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

db_url = settings.DATABASE_URL
engine = None
_session_maker = None

def get_engine(url: str):
    if url.startswith("sqlite"):
        return create_async_engine(url, echo=False)
    return create_async_engine(
        url,
        echo=False,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True
    )

def set_engine_url(url: str):
    global engine, _session_maker
    engine = get_engine(url)
    _session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Initialize default
set_engine_url(db_url)

async def init_db():
    global engine, _session_maker
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.warning(f"Database connection failed ({e}). Falling back to SQLite for local development...")
        fallback_url = "sqlite+aiosqlite:///./maosh_xarajatlar.db"
        set_engine_url(fallback_url)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Fallback SQLite database initialized successfully.")

@asynccontextmanager
async def get_session():
    """Always yields session from the currently active session maker."""
    async with _session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_db():
    async with get_session() as session:
        yield session
