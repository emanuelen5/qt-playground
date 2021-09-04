from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QFont, QIcon
from .ui.projects import Ui_MainWindow
from .gui_new_project import NewProjectDialog
import sys
from datetime import datetime, time, timedelta
import logging

logger = logging.getLogger(__name__)


class TableModel(QAbstractTableModel):
    HEADERS = ("id", "name", "description", "start_date", "is_active")
    data_updated = Signal(date, date, date)

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
                    return "---" if role == Qt.DisplayRole else datetime.now().time()
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
            d = data[]

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        def_flags = Qt.ItemIsSelectable
        col_name = self.HEADERS[index.column()]
        if col_name in ("came", "went", "note"):
            return Qt.ItemIsEditable | Qt.ItemIsEnabled | def_flags
        return def_flags

    def setData(self, index: QModelIndex, value: Union[str, time], role: int = Qt.EditRole) -> bool:
        day = sorted(self._data.keys())[index.row()]
        col_name = self.HEADERS[index.column()]
        if day not in testdata.test_table_days:
            testdata.test_table_days[day] = dict(came=datetime.now().time(), went=datetime.now().time(), note="")
        if col_name == "came":
            testdata.test_table_days[day][col_name] = value
            testdata.test_table_days[day]["went"] = max(value, testdata.test_table_days[day]["went"])
        elif col_name == "went":
            testdata.test_table_days[day][col_name] = value
            testdata.test_table_days[day]["came"] = min(value, testdata.test_table_days[day]["came"])
        elif col_name in ("note", ):
            testdata.test_table_days[day][col_name] = value
        else:
            logger.error(f"Unhandled column {col_name}")
            return False
        self.dataChanged.emit(index, index, [])
        return True

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



class ProjectWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tableView.setModel()

        self.ui.actionNew.triggered.connect(self.on_new_project)
        self.new_project_dialog = NewProjectDialog(self)

    def on_new_project(self):
        response, accepted = self.new_project_dialog.exec()
        if accepted:
            id_, name, description, start_date = response
            print(id_, name, description, start_date)


def main():
    app = QApplication(sys.argv)
    projects = ProjectWindow()
    projects.show()
    app.exec()


if __name__ == "__main__":
    main()
