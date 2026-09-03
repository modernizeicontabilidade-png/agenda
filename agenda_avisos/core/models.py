from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class RepeatType(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReminderStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass(slots=True)
class Reminder:
    id: Optional[int]
    title: str
    message: str
    next_run_at: datetime
    repeat_type: RepeatType
    status: ReminderStatus
    snooze_until: Optional[datetime] = None
    last_fired_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
