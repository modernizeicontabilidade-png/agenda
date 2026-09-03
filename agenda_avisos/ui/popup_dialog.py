from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout


class ReminderPopup(QDialog):
    def __init__(self, title: str, message: str, overdue: bool, parent=None) -> None:
        super().__init__(parent)
        self.action = "ok"
        self.setWindowTitle("Atrasado" if overdue else "Lembrete")
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)
        self.setModal(True)
        self.resize(420, 220)

        label_title = QLabel(f"<b>{title}</b>")
        label_msg = QLabel(message)
        label_msg.setWordWrap(True)

        buttons_row1 = QHBoxLayout()
        for text, action in [("OK", "ok"), ("Soneca (5 min)", "snooze_5"), ("Soneca (15 min)", "snooze_15")]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _=False, a=action: self._finish(a))
            buttons_row1.addWidget(btn)

        buttons_row2 = QHBoxLayout()
        for text, action in [("Adiar para amanhã", "tomorrow"), ("Marcar como concluído", "complete")]:
            btn = QPushButton(text)
            btn.clicked.connect(lambda _=False, a=action: self._finish(a))
            buttons_row2.addWidget(btn)

        layout = QVBoxLayout(self)
        layout.addWidget(label_title)
        layout.addWidget(label_msg)
        layout.addLayout(buttons_row1)
        layout.addLayout(buttons_row2)

    def _finish(self, action: str) -> None:
        self.action = action
        self.accept()
