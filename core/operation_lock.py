"""Resource lock manager for concurrent operation coordination."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .logging_config import get_logger, timing_decorator

logger = get_logger(__name__)


@dataclass
class AtomicOperation:
    """Operation metadata for atomic execution."""

    resource_id: str
    operation: Callable[[], Awaitable[object]]
    rollback: Callable[[], Awaitable[object]] | None = None


class OperationLockManager:
    """Per-resource lock manager with atomic multi-resource execution support."""

    def __init__(self):
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    async def _get_lock(self, resource_id: str) -> asyncio.Lock:
        async with self._global_lock:
            if resource_id not in self._locks:
                self._locks[resource_id] = asyncio.Lock()
            return self._locks[resource_id]

    async def acquire_lock(self, resource_id: str) -> asyncio.Lock:
        """Acquire lock for a single resource and return lock object."""
        lock = await self._get_lock(resource_id)
        await lock.acquire()
        return lock

    @timing_decorator(name="execute_atomic_operations")
    async def execute_atomic(self, operations: list[AtomicOperation]) -> list[object]:
        """Execute operations atomically with rollback on failure."""
        ordered = sorted(operations, key=lambda op: op.resource_id)
        acquired_locks: list[asyncio.Lock] = []
        completed: list[AtomicOperation] = []
        results: list[object] = []

        try:
            unique_resource_ids = sorted({op.resource_id for op in ordered})
            for resource_id in unique_resource_ids:
                lock = await self.acquire_lock(resource_id)
                acquired_locks.append(lock)

            for op in ordered:
                result = await op.operation()
                results.append(result)
                completed.append(op)

            return results
        except Exception as exc:
            logger.warning("Atomic execution failed, triggering rollback: %s", exc)
            for op in reversed(completed):
                if op.rollback is None:
                    continue
                try:
                    await op.rollback()
                except Exception as rollback_exc:
                    logger.error("Rollback failed for %s: %s", op.resource_id, rollback_exc)
            raise
        finally:
            for lock in reversed(acquired_locks):
                if lock.locked():
                    lock.release()
