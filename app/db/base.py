from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL query logging
    pool_size=5,
    max_overflow=10,
    connect_args={"statement_cache_size": 0}
)

async_session_factory = async_sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)

class Base(DeclarativeBase):
    pass

async def get_db_session():
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
