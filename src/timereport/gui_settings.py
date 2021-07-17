from PySide6.QtWidgets import QDialog, QApplication
from PySide6.QtCore import QTime
from .ui.settings import Ui_SettingsDialog
from .session import SessionSettings
from datetime import time, timedelta
import sys


def qtime_to_time(t: QTime) -> time:
    return time(t.hour(), t.minute(), t.second())


class SettingsDialog(QDialog):
    def __init__(self, session_settings: SessionSettings, parent=None):
        super().__init__(parent)
        self.ui = Ui_SettingsDialog()
        self.ui.setupUi(self)
        self.session_settings = session_settings

        self.ui.time_lunch_from.timeChanged.connect(self.update_lunch_from_time)
        self.ui.time_lunch_to.timeChanged.connect(self.update_lunch_to_time)

        # Default values
        self.ui.time_lunch_from.setTime(self.session_settings.lunch_interval[0])
        self.ui.time_lunch_to.setTime(self.session_settings.lunch_interval[1])

    def update_lunch_from_time(self, t: QTime):
        if self.ui.time_lunch_to.time() < t:
            self.ui.time_lunch_to.setTime(t)
        self.update_total_time()

    def update_lunch_to_time(self, t: QTime):
        if self.ui.time_lunch_from.time() > t:
            self.ui.time_lunch_from.setTime(t)
        self.update_total_time()

    def update_total_time(self):
        to_time = self.ui.time_lunch_to.time()
        from_time = self.ui.time_lunch_from.time()
        t = timedelta(hours=to_time.hour(), minutes=to_time.minute(), seconds=to_time.second()) - \
            timedelta(hours=from_time.hour(), minutes=from_time.minute(), seconds=from_time.second())
        self.ui.lbl_lunch_total_out.setText(str(int(t.total_seconds() / 60)))

    def accept(self) -> None:
        super().accept()
        self.session_settings.lunch_interval = [
            qtime_to_time(self.ui.time_lunch_from.time()),
            qtime_to_time(self.ui.time_lunch_to.time())
        ]


def main():
    QApplication(sys.argv)
    session_settings = SessionSettings()
    dialog = SettingsDialog(session_settings)
    accept = dialog.exec()
    print("Accept?", accept)


if __name__ == "__main__":
    main()
