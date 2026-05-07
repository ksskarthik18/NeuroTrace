"""
NeuroTrace Database
SQLite connection and session management using SQLAlchemy async.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, String, Text, Float, Integer, DateTime
from datetime import datetime

from backend.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


class DebugSession(Base):
    """Stores every debug session for evaluation and history."""
    __tablename__ = "debug_sessions"

    id = Column(String, primary_key=True)
    source_code = Column(Text, nullable=False)
    bug_type = Column(String, default="")
    root_cause = Column(Text, default="")
    patched_code = Column(Text, default="")
    diff = Column(Text, default="")
    confidence = Column(Float, default=0.0)
    validation_status = Column(String, default="pending")
    attempts = Column(Integer, default=0)
    latency_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


settings = get_settings()
engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency that yields a database session."""
    async with async_session() as session:
        yield session
