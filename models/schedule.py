from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TaskSchedule:
    task_id: str
    task_name: str
    start_date: str
    end_date: str
    duration_days: int
    dependencies: list[str] = field(default_factory=list)
    is_critical: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            'task_id': self.task_id,
            'task_name': self.task_name,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'duration_days': self.duration_days,
            'dependencies': list(self.dependencies),
            'is_critical': self.is_critical,
        }


@dataclass(slots=True)
class ScheduleResult:
    project_start_date: str
    project_end_date: str
    tasks: list[TaskSchedule] = field(default_factory=list)
    critical_path: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'project_start_date': self.project_start_date,
            'project_end_date': self.project_end_date,
            'tasks': [item.to_dict() for item in self.tasks],
            'critical_path': list(self.critical_path),
        }
