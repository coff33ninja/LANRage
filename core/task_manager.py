"""Background task management for LANrage"""

import asyncio
from collections.abc import Callable, Coroutine

from .logging_config import get_logger, timing_decorator

logger = get_logger(__name__)


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
