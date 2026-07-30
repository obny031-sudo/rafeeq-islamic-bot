"""
ViewStrategy Pattern for Rafeeq Enterprise Islamic OS.
Implements content rotation between different views/interpretations.
"""

import logging
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass

from models.knowledge_graph import ContentNode, Tafsir
from utils.logger import get_logger

logger = get_logger("rafeeq.view_strategy")


class ViewType(str, Enum):
    """Types of content views"""
    TAFSIR_IBN_KATHIR = "tafsir_ibn_kathir"
    TAFSIR_AL_SADI = "tafsir_al_sadi"
    TAFSIR_AL_TABARI = "tafsir_al_tabari"
    ARABIC_ONLY = "arabic_only"
    TRANSLATION_ONLY = "translation_only"
    ARABIC_WITH_TRANSLATION = "arabic_with_translation"
    TRANSLITERATION_WITH_TRANSLATION = "transliteration_with_translation"


@dataclass
class ContentView:
    """Single view of content"""
    view_type: ViewType
    content: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "view_type": self.view_type.value,
            "content": self.content,
            "metadata": self.metadata
        }


class ViewStrategy(ABC):
    """Abstract base class for view strategies"""
    
    @abstractmethod
    async def get_view(self, content_node: ContentNode) -> ContentView:
        """
        Get a specific view of the content.
        
        Args:
            content_node: Content node to view
        
        Returns:
            ContentView with the specific view
        """
        pass
    
    @abstractmethod
    def get_available_views(self, content_node: ContentNode) -> List[ViewType]:
        """
        Get available view types for this content.
        
        Args:
            content_node: Content node
        
        Returns:
            List of available ViewTypes
        """
        pass


class TafsirViewStrategy(ViewStrategy):
    """Strategy for Tafsir (Quran interpretation) views"""
    
    def __init__(self, session):
        """
        Initialize Tafsir view strategy.
        
        Args:
            session: Database session
        """
        self.session = session
        self._current_scholar_index = 0
        self._scholars = [
            ViewType.TAFSIR_IBN_KATHIR,
            ViewType.TAFSIR_AL_SADI,
            ViewType.TAFSIR_AL_TABARI
        ]
    
    async def get_view(self, content_node: ContentNode) -> ContentView:
        """Get current Tafsir view with rotation"""
        # In a real implementation, this would fetch from the Tafsir table
        # For now, we'll simulate rotation
        
        current_scholar = self._scholars[self._current_scholar_index]
        
        # Rotate to next scholar for next call
        self._current_scholar_index = (self._current_scholar_index + 1) % len(self._scholars)
        
        # Simulate fetching Tafsir content
        tafsir_content = self._get_tafsir_content(content_node, current_scholar)
        
        return ContentView(
            view_type=current_scholar,
            content=tafsir_content,
            metadata={
                "scholar": current_scholar.value.replace("tafsir_", "").replace("_", " ").title(),
                "source_id": content_node.source_id
            }
        )
    
    def get_available_views(self, content_node: ContentNode) -> List[ViewType]:
        """Get available Tafsir views"""
        return self._scholars
    
    def _get_tafsir_content(self, content_node: ContentNode, view_type: ViewType) -> str:
        """Simulate getting Tafsir content based on view type"""
        # In real implementation, this would query the Tafsir table
        base_text = content_node.text_translation or content_node.text_arabic or ""
        
        scholar_name = view_type.value.replace("tafsir_", "").replace("_", " ").title()
        
        return f"[{scholar_name} Tafsir]\n{base_text}\n\n(Interpretation by {scholar_name})"
    
    def set_scholar(self, scholar: ViewType) -> None:
        """Set specific scholar view"""
        if scholar in self._scholars:
            self._current_scholar_index = self._scholars.index(scholar)
            logger.info(f"Set Tafsir view to: {scholar.value}")


class QuranViewStrategy(ViewStrategy):
    """Strategy for Quran content views"""
    
    def __init__(self):
        """Initialize Quran view strategy"""
        self._current_view_index = 0
        self._views = [
            ViewType.ARABIC_WITH_TRANSLATION,
            ViewType.TRANSLATION_ONLY,
            ViewType.ARABIC_ONLY,
            ViewType.TRANSLITERATION_WITH_TRANSLATION
        ]
    
    async def get_view(self, content_node: ContentNode) -> ContentView:
        """Get current Quran view with rotation"""
        current_view = self._views[self._current_view_index]
        
        # Rotate to next view
        self._current_view_index = (self._current_view_index + 1) % len(self._views)
        
        content = self._format_quran_view(content_node, current_view)
        
        return ContentView(
            view_type=current_view,
            content=content,
            metadata={
                "source_id": content_node.source_id,
                "reference": content_node.reference
            }
        )
    
    def get_available_views(self, content_node: ContentNode) -> List[ViewType]:
        """Get available Quran views"""
        return self._views
    
    def _format_quran_view(self, content_node: ContentNode, view_type: ViewType) -> str:
        """Format Quran content based on view type"""
        arabic = content_node.text_arabic or ""
        translation = content_node.text_translation or ""
        transliteration = content_node.text_transliteration or ""
        
        if view_type == ViewType.ARABIC_WITH_TRANSLATION:
            return f"📖 *Arabic:*\n{arabic}\n\n📝 *Translation:*\n{translation}"
        elif view_type == ViewType.TRANSLATION_ONLY:
            return f"📝 *Translation:*\n{translation}"
        elif view_type == ViewType.ARABIC_ONLY:
            return f"📖 *Arabic:*\n{arabic}"
        elif view_type == ViewType.TRANSLITERATION_WITH_TRANSLATION:
            return f"🔤 *Transliteration:*\n{transliteration}\n\n📝 *Translation:*\n{translation}"
        
        return translation
    
    def set_view(self, view: ViewType) -> None:
        """Set specific view"""
        if view in self._views:
            self._current_view_index = self._views.index(view)
            logger.info(f"Set Quran view to: {view.value}")


