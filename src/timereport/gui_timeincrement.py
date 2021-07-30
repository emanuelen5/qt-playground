from PySide6.QtWidgets import QApplication, QDialog
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from .ui.timeincrement import Ui_Dialog
from datetime import time, datetime
import sys


class TimeIncrement(QDialog):
    def __init__(self, in_time: time, parent=None):
        super().__init__(parent)
        self.in_time = in_time
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.spin_hour.valueChanged.connect(lambda i: self.update_time())
        self.ui.spin_minutes.valueChanged.connect(lambda i: self.update_time())

        # Make the children call eventFilter on this Widget
        self.ui.spin_hour.installEventFilter(self)
        self.ui.spin_minutes.installEventFilter(self)

        # Preselect hour increment so it's easy to type the time
        self.ui.spin_hour.selectAll()
        self.ui.time_in.setText(in_time.strftime("%H:%M"))
        self.update_time()

    def update_time(self) -> None:
        res_hours, res_minutes = self.get_result_time()
        self.ui.time_result.setText(f"{res_hours: 2d}:{res_minutes:02d}")

    def get_result_time(self) -> tuple[int, int]:
        res_hours, res_minutes = divmod((self.in_time.hour + self.ui.spin_hour.value()) * 60 +
                                        (self.in_time.minute + self.ui.spin_minutes.value()), 60)
        return res_hours, res_minutes

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> bool:
        key = chr(event.key() & 0xFF).lower()
        if key == 'q' or event.key() == Qt.Key.Key_Escape:
            self.reject()
            return True
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept()
            return True
        return False

    def eventFilter(self, target: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """
        Propagate keypress events to the parent.
        See https://flylib.com/books/en/2.18.1/installing_event_filters.html
        """
        if event.type() is QtCore.QEvent.KeyPress:
            return self.keyPressEvent(event)
        return super().eventFilter(target, event)

    def exec(self) -> tuple[bool, int, int]:
        """
        :return: changed: bool, hours: int, minutes: int
        """
        accepted = super().exec()
        if accepted:
            res_hours, res_minutes = self.get_result_time()
            return True, res_hours, res_minutes
        return False, self.in_time.hour, self.in_time.minute


def main():
    QApplication(sys.argv)
    tinc = TimeIncrement(datetime.now().time())
    return tinc.exec()


if __name__ == "__main__":
    sys.exit(main())
