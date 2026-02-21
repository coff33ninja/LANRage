"""Tests for task manager"""

import asyncio
import contextlib

import pytest

from core.task_manager import (
    TaskDefinition,
    TaskExecutionEngine,
    TaskManager,
    TaskPriority,
    cancel_all_background_tasks,
    create_background_task,
    get_task_manager,
)


@pytest.fixture
def task_manager():
    """Create task manager"""
    return TaskManager()


def test_task_manager_initialization(task_manager):
    """Test task manager initializes correctly"""
    assert task_manager.tasks == set()
    assert task_manager.running is True
    assert task_manager.completion_callbacks == []


@pytest.mark.asyncio
async def test_create_task(task_manager):
    """Test creating a task"""

    async def dummy_task():
        await asyncio.sleep(0.1)
        return "done"

    task = task_manager.create_task(dummy_task(), name="test_task")

    assert task in task_manager.tasks
    assert task.get_name() == "test_task"

    # Wait for task to complete
    result = await task
    assert result == "done"

    # Task should be removed after completion
    await asyncio.sleep(0.01)
    assert task not in task_manager.tasks


@pytest.mark.asyncio
async def test_task_count(task_manager):
    """Test getting task count"""
    assert task_manager.task_count() == 0

    async def dummy_task():
        await asyncio.sleep(0.5)

    # Create multiple tasks
    task1 = task_manager.create_task(dummy_task(), name="task1")
    task2 = task_manager.create_task(dummy_task(), name="task2")
    task3 = task_manager.create_task(dummy_task(), name="task3")

    assert task_manager.task_count() == 3

    # Cancel tasks
    task1.cancel()
    task2.cancel()
    task3.cancel()

    with contextlib.suppress(Exception):
        await asyncio.gather(task1, task2, task3, return_exceptions=True)


@pytest.mark.asyncio
async def test_get_tasks(task_manager):
    """Test getting all tasks"""

    async def dummy_task():
        await asyncio.sleep(0.5)

    task1 = task_manager.create_task(dummy_task(), name="task1")
    task2 = task_manager.create_task(dummy_task(), name="task2")

    tasks = task_manager.get_tasks()

    assert len(tasks) == 2
    assert task1 in tasks
    assert task2 in tasks

    # Cancel tasks
    task1.cancel()
    task2.cancel()
    with contextlib.suppress(Exception):
        await asyncio.gather(task1, task2, return_exceptions=True)


@pytest.mark.asyncio
async def test_cancel_all(task_manager):
    """Test cancelling all tasks"""

    async def long_task():
        await asyncio.sleep(10)

    # Create tasks
    _task1 = task_manager.create_task(long_task(), name="task1")
    _task2 = task_manager.create_task(long_task(), name="task2")

    assert task_manager.task_count() == 2

    # Cancel all
    await task_manager.cancel_all(timeout=1)

    assert task_manager.task_count() == 0
    assert task_manager.running is False


@pytest.mark.asyncio
async def test_wait_all(task_manager):
    """Test waiting for all tasks"""
    results = []

    async def task_with_result(value):
        await asyncio.sleep(0.1)
        results.append(value)

    _task1 = task_manager.create_task(task_with_result(1), name="task1")
    _task2 = task_manager.create_task(task_with_result(2), name="task2")

    await task_manager.wait_all(timeout=1)

    assert len(results) == 2
    assert 1 in results
    assert 2 in results


@pytest.mark.asyncio
async def test_task_completion_callback(task_manager):
    """Test task completion callback"""
    completed_tasks = []

    def on_complete(task):
        completed_tasks.append(task.get_name())

    task_manager.register_completion_callback(on_complete)

    async def dummy_task():
        await asyncio.sleep(0.1)

    task = task_manager.create_task(dummy_task(), name="test_task")
    await task

    await asyncio.sleep(0.01)
    assert "test_task" in completed_tasks


@pytest.mark.asyncio
async def test_task_exception_handling(task_manager):
    """Test task exception handling"""

    async def failing_task():
        await asyncio.sleep(0.1)
        raise ValueError("Test error")

    task = task_manager.create_task(failing_task(), name="failing_task")

    with contextlib.suppress(ValueError):
        await task

    await asyncio.sleep(0.01)
    # Task should be removed even after exception
    assert task not in task_manager.tasks


