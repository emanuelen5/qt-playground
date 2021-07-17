from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtCore import QTime
from .ui.settings import Ui_SettingsDialog
from .session import SessionSettings
import sys


class SettingsDialog(QDialog):
    def __init__(self, session_settings: SessionSettings, parent=None):
        super().__init__(parent)
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)
        self.session_settings = session_settings

        self.ui.time_lunch_from.timeChanged.connect(self.update_lunch_from_time)
        self.ui.time_lunch_to.timeChanged.connect(self.update_lunch_to_time)

    def update_lunch_from_time(self, t: QTime):
        if self.ui.time_lunch_to.time() < t:
            self.ui.time_lunch_to.setTime(t)

    def update_lunch_to_time(self, t: QTime):
        if self.ui.time_lunch_from.time() > t:
            self.ui.time_lunch_from.setTime(t)

    def accept(self) -> None:
        super().accept()


def main():
    QApplication(sys.argv)
    session_settings = SessionSettings()
    dialog = SettingsDialog(session_settings)
    accept = dialog.exec()
    print(accept)


if __name__ == "__main__":
    main()
