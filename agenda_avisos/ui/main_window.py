from __future__ import annotations

import logging
from datetime import datetime

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from agenda_avisos.core.models import ReminderStatus
from agenda_avisos.core.reminder_logic import apply_popup_ok
from agenda_avisos.core.startup import is_windows_startup_enabled, set_windows_startup
from agenda_avisos.db.database import Database
from agenda_avisos.scheduler.reminder_scheduler import ReminderScheduler
from agenda_avisos.ui.popup_dialog import ReminderPopup
from agenda_avisos.ui.reminder_dialog import ReminderDialog

logger = logging.getLogger(__name__)


class TriggerBridge(QObject):
    triggered = Signal(int, str, bool)


class MainWindow(QMainWindow):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle("AgendaAvisos")
        self.resize(900, 500)

        self.bridge = TriggerBridge()
        self.bridge.triggered.connect(self._show_popup)

        self.scheduler = ReminderScheduler(db, self._scheduler_trigger_callback)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Título", "Próxima execução", "Repetição", "Status", "Soneca até"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.startup_checkbox = QCheckBox("Iniciar com Windows")
        self.startup_checkbox.setChecked(is_windows_startup_enabled())
        self.startup_checkbox.stateChanged.connect(self._toggle_startup)

        self._build_ui()
        self.refresh_table()
        self.scheduler.start()

    def closeEvent(self, event):
        self.scheduler.shutdown()
        super().closeEvent(event)

    def _build_ui(self) -> None:
        toolbar = QToolBar("Ações")
        self.addToolBar(toolbar)

        new_action = QAction("Novo", self)
        edit_action = QAction("Editar", self)
        delete_action = QAction("Excluir", self)
        complete_action = QAction("Concluir", self)

        new_action.triggered.connect(self._new_reminder)
        edit_action.triggered.connect(self._edit_reminder)
        delete_action.triggered.connect(self._delete_reminder)
        complete_action.triggered.connect(self._complete_reminder)

        toolbar.addAction(new_action)
        toolbar.addAction(edit_action)
        toolbar.addAction(delete_action)
        toolbar.addAction(complete_action)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.table)

        settings_row = QHBoxLayout()
        settings_row.addWidget(self.startup_checkbox)
        settings_row.addStretch()

        reload_btn = QPushButton("Atualizar")
        reload_btn.clicked.connect(self.refresh_table)
        settings_row.addWidget(reload_btn)

        layout.addLayout(settings_row)
        self.setCentralWidget(container)

    def refresh_table(self) -> None:
        reminders = self.db.list_reminders()
        self.table.setRowCount(len(reminders))

        for row, reminder in enumerate(reminders):
            values = [
                str(reminder.id),
                reminder.title,
                reminder.next_run_at.strftime("%d/%m/%Y %H:%M"),
                reminder.repeat_type.value,
                reminder.status.value,
                reminder.snooze_until.strftime("%d/%m/%Y %H:%M") if reminder.snooze_until else "-",
            ]
            for col, value in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(value))

        self.table.resizeColumnsToContents()

    def _selected_reminder_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return int(self.table.item(row, 0).text())

    def _new_reminder(self) -> None:
        dialog = ReminderDialog(self)
        if dialog.exec() and dialog.result_reminder:
            reminder_id = self.db.add_reminder(dialog.result_reminder)
            reminder = self.db.get_reminder(reminder_id)
            self.scheduler.schedule_reminder(reminder)
            self.refresh_table()

    def _edit_reminder(self) -> None:
        reminder_id = self._selected_reminder_id()
        if not reminder_id:
            QMessageBox.warning(self, "Ação", "Selecione um lembrete.")
            return

        reminder = self.db.get_reminder(reminder_id)
        dialog = ReminderDialog(self, reminder)
        if dialog.exec() and dialog.result_reminder:
            self.db.update_reminder(dialog.result_reminder)
            self.scheduler.schedule_reminder(dialog.result_reminder)
            self.refresh_table()

    def _delete_reminder(self) -> None:
        reminder_id = self._selected_reminder_id()
        if not reminder_id:
            QMessageBox.warning(self, "Ação", "Selecione um lembrete.")
            return
        self.scheduler.unschedule_reminder(reminder_id)
        self.db.delete_reminder(reminder_id)
        self.refresh_table()

    def _complete_reminder(self) -> None:
        reminder_id = self._selected_reminder_id()
        if not reminder_id:
            QMessageBox.warning(self, "Ação", "Selecione um lembrete.")
            return
        self.scheduler.mark_completed(reminder_id)
        self.refresh_table()

    def _scheduler_trigger_callback(self, reminder_id: int, trigger_kind: str, overdue: bool) -> None:
        self.bridge.triggered.emit(reminder_id, trigger_kind, overdue)

    def _show_popup(self, reminder_id: int, trigger_kind: str, overdue: bool) -> None:
        reminder = self.db.get_reminder(reminder_id)
        if not reminder or reminder.status != ReminderStatus.ACTIVE:
            return

        self.showNormal()
        self.raise_()
        self.activateWindow()

        popup = ReminderPopup(reminder.title, reminder.message, overdue, self)
        popup.exec()

        if popup.action == "snooze_5":
            self.scheduler.snooze(reminder_id, 5)
        elif popup.action == "snooze_15":
            self.scheduler.snooze(reminder_id, 15)
        elif popup.action == "tomorrow":
            self.scheduler.postpone_to_tomorrow(reminder_id)
        elif popup.action == "complete":
            self.scheduler.mark_completed(reminder_id)
        else:
            current = self.db.get_reminder(reminder_id)
            if current:
                updated = apply_popup_ok(current, trigger_kind)
                self.db.update_reminder(updated)
                self.scheduler.schedule_reminder(updated)

        self.refresh_table()

    def _toggle_startup(self, state: int) -> None:
        enabled = state == Qt.Checked
        try:
            set_windows_startup(enabled)
            self.db.set_setting("start_with_windows", "1" if enabled else "0")
        except Exception as exc:
            logger.exception("Falha ao alterar startup")
            QMessageBox.critical(self, "Erro", f"Não foi possível alterar startup: {exc}")
            self.startup_checkbox.setChecked(not enabled)
