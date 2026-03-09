"""In-memory task manager for tracking async video processing jobs."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class TaskInfo:
    task_id: str
    status: str = "pending"  # pending | processing | completed | failed
    progress: float = 0.0
    message: str = ""
    result: dict[str, Any] | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class TaskManager:
    """Simple in-memory task tracker. Stores status for background jobs."""

    def __init__(self):
        self._tasks: dict[str, TaskInfo] = {}

    def create_task(self) -> str:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = TaskInfo(task_id=task_id)
        return task_id

    def get_task(self, task_id: str) -> TaskInfo | None:
        return self._tasks.get(task_id)

    def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        progress: float | None = None,
        message: str | None = None,
        result: dict[str, Any] | None = None,
    ):
        task = self._tasks.get(task_id)
        if not task:
            return
        if status is not None:
            task.status = status
        if progress is not None:
            task.progress = progress
        if message is not None:
            task.message = message
        if result is not None:
            task.result = result

    def cleanup_old_tasks(self, max_age_hours: int = 24):
        now = datetime.now(timezone.utc)
        to_remove = [
            tid
            for tid, t in self._tasks.items()
            if (now - t.created_at).total_seconds() > max_age_hours * 3600
        ]
        for tid in to_remove:
            del self._tasks[tid]


# Global singleton
task_manager = TaskManager()
