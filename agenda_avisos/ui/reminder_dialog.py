from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QTimeEdit,
    QVBoxLayout,
)

from agenda_avisos.core.models import Reminder, ReminderStatus, RepeatType
from agenda_avisos.core.reminder_logic import validate_future_datetime


class ReminderDialog(QDialog):
    def __init__(self, parent=None, reminder: Reminder | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Novo lembrete" if reminder is None else "Editar lembrete")
        self.reminder = reminder
        self.result_reminder: Reminder | None = None

        self.title_edit = QLineEdit()
        self.msg_edit = QTextEdit()

        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())

        self.time_edit = QTimeEdit()
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setTime(QTime.currentTime())

        self.repeat_combo = QComboBox()
        self.repeat_combo.addItem("Nenhuma", RepeatType.NONE)
        self.repeat_combo.addItem("Diária", RepeatType.DAILY)
        self.repeat_combo.addItem("Semanal", RepeatType.WEEKLY)
        self.repeat_combo.addItem("Mensal", RepeatType.MONTHLY)

        self._build_layout()
        if reminder:
            self._populate(reminder)

    def _build_layout(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow(QLabel("Título"), self.title_edit)
        form.addRow(QLabel("Mensagem"), self.msg_edit)
        form.addRow(QLabel("Data"), self.date_edit)
        form.addRow(QLabel("Hora"), self.time_edit)
        form.addRow(QLabel("Repetição"), self.repeat_combo)

        buttons = QHBoxLayout()
        save_btn = QPushButton("Salvar")
        cancel_btn = QPushButton("Cancelar")
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)

        layout.addLayout(form)
        layout.addLayout(buttons)

    def _populate(self, reminder: Reminder) -> None:
        self.title_edit.setText(reminder.title)
        self.msg_edit.setPlainText(reminder.message)
        self.date_edit.setDate(QDate(reminder.next_run_at.year, reminder.next_run_at.month, reminder.next_run_at.day))
        self.time_edit.setTime(QTime(reminder.next_run_at.hour, reminder.next_run_at.minute))
        index = self.repeat_combo.findData(reminder.repeat_type)
        if index >= 0:
            self.repeat_combo.setCurrentIndex(index)

    def _on_save(self) -> None:
        title = self.title_edit.text().strip()
        message = self.msg_edit.toPlainText().strip()
        if not title or not message:
            QMessageBox.warning(self, "Validação", "Título e mensagem são obrigatórios.")
            return

        date = self.date_edit.date().toPython()
        time = self.time_edit.time().toPython()
        next_run = datetime(date.year, date.month, date.day, time.hour, time.minute)

        try:
            validate_future_datetime(next_run)
        except ValueError as exc:
            QMessageBox.warning(self, "Validação", str(exc))
            return

        repeat_type = self.repeat_combo.currentData()
        self.result_reminder = Reminder(
            id=self.reminder.id if self.reminder else None,
            title=title,
            message=message,
            next_run_at=next_run,
            repeat_type=repeat_type,
            status=self.reminder.status if self.reminder else ReminderStatus.ACTIVE,
            snooze_until=None,
            last_fired_at=self.reminder.last_fired_at if self.reminder else None,
            created_at=self.reminder.created_at if self.reminder else None,
            updated_at=self.reminder.updated_at if self.reminder else None,
        )
        self.accept()