@pytest.mark.asyncio
async def test_task_cancellation(task_manager):
    """Test task cancellation"""

    async def long_task():
        await asyncio.sleep(10)

    task = task_manager.create_task(long_task(), name="long_task")

    # Cancel task
    task.cancel()

    with contextlib.suppress(asyncio.CancelledError):
        await task

    await asyncio.sleep(0.01)
    assert task not in task_manager.tasks


@pytest.mark.asyncio
async def test_multiple_completion_callbacks(task_manager):
    """Test multiple completion callbacks"""
    callback1_called = []
    callback2_called = []

    def callback1(task):
        callback1_called.append(task.get_name())

    def callback2(task):
        callback2_called.append(task.get_name())

    task_manager.register_completion_callback(callback1)
    task_manager.register_completion_callback(callback2)

    async def dummy_task():
        await asyncio.sleep(0.1)

    task = task_manager.create_task(dummy_task(), name="test_task")
    await task

    await asyncio.sleep(0.01)
    assert "test_task" in callback1_called
    assert "test_task" in callback2_called


@pytest.mark.asyncio
async def test_get_task_manager():
    """Test getting global task manager"""
    manager1 = get_task_manager()
    manager2 = get_task_manager()

    # Should return same instance
    assert manager1 is manager2


@pytest.mark.asyncio
async def test_create_background_task():
    """Test creating background task with global manager"""

    async def dummy_task():
        await asyncio.sleep(0.1)
        return "done"

    task = create_background_task(dummy_task(), name="bg_task")

    assert task is not None
    result = await task
    assert result == "done"


@pytest.mark.asyncio
async def test_cancel_all_background_tasks():
    """Test cancelling all background tasks"""

    async def long_task():
        await asyncio.sleep(10)

    # Create some background tasks
    task1 = create_background_task(long_task(), name="bg1")
    task2 = create_background_task(long_task(), name="bg2")

    # Cancel all
    await cancel_all_background_tasks(timeout=1)

    # Tasks should be cancelled
    assert task1.cancelled() or task1.done()
    assert task2.cancelled() or task2.done()


@pytest.mark.asyncio
async def test_task_without_name(task_manager):
    """Test creating task without name"""

    async def dummy_task():
        await asyncio.sleep(0.1)

    task = task_manager.create_task(dummy_task())

    assert task in task_manager.tasks
    assert task.get_name() is not None

    await task


@pytest.mark.asyncio
async def test_empty_cancel_all(task_manager):
    """Test cancelling when no tasks exist"""
    # Should not raise error
    await task_manager.cancel_all()

    assert task_manager.task_count() == 0


@pytest.mark.asyncio
async def test_empty_wait_all(task_manager):
    """Test waiting when no tasks exist"""
    # Should not raise error
    await task_manager.wait_all()


@pytest.mark.asyncio
async def test_concurrent_task_creation(task_manager):
    """Test creating tasks concurrently"""

    async def dummy_task(value):
        await asyncio.sleep(0.1)
        return value

    # Create many tasks concurrently
    tasks = [
        task_manager.create_task(dummy_task(i), name=f"task{i}") for i in range(10)
    ]

    assert task_manager.task_count() == 10

    # Wait for all
    results = await asyncio.gather(*tasks)
    assert results == list(range(10))


@pytest.mark.asyncio
async def test_task_cleanup_on_completion(task_manager):
    """Test tasks are cleaned up after completion"""

    async def quick_task():
        await asyncio.sleep(0.05)

    task = task_manager.create_task(quick_task(), name="quick")

    assert task in task_manager.tasks

    await task
    await asyncio.sleep(0.01)

    # Should be removed
    assert task not in task_manager.tasks


@pytest.mark.asyncio
async def test_wait_all_with_timeout(task_manager):
    """Test wait_all with timeout"""

    async def long_task():
        await asyncio.sleep(10)

    task = task_manager.create_task(long_task(), name="long")

    # Should timeout
    await task_manager.wait_all(timeout=0.1)

    # Clean up
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task


@pytest.mark.asyncio
async def test_callback_exception_handling(task_manager):
    """Test callback exceptions don't break task manager"""

    def bad_callback(task):
        raise RuntimeError("Callback error")

    task_manager.register_completion_callback(bad_callback)

    async def dummy_task():
        await asyncio.sleep(0.1)

    # Should not raise despite callback error
    task = task_manager.create_task(dummy_task(), name="test")
    await task
    await asyncio.sleep(0.01)


