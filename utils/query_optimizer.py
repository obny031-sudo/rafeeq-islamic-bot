"""
Query Optimization Service for Rafeeq Enterprise Islamic OS.
Optimizes database queries for large dataset performance.
"""

import logging
from typing import Optional, List, Dict, Any, Type
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc, text
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from utils.logger import get_logger

logger = get_logger("rafeeq.query_optimizer")


class QueryOptimizer:
    """
    Query optimization service for large dataset performance.
    Provides pagination, caching, and query optimization strategies.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize query optimizer.
        
        Args:
            session: Database session
        """
        self.session = session
        self._query_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def execute_paginated_query(
        self,
        query: Select,
        page: int = 1,
        page_size: int = 20,
        max_page_size: int = 100
    ) -> Dict[str, Any]:
        """
        Execute a paginated query with optimized performance.
        
        Args:
            query: SQLAlchemy Select query
            page: Page number (1-indexed)
            page_size: Items per page
            max_page_size: Maximum allowed page size
        
        Returns:
            Dictionary with results and pagination metadata
        """
        try:
            # Limit page size to prevent excessive queries
            page_size = min(page_size, max_page_size)
            
            # Calculate offset
            offset = (page - 1) * page_size
            
            # Get total count (optimized with separate query)
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.session.execute(count_query)
            total_count = total_result.scalar() or 0
            
            # Apply pagination
            paginated_query = query.offset(offset).limit(page_size)
            
            # Execute paginated query
            result = await self.session.execute(paginated_query)
            items = list(result.scalars().all())
            
            # Calculate pagination metadata
            total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 0
            
            return {
                "items": items,
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "has_next": page < total_pages,
                    "has_prev": page > 1
                }
            }
            
        except Exception as e:
            logger.error(f"Error executing paginated query: {e}")
            return {
                "items": [],
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_count": 0,
                    "total_pages": 0,
                    "has_next": False,
                    "has_prev": False
                }
            }
    
    async def execute_batch_query(
        self,
        query: Select,
        batch_size: int = 100,
        callback: callable = None
    ) -> List[Any]:
        """
        Execute a query in batches for large datasets.
        
        Args:
            query: SQLAlchemy Select query
            batch_size: Number of items per batch
            callback: Optional callback function for each batch
        
        Returns:
            List of all results
        """
        try:
            all_results = []
            offset = 0
            
            while True:
                # Get batch
                batch_query = query.offset(offset).limit(batch_size)
                result = await self.session.execute(batch_query)
                batch_items = list(result.scalars().all())
                
                if not batch_items:
                    break
                
                # Process batch with callback if provided
                if callback:
                    await callback(batch_items)
                
                all_results.extend(batch_items)
                offset += batch_size
                
                # If we got fewer items than batch_size, we're done
                if len(batch_items) < batch_size:
                    break
            
            logger.info(f"Batch query completed: {len(all_results)} total items")
            return all_results
            
        except Exception as e:
            logger.error(f"Error executing batch query: {e}")
            return []
    
    async def execute_cached_query(
        self,
        cache_key: str,
        query: Select,
        ttl: int = 300
    ) -> Optional[List[Any]]:
        """
        Execute a query with caching for frequently accessed data.
        
        Args:
            cache_key: Unique cache key
            query: SQLAlchemy Select query
            ttl: Cache time-to-live in seconds
        
        Returns:
            Query results or None
        """
        try:
            # Check cache
            if cache_key in self._query_cache:
                cached_data, cached_time = self._query_cache[cache_key]
                if (datetime.now(timezone.utc) - cached_time).total_seconds() < ttl:
                    logger.debug(f"Cache hit for key: {cache_key}")
                    return cached_data
            
            # Execute query
            result = await self.session.execute(query)
            items = list(result.scalars().all())
            
            # Cache results
            self._query_cache[cache_key] = (items, datetime.now(timezone.utc))
            
            logger.debug(f"Cached query results for key: {cache_key}")
            return items
            
        except Exception as e:
            logger.error(f"Error executing cached query: {e}")
            return None
    
    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear query cache.
        
        Args:
            pattern: Optional pattern to match cache keys
        
        Returns:
            Number of cache entries cleared
        """
        if pattern:
            keys_to_remove = [k for k in self._query_cache.keys() if pattern in k]
        else:
            keys_to_remove = list(self._query_cache.keys())
        
        for key in keys_to_remove:
            del self._query_cache[key]
        
        logger.info(f"Cleared {len(keys_to_remove)} cache entries")
        return len(keys_to_remove)
    
    def optimize_query_with_indexes(
        self,
        query: Select,
        indexed_columns: List[str]
    ) -> Select:
        """
        Optimize query by ensuring indexed columns are used effectively.
        
        Args:
            query: SQLAlchemy Select query
            indexed_columns: List of indexed column names
        
        Returns:
            Optimized query
        """
        # This is a placeholder for query optimization logic
        # In a real implementation, this would analyze the query
        # and suggest or apply optimizations
        
        logger.debug(f"Optimizing query with indexed columns: {indexed_columns}")
        return query
    
    async def get_query_performance_stats(self) -> Dict[str, Any]:
        """
        Get query performance statistics.
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            "cache_size": len(self._query_cache),
            "cache_ttl": self._cache_ttl,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class IndexOptimizer:
    """
    Database index optimization recommendations.
    """
    
    @staticmethod
    def get_index_recommendations() -> List[Dict[str, Any]]:
        """
        Get recommended indexes for the Rafeeq database.
        
        Returns:
            List of index recommendations
        """
        return [
            {
                "table": "user_activity_logs",
                "columns": ["user_id", "content_node_id"],
                "type": "composite",
                "reason": "Frequent queries for user seen content"
            },
            {
                "table": "user_activity_logs",
                "columns": ["user_id", "viewed_at"],
                "type": "composite",
                "reason": "User activity timeline queries"
            },
            {
                "table": "content_nodes",
                "columns": ["content_type", "engagement_score"],
                "type": "composite",
                "reason": "Content type filtering with sorting"
            },
            {
                "table": "content_edges",
                "columns": ["source_node_id", "target_node_id"],
                "type": "composite",
                "reason": "Knowledge graph traversal"
            },
            {
                "table": "content_edges",
                "columns": ["edge_type", "weight"],
                "type": "composite",
                "reason": "Edge type filtering with weight sorting"
            },
            {
                "table": "content_themes",
                "columns": ["theme_id", "content_node_id"],
                "type": "composite",
                "reason": "Theme-based content queries"
            },
            {
                "table": "users",
                "columns": ["last_active_date"],
                "type": "single",
                "reason": "DAU calculations"
            },
            {
                "table": "users",
                "columns": ["role"],
                "type": "single",
                "reason": "RBAC filtering"
            }
        ]
    
    @staticmethod
    def get_index_creation_sql() -> List[str]:
        """
        Get SQL statements to create recommended indexes.
        
        Returns:
            List of SQL CREATE INDEX statements
        """
        recommendations = IndexOptimizer.get_index_recommendations()
        sql_statements = []
        
        for rec in recommendations:
            table = rec["table"]
            columns = rec["columns"]
            index_name = f"idx_{table}_{'_'.join(columns)}"
            
            if rec["type"] == "composite":
                col_list = ", ".join(columns)
                sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({col_list});"
            else:
                sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table} ({columns[0]});"
            
            sql_statements.append(sql)
        
        return sql_statements


