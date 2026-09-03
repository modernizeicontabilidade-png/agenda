import sys

from PySide6.QtWidgets import QApplication

from agenda_avisos.db.database import Database
from agenda_avisos.ui.main_window import MainWindow
from agenda_avisos.utils.logging_config import setup_logging


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)

    db = Database()
    window = MainWindow(db)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
