"""
Workflow Engine for Rafeeq Enterprise Islamic OS.
Executes predefined action chains when events occur.
"""

import asyncio
import logging
from typing import Callable, Dict, List, Any, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum

from .event_bus import Event, EventType, event_bus
from utils.logger import get_logger

logger = get_logger("rafeeq.workflow")


class ActionStatus(str, Enum):
    """Status of workflow action execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Action:
    """Single action in a workflow"""
    name: str
    handler: Callable[[Event], Any]
    status: ActionStatus = ActionStatus.PENDING
    error: Optional[str] = None
    result: Optional[Any] = None
    
    async def execute(self, event: Event) -> None:
        """Execute the action"""
        self.status = ActionStatus.RUNNING
        try:
            if asyncio.iscoroutinefunction(self.handler):
                self.result = await self.handler(event)
            else:
                self.result = self.handler(event)
            self.status = ActionStatus.COMPLETED
            logger.debug(f"Action '{self.name}' completed successfully")
        except Exception as e:
            self.status = ActionStatus.FAILED
            self.error = str(e)
            logger.error(f"Action '{self.name}' failed: {e}", exc_info=True)
            raise


@dataclass
class Workflow:
    """Workflow definition with action chain"""
    name: str
    trigger_event: EventType
    actions: List[Action] = field(default_factory=list)
    enabled: bool = True
    description: str = ""
    
    def add_action(self, action: Action) -> None:
        """Add an action to the workflow"""
        self.actions.append(action)
    
    async def execute(self, event: Event) -> Dict[str, Any]:
        """
        Execute all actions in the workflow.
        
        Args:
            event: Trigger event
        
        Returns:
            Execution results
        """
        if not self.enabled:
            logger.debug(f"Workflow '{self.name}' is disabled, skipping")
            return {"status": "skipped", "reason": "workflow_disabled"}
        
        logger.info(f"Executing workflow: {self.name}")
        results = []
        
        for action in self.actions:
            try:
                await action.execute(event)
                results.append({
                    "action": action.name,
                    "status": action.status.value,
                    "result": action.result
                })
                
                # Stop if action failed
                if action.status == ActionStatus.FAILED:
                    logger.error(f"Workflow '{self.name}' stopped due to failed action: {action.name}")
                    break
            except Exception as e:
                logger.error(f"Error executing action '{action.name}': {e}")
                results.append({
                    "action": action.name,
                    "status": "failed",
                    "error": str(e)
                })
                break
        
        return {
            "workflow": self.name,
            "status": "completed",
            "actions": results
        }


class WorkflowEngine:
    """
    Workflow Engine that manages and executes workflows.
    Automatically triggers workflows based on events.
    """
    
    def __init__(self):
        self.workflows: Dict[EventType, List[Workflow]] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._execution_queue: asyncio.Queue = asyncio.Queue()
    
    def register_workflow(self, workflow: Workflow) -> None:
        """
        Register a workflow with the engine.
        
        Args:
            workflow: Workflow to register
        """
        event_type = workflow.trigger_event
        
        if event_type not in self.workflows:
            self.workflows[event_type] = []
        
        self.workflows[event_type].append(workflow)
        logger.info(f"Registered workflow: {workflow.name} for event: {event_type.value}")
    
    def unregister_workflow(self, workflow_name: str) -> None:
        """
        Unregister a workflow by name.
        
        Args:
            workflow_name: Name of workflow to remove
        """
        for event_type, workflows in self.workflows.items():
            self.workflows[event_type] = [
                w for w in workflows if w.name != workflow_name
            ]
        
        logger.info(f"Unregistered workflow: {workflow_name}")
    
    def get_workflow(self, name: str) -> Optional[Workflow]:
        """Get a workflow by name."""
        for workflows in self.workflows.values():
            for workflow in workflows:
                if workflow.name == name:
                    return workflow
        return None
    
    def enable_workflow(self, name: str) -> bool:
        """Enable a workflow."""
        workflow = self.get_workflow(name)
        if workflow:
            workflow.enabled = True
            logger.info(f"Enabled workflow: {name}")
            return True
        return False
    
    def disable_workflow(self, name: str) -> bool:
        """Disable a workflow."""
        workflow = self.get_workflow(name)
        if workflow:
            workflow.enabled = False
            logger.info(f"Disabled workflow: {name}")
            return True
        return False
    
    async def _handle_event(self, event: Event) -> None:
        """
        Handle an event by triggering matching workflows.
        
        Args:
            event: Event to handle
        """
        workflows = self.workflows.get(event.type, [])
        
        if not workflows:
            return
        
        logger.info(f"Triggering {len(workflows)} workflows for event: {event.type.value}")
        
        # Execute all workflows concurrently
        tasks = []
        for workflow in workflows:
            if workflow.enabled:
                task = asyncio.create_task(workflow.execute(event))
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _worker(self) -> None:
        """Worker task that processes events from the queue."""
        while self._running:
            try:
                event = await asyncio.wait_for(
                    self._execution_queue.get(),
                    timeout=1.0
                )
                await self._handle_event(event)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in workflow engine worker: {e}", exc_info=True)
    
    async def start(self) -> None:
        """Start the workflow engine."""
        if self._running:
            logger.warning("Workflow engine is already running")
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        
        # Subscribe to all relevant events
        for event_type in self.workflows.keys():
            event_bus.subscribe(event_type, self._on_event)
        
        logger.info("Workflow engine started")
    
    async def stop(self) -> None:
        """Stop the workflow engine."""
        if not self._running:
            return
        
        self._running = False
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        # Unsubscribe from events
        for event_type in self.workflows.keys():
            event_bus.unsubscribe(event_type, self._on_event)
        
        logger.info("Workflow engine stopped")
    
    async def _on_event(self, event: Event) -> None:
        """Event handler callback."""
        await self._execution_queue.put(event)
    
    def get_all_workflows(self) -> List[Workflow]:
        """Get all registered workflows."""
        all_workflows = []
        for workflows in self.workflows.values():
            all_workflows.extend(workflows)
        return all_workflows


# Global workflow engine instance
workflow_engine = WorkflowEngine()


# Predefined workflow actions
class WorkflowActions:
    """Common workflow actions"""
    
    @staticmethod
    async def award_xp(event: Event, xp_amount: int = 10) -> None:
        """Award XP to user."""
        from repositories import UserMetricsRepository
        from sqlalchemy.ext.asyncio import AsyncSession
        
        user_id = event.user_id
        if not user_id:
            return
        
        # This would need a DB session - placeholder for now
        logger.info(f"Awarding {xp_amount} XP to user {user_id}")
    
    @staticmethod
    async def notify_user(event: Event, message: str) -> None:
        """Send notification to user."""
        # Placeholder for notification logic
        logger.info(f"Notifying user {event.user_id}: {message}")
    
    @staticmethod
    async def increment_streak(event: Event) -> None:
        """Increment user streak."""
        from repositories import UserRepository
        logger.info(f"Incrementing streak for user {event.user_id}")
    
    @staticmethod
    async def unlock_achievement(event: Event, achievement_id: int) -> None:
        """Unlock achievement for user."""
        from repositories import UserAchievementRepository
        logger.info(f"Unlocking achievement {achievement_id} for user {event.user_id}")
    
    @staticmethod
    async def log_activity(event: Event, activity_type: str) -> None:
        """Log user activity."""
        logger.info(f"Logging activity {activity_type} for user {event.user_id}")
