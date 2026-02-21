"""Background task management for LANrage"""

import asyncio
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import IntEnum

from .logging_config import get_logger, timing_decorator

logger = get_logger(__name__)


class TaskPriority(IntEnum):
    """Task priority levels for advanced execution."""

    DEFERRED = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class TaskDefinition:
    """Task definition for priority/dependency execution."""

    name: str
    coroutine_factory: Callable[[], Coroutine]
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: list[str] = field(default_factory=list)
    retries: int = 0
    retry_backoff_seconds: float = 0.1


class TaskExecutionEngine:
    """Executes named tasks with priority and dependency support."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

    def __init__(self):
        self.tasks: dict[str, TaskDefinition] = {}
        self.status: dict[str, str] = {}
        self.results: dict[str, object] = {}
        self.execution_order: list[str] = []

    def register_task(self, task: TaskDefinition) -> None:
        """Register a task in the execution graph."""
        self.tasks[task.name] = task
        self.status[task.name] = self.PENDING

    def _dependencies_completed(self, task_name: str) -> bool:
        task = self.tasks[task_name]
        return all(self.status.get(dep) == self.COMPLETED for dep in task.dependencies)

    def _dependency_failed(self, task_name: str) -> bool:
        task = self.tasks[task_name]
        return any(
            self.status.get(dep) in {self.FAILED, self.SKIPPED}
            for dep in task.dependencies
        )

    async def _execute_single(self, task: TaskDefinition) -> tuple[str, object | None]:
        self.status[task.name] = self.RUNNING
        attempt = 0
        while True:
            try:
                result = await task.coroutine_factory()
                self.status[task.name] = self.COMPLETED
                self.results[task.name] = result
                self.execution_order.append(task.name)
                return task.name, result
            except Exception as exc:
                attempt += 1
                if attempt > task.retries:
                    self.status[task.name] = self.FAILED
                    self.results[task.name] = exc
                    self.execution_order.append(task.name)
                    return task.name, None
                await asyncio.sleep(task.retry_backoff_seconds * (2 ** (attempt - 1)))

    @timing_decorator(name="execute_task_graph")
    async def execute_all(self) -> dict[str, object]:
        """Execute all registered tasks honoring priority and dependencies."""
        while True:
            pending = [
                name for name, state in self.status.items() if state == self.PENDING
            ]
            if not pending:
                break

            progressed = False
            for task_name in pending:
                if self._dependency_failed(task_name):
                    self.status[task_name] = self.SKIPPED
                    progressed = True

            runnable = [
                self.tasks[name]
                for name in pending
                if self.status[name] == self.PENDING
                and self._dependencies_completed(name)
            ]
            if not runnable:
                if not progressed:
                    # Unresolvable dependency cycle.
                    for task_name in pending:
                        if self.status[task_name] == self.PENDING:
                            self.status[task_name] = self.FAILED
                    break
                continue

            highest_priority = max(task.priority for task in runnable)
            to_run = [task for task in runnable if task.priority == highest_priority]
            progressed = True

            if len(to_run) == 1:
                await self._execute_single(to_run[0])
            else:
                await asyncio.gather(*(self._execute_single(task) for task in to_run))

            if not progressed:
                break

        return self.results.copy()


class TaskManager:
    """Manages background tasks with proper tracking and cancellation

    This ensures that:
    - All tasks are tracked and can be cancelled gracefully
    - Tasks are properly cleaned up on shutdown
    - No orphaned tasks remain after application exit
    - Task completion callbacks for monitoring and event handling
    """

    def __init__(self):
        self.tasks: set[asyncio.Task] = set()
        self.running = True
        self.completion_callbacks: list[Callable[[asyncio.Task], None]] = []

    def register_completion_callback(
        self, callback: Callable[[asyncio.Task], None]
    ) -> None:
        """Register a callback to be called when any task completes

        Args:
            callback: Function to call with completed task as argument
        """
        self.completion_callbacks.append(callback)
        logger.debug(f"Registered task completion callback: {callback.__name__}")

    def create_task(self, coro: Coroutine, name: str | None = None) -> asyncio.Task:
        """Create and track a background task

        Args:
            coro: Coroutine to run as a task
            name: Optional name for the task (for debugging)

        Returns:
            The created asyncio.Task
        """
        task = asyncio.create_task(coro)
        if name:
            task.set_name(name)

        self.tasks.add(task)

        # Remove from set when task completes
        task.add_done_callback(self._task_done)

        logger.debug(f"Created task: {name or task.get_name()}")
        return task

    def _task_done(self, task: asyncio.Task) -> None:
        """Callback when a task completes"""
        self.tasks.discard(task)

        # Log completion/errors
        if task.cancelled():
            logger.debug(f"Task cancelled: {task.get_name()}")
        elif task.exception():
            logger.error(f"Task failed: {task.get_name()}: {task.exception()}")
        else:
            logger.debug(f"Task completed: {task.get_name()}")

        # Call registered completion callbacks
        for callback in self.completion_callbacks:
            try:
                callback(task)
            except Exception as e:
                logger.error(
                    f"Error in task completion callback {callback.__name__}: {type(e).__name__}: {e}"
                )

    async def cancel_all(self, timeout: float = 30) -> None:
        """Cancel all tracked tasks gracefully

        Args:
            timeout: Seconds to wait for tasks to complete after cancel
        """
        if not self.tasks:
            logger.info("No tasks to cancel")
            return

        self.running = False
        logger.info(f"Cancelling {len(self.tasks)} background tasks...")

        tasks_to_cancel = self.tasks.copy()

        # Cancel all tracked tasks
        for task in tasks_to_cancel:
            task.cancel()
            logger.debug(f"Cancelled task: {task.get_name()}")

        # Wait for cancellation with timeout
        _done, pending = await asyncio.wait(tasks_to_cancel, timeout=timeout)
        if pending:
            logger.warning(f"Task cancellation timeout after {timeout}s")
            # Force-remove remaining tasks
            self.tasks.clear()

        logger.info("All background tasks cancelled")

    async def wait_all(self, timeout: float | None = None) -> None:
        """Wait for all tasks to complete

        Args:
            timeout: Optional timeout in seconds
        """
        if not self.tasks:
            return

        _done, pending = await asyncio.wait(self.tasks.copy(), timeout=timeout)
        if pending:
            logger.warning(f"Task wait timeout after {timeout}s")

    def task_count(self) -> int:
        """Get count of currently tracked tasks"""
        return len(self.tasks)

    def get_tasks(self) -> set[asyncio.Task]:
        """Get all tracked tasks"""
        return self.tasks.copy()


# Global task manager instance
_global_task_manager: TaskManager | None = None


def get_task_manager() -> TaskManager:
    """Get or create the global task manager"""
    global _global_task_manager
    if _global_task_manager is None:
        _global_task_manager = TaskManager()
    return _global_task_manager


def create_background_task(coro: Coroutine, name: str | None = None) -> asyncio.Task:
    """Create a background task using the global task manager

    Args:
        coro: Coroutine to run as a task
        name: Optional name for the task (for debugging)

    Returns:
        The created asyncio.Task
    """
    return get_task_manager().create_task(coro, name)


async def cancel_all_background_tasks(timeout: float = 30) -> None:
    """Cancel all background tasks using the global task manager

    Args:
        timeout: Seconds to wait for tasks to complete after cancel
    """
    await get_task_manager().cancel_all(timeout)
