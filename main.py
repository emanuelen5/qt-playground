from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, QItemSelection
from PySide6.QtGui import QIcon
from ui.task_view import Ui_MainWindow
from dataclasses import dataclass
from datetime import datetime, time, timedelta, date
from enum import Enum, unique, auto
from random import randint
import sys


@unique
class TimeViewType(Enum):
    DAY = auto()
    WEEK = auto()
    MONTH = auto()
    AROUND_DAY = auto()


def timedelta_to_time(td: timedelta) -> time:
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hours, minutes, seconds, td.microseconds)


def time_to_timedelta(t: time) -> timedelta:
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)


# A test database with some came and went times
test_table_days = {
    date.today() + timedelta(days=i): {
        "came": timedelta_to_time(timedelta(8, 30) + timedelta(minutes=randint(-60, 60))),
        "went": timedelta_to_time(timedelta(17, 00) + timedelta(minutes=randint(-60, 60))),
        "note": None
    } for i in range(-2, 3)
}


@dataclass
class Row:
    date: date
    came: time
    went: time
    total: timedelta


class TableModel(QAbstractTableModel):
    HEADERS = tuple(field.capitalize() for field in Row.__dataclass_fields__.keys())

    def __init__(self):
        super().__init__()
        self._data: tuple[Row] = {}
        self.time_view_type = TimeViewType.MONTH
        self.view_date = date.today()
        self.fetch_data()

    def fetch_data(self):
        if self.time_view_type == TimeViewType.AROUND_DAY:
            start_day = self.view_date - timedelta(days=2)
            end_day = self.view_date + timedelta(days=2)
        elif self.time_view_type == TimeViewType.WEEK:
            year, week, day = self.view_date.isocalendar()
            start_day = date.fromisocalendar(year, week, 0)
            end_day = date.fromisocalendar(year, week, 5)
        elif self.time_view_type == TimeViewType.MONTH:
            start_day = date(self.view_date.year, self.view_date.month, 1)
            end_day = date(self.view_date.year, self.view_date.month+1, 1) + timedelta(days=-1)
        else:
            start_day = end_day = date.today()

        wanted_days = (start_day + timedelta(days=i) for i in range((end_day - start_day).days + 1))
        self._data = {}
        for day in wanted_days:
            try:
                data = test_table_days[day]
                came = data["came"]
                went = data["went"]
                total = time_to_timedelta(went) - time_to_timedelta(came)
                self._data[day] = Row(day, came, went, total)
            except KeyError:
                self._data[day] = Row(day, None, None, None)
        self.layoutChanged.emit()

    def set_view_type(self, time_view_type: TimeViewType):
        if time_view_type == self.time_view_type:
            return
        self.time_view_type = time_view_type
        self.fetch_data()

    def data(self, index: QModelIndex, role: int):
        dt = sorted(self._data.keys())[index.row()]
        row = self._data[dt]
        data = [row.date, row.came, row.went, row.total]

        if role == Qt.DisplayRole:
            d = data[index.column()]
            if isinstance(d, timedelta):
                return str(d)
            else:
                return str(d)

        elif role == Qt.DecorationRole:
            if self.HEADERS[index.column()].lower() == "total":
                return QIcon.fromTheme("emblem-default") if row.total else QIcon.fromTheme("image-missing")

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.HEADERS[section]
            elif orientation == Qt.Vertical:
                return str(sorted(self._data.keys())[section])

    def rowCount(self, index: QModelIndex) -> int:
        return len(self._data)

    def columnCount(self, index: QModelIndex) -> int:
        return len(self.HEADERS)

    def add_task(self, taskname: str):
        self._data.append((False, taskname))
        self.layoutChanged.emit()

    def remove_task(self, row: int):
        if 0 <= row < len(self._data):
            del self._data[row]
            self.layoutChanged.emit()


class TimeReportOverview(QMainWindow):
    # Emit a bool to indicate whether a row is selected or not
    row_selected = Signal(bool)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.model = TableModel()
        self.ui.tableview_days.setModel(self.model)

        self.ui.tableview_days.selectionModel().selectionChanged.connect(self.selection_changed)

    def selection_changed(self, sel: QItemSelection, dsel: QItemSelection):
        self.row_selected.emit(len(sel.indexes()) != 0)


if __name__ == '__main__':
    app = QApplication([])
    w = TimeReportOverview()
    w.show()
    sys.exit(app.exec())
