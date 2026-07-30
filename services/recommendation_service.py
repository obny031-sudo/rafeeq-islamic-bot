"""
Recommendation Service for Rafeeq Enterprise Islamic OS.
Analyzes user activity to suggest related content.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from repositories import ActivityTrackerRepository
from models.knowledge_graph import ContentNode, ContentEdge, EdgeType, Theme, ContentTheme
from utils.logger import get_logger

logger = get_logger("rafeeq.recommendation")


class RecommendationService:
    """
    Recommendation service that analyzes user activity to suggest content.
    Implements theme-based and graph-based recommendations.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize recommendation service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.activity_tracker = ActivityTrackerRepository(session)
    
    async def get_theme_recommendations(
        self,
        user_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get content recommendations based on user's favorite themes.
        
        Args:
            user_id: User ID
            limit: Number of recommendations
        
        Returns:
            List of recommended content
        """
        try:
            # Get user's most engaged themes
            user_themes = await self.activity_tracker.get_user_themes(user_id, limit=3)
            
            if not user_themes:
                return []
            
            # Get content from top themes that user hasn't seen
            seen_ids = await self.activity_tracker.get_seen_content_ids(user_id)
            
            recommendations = []
            
            for theme_data in user_themes:
                theme = theme_data["theme"]
                
                # Get content for this theme
                query = select(ContentNode).join(
                    ContentTheme,
                    ContentNode.id == ContentTheme.content_node_id
                ).where(
                    and_(
                        ContentTheme.theme_id == theme.id,
                        ContentNode.id.notin_(seen_ids) if seen_ids else True
                    )
                ).order_by(ContentNode.engagement_score.desc()).limit(limit)
                
                result = await self.session.execute(query)
                content_list = list(result.scalars().all())
                
                for content in content_list:
                    recommendations.append({
                        "content_id": content.id,
                        "content_type": content.content_type,
                        "title": content.title,
                        "source_id": content.source_id,
                        "reason": f"Based on your interest in {theme.name}",
                        "theme": theme.name,
                        "engagement_score": content.engagement_score
                    })
            
            # Sort by engagement score and limit
            recommendations.sort(key=lambda x: x["engagement_score"], reverse=True)
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting theme recommendations for user {user_id}: {e}")
            return []
    
    async def get_graph_recommendations(
        self,
        user_id: int,
        content_node_id: int,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get content recommendations based on knowledge graph relationships.
        
        Args:
            user_id: User ID
            content_node_id: Content node to find related content for
            limit: Number of recommendations
        
        Returns:
            List of recommended content
        """
        try:
            # Get related content from knowledge graph
            query = select(ContentEdge, ContentNode).join(
                ContentNode,
                ContentEdge.target_node_id == ContentNode.id
            ).where(
                and_(
                    ContentEdge.source_node_id == content_node_id,
                    ContentEdge.weight >= 0.5  # Only strong relationships
                )
            ).order_by(desc(ContentEdge.weight)).limit(limit)
            
            result = await self.session.execute(query)
            related_content = []
            
            for edge, content in result:
                related_content.append({
                    "content": content,
                    "relationship_type": edge.edge_type,
                    "weight": edge.weight,
                    "description": edge.description
                })
            
            # Filter out seen content
            seen_ids = await self.activity_tracker.get_seen_content_ids(user_id)
            recommendations = [
                {
                    "content_id": item["content"].id,
                    "content_type": item["content"].content_type,
                    "title": item["content"].title,
                    "source_id": item["content"].source_id,
                    "reason": f"Related by {item['relationship_type']} (strength: {item['weight']:.2f})",
                    "relationship": item["relationship_type"],
                    "weight": item["weight"]
                }
                for item in related_content
                if item["content"].id not in seen_ids
            ]
            
            return recommendations[:limit]
            
        except Exception as e:
            logger.error(f"Error getting graph recommendations for user {user_id}: {e}")
            return []
    
    async def get_trending_content(
        self,
        user_id: int,
        content_type: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Get trending content that user hasn't seen.
        
        Args:
            user_id: User ID
            content_type: Filter by content type (optional)
            limit: Number of recommendations
        
        Returns:
            List of trending content
        """
        try:
            # Get seen content IDs
            seen_ids = await self.activity_tracker.get_seen_content_ids(user_id, content_type)
            
            # Get trending content (high engagement, recent views)
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=7)
            
            query = select(ContentNode).where(
                and_(
                    ContentNode.id.notin_(seen_ids) if seen_ids else True,
                    ContentNode.updated_at >= cutoff_date
                )
            )
            
            if content_type:
                query = query.where(ContentNode.content_type == content_type)
            
            query = query.order_by(
                desc(ContentNode.engagement_score),
                desc(ContentNode.view_count)
            ).limit(limit)
            
            result = await self.session.execute(query)
            content_list = list(result.scalars().all())
            
            recommendations = []
            for content in content_list:
                recommendations.append({
                    "content_id": content.id,
                    "content_type": content.content_type,
                    "title": content.title,
                    "source_id": content.source_id,
                    "reason": "Trending content",
                    "engagement_score": content.engagement_score,
                    "view_count": content.view_count
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting trending content for user {user_id}: {e}")
            return []
    
    async def get_personalized_recommendations(
        self,
        user_id: int,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get personalized recommendations combining multiple strategies.
        
        Args:
            user_id: User ID
            limit: Total number of recommendations
        
        Returns:
            List of personalized recommendations
        """
        try:
            # Get recommendations from different strategies
            theme_recs = await self.get_theme_recommendations(user_id, limit=3)
            trending_recs = await self.get_trending_content(user_id, limit=3)
            
            # Combine and deduplicate
            all_recs = theme_recs + trending_recs
            seen_content_ids = set()
            
            unique_recs = []
            for rec in all_recs:
                if rec["content_id"] not in seen_content_ids:
                    seen_content_ids.add(rec["content_id"])
                    unique_recs.append(rec)
            
            return unique_recs[:limit]
            
        except Exception as e:
            logger.error(f"Error getting personalized recommendations for user {user_id}: {e}")
            return []
    
    async def should_notify_theme(
        self,
        user_id: int,
        theme_id: int
    ) -> bool:
        """
        Determine if user should be notified about new content in a theme.
        
        Args:
            user_id: User ID
            theme_id: Theme ID
        
        Returns:
            True if notification should be sent
        """
        try:
            # Check if user has consumed 3+ pieces of content in this theme
            user_themes = await self.activity_tracker.get_user_themes(user_id, limit=10)
            
            for theme_data in user_themes:
                if theme_data["theme"].id == theme_id:
                    engagement_count = theme_data["engagement_count"]
                    return engagement_count >= 3
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking theme notification for user {user_id}: {e}")
            return False
    
    async def get_notification_settings(
        self,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Get recommended notification settings for user.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary with notification settings
        """
        try:
            # Get user's top themes
            user_themes = await self.activity_tracker.get_user_themes(user_id, limit=5)
            
            notification_settings = {
                "user_id": user_id,
                "enabled_themes": [],
                "recommended_frequency": "daily"
            }
            
            # Recommend notifications for themes with high engagement
            for theme_data in user_themes:
                if theme_data["engagement_count"] >= 3:
                    notification_settings["enabled_themes"].append({
                        "theme_id": theme_data["theme"].id,
                        "theme_name": theme_data["theme"].name,
                        "engagement_count": theme_data["engagement_count"]
                    })
            
            # Adjust frequency based on overall activity
            activity_stats = await self.activity_tracker.get_user_activity_stats(user_id)
            total_activities = activity_stats.get("total_activities", 0)
            
            if total_activities > 50:
                notification_settings["recommended_frequency"] = "daily"
            elif total_activities > 20:
                notification_settings["recommended_frequency"] = "weekly"
            else:
                notification_settings["recommended_frequency"] = "bi-weekly"
            
            return notification_settings
            
        except Exception as e:
            logger.error(f"Error getting notification settings for user {user_id}: {e}")
            return {}
    
    async def track_recommendation_click(
        self,
        user_id: int,
        content_id: int,
        recommendation_type: str
    ) -> bool:
        """
        Track when user clicks on a recommendation.
        
        Args:
            user_id: User ID
            content_id: Content ID
            recommendation_type: Type of recommendation (theme, graph, trending)
        
        Returns:
            True if successful
        """
        try:
            # Log the activity with recommendation context
            await self.activity_tracker.log_activity(
                user_id=user_id,
                content_node_id=content_id,
                content_type="recommendation",
                source_id=f"rec_{recommendation_type}",
                context={"recommendation_type": recommendation_type}
            )
            
            logger.info(f"Tracked recommendation click: user={user_id}, content={content_id}, type={recommendation_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking recommendation click: {e}")
            return False
