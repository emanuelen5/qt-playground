from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
from PySide6.QtGui import QIcon, QFont, QColor
from PySide6 import QtCore, QtWidgets
from dataclasses import dataclass
from datetime import datetime, time, timedelta, date
from enum import Enum
from typing import Union
import threading
from logging import getLogger
from .session import SessionSettings, TimeViewType
from .testdata import test_table_days
from .util import time_to_timedelta

logger = getLogger(__name__)


class Palette(Enum):
    Red = QColor(239, 71, 111)
    Yellow = QColor(255, 209, 102)
    Green = QColor(6, 214, 160)
    Blue = QColor(17, 138, 178)
    Dark = QColor(7, 59, 76)


class RowColors(Enum):
    Today = Palette.Green.value
    Weekend = QColor(150, 150, 150)


@dataclass
class Row:
    date: date
    came: time
    went: time
    total: timedelta
    note: str
    

class TimeDelegate(QtWidgets.QStyledItemDelegate):
    def createEditor(self, parent: QtWidgets.QWidget, option: QtWidgets.QStyleOptionViewItem, index: QModelIndex):
        editor = QtWidgets.QTimeEdit(parent)
        editor.setDisplayFormat("hh:mm")
        return editor

    def setEditorData(self, editor: QtWidgets.QTimeEdit, index: QModelIndex):
        value = index.model().data(index, QtCore.Qt.EditRole)
        editor.setTime(value)

    def setModelData(self, editor: QtWidgets.QTimeEdit, model: QAbstractTableModel, index: QtWidgets.QTimeEdit):
        editor.interpretText()
        t = editor.time()
        model.setData(index, time(t.hour(), t.minute()), QtCore.Qt.EditRole)

    def updateEditorGeometry(self, editor: QtWidgets.QTimeEdit, option: QtWidgets.QStyleOptionViewItem, index: QtWidgets.QTimeEdit):
        editor.setGeometry(option.rect)


class TableModel(QAbstractTableModel):
    HEADERS = ("week", "weekday", "came", "went", "total", "note")
    data_updated = Signal(date, date, date)

    def __init__(self):
        super().__init__()
        self._data_lock = threading.Lock()
        self._data: dict[date, Row] = {}
        self.columns = []
        self.headers = []
        self.session_settings = SessionSettings()
        self.dataChanged.connect(lambda *args: self.fetch_data())

    def fetch_data(self):
        if self.session_settings.time_view_type == TimeViewType.AROUND_DAY:
            start_day = self.session_settings.view_date - timedelta(days=10)
            end_day = self.session_settings.view_date + timedelta(days=10)
        elif self.session_settings.time_view_type == TimeViewType.WEEK:
            year, week, day = self.session_settings.view_date.isocalendar()
            start_day = date.fromisocalendar(year, week, 1)
            end_day = date.fromisocalendar(year, week, 7)
        elif self.session_settings.time_view_type == TimeViewType.MONTH:
            start_day = date(self.session_settings.view_date.year, self.session_settings.view_date.month, 1)
            # Get last day of month: https://stackoverflow.com/a/13565185/4713758
            next_month = date(self.session_settings.view_date.year, self.session_settings.view_date.month, 28) + timedelta(days=4)
            end_day = next_month - timedelta(days=next_month.day)
        else:
            start_day = end_day = self.session_settings.view_date

        wanted_days = (start_day + timedelta(days=i) for i in range((end_day - start_day).days + 1))
        new_data = {}
        for day in wanted_days:
            try:
                data = test_table_days[day]
                came = data["came"]
                went = data["went"]
                total = time_to_timedelta(went) - time_to_timedelta(came)
                new_data[day] = Row(day, came, went, total, data["note"])
            except KeyError:
                new_data[day] = Row(day, None, None, None, None)
        with self._data_lock:
            self._data = new_data
        self.data_updated.emit(self.session_settings.view_date, start_day, end_day)
        self.layoutChanged.emit()

    def set_view_type(self, time_view_type: TimeViewType):
        if time_view_type == self.session_settings.time_view_type:
            return
        self.session_settings.time_view_type = time_view_type
        self.fetch_data()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        with self._data_lock:
            day = sorted(self._data.keys())[index.row()]
            row = self._data[day]
        data = [day.isocalendar().week, day.strftime("%A"), row.came, row.went, row.total, row.note]

        if role in (Qt.DisplayRole, Qt.EditRole):
            d = data[index.column()]
            col_name = self.HEADERS[index.column()]
            if col_name in ("came", "went"):
                if d is None:
                    return "---"
                elif role == Qt.DisplayRole:
                    return d.strftime("%H:%M:%S")
                elif role == Qt.EditRole:
                    return d
            elif col_name in ("total", ):
                if d is None:
                    return ""
                else:
                    return str(d)
            elif col_name in ("note", ):
                return d
            return str(d)

        elif role == Qt.BackgroundRole:
            if day == datetime.today().date():
                return RowColors.Today.value
            elif day.weekday() >= 5:
                return RowColors.Weekend.value

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        def_flags = Qt.ItemIsSelectable
        col_name = self.HEADERS[index.column()]
        if col_name in ("came", "went", "note"):
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | def_flags
        return def_flags

    def setData(self, index: QModelIndex, value: Union[str, time], role: int = Qt.EditRole) -> bool:
        day = sorted(self._data.keys())[index.row()]
        col_name = self.HEADERS[index.column()]
        if col_name in ("came", "went"):
            test_table_days[day][col_name] = value
            self.dataChanged.emit(index, index, [])
            return True
        elif col_name in ("note", ):
            test_table_days[day]["note"] = value
            self.dataChanged.emit(index, index, [])
            return True
        logger.error(f"Unhandled column {col_name}")
        return False

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if orientation == Qt.Vertical:
            with self._data_lock:
                day = sorted(self._data.keys())[section]
                row = self._data[day]

        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.HEADERS[section].capitalize()
            elif orientation == Qt.Vertical:
                return str(day)

        elif role == Qt.FontRole:
            font = QFont()
            font.setBold(True)
            return font

        elif role == Qt.BackgroundRole:
            if orientation == Qt.Vertical:
                if day == datetime.today().date():
                    return RowColors.Today.value
                elif day.weekday() >= 5:
                    return RowColors.Weekend.value

        elif role == Qt.DecorationRole:
            if orientation == Qt.Vertical:
                return QIcon.fromTheme("emblem-default") if row.total else \
                    QIcon.fromTheme("image-missing") if day.weekday() < 5 and day <= date.today() else \
                        None

        elif role == Qt.TextAlignmentRole:
            if orientation == Qt.Vertical:
                return Qt.AlignRight

    def rowCount(self, index: QModelIndex) -> int:
        return len(self._data)

    def columnCount(self, index: QModelIndex) -> int:
        return len(self.HEADERS)

    def remove_task(self, row: int):
        with self._data_lock:
            if 0 <= row < len(self._data):
                del self._data[row]
                self.layoutChanged.emit()

    def scroll_to_today(self):
        self.session_settings.view_date = date.today()
        self.fetch_data()

    def scroll(self, forward: bool):
        if self.session_settings.time_view_type in (TimeViewType.MONTH, TimeViewType.WEEK):
            days_jump = len(self._data)
        else:
            days_jump = 1
        days_jump = days_jump if forward else -days_jump
        self.session_settings.view_date += timedelta(days=days_jump)
        self.fetch_data()
