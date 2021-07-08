from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal, QItemSelection, QSize
from PySide6.QtGui import QIcon, QFont, QColor, QCloseEvent, QResizeEvent
from .ui.task_view import Ui_MainWindow
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta, date
from enum import Enum, unique, auto
from pathlib import Path
import json
from random import randint
import sys
import threading
from logging import getLogger
from typing import Union

logger = getLogger(__name__)


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
        "note": ""
    } for i in range(-2, 3)
}

test_table_days[sorted(test_table_days.keys())[0]]["note"] = "Here is a testnote with some details about the specific date"


@dataclass
class SessionSettings:
    # Default value
    time_view_type: TimeViewType = TimeViewType.MONTH
    view_date: date = date.today()
    window_size: QSize = QSize(300, 600)
    recent_files: list[Path] = field(default_factory=lambda: [])

    # Serialize function, Deserialize function
    serdes = {
        "time_view_type": (lambda v: v.name, lambda s: TimeViewType[s]),
        "view_date": (lambda v: v.strftime("%Y-%m-%d"), lambda s: datetime.strptime(s, "%Y-%m-%d").date()),
        "window_size": (lambda v: dict(w=v.width(), h=v.height()), lambda s: QSize(s["w"], s["h"])),
        "recent_files": (lambda v: [str(f.absolute()) for f in v], lambda s: [Path(f) for f in s])
    }

    def load(self, filepath: Path):
        if not filepath.exists():
            logger.info(f"The session file {filepath.absolute()} does not exist. No changes.")
            return

        with open(filepath, 'r') as f:
            file_dict = json.loads(f.read())
        for prop in self.__dataclass_fields__.keys():
            if prop not in self.serdes:
                logger.warning(f"Missing deserializer for property {prop}.")
                continue

            _, deserialize = self.serdes[prop]
            try:
                value = deserialize(file_dict[prop])
                setattr(self, prop, value)
            except KeyError:
                logger.warning(f"Key {prop} missing in session file. Skipping.")
            except BaseException as e:
                logger.exception(f"Error while serializing {prop}.")
                continue

    def save(self, filepath: Path):
        kwargs = dict()
        for prop in self.__dataclass_fields__.keys():
            if prop not in self.serdes:
                logger.warning(f"Missing serializer for property {prop}.")
                continue
            value = getattr(self, prop)
            serialize, _ = self.serdes[prop]
            try:
                value = serialize(getattr(self, prop))
            except KeyError:
                logger.error(f"Key {prop} missing in session setting. Skipping.")
            except BaseException as e:
                logger.warning(f"Error while serializing {prop}. Got the following error: {e}")
                continue
            kwargs[prop] = value

        with open(filepath, 'w') as f:
            f.write(json.dumps(kwargs, sort_keys=True, indent=4))


@dataclass
class Row:
    date: date
    came: time
    went: time
    total: timedelta
    note: str


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
                    return d.strftime("%H:%M")
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

    def setData(self, index: QModelIndex, value: str, role: int = Qt.EditRole) -> bool:
        day = sorted(self._data.keys())[index.row()]
        col_name = self.HEADERS[index.column()]
        if col_name in ("came", "went"):
            for fmt in ("%H:%M:%s.%f", "%H:%M:%s", "%H:%M", "%H"):
                try:
                    test_table_days[day][col_name] = datetime.strptime(value, fmt)
                    self.dataChanged.emit(index, index, [])
                    return True
                except ValueError:
                    pass
            return False
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

    def add_task(self, taskname: str):
        self._data.append((False, taskname))
        self.layoutChanged.emit()

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


