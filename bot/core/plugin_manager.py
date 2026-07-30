"""
Plugin Manager for Rafeeq Islamic Telegram Super App.

This module manages the loading, initialization, and lifecycle of all plugins.
"""

import logging
from typing import Dict, List, Optional
from aiogram import Bot, Dispatcher
from aiogram import Router

from .base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Central manager for all plugins in the system.
    Handles plugin registration, initialization, and lifecycle management.
    """
    
    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.bot: Optional[Bot] = None
        self.dispatcher: Optional[Dispatcher] = None
    
    def register_plugin(self, plugin: BasePlugin) -> None:
        """
        Register a plugin with the manager.
        
        Args:
            plugin: Plugin instance to register
        """
        plugin_name = plugin.get_name()
        
        if plugin_name in self.plugins:
            logger.warning(f"Plugin {plugin_name} is already registered. Skipping.")
            return
        
        if not plugin.is_enabled():
            logger.info(f"Plugin {plugin_name} is disabled. Skipping registration.")
            return
        
        self.plugins[plugin_name] = plugin
        logger.info(f"Registered plugin: {plugin_name} v{plugin.get_version()}")
    
    async def initialize_all(self, bot: Bot, dispatcher: Dispatcher) -> None:
        """
        Initialize all registered plugins.
        
        Args:
            bot: Aiogram Bot instance
            dispatcher: Aiogram Dispatcher instance
        """
        self.bot = bot
        self.dispatcher = dispatcher
        
        logger.info(f"Initializing {len(self.plugins)} plugins...")
        
        for plugin_name, plugin in self.plugins.items():
            try:
                await plugin.initialize(bot)
                
                # Register plugin router with dispatcher
                router = plugin.get_router()
                if router:
                    dispatcher.include_router(router)
                    logger.info(f"Registered router for plugin: {plugin_name}")
                
                logger.info(f"Successfully initialized plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Failed to initialize plugin {plugin_name}: {e}", exc_info=True)
    
    async def shutdown_all(self) -> None:
        """Shutdown all registered plugins"""
        logger.info("Shutting down all plugins...")
        
        for plugin_name, plugin in self.plugins.items():
            try:
                await plugin.shutdown()
                logger.info(f"Successfully shutdown plugin: {plugin_name}")
            except Exception as e:
                logger.error(f"Error shutting down plugin {plugin_name}: {e}", exc_info=True)
    
    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        """
        Get a specific plugin by name.
        
        Args:
            name: Plugin name
        
        Returns:
            Plugin instance or None if not found
        """
        return self.plugins.get(name)
    
    def get_all_plugins(self) -> List[BasePlugin]:
        """Get all registered plugins"""
        return list(self.plugins.values())
    
    def get_enabled_plugins(self) -> List[BasePlugin]:
        """Get all enabled plugins"""
        return [p for p in self.plugins.values() if p.is_enabled()]
    
    def enable_plugin(self, name: str) -> bool:
        """
        Enable a specific plugin.
        
        Args:
            name: Plugin name
        
        Returns:
            True if successful, False otherwise
        """
        plugin = self.plugins.get(name)
        if plugin:
            plugin.enable()
            logger.info(f"Enabled plugin: {name}")
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """
        Disable a specific plugin.
        
        Args:
            name: Plugin name
        
        Returns:
            True if successful, False otherwise
        """
        plugin = self.plugins.get(name)
        if plugin:
            plugin.disable()
            logger.info(f"Disabled plugin: {name}")
            return True
        return False
    
    async def notify_user_join(self, user_id: int, db_session) -> None:
        """
        Notify all plugins that a user has joined.
        
        Args:
            user_id: Telegram user ID
            db_session: Database session
        """
        for plugin in self.get_enabled_plugins():
            try:
                await plugin.on_user_join(user_id, db_session)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.get_name()} on_user_join: {e}")
    
    async def notify_user_leave(self, user_id: int, db_session) -> None:
        """
        Notify all plugins that a user has left.
        
        Args:
            user_id: Telegram user ID
            db_session: Database session
        """
        for plugin in self.get_enabled_plugins():
            try:
                await plugin.on_user_leave(user_id, db_session)
            except Exception as e:
                logger.error(f"Error in plugin {plugin.get_name()} on_user_leave: {e}")


# Global plugin manager instance
plugin_manager = PluginManager()