class QueryBuilder:
    """
    Helper class for building optimized queries.
    """
    
    @staticmethod
    def build_exclude_seen_query(
        base_query: Select,
        seen_ids: List[int],
        id_column: str = "id"
    ) -> Select:
        """
        Build a query that excludes seen content IDs.
        
        Args:
            base_query: Base SQLAlchemy query
            seen_ids: List of IDs to exclude
            id_column: Column name for ID
        
        Returns:
            Modified query with exclusion
        """
        if seen_ids:
            # Use NOT IN with subquery for better performance with large lists
            return base_query.where(
                getattr(base_query.columns, id_column).notin_(seen_ids)
            )
        return base_query
    
    @staticmethod
    def build_date_range_query(
        base_query: Select,
        date_column: str,
        start_date: datetime,
        end_date: datetime
    ) -> Select:
        """
        Build a query with date range filtering.
        
        Args:
            base_query: Base SQLAlchemy query
            date_column: Column name for date
            start_date: Start date
            end_date: End date
        
        Returns:
            Modified query with date range
        """
        return base_query.where(
            and_(
                getattr(base_query.columns, date_column) >= start_date,
                getattr(base_query.columns, date_column) <= end_date
            )
        )
    
    @staticmethod
    def build_theme_filter_query(
        base_query: Select,
        theme_ids: List[int]
    ) -> Select:
        """
        Build a query that filters by themes.
        
        Args:
            base_query: Base SQLAlchemy query
            theme_ids: List of theme IDs to filter by
        
        Returns:
            Modified query with theme filter
        """
        if theme_ids:
            # Join with content_themes table
            return base_query.join(
                ContentTheme,
                base_query.columns.id == ContentTheme.content_node_id
            ).where(
                ContentTheme.theme_id.in_(theme_ids)
            )
        return base_query


class BulkOperationOptimizer:
    """
    Optimizer for bulk database operations.
    """
    
    @staticmethod
    async def bulk_insert(
        session: AsyncSession,
        model: Type,
        items: List[Any],
        batch_size: int = 1000
    ) -> int:
        """
        Perform bulk insert with batching for large datasets.
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            items: List of items to insert
            batch_size: Number of items per batch
        
        Returns:
            Number of items inserted
        """
        try:
            total_inserted = 0
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                session.add_all(batch)
                await session.flush()
                total_inserted += len(batch)
            
            await session.commit()
            logger.info(f"Bulk insert completed: {total_inserted} items")
            return total_inserted
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in bulk insert: {e}")
            return 0
    
    @staticmethod
    async def bulk_update(
        session: AsyncSession,
        model: Type,
        items: List[Any],
        update_fields: List[str],
        batch_size: int = 1000
    ) -> int:
        """
        Perform bulk update with batching.
        
        Args:
            session: Database session
            model: SQLAlchemy model class
            items: List of items to update
            update_fields: List of field names to update
            batch_size: Number of items per batch
        
        Returns:
            Number of items updated
        """
        try:
            total_updated = 0
            
            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]
                
                for item in batch:
                    # Update specified fields
                    for field in update_fields:
                        if hasattr(item, field):
                            setattr(item, field, getattr(item, field))
                
                await session.flush()
                total_updated += len(batch)
            
            await session.commit()
            logger.info(f"Bulk update completed: {total_updated} items")
            return total_updated
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error in bulk update: {e}")
            return 0


# Global query optimizer instance (initialized per session)
def get_query_optimizer(session: AsyncSession) -> QueryOptimizer:
    """
    Get a query optimizer instance for the given session.
    
    Args:
        session: Database session
    
    Returns:
        QueryOptimizer instance
    """
    return QueryOptimizer(session)
