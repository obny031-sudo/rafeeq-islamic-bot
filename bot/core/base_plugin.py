"""
Base Plugin System for Rafeeq Islamic Telegram Super App.

This module defines the abstract base class that all plugins must implement.
Plugins are self-contained modules with their own routers, services, models, and handlers.
"""

from abc import ABC, abstractmethod
from typing import Optional
from aiogram import Router
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession


class BasePlugin(ABC):
    """
    Abstract base class for all plugins in the Rafeeq system.
    
    Each plugin must implement this interface to be loaded by the plugin manager.
    Plugins should be self-contained and independent of other plugins.
    """
    
    # Plugin metadata
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    enabled: bool = True
    
    def __init__(self):
        """Initialize the plugin"""
        self.router: Optional[Router] = None
        self._initialized = False
    
    @abstractmethod
    async def initialize(self, bot: Bot) -> None:
        """
        Initialize the plugin with bot instance.
        Called when the plugin is loaded.
        
        Args:
            bot: Aiogram Bot instance
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        Cleanup and shutdown the plugin.
        Called when the bot is shutting down.
        """
        pass
    
    @abstractmethod
    def get_router(self) -> Router:
        """
        Get the router for this plugin.
        
        Returns:
            Router: Aiogram Router instance
        """
        pass
    
    def get_name(self) -> str:
        """Get plugin name"""
        return self.name
    
    def get_version(self) -> str:
        """Get plugin version"""
        return self.version
    
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        return self.enabled
    
    def enable(self) -> None:
        """Enable the plugin"""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the plugin"""
        self.enabled = False
    
    async def on_user_join(self, user_id: int, db: AsyncSession) -> None:
        """
        Called when a new user joins the bot.
        Optional hook for plugins to initialize user data.
        
        Args:
            user_id: Telegram user ID
            db: Database session
        """
        pass
    
    async def on_user_leave(self, user_id: int, db: AsyncSession) -> None:
        """
        Called when a user leaves the bot.
        Optional hook for plugins to cleanup user data.
        
        Args:
            user_id: Telegram user ID
            db: Database session
        """
        pass


class PluginMetadata:
    """Metadata container for plugin information"""
    
    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        author: str,
        dependencies: Optional[list[str]] = None
    ):
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.dependencies = dependencies or []
    
    def to_dict(self) -> dict:
        """Convert metadata to dictionary"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "dependencies": self.dependencies
        }