class TimeReportOverview(QMainWindow):
    # Emit a bool to indicate whether a row is selected or not
    row_selected = Signal(bool)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.model = TableModel()
        self.dirty: bool = False
        self.filepath: Path = None
        self.ui.tableview_days.setModel(self.model)

        self.ui.tableview_days.selectionModel().selectionChanged.connect(self.selection_changed)
        self.ui.actionMonth_view.triggered.connect(lambda: self.model.set_view_type(TimeViewType.MONTH))
        self.ui.actionWeek_view.triggered.connect(lambda: self.model.set_view_type(TimeViewType.WEEK))
        self.ui.actionAround_view.triggered.connect(lambda: self.model.set_view_type(TimeViewType.AROUND_DAY))
        self.ui.actionDay_view.triggered.connect(lambda: self.model.set_view_type(TimeViewType.DAY))
        self.ui.actionGotoToday.triggered.connect(self.model.scroll_to_today)
        self.ui.actionGotoPrevious.triggered.connect(lambda: self.model.scroll(forward=False))
        self.ui.actionGotoNext.triggered.connect(lambda: self.model.scroll(forward=True))
        self.ui.actionUpdate_came_went_time.triggered.connect(self.update_came_went)
        self.ui.actionSave.triggered.connect(lambda: self.save_db_to_file(self.filepath))
        self.ui.actionSave_As.triggered.connect(lambda: self.save_db_to_file(None))
        self.model.data_updated.connect(self.update_current_period)

        self.model.session_settings.load(Path(".timereport-session.json"))
        self.resize(self.model.session_settings.window_size)
        self.model.fetch_data()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.dirty:
            resp = QMessageBox.warning(
                self,
                "You have unsaved changes",
                "You have unsaved changes. Do you want to save them before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,

            )
            if resp == QMessageBox.Yes:
                self.save_db_to_file(self.filepath)
            elif resp == QMessageBox.Cancel:
                self.ui.statusbar.showMessage("Canceled. Database still has unsaved changes.")
                event.ignore()
        logger.debug("Saving session settings")
        self.model.session_settings.save(Path(".timereport-session.json"))

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.model.session_settings.window_size = event.size()

    def get_save_location(self) -> Union[Path, None]:
        # Cannot use QFileDialog.saveFileDialog with a default saving suffix, so using this way
        dialog = QFileDialog(self, "Select where to save the trep database", "trep.db.json", "trep DB (*.json)")
        dialog.setModal(True)
        dialog.setDefaultSuffix("json")
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setAcceptMode(QFileDialog.AcceptSave)
        # Preselecting file does not seem to work when running from Pycharm. Not using native dialogs fixes it,
        # but looks worse, i.e.:
        # dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.selectFile("trep.db.json")
        if dialog.exec():
            return Path(dialog.selectedFiles()[0])

    def save_db_to_file(self, filepath: Path = None):
        if filepath is None:
            filepath = self.get_save_location()

            if filepath is None:
                # User canceled "save as dialog" before
                self.ui.statusbar.showMessage("Canceled", 1000)
                return
            self.filepath = filepath

        logger.info(f"Saving as {self.filepath}")
        data = json.dumps(test_table_days)
        with open(self.filepath, 'w') as f:
            f.write(data)
        self.ui.statusbar.showMessage("Saved database", 2000)

    def update_current_period(self, view_date: date, start_date: date, end_date: date):
        if self.model.session_settings.time_view_type == TimeViewType.MONTH:
            period = view_date.strftime("%B, %Y")
        elif self.model.session_settings.time_view_type == TimeViewType.WEEK:
            period = f"Week {view_date.strftime('%V, %Y')}"
        elif self.model.session_settings.time_view_type == TimeViewType.DAY:
            period = str(view_date)
        else:
            period = f"{start_date} - {end_date}"
        self.ui.lbl_current_period.setText(period)

    def update_came_went(self):
        dt = datetime.now()
        row = self.model._data[dt.date()]
        row.came = min(dt.time(), row.came)
        row.went = max(dt.time(), row.went)
        test_table_days[dt.date()] = {k: getattr(row, k) for k in row.__dataclass_fields__.keys()}
        self.model.fetch_data()

    def selection_changed(self, sel: QItemSelection, dsel: QItemSelection):
        self.row_selected.emit(len(sel.indexes()) != 0)


def main():
    app = QApplication([])
    w = TimeReportOverview()
    w.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
