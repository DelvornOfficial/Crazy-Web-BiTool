import os
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

logger = logging.getLogger("nextlevelcheat.database")

Base = declarative_base()


class AsyncDatabaseManager:
    def __init__(self):
        self.engine = None
        self._sessionmaker = None
        self.active_url = None

    def setup(self, url: str):
        self.active_url = url
        connect_args = {}
        if url.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        else:
            # PostgreSQL High-Performance Tuning: Server-Side Prepared Statements
            connect_args["prepared_statement_cache_size"] = 500

        self.engine = create_async_engine(
            url,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=20,
            max_overflow=40,
            pool_recycle=1800,
            connect_args=connect_args,
        )
        self._sessionmaker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    def session(self) -> AsyncSession:
        if self._sessionmaker is None:
            self.setup(settings.DATABASE_URL)
        return self._sessionmaker()

    def __call__(self) -> AsyncSession:
        return self.session()


db_manager = AsyncDatabaseManager()
db_manager.setup(settings.DATABASE_URL)


def async_session() -> AsyncSession:
    return db_manager.session()


async def init_db():
    """
    Initializes database tables on PostgreSQL.
    If PostgreSQL fails and FALLBACK_TO_SQLITE is True,
    seamlessly shifts to SQLite so local developers can run immediately.
    """
    from app.models import Admin, AppRelease, DownloadLog, AuditLog  # noqa

    try:
        masked_url = settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
        logger.info(f"Connecting to database: {masked_url}...")
        async with db_manager.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully via primary connection.")
    except Exception as e:
        if settings.FALLBACK_TO_SQLITE:
            logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to local SQLite database.")
            os.makedirs("./data", exist_ok=True)
            sqlite_url = "sqlite+aiosqlite:///./data/local.db"
            db_manager.setup(sqlite_url)
            async with db_manager.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Local SQLite database initialized at ./data/local.db")
        else:
            logger.error(f"Database initialization failed: {e}")
            raise e


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Standard FastAPI Dependency Provider for SQLAlchemy AsyncSession.
    Automatically rolls back on errors and closes session on exit.
    """
    async with db_manager.session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
