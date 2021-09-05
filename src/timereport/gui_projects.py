from PySide6.QtWidgets import QApplication, QMainWindow, QTableView, QHeaderView, QWidget, QStyledItemDelegate, QDateEdit, QStyleOptionViewItem
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QFont, QColor
from .ui.projects import Ui_MainWindow
from .gui_new_project import NewProjectDialog
import sys
from datetime import date
from typing import Any
from .testdata import test_table_projects
from threading import Lock
import logging

logger = logging.getLogger(__name__)


COLOR_GRAY = QColor(128, 128, 128)
COLOR_WHITE = QColor(255, 255, 255)


class DateDelegate(QStyledItemDelegate):
    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex):
        editor = QDateEdit(parent)
        editor.setDisplayFormat("%Y-%m-%d")
        return editor

    def setEditorData(self, editor: QDateEdit, index: QModelIndex):
        value = index.model().data(index, Qt.EditRole)
        editor.setDate(value)

    def setModelData(self, editor: QDateEdit, model: QAbstractTableModel, index: QDateEdit):
        editor.interpretText()
        t = editor.date()
        model.setData(index, date(t.year(), t.month(), t.day()), Qt.EditRole)

    def updateEditorGeometry(self, editor: QDateEdit, option: QStyleOptionViewItem, index: QDateEdit):
        editor.setGeometry(option.rect)


class TableModel(QAbstractTableModel):
    HEADERS = ("id", "name", "description", "start date", "active")

    def __init__(self, view: QTableView):
        super().__init__()
        self.view = view
        self._data_lock = Lock()
        self._data = test_table_projects

    def setup_column_width(self, view: QTableView):
        """ Set up the preferred width of each column """
        for i, h in enumerate(self.HEADERS):
            sizepolicy = QHeaderView.ResizeToContents if h != "description" else QHeaderView.Stretch
            view.horizontalHeader().setSectionResizeMode(i, sizepolicy)
        view.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

    def data(self, index: QModelIndex, role: Qt.ItemDataRole):
        data = self._data[index.row()]
        col_name = self.HEADERS[index.column()]
        d = data[index.column()]

        if role in (Qt.DisplayRole, Qt.EditRole):
            if col_name == "active":
                return
            elif col_name == "start date":
                if role == Qt.EditRole:
                    return data[index.column()]
                elif role == Qt.DisplayRole:
                    return d.strftime("%Y-%m-%d")
            else:
                return str(d)

        if role == Qt.CheckStateRole and col_name == "active":
            return d

        if role == Qt.BackgroundRole:
            return COLOR_WHITE if data[self.HEADERS.index("active")] else COLOR_GRAY

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        d = self._data[index.row()]
        is_active = d[self.HEADERS.index("active")]
        if index.column() == self.HEADERS.index("active"):
            return Qt.ItemIsEnabled | Qt.ItemIsUserCheckable
        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable if is_active else Qt.ItemIsSelectable

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.HEADERS[section].capitalize()
            elif orientation == Qt.Vertical:
                return ""

        elif role == Qt.FontRole:
            font = QFont()
            font.setBold(True)
            return font

        elif role == Qt.BackgroundRole:
            if orientation == Qt.Vertical:
                data = test_table_projects[section]
                return COLOR_WHITE if data[self.HEADERS.index("active")] else COLOR_GRAY

        elif role == Qt.TextAlignmentRole:
            if orientation == Qt.Vertical:
                return Qt.AlignRight

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        col_name = self.HEADERS[index.column()]
        if col_name == "active":
            self._data[index.row()][index.column()] = not self._data[index.row()][index.column()]
            self.view.dataChanged(self.createIndex(index.row(), 0), self.createIndex(index.row(), 4))
        elif col_name == "start date":
            self._data[index.row()][index.column()] = value
        else:
            self._data[index.row()][index.column()] = value
        return True

    def rowCount(self, index: QModelIndex) -> int:
        return len(self._data)

    def columnCount(self, index: QModelIndex) -> int:
        return len(self.HEADERS)


class ProjectWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.model = TableModel(self.ui.tableView)
        self.ui.tableView.setModel(self.model)
        self.model.setup_column_width(self.ui.tableView)
        self.date_delegate = DateDelegate(self)
        self.ui.tableView.setItemDelegateForColumn(self.model.HEADERS.index("start date"), self.date_delegate)

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
