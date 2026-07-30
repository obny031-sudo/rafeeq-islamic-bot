"""
Message Queue for Rafeeq Enterprise Islamic OS.
Background worker system with rate limiting for high-load operations.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

from aiogram import Bot
from aiogram.types import Message
from utils.logger import get_logger

logger = get_logger("rafeeq.message_queue")


class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task execution status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """Background task definition"""
    id: str
    handler: Callable
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    result: Optional[Any] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary"""
        return {
            "id": self.id,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "retry_count": self.retry_count
        }


class RateLimiter:
    """
    Telegram API rate limiter.
    Respects Telegram's rate limits (30 messages/sec).
    """
    
    def __init__(self, messages_per_second: int = 30, messages_per_minute: int = 20):
        """
        Initialize rate limiter.
        
        Args:
            messages_per_second: Max messages per second
            messages_per_minute: Max messages per minute
        """
        self.messages_per_second = messages_per_second
        self.messages_per_minute = messages_per_minute
        self._second_queue: deque = deque()
        self._minute_queue: deque = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> None:
        """
        Acquire rate limit permission.
        Blocks if rate limit would be exceeded.
        """
        async with self._lock:
            now = datetime.utcnow()
            
            # Clean old entries
            self._second_queue = deque([
                t for t in self._second_queue 
                if t > now - timedelta(seconds=1)
            ])
            self._minute_queue = deque([
                t for t in self._minute_queue 
                if t > now - timedelta(minutes=1)
            ])
            
            # Check limits
            if len(self._second_queue) >= self.messages_per_second:
                sleep_time = 1.0 - (now - self._second_queue[0]).total_seconds()
                if sleep_time > 0:
                    logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            if len(self._minute_queue) >= self.messages_per_minute:
                sleep_time = 60.0 - (now - self._minute_queue[0]).total_seconds()
                if sleep_time > 0:
                    logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            
            # Add current time to queues
            self._second_queue.append(now)
            self._minute_queue.append(now)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        now = datetime.utcnow()
        second_count = len([t for t in self._second_queue if t > now - timedelta(seconds=1)])
        minute_count = len([t for t in self._minute_queue if t > now - timedelta(minutes=1)])
        
        return {
            "messages_per_second": second_count,
            "messages_per_minute": minute_count,
            "limit_per_second": self.messages_per_second,
            "limit_per_minute": self.messages_per_minute,
            "second_usage": round((second_count / self.messages_per_second) * 100, 2),
            "minute_usage": round((minute_count / self.messages_per_minute) * 100, 2)
        }


