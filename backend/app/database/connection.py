"""
app/database/connection.py
──────────────────────────
Async PostgreSQL connection using SQLAlchemy 2.0 + AsyncPG driver.

Libraries:
  - sqlalchemy[asyncio]: pip install sqlalchemy[asyncio]
  - asyncpg: pip install asyncpg          (async PostgreSQL driver)
  - alembic: pip install alembic          (schema migrations)
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# ── Engine ────────────────────────────────────────────────────────────────────
# pool_size: Number of persistent DB connections to keep open
# max_overflow: Extra connections allowed beyond pool_size under load
# echo: Set True in dev to log all SQL queries
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    echo=(settings.APP_ENV == "development"),
)

# ── Session Factory ───────────────────────────────────────────────────────────
# expire_on_commit=False prevents lazy loading errors after commit
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Base Class ────────────────────────────────────────────────────────────────
# All SQLAlchemy models inherit from this Base
class Base(DeclarativeBase):
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db():
    """
    FastAPI dependency that yields a DB session per request.
    Usage in routes:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()