@pytest.mark.asyncio
async def test_task_manager_running_state(task_manager):
    """Test task manager running state"""
    assert task_manager.running is True

    async def dummy_task():
        await asyncio.sleep(0.5)

    _task = task_manager.create_task(dummy_task())

    await task_manager.cancel_all()

    assert task_manager.running is False


@pytest.mark.asyncio
async def test_cancel_all_timeout(task_manager):
    """Test cancel_all with very short timeout"""

    async def stubborn_task():
        try:
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            # Ignore cancellation
            await asyncio.sleep(10)

    _task = task_manager.create_task(stubborn_task(), name="stubborn")

    # Cancel with very short timeout
    await task_manager.cancel_all(timeout=0.1)

    # Should have cleared tasks despite timeout
    assert task_manager.task_count() == 0


@pytest.mark.asyncio
async def test_task_execution_respects_priority_order():
    """Higher-priority tasks run before lower-priority tasks."""
    engine = TaskExecutionEngine()
    execution = []

    async def low():
        execution.append("low")
        return "low"

    async def high():
        execution.append("high")
        return "high"

    engine.register_task(
        TaskDefinition(
            name="low",
            coroutine_factory=low,
            priority=TaskPriority.LOW,
        )
    )
    engine.register_task(
        TaskDefinition(
            name="high",
            coroutine_factory=high,
            priority=TaskPriority.HIGH,
        )
    )

    await engine.execute_all()
    assert execution[0] == "high"


@pytest.mark.asyncio
async def test_dependency_resolution_and_sequencing():
    """Dependent tasks run only after prerequisites."""
    engine = TaskExecutionEngine()
    execution = []

    async def first():
        execution.append("first")
        return "done"

    async def second():
        execution.append("second")
        return "done"

    engine.register_task(TaskDefinition(name="first", coroutine_factory=first))
    engine.register_task(
        TaskDefinition(
            name="second",
            coroutine_factory=second,
            dependencies=["first"],
        )
    )

    await engine.execute_all()
    assert execution == ["first", "second"]


@pytest.mark.asyncio
async def test_parallel_execution_of_independent_tasks():
    """Independent tasks of same priority execute in parallel."""
    engine = TaskExecutionEngine()
    starts = []

    async def first():
        starts.append("first")
        await asyncio.sleep(0.05)
        return 1

    async def second():
        starts.append("second")
        await asyncio.sleep(0.05)
        return 2

    engine.register_task(
        TaskDefinition(
            name="first",
            coroutine_factory=first,
            priority=TaskPriority.NORMAL,
        )
    )
    engine.register_task(
        TaskDefinition(
            name="second",
            coroutine_factory=second,
            priority=TaskPriority.NORMAL,
        )
    )

    results = await engine.execute_all()
    assert results["first"] == 1
    assert results["second"] == 2
    assert set(starts) == {"first", "second"}


@pytest.mark.asyncio
async def test_failure_propagation_skips_dependents():
    """Dependent task should be skipped when dependency fails."""
    engine = TaskExecutionEngine()

    async def failing():
        raise RuntimeError("boom")

    async def dependent():
        return "never"

    engine.register_task(TaskDefinition(name="failing", coroutine_factory=failing))
    engine.register_task(
        TaskDefinition(
            name="dependent",
            coroutine_factory=dependent,
            dependencies=["failing"],
        )
    )

    await engine.execute_all()
    assert engine.status["failing"] == TaskExecutionEngine.FAILED
    assert engine.status["dependent"] == TaskExecutionEngine.SKIPPED


@pytest.mark.asyncio
async def test_retry_logic_for_transient_failures():
    """Transient errors should be retried with backoff."""
    engine = TaskExecutionEngine()
    attempts = {"count": 0}

    async def flaky():
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("transient")
        return "ok"

    engine.register_task(
        TaskDefinition(
            name="flaky",
            coroutine_factory=flaky,
            retries=2,
            retry_backoff_seconds=0.01,
        )
    )

    results = await engine.execute_all()
    assert results["flaky"] == "ok"
    assert attempts["count"] == 2