class MessageQueue:
    """
    Background message queue for high-load operations.
    Handles broadcasts, heavy notifications with rate limiting.
    """
    
    def __init__(self, bot: Bot, max_workers: int = 5):
        """
        Initialize message queue.
        
        Args:
            bot: Aiogram Bot instance
            max_workers: Maximum number of concurrent workers
        """
        self.bot = bot
        self.max_workers = max_workers
        self._task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._tasks: Dict[str, Task] = {}
        self._workers: List[asyncio.Task] = []
        self._running = False
        self._rate_limiter = RateLimiter()
        self._task_counter = 0
    
    def _get_task_id(self) -> str:
        """Generate unique task ID."""
        self._task_counter += 1
        return f"task_{self._task_counter}_{datetime.utcnow().timestamp()}"
    
    async def enqueue(
        self,
        handler: Callable,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3
    ) -> str:
        """
        Enqueue a task for background processing.
        
        Args:
            handler: Async function to execute
            priority: Task priority
            max_retries: Maximum retry attempts
        
        Returns:
            Task ID
        """
        task_id = self._get_task_id()
        task = Task(
            id=task_id,
            handler=handler,
            priority=priority,
            max_retries=max_retries
        )
        
        # Priority mapping for queue (lower number = higher priority)
        priority_map = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.LOW: 3
        }
        
        await self._task_queue.put((priority_map[priority], task))
        self._tasks[task_id] = task
        
        logger.info(f"Task enqueued: {task_id} with priority {priority.value}")
        return task_id
    
    async def _worker(self, worker_id: int) -> None:
        """
        Worker task that processes queued tasks.
        
        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Worker {worker_id} started")
        
        while self._running:
            try:
                priority, task = await asyncio.wait_for(
                    self._task_queue.get(),
                    timeout=1.0
                )
                
                await self._process_task(task, worker_id)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _process_task(self, task: Task, worker_id: int) -> None:
        """
        Process a single task.
        
        Args:
            task: Task to process
            worker_id: Worker identifier
        """
        task.status = TaskStatus.PROCESSING
        task.started_at = datetime.utcnow()
        
        logger.info(f"Worker {worker_id} processing task: {task.id}")
        
        try:
            # Acquire rate limit if this is a message task
            await self._rate_limiter.acquire()
            
            # Execute the task
            if asyncio.iscoroutinefunction(task.handler):
                task.result = await task.handler()
            else:
                task.result = task.handler()
            
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            logger.info(f"Task {task.id} completed successfully")
            
        except Exception as e:
            task.error = str(e)
            task.retry_count += 1
            
            if task.retry_count < task.max_retries:
                task.status = TaskStatus.PENDING
                # Re-queue with same priority
                priority_map = {
                    TaskPriority.CRITICAL: 0,
                    TaskPriority.HIGH: 1,
                    TaskPriority.NORMAL: 2,
                    TaskPriority.LOW: 3
                }
                await self._task_queue.put((priority_map[task.priority], task))
                logger.warning(f"Task {task.id} failed, retrying ({task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                logger.error(f"Task {task.id} failed after {task.max_retries} retries: {e}")
    
    async def start(self) -> None:
        """Start the message queue workers."""
        if self._running:
            logger.warning("Message queue is already running")
            return
        
        self._running = True
        
        # Start workers
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(i))
            self._workers.append(worker)
        
        logger.info(f"Message queue started with {self.max_workers} workers")
    
    async def stop(self) -> None:
        """Stop the message queue workers."""
        if not self._running:
            return
        
        self._running = False
        
        # Cancel all workers
        for worker in self._workers:
            worker.cancel()
        
        # Wait for workers to finish
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        
        logger.info("Message queue stopped")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific task.
        
        Args:
            task_id: Task ID
        
        Returns:
            Task status dictionary or None
        """
        task = self._tasks.get(task_id)
        return task.to_dict() if task else None
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.
        
        Returns:
            Queue status dictionary
        """
        pending_count = sum(
            1 for task in self._tasks.values() 
            if task.status == TaskStatus.PENDING
        )
        processing_count = sum(
            1 for task in self._tasks.values() 
            if task.status == TaskStatus.PROCESSING
        )
        completed_count = sum(
            1 for task in self._tasks.values() 
            if task.status == TaskStatus.COMPLETED
        )
        failed_count = sum(
            1 for task in self._tasks.values() 
            if task.status == TaskStatus.FAILED
        )
        
        return {
            "queue_size": self._task_queue.qsize(),
            "pending_tasks": pending_count,
            "processing_tasks": processing_count,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "total_tasks": len(self._tasks),
            "active_workers": len(self._workers),
            "rate_limiter": self._rate_limiter.get_status()
        }
    
    async def broadcast_message(
        self,
        user_ids: List[int],
        message_text: str,
        priority: TaskPriority = TaskPriority.LOW
    ) -> List[str]:
        """
        Broadcast a message to multiple users.
        
        Args:
            user_ids: List of user IDs
            message_text: Message text to send
            priority: Task priority
        
        Returns:
            List of task IDs
        """
        task_ids = []
        
        for user_id in user_ids:
            async def send_message():
                try:
                    await self.bot.send_message(user_id, message_text)
                except Exception as e:
                    logger.error(f"Failed to send message to {user_id}: {e}")
                    raise
            
            task_id = await self.enqueue(send_message, priority)
            task_ids.append(task_id)
        
        logger.info(f"Broadcast enqueued to {len(user_ids)} users")
        return task_ids
    
    async def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """
        Clear completed tasks older than specified hours.
        
        Args:
            older_than_hours: Age threshold in hours
        
        Returns:
            Number of tasks cleared
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        cleared_count = 0
        
        tasks_to_remove = []
        for task_id, task in self._tasks.items():
            if (
                task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and
                task.completed_at and
                task.completed_at < cutoff_time
            ):
                tasks_to_remove.append(task_id)
        
        for task_id in tasks_to_remove:
            del self._tasks[task_id]
            cleared_count += 1
        
        logger.info(f"Cleared {cleared_count} completed tasks")
        return cleared_count


# Global message queue instance (initialized in main.py)
message_queue: Optional[MessageQueue] = None


def get_message_queue() -> MessageQueue:
    """Get the global message queue instance."""
    if message_queue is None:
        raise RuntimeError("Message queue not initialized. Call init_message_queue() first.")
    return message_queue


async def init_message_queue(bot: Bot, max_workers: int = 5) -> MessageQueue:
    """
    Initialize the global message queue instance.
    
    Args:
        bot: Aiogram Bot instance
        max_workers: Maximum number of concurrent workers
    
    Returns:
        Initialized MessageQueue instance
    """
    global message_queue
    message_queue = MessageQueue(bot, max_workers)
    await message_queue.start()
    logger.info("Message queue initialized")
    return message_queue
