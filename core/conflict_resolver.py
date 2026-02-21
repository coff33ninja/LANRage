"""Conflict detection and resolution for concurrent operations."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import Enum

from .logging_config import get_logger, set_context, timing_decorator
from .operation_lock import AtomicOperation, OperationLockManager
from .task_manager import TaskPriority

logger = get_logger(__name__)

CONFLICTING_OPS = {
    "configure_network": {"configure_network", "restart_network"},
    "restart_network": {"configure_network", "restart_network"},
    "allocate_ip": {"allocate_ip"},
    "join_party": {"leave_party"},
    "leave_party": {"join_party"},
}


class ResolutionStrategy(str, Enum):
    """Available conflict resolution strategies."""

    QUEUE = "queue"
    ABORT = "abort"
    PRIORITIZE = "prioritize"
    MERGE = "merge"


@dataclass
class OperationSpec:
    """Operation with metadata for conflict resolution."""

    resource_id: str
    operation_type: str
    priority: TaskPriority
    execute: Callable[[], Awaitable[object]]
    rollback: Callable[[], Awaitable[object]] | None = None


class ConflictResolver:
    """Detects and resolves operation conflicts."""

    def __init__(self, lock_manager: OperationLockManager | None = None):
        self.lock_manager = lock_manager or OperationLockManager()

    @staticmethod
    def has_conflict(first_op_type: str, second_op_type: str) -> bool:
        """Check if two operation types conflict."""
        return second_op_type in CONFLICTING_OPS.get(first_op_type, set())

    def resolve_strategy(
        self, first: OperationSpec, second: OperationSpec
    ) -> ResolutionStrategy:
        """Choose conflict resolution strategy."""
        if not self.has_conflict(first.operation_type, second.operation_type):
            return ResolutionStrategy.QUEUE
        if first.operation_type == second.operation_type:
            if first.priority != second.priority:
                return ResolutionStrategy.PRIORITIZE
            return ResolutionStrategy.QUEUE
        if first.priority != second.priority:
            return ResolutionStrategy.PRIORITIZE
        return ResolutionStrategy.ABORT

    @timing_decorator(name="resolve_conflicts")
    async def resolve_pair(self, first: OperationSpec, second: OperationSpec) -> object:
        """Resolve and execute two operations."""
        set_context(correlation_id_val=f"{first.operation_type}:{second.operation_type}")
        strategy = self.resolve_strategy(first, second)
        logger.warning(
            "Conflict resolution strategy=%s for %s vs %s on %s",
            strategy.value,
            first.operation_type,
            second.operation_type,
            first.resource_id,
        )

        if strategy == ResolutionStrategy.ABORT:
            raise RuntimeError(
                f"Conflicting operations aborted: {first.operation_type} vs {second.operation_type}"
            )

        if strategy == ResolutionStrategy.PRIORITIZE:
            chosen = first if first.priority >= second.priority else second
            return await self.lock_manager.execute_atomic(
                [
                    AtomicOperation(
                        resource_id=chosen.resource_id,
                        operation=chosen.execute,
                        rollback=chosen.rollback,
                    )
                ]
            )

        # QUEUE and fallback path: run sequentially under lock manager.
        return await self.lock_manager.execute_atomic(
            [
                AtomicOperation(
                    resource_id=first.resource_id,
                    operation=first.execute,
                    rollback=first.rollback,
                ),
                AtomicOperation(
                    resource_id=second.resource_id,
                    operation=second.execute,
                    rollback=second.rollback,
                ),
            ]
        )
