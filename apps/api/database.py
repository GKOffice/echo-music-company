from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://echo:echo_dev@localhost:5432/echo"
)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# BUG FIX: Explicit connection pool config for production.
# NullPool for testing (no pooling), AsyncAdaptedQueuePool for prod, default for dev.
if ENVIRONMENT == "testing":
    _pool_kwargs = {"poolclass": NullPool}
elif ENVIRONMENT == "production":
    _pool_kwargs = {
        "poolclass": AsyncAdaptedQueuePool,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "pool_recycle": 1800,  # recycle connections every 30 min
    }
else:
    _pool_kwargs = {}  # SQLAlchemy default for development

engine = create_async_engine(
    DATABASE_URL,
    echo=ENVIRONMENT == "development",
    pool_pre_ping=True,
    **_pool_kwargs,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
