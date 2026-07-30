"""
Base repository class for database operations.
Provides async CRUD operations with metrics collection.
"""

import logging
from typing import Optional, List, Type, TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload

from models.base import Base

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic base repository for async database operations.
    Provides common CRUD methods with logging and error handling.
    """
    
    def __init__(self, model: Type[T], session: AsyncSession):
        """
        Initialize repository.
        
        Args:
            model: SQLAlchemy model class
            session: Async database session
        """
        self.model = model
        self.session = session
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """
        Get entity by ID.
        
        Args:
            id: Entity ID
        
        Returns:
            Entity instance or None
        """
        try:
            result = await self.session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting {self.model.__name__} by id {id}: {e}")
            return None
    
    async def get_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[T]:
        """
        Get all entities with optional pagination.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
        
        Returns:
            List of entity instances
        """
        try:
            query = select(self.model)
            if limit:
                query = query.limit(limit)
            if offset:
                query = query.offset(offset)
            
            result = await self.session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting all {self.model.__name__}: {e}")
            return []
    
    async def create(self, entity: T) -> T:
        """
        Create new entity.
        
        Args:
            entity: Entity instance
        
        Returns:
            Created entity instance
        """
        try:
            self.session.add(entity)
            await self.session.flush()
            await self.session.refresh(entity)
            logger.info(f"Created {self.model.__name__} with id {entity.id}")
            return entity
        except Exception as e:
            logger.error(f"Error creating {self.model.__name__}: {e}")
            raise
    
    async def update(self, entity: T) -> T:
        """
        Update existing entity.
        
        Args:
            entity: Entity instance with updated fields
        
        Returns:
            Updated entity instance
        """
        try:
            await self.session.flush()
            await self.session.refresh(entity)
            logger.info(f"Updated {self.model.__name__} with id {entity.id}")
            return entity
        except Exception as e:
            logger.error(f"Error updating {self.model.__name__}: {e}")
            raise
    
    async def delete(self, entity: T) -> bool:
        """
        Delete entity.
        
        Args:
            entity: Entity instance
        
        Returns:
            True if successful, False otherwise
        """
        try:
            await self.session.delete(entity)
            await self.session.flush()
            logger.info(f"Deleted {self.model.__name__} with id {entity.id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {self.model.__name__}: {e}")
            return False
    
    async def count(self) -> int:
        """
        Count all entities.
        
        Returns:
            Number of entities
        """
        try:
            result = await self.session.execute(
                select(func.count()).select_from(self.model)
            )
            return result.scalar()
        except Exception as e:
            logger.error(f"Error counting {self.model.__name__}: {e}")
            return 0
    
    async def exists(self, id: int) -> bool:
        """
        Check if entity exists by ID.
        
        Args:
            id: Entity ID
        
        Returns:
            True if exists, False otherwise
        """
        try:
            result = await self.session.execute(
                select(func.count()).select_from(self.model).where(self.model.id == id)
            )
            return result.scalar() > 0
        except Exception as e:
            logger.error(f"Error checking existence of {self.model.__name__} with id {id}: {e}")
            return False
    
    async def bulk_create(self, entities: List[T]) -> List[T]:
        """
        Create multiple entities in bulk.
        
        Args:
            entities: List of entity instances
        
        Returns:
            List of created entity instances
        """
        try:
            self.session.add_all(entities)
            await self.session.flush()
            for entity in entities:
                await self.session.refresh(entity)
            logger.info(f"Bulk created {len(entities)} {self.model.__name__} instances")
            return entities
        except Exception as e:
            logger.error(f"Error bulk creating {self.model.__name__}: {e}")
            raise
