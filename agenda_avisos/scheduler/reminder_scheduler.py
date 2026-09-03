from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from agenda_avisos.core.models import Reminder, ReminderStatus
from agenda_avisos.core.reminder_logic import compute_next_occurrence
from agenda_avisos.db.database import Database

logger = logging.getLogger(__name__)


class ReminderScheduler:
    def __init__(self, db: Database, on_trigger: Callable[[int, str, bool], None]) -> None:
        self.db = db
        self.on_trigger = on_trigger
        self.scheduler = BackgroundScheduler()

    def start(self) -> None:
        self.scheduler.start()
        self.reload_all()
        self.process_overdue()

    def shutdown(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

    def reload_all(self) -> None:
        self.scheduler.remove_all_jobs()
        for reminder in self.db.list_active_reminders():
            self.schedule_reminder(reminder)

    def schedule_reminder(self, reminder: Reminder) -> None:
        if reminder.status != ReminderStatus.ACTIVE:
            return

        job_id_main = f"reminder_main_{reminder.id}"
        if reminder.next_run_at:
            self._safe_remove_job(job_id_main)
            self.scheduler.add_job(
                self._fire_main,
                trigger=DateTrigger(run_date=reminder.next_run_at),
                args=[reminder.id],
                id=job_id_main,
                replace_existing=True,
                misfire_grace_time=3600,
            )

        if reminder.snooze_until:
            job_id_snooze = f"reminder_snooze_{reminder.id}"
            self._safe_remove_job(job_id_snooze)
            self.scheduler.add_job(
                self._fire_snooze,
                trigger=DateTrigger(run_date=reminder.snooze_until),
                args=[reminder.id],
                id=job_id_snooze,
                replace_existing=True,
                misfire_grace_time=3600,
            )

    def unschedule_reminder(self, reminder_id: int) -> None:
        self._safe_remove_job(f"reminder_main_{reminder_id}")
        self._safe_remove_job(f"reminder_snooze_{reminder_id}")

    def snooze(self, reminder_id: int, minutes: int) -> None:
        reminder = self.db.get_reminder(reminder_id)
        if not reminder:
            return
        reminder.snooze_until = datetime.now() + timedelta(minutes=minutes)
        self.db.update_reminder(reminder)
        self.schedule_reminder(reminder)

    def postpone_to_tomorrow(self, reminder_id: int) -> None:
        reminder = self.db.get_reminder(reminder_id)
        if not reminder:
            return

        if reminder.repeat_type.value == "none":
            reminder.next_run_at = datetime.now() + timedelta(days=1)
        else:
            reminder.snooze_until = datetime.now() + timedelta(days=1)

        self.db.update_reminder(reminder)
        self.schedule_reminder(reminder)

    def mark_completed(self, reminder_id: int) -> None:
        reminder = self.db.get_reminder(reminder_id)
        if not reminder:
            return
        reminder.status = ReminderStatus.COMPLETED
        reminder.snooze_until = None
        self.db.update_reminder(reminder)
        self.unschedule_reminder(reminder_id)

    def process_overdue(self) -> None:
        now = datetime.now()
        for reminder in self.db.list_overdue_reminders():
            if reminder.next_run_at <= now:
                self._prepare_next_if_needed(reminder, is_main=True)
                self.on_trigger(reminder.id, "main", True)

            if reminder.snooze_until and reminder.snooze_until <= now:
                reminder.snooze_until = None
                self.db.update_reminder(reminder)
                self.on_trigger(reminder.id, "snooze", True)

            latest = self.db.get_reminder(reminder.id)
            if latest:
                self.schedule_reminder(latest)

    def _fire_main(self, reminder_id: int) -> None:
        reminder = self.db.get_reminder(reminder_id)
        if not reminder or reminder.status != ReminderStatus.ACTIVE:
            return

        self._prepare_next_if_needed(reminder, is_main=True)
        self.on_trigger(reminder.id, "main", False)

    def _fire_snooze(self, reminder_id: int) -> None:
        reminder = self.db.get_reminder(reminder_id)
        if not reminder or reminder.status != ReminderStatus.ACTIVE:
            return
        reminder.snooze_until = None
        self.db.update_reminder(reminder)
        self.on_trigger(reminder.id, "snooze", False)

    def _prepare_next_if_needed(self, reminder: Reminder, is_main: bool) -> None:
        if is_main:
            reminder.last_fired_at = datetime.now()
            next_dt = compute_next_occurrence(reminder.next_run_at, reminder.repeat_type)
            if next_dt:
                while next_dt <= datetime.now():
                    next_dt = compute_next_occurrence(next_dt, reminder.repeat_type)
                reminder.next_run_at = next_dt
            else:
                reminder.next_run_at = datetime.now()
            self.db.update_reminder(reminder)

    def _safe_remove_job(self, job_id: str) -> None:
        try:
            self.scheduler.remove_job(job_id)
        except Exception:
            logger.debug("Job %s inexistente para remoção", job_id)
