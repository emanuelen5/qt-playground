from PySide6.QtWidgets import QApplication, QDialog
from PySide6 import QtCore, QtGui
from .ui.timeincrement import Ui_Dialog
from datetime import time, datetime
import sys


class TimeIncrement(QDialog):
    def __init__(self, in_time: time, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.ui.spin_hour.valueChanged.connect(lambda i: self.update_time())
        self.ui.spin_minutes.valueChanged.connect(lambda i: self.update_time())

        # Make the children call eventFilter on this Widget
        self.ui.spin_hour.installEventFilter(self)
        self.ui.spin_minutes.installEventFilter(self)

        # Preselect hour increment so it's easy to type the time
        self.ui.spin_hour.selectAll()
        self.ui.time_in.setTime(in_time)
        self.update_time()

    def update_time(self) -> None:
        t = self.ui.time_in.time()
        res_hours, res_minutes = divmod((t.hour() + self.ui.spin_hour.value()) * 60 +
                                        (t.minute() + self.ui.spin_minutes.value()), 60)
        self.ui.time_result.setTime(time(res_hours, res_minutes))

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        key = chr(event.key() & 0xFF).lower()
        if key == 'q':
            self.reject()
        else:
            super().keyPressEvent(event)

    def eventFilter(self, target: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """ Propagate keypress events to the parent """
        if event.type() is QtCore.QEvent.KeyPress:
            self.keyPressEvent(event)
        return False


def main():
    QApplication(sys.argv)
    tinc = TimeIncrement(datetime.now().time())
    return tinc.exec()


if __name__ == "__main__":
    sys.exit(main())
