from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, QItemSelection, QSize
from PySide6.QtGui import QIcon, QFont, QColor
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


class Palette(Enum):
    Red = QColor(239, 71, 111)
    Yellow = QColor(255, 209, 102)
    Green = QColor(6, 214, 160)
    Blue = QColor(17, 138, 178)
    Dark = QColor(7, 59, 76)


class RowColors(Enum):
    Today = Palette.Green.value
    Weekend = QColor(150, 150, 150)


def timedelta_to_time(td: timedelta) -> time:
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hours, minutes, seconds, td.microseconds)


def time_to_timedelta(t: time) -> timedelta:
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)


# A test database with some came and went times
test_table_days = {
    date.today() + timedelta(days=i): {
        "came": timedelta_to_time(timedelta(hours=8, minutes=30) + timedelta(seconds=randint(-60*60, 60*60))),
        "went": timedelta_to_time(timedelta(hours=17, minutes=00) + timedelta(seconds=randint(-60*60, 60*60))),
        "note": None
    } for i in range(-2, 3)
}

test_table_days[sorted(test_table_days.keys())[0]]["note"] = "Here is a testnote with some details about the specific date"


@dataclass
class Row:
    date: date
    came: time
    went: time
    total: timedelta
    note: str


class TableModel(QAbstractTableModel):
    HEADERS = ("week", "weekday", "came", "went", "total", "note")

    def __init__(self):
        super().__init__()
        self._data: dict[date, Row] = {}
        self.time_view_type = TimeViewType.MONTH
        self.view_date = date.today()
        self.fetch_data()

    def fetch_data(self):
        if self.time_view_type == TimeViewType.AROUND_DAY:
            start_day = self.view_date - timedelta(days=10)
            end_day = self.view_date + timedelta(days=10)
        elif self.time_view_type == TimeViewType.WEEK:
            year, week, day = self.view_date.isocalendar()
            start_day = date.fromisocalendar(year, week, 1)
            end_day = date.fromisocalendar(year, week, 7)
        elif self.time_view_type == TimeViewType.MONTH:
            start_day = date(self.view_date.year, self.view_date.month, 1)
            end_day = date(self.view_date.year, self.view_date.month+1, 1) + timedelta(days=-1)
        else:
            start_day = end_day = self.view_date

        wanted_days = (start_day + timedelta(days=i) for i in range((end_day - start_day).days + 1))
        self._data = {}
        for day in wanted_days:
            try:
                data = test_table_days[day]
                came = data["came"]
                went = data["went"]
                total = time_to_timedelta(went) - time_to_timedelta(came)
                self._data[day] = Row(day, came, went, total, data["note"])
            except KeyError:
                self._data[day] = Row(day, None, None, None, None)
        self.layoutChanged.emit()

    def set_view_type(self, time_view_type: TimeViewType):
        if time_view_type == self.time_view_type:
            return
        self.time_view_type = time_view_type
        self.fetch_data()

    def data(self, index: QModelIndex, role: int):
        dt = sorted(self._data.keys())[index.row()]
        row = self._data[dt]
        data = [dt.isocalendar().week, dt.strftime("%A"), row.came, row.went, row.total, row.note]

        if role == Qt.DisplayRole:
            d = data[index.column()]
            if d is None:
                return "---"
            else:
                return str(d)

        elif role == Qt.BackgroundRole:
            day = sorted(self._data.keys())[index.row()]
            if day == datetime.today().date():
                return RowColors.Today.value
            elif day.weekday() >= 5:
                return RowColors.Weekend.value

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.HEADERS[section].capitalize()
            elif orientation == Qt.Vertical:
                day = sorted(self._data.keys())[section]
                return str(day)

        elif role == Qt.FontRole:
            font = QFont()
            font.setBold(True)
            return font

        elif role == Qt.BackgroundRole:
            if orientation == Qt.Vertical:
                day = sorted(self._data.keys())[section]
                if day == datetime.today().date():
                    return RowColors.Today.value
                elif day.weekday() >= 5:
                    return RowColors.Weekend.value

        elif role == Qt.DecorationRole:
            if orientation == Qt.Vertical:
                day = sorted(self._data.keys())[section]
                row = self._data[day]
                return QIcon.fromTheme("emblem-default") if row.total else QIcon.fromTheme("image-missing") if day.weekday() < 5 and day <= date.today() else None

        elif role == Qt.TextAlignmentRole:
            if orientation == Qt.Vertical:
                return Qt.AlignRight

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

    def scroll_to_today(self):
        self.view_date = date.today()
        self.fetch_data()

    def scroll(self, forward: bool):
        if self.time_view_type in (TimeViewType.MONTH, TimeViewType.WEEK):
            days_jump = len(self._data)
        else:
            days_jump = 1
        days_jump = days_jump if forward else -days_jump
        self.view_date += timedelta(days=days_jump)
        self.fetch_data()


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
        self.ui.actionMonth_view.triggered.connect(lambda: self.model.set_view_type(TimeViewType.MONTH))
        self.ui.actionWeek_view.triggered.connect(lambda: self.model.set_view_type(TimeViewType.WEEK))
        self.ui.actionAround_view.triggered.connect(lambda: self.model.set_view_type(TimeViewType.AROUND_DAY))
        self.ui.actionDay_view.triggered.connect(lambda: self.model.set_view_type(TimeViewType.DAY))
        self.ui.actionGotoToday.triggered.connect(self.model.scroll_to_today)
        self.ui.actionGotoPrevious.triggered.connect(lambda: self.model.scroll(forward=False))
        self.ui.actionGotoNext.triggered.connect(lambda: self.model.scroll(forward=True))

    def selection_changed(self, sel: QItemSelection, dsel: QItemSelection):
        self.row_selected.emit(len(sel.indexes()) != 0)


if __name__ == '__main__':
    app = QApplication([])
    w = TimeReportOverview()
    w.show()
    sys.exit(app.exec())
