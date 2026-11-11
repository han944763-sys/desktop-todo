from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class Task:
    id: int
    title: str
    task_date: date
    is_completed: bool
    completed_at: datetime | None
    project_id: int | None
    source_action: str | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Project:
    id: int
    name: str
    goal: str
    current_stage: str
    next_action: str
    is_archived: bool
    created_at: datetime
    updated_at: datetime

