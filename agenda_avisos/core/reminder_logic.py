from __future__ import annotations

from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

from agenda_avisos.core.models import Reminder, ReminderStatus, RepeatType


def validate_future_datetime(target_dt: datetime) -> None:
    if target_dt <= datetime.now():
        raise ValueError("A data/hora deve estar no futuro.")


def compute_next_occurrence(current: datetime, repeat: RepeatType) -> datetime | None:
    if repeat == RepeatType.NONE:
        return None
    if repeat == RepeatType.DAILY:
        return current + timedelta(days=1)
    if repeat == RepeatType.WEEKLY:
        return current + timedelta(weeks=1)
    if repeat == RepeatType.MONTHLY:
        return current + relativedelta(months=1)
    return None


def apply_popup_ok(reminder: Reminder, trigger_kind: str) -> Reminder:
    if reminder.repeat_type == RepeatType.NONE and trigger_kind == "main":
        reminder.status = ReminderStatus.COMPLETED
    if trigger_kind == "snooze":
        reminder.snooze_until = None
    return reminder