class HadithViewStrategy(ViewStrategy):
    """Strategy for Hadith content views"""
    
    def __init__(self):
        """Initialize Hadith view strategy"""
        self._current_view_index = 0
        self._views = [
            ViewType.ARABIC_WITH_TRANSLATION,
            ViewType.TRANSLATION_ONLY,
            ViewType.ARABIC_ONLY
        ]
    
    async def get_view(self, content_node: ContentNode) -> ContentView:
        """Get current Hadith view with rotation"""
        current_view = self._views[self._current_view_index]
        
        # Rotate to next view
        self._current_view_index = (self._current_view_index + 1) % len(self._views)
        
        content = self._format_hadith_view(content_node, current_view)
        
        return ContentView(
            view_type=current_view,
            content=content,
            metadata={
                "source": content_node.source_name,
                "reference": content_node.reference
            }
        )
    
    def get_available_views(self, content_node: ContentNode) -> List[ViewType]:
        """Get available Hadith views"""
        return self._views
    
    def _format_hadith_view(self, content_node: ContentNode, view_type: ViewType) -> str:
        """Format Hadith content based on view type"""
        arabic = content_node.text_arabic or ""
        translation = content_node.text_translation or ""
        source = content_node.source_name or ""
        reference = content_node.reference or ""
        
        if view_type == ViewType.ARABIC_WITH_TRANSLATION:
            return f"📚 *Source:* {source}\n📖 *Arabic:*\n{arabic}\n\n📝 *Translation:*\n{translation}\n\n📌 *Reference:* {reference}"
        elif view_type == ViewType.TRANSLATION_ONLY:
            return f"📚 *Source:* {source}\n📝 *Translation:*\n{translation}\n\n📌 *Reference:* {reference}"
        elif view_type == ViewType.ARABIC_ONLY:
            return f"📚 *Source:* {source}\n📖 *Arabic:*\n{arabic}\n\n📌 *Reference:* {reference}"
        
        return translation
    
    def set_view(self, view: ViewType) -> None:
        """Set specific view"""
        if view in self._views:
            self._current_view_index = self._views.index(view)
            logger.info(f"Set Hadith view to: {view.value}")


class ViewStrategyFactory:
    """Factory for creating appropriate view strategies"""
    
    @staticmethod
    def create_strategy(content_type: str, session=None) -> ViewStrategy:
        """
        Create appropriate view strategy for content type.
        
        Args:
            content_type: Type of content
            session: Database session (for strategies that need it)
        
        Returns:
            Appropriate ViewStrategy instance
        """
        if content_type == "quran_ayah":
            return QuranViewStrategy()
        elif content_type == "tafsir":
            return TafsirViewStrategy(session)
        elif content_type == "hadith":
            return HadithViewStrategy()
        else:
            # Default to Quran view strategy for unknown types
            logger.warning(f"Unknown content type {content_type}, using default strategy")
            return QuranViewStrategy()


class ViewRotationManager:
    """
    Manages view rotation across different content types.
    Ensures users see different perspectives of the same content.
    """
    
    def __init__(self):
        """Initialize view rotation manager"""
        self._strategies: Dict[str, ViewStrategy] = {}
        self._user_preferences: Dict[int, Dict[str, ViewType]] = {}
    
    def get_strategy(self, content_type: str, session=None) -> ViewStrategy:
        """
        Get or create view strategy for content type.
        
        Args:
            content_type: Type of content
            session: Database session
        
        Returns:
            ViewStrategy instance
        """
        if content_type not in self._strategies:
            self._strategies[content_type] = ViewStrategyFactory.create_strategy(
                content_type, session
            )
        
        return self._strategies[content_type]
    
    async def get_rotated_view(
        self,
        content_node: ContentNode,
        user_id: Optional[int] = None,
        session=None
    ) -> ContentView:
        """
        Get rotated view of content.
        
        Args:
            content_node: Content node to view
            user_id: User ID (for preferences)
            session: Database session
        
        Returns:
            ContentView with rotated perspective
        """
        strategy = self.get_strategy(content_node.content_type, session)
        
        # Check if user has specific preference
        if user_id and user_id in self._user_preferences:
            user_prefs = self._user_preferences[user_id]
            if content_node.content_type in user_prefs:
                preferred_view = user_prefs[content_node.content_type]
                if hasattr(strategy, 'set_view'):
                    strategy.set_view(preferred_view)
        
        return await strategy.get_view(content_node)
    
    def set_user_preference(
        self,
        user_id: int,
        content_type: str,
        view_type: ViewType
    ) -> None:
        """
        Set user's preferred view for a content type.
        
        Args:
            user_id: User ID
            content_type: Content type
            view_type: Preferred view type
        """
        if user_id not in self._user_preferences:
            self._user_preferences[user_id] = {}
        
        self._user_preferences[user_id][content_type] = view_type
        logger.info(f"Set user {user_id} preference for {content_type} to {view_type.value}")
    
    def get_user_preferences(self, user_id: int) -> Dict[str, ViewType]:
        """
        Get user's view preferences.
        
        Args:
            user_id: User ID
        
        Returns:
            Dictionary of content_type -> ViewType
        """
        return self._user_preferences.get(user_id, {})
    
    def reset_user_preferences(self, user_id: int) -> None:
        """
        Reset user's view preferences.
        
        Args:
            user_id: User ID
        """
        if user_id in self._user_preferences:
            del self._user_preferences[user_id]
            logger.info(f"Reset user {user_id} view preferences")


# Global view rotation manager instance
view_rotation_manager = ViewRotationManager()
