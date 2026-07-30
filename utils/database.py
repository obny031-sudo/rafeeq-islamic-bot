from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from config.database import AsyncSessionLocal

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
