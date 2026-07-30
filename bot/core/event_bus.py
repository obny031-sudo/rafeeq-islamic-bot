"""
Event Bus for Rafeeq Enterprise Islamic OS.
Provides async pub/sub pattern for plugin communication.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from utils.logger import get_logger

logger = get_logger("rafeeq.event_bus")


class EventType(str, Enum):
    """Standard event types in the system"""
    # User Events
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_LEVEL_UP = "user_level_up"
    USER_ACHIEVEMENT_UNLOCKED = "user_achievement_unlocked"
    USER_STREAK_HIT = "user_streak_hit"
    
    # Content Events
    QURAN_FINISHED = "quran_finished"
    QURAN_AYAH_READ = "quran_ayah_read"
    PRAYER_TIME_REACHED = "prayer_time_reached"
    PRAYER_COMPLETED = "prayer_completed"
    ADHKAR_COMPLETED = "adhkar_completed"
    
    # System Events
    PLUGIN_LOADED = "plugin_loaded"
    PLUGIN_UNLOADED = "plugin_unloaded"
    SYSTEM_ERROR = "system_error"
    HEALTH_CHECK = "health_check"


@dataclass
class Event:
    """Event data structure"""
    type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: Optional[str] = None  # Plugin or component that emitted the event
    user_id: Optional[int] = None  # User ID if event is user-specific
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return {
            "type": self.type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "user_id": self.user_id
        }


class EventBus:
    """
    Async Event Bus using asyncio.Queue for plugin communication.
    Implements pub/sub pattern for decoupled plugin communication.
    """
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._event_history: List[Event] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Async callback function that receives Event
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.info(f"Subscribed handler to event: {event_type.value}")
    
    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], Any]) -> None:
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler to remove
        """
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.info(f"Unsubscribed handler from event: {event_type.value}")
    
    async def emit(self, event: Event) -> None:
        """
        Emit an event to the bus.
        
        Args:
            event: Event to emit
        """
        await self._event_queue.put(event)
        logger.debug(f"Event emitted: {event.type.value}")
    
    async def _process_event(self, event: Event) -> None:
        """
        Process a single event by calling all subscribers.
        
        Args:
            event: Event to process
        """
        subscribers = self._subscribers.get(event.type, [])
        
        if not subscribers:
            logger.debug(f"No subscribers for event: {event.type.value}")
            return
        
        # Call all subscribers concurrently
        tasks = []
        for handler in subscribers:
            try:
                task = asyncio.create_task(self._call_handler(handler, event))
                tasks.append(task)
            except Exception as e:
                logger.error(f"Error creating task for handler: {e}")
        
        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Add to history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
    
    async def _call_handler(self, handler: Callable[[Event], Any], event: Event) -> None:
        """
        Call a single event handler with error handling.
        
        Args:
            handler: Handler function
            event: Event to pass to handler
        """
        try:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
        except Exception as e:
            logger.error(f"Error in event handler for {event.type.value}: {e}", exc_info=True)
    
    async def _worker(self) -> None:
        """Worker task that processes events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                await self._process_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in event bus worker: {e}", exc_info=True)
    
    async def start(self) -> None:
        """Start the event bus worker."""
        if self._running:
            logger.warning("Event bus is already running")
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Event bus started")
    
    async def stop(self) -> None:
        """Stop the event bus worker."""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Event bus stopped")
    
    def get_event_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get recent event history.
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            List of event dictionaries
        """
        events = self._event_history[-limit:]
        return [event.to_dict() for event in events]
    
    def get_subscriber_count(self, event_type: EventType) -> int:
        """Get number of subscribers for an event type."""
        return len(self._subscribers.get(event_type, []))
    
    def get_all_event_types(self) -> List[EventType]:
        """Get all event types with subscribers."""
        return list(self._subscribers.keys())


# Global event bus instance
event_bus = EventBus()
