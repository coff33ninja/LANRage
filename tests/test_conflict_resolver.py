"""Tests for concurrent operation conflict resolution."""

import asyncio

import pytest

from core.conflict_resolver import ConflictResolver, OperationSpec, ResolutionStrategy
from core.operation_lock import AtomicOperation, OperationLockManager
from core.task_manager import TaskPriority


@pytest.mark.asyncio
async def test_conflict_detection_between_incompatible_operations():
    resolver = ConflictResolver()
    assert resolver.has_conflict("configure_network", "restart_network") is True
    assert resolver.has_conflict("allocate_ip", "join_party") is False


@pytest.mark.asyncio
async def test_queue_strategy_waits_for_second_operation():
    lock_manager = OperationLockManager()
    resolver = ConflictResolver(lock_manager)
    order = []

    async def first():
        order.append("first-start")
        await asyncio.sleep(0.05)
        order.append("first-end")
        return "first"

    async def second():
        order.append("second")
        return "second"

    first_spec = OperationSpec(
        resource_id="party-1",
        operation_type="allocate_ip",
        priority=TaskPriority.NORMAL,
        execute=first,
    )
    second_spec = OperationSpec(
        resource_id="party-1",
        operation_type="allocate_ip",
        priority=TaskPriority.NORMAL,
        execute=second,
    )

    strategy = resolver.resolve_strategy(first_spec, second_spec)
    assert strategy == ResolutionStrategy.QUEUE

    await resolver.resolve_pair(first_spec, second_spec)
    assert order == ["first-start", "first-end", "second"]


@pytest.mark.asyncio
async def test_prioritization_high_priority_operation_succeeds():
    resolver = ConflictResolver()
    executed = []

    async def low():
        executed.append("low")
        return "low"

    async def high():
        executed.append("high")
        return "high"

    low_spec = OperationSpec(
        resource_id="party-1",
        operation_type="restart_network",
        priority=TaskPriority.LOW,
        execute=low,
    )
    high_spec = OperationSpec(
        resource_id="party-1",
        operation_type="restart_network",
        priority=TaskPriority.CRITICAL,
        execute=high,
    )

    result = await resolver.resolve_pair(low_spec, high_spec)
    assert executed == ["high"]
    assert result[0] == "high"


@pytest.mark.asyncio
async def test_merging_equivalent_with_atomic_execution():
    lock_manager = OperationLockManager()
    values = []

    async def op_one():
        values.append(1)
        return 1

    async def op_two():
        values.append(2)
        return 2

    results = await lock_manager.execute_atomic(
        [
            AtomicOperation(resource_id="party-1", operation=op_one),
            AtomicOperation(resource_id="party-1", operation=op_two),
        ]
    )
    assert values == [1, 2]
    assert results == [1, 2]


@pytest.mark.asyncio
async def test_rollback_on_failure_in_multi_operation_transaction():
    lock_manager = OperationLockManager()
    state = {"value": 0}

    async def increment():
        state["value"] += 1
        return state["value"]

    async def rollback_increment():
        state["value"] -= 1
        return state["value"]

    async def fail():
        raise RuntimeError("fail second op")

    with pytest.raises(RuntimeError):
        await lock_manager.execute_atomic(
            [
                AtomicOperation(
                    resource_id="resource-a",
                    operation=increment,
                    rollback=rollback_increment,
                ),
                AtomicOperation(resource_id="resource-b", operation=fail),
            ]
        )

    assert state["value"] == 0
