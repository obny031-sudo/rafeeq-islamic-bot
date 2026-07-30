"""
Smart Content Fetcher for Rafeeq Enterprise Islamic OS.
Refactored random fetchers to exclude seen content (No-Repeat experience).
"""

import logging
import random
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from repositories import ActivityTrackerRepository
from models.knowledge_graph import ContentNode, ContentType
from utils.logger import get_logger

logger = get_logger("rafeeq.content_fetcher")


class SmartContentFetcher:
    """
    Smart content fetcher that implements "No-Repeat" experience.
    Excludes content that users have already seen.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize content fetcher.
        
        Args:
            session: Database session
        """
        self.session = session
        self.activity_tracker = ActivityTrackerRepository(session)
    
    async def get_random_adhkar(
        self,
        user_id: int,
        category: Optional[str] = None,
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get random Adhkar that user hasn't seen.
        
        Args:
            user_id: User ID
            category: Adhkar category (optional)
            limit: Number of results
        
        Returns:
            List of Adhkar dictionaries
        """
        try:
            # Get unseen content
            unseen_content = await self.activity_tracker.get_unseen_content(
                user_id=user_id,
                content_type=ContentType.ADHKAR,
                limit=limit * 3
            )
            
            # Filter by category if specified
            if category:
                unseen_content = [
                    content for content in unseen_content
                    if content.tags and category in content.tags
                ]
            
            # Randomly select from unseen content
            selected = random.sample(unseen_content, min(limit, len(unseen_content)))
            
            # Log the activity
            for content in selected:
                await self.activity_tracker.log_activity(
                    user_id=user_id,
                    content_node_id=content.id,
                    content_type=content.content_type,
                    source_id=content.source_id
                )
            
            # Format results
            results = []
            for content in selected:
                results.append({
                    "arabic": content.text_arabic,
                    "transliteration": content.text_transliteration,
                    "translation": content.text_translation,
                    "reference": content.reference,
                    "source_id": content.source_id
                })
            
            logger.info(f"Fetched {len(results)} unseen Adhkar for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching random Adhkar for user {user_id}: {e}")
            # Fallback to static data if no content in database
            return self._get_fallback_adhkar(category, limit)
    
    async def get_random_quran_ayah(
        self,
        user_id: int,
        surah_number: Optional[int] = None,
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get random Quran Ayah that user hasn't seen.
        
        Args:
            user_id: User ID
            surah_number: Specific Surah (optional)
            limit: Number of results
        
        Returns:
            List of Quran Ayah dictionaries
        """
        try:
            # Get unseen Quran content
            unseen_content = await self.activity_tracker.get_unseen_content(
                user_id=user_id,
                content_type=ContentType.QURAN_AYAH,
                limit=limit * 3
            )
            
            # Filter by Surah if specified
            if surah_number:
                unseen_content = [
                    content for content in unseen_content
                    if content.source_id and f"quran_{surah_number}:" in content.source_id
                ]
            
            # Randomly select
            selected = random.sample(unseen_content, min(limit, len(unseen_content)))
            
            # Log activity
            for content in selected:
                await self.activity_tracker.log_activity(
                    user_id=user_id,
                    content_node_id=content.id,
                    content_type=content.content_type,
                    source_id=content.source_id
                )
            
            # Format results
            results = []
            for content in selected:
                results.append({
                    "arabic": content.text_arabic,
                    "translation": content.text_translation,
                    "source_id": content.source_id,
                    "reference": content.reference
                })
            
            logger.info(f"Fetched {len(results)} unseen Quran Ayahs for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching random Quran Ayah for user {user_id}: {e}")
            return []
    
    async def get_random_hadith(
        self,
        user_id: int,
        collection: Optional[str] = None,
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Get random Hadith that user hasn't seen.
        
        Args:
            user_id: User ID
            collection: Specific collection (optional)
            limit: Number of results
        
        Returns:
            List of Hadith dictionaries
        """
        try:
            # Get unseen Hadith content
            unseen_content = await self.activity_tracker.get_unseen_content(
                user_id=user_id,
                content_type=ContentType.HADITH,
                limit=limit * 3
            )
            
            # Filter by collection if specified
            if collection:
                unseen_content = [
                    content for content in unseen_content
                    if content.source_name and collection.lower() in content.source_name.lower()
                ]
            
            # Randomly select
            selected = random.sample(unseen_content, min(limit, len(unseen_content)))
            
            # Log activity
            for content in selected:
                await self.activity_tracker.log_activity(
                    user_id=user_id,
                    content_node_id=content.id,
                    content_type=content.content_type,
                    source_id=content.source_id
                )
            
            # Format results
            results = []
            for content in selected:
                results.append({
                    "arabic": content.text_arabic,
                    "translation": content.text_translation,
                    "source": content.source_name,
                    "reference": content.reference
                })
            
            logger.info(f"Fetched {len(results)} unseen Hadiths for user {user_id}")
            return results
            
        except Exception as e:
            logger.error(f"Error fetching random Hadith for user {user_id}: {e}")
            return []
    
    def _get_fallback_adhkar(self, category: Optional[str], limit: int) -> List[Dict[str, Any]]:
        """
        Fallback Adhkar data when database is empty.
        
        Args:
            category: Adhkar category
            limit: Number of results
        
        Returns:
            List of Adhkar dictionaries
        """
        fallback_data = {
            "morning": [
                {
                    "arabic": "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ",
                    "transliteration": "Asbahna wa asbahal mulku lillah",
                    "translation": "We have entered the morning and the dominion belongs to Allah",
                    "reference": "Muslim 271"
                }
            ],
            "evening": [
                {
                    "arabic": "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ",
                    "transliteration": "Amsayna wa amsal mulku lillah",
                    "translation": "We have entered the evening and the dominion belongs to Allah",
                    "reference": "Muslim 271"
                }
            ],
            "general": [
                {
                    "arabic": "سُبْحَانَ اللهِ",
                    "transliteration": "SubhanAllah",
                    "translation": "Glory be to Allah",
                    "reference": "Muslim 2692"
                }
            ]
        }
        
        if category and category in fallback_data:
            return random.sample(fallback_data[category], min(limit, len(fallback_data[category])))
        
        # Return random from all categories
        all_adhkar = []
        for cat_data in fallback_data.values():
            all_adhkar.extend(cat_data)
        
        return random.sample(all_adhkar, min(limit, len(all_adhkar)))
    
    async def reset_user_seen_content(
        self,
        user_id: int,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Reset seen content for a user (allow them to see content again).
        
        Args:
            user_id: User ID
            content_type: Specific content type to reset (optional)
        
        Returns:
            True if successful
        """
        try:
            # Clear old activities
            await self.activity_tracker.clear_old_activities(
                older_than_days=0,  # Clear all
                user_id=user_id
            )
            logger.info(f"Reset seen content for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting seen content for user {user_id}: {e}")
            return False
    
    async def get_user_content_progress(
        self,
        user_id: int,
        content_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user's content consumption progress.
        
        Args:
            user_id: User ID
            content_type: Specific content type (optional)
        
        Returns:
            Progress statistics
        """
        try:
            seen_ids = await self.activity_tracker.get_seen_content_ids(user_id, content_type)
            total_content = await self.activity_tracker.count()  # Total available content
            
            progress_percentage = 0
            if total_content > 0:
                progress_percentage = round((len(seen_ids) / total_content) * 100, 2)
            
            return {
                "user_id": user_id,
                "content_type": content_type,
                "seen_count": len(seen_ids),
                "total_available": total_content,
                "progress_percentage": progress_percentage,
                "remaining": total_content - len(seen_ids)
            }
        except Exception as e:
            logger.error(f"Error getting content progress for user {user_id}: {e}")
            return {}
