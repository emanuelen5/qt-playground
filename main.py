import sys

from PySide6.QtWidgets import (
    QApplication, QMessageBox, QMainWindow, QPushButton,
    QTreeView, QHBoxLayout, QVBoxLayout, QWidget, QInputDialog, QTableView
)
from PySide6.QtCore import QSize, QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt, Signal, QItemSelection
from PySide6.QtGui import QIcon
from ui.task_view import Ui_MainWindow


class TableModel(QAbstractTableModel):
    HEADERS = ("Task name", )

    def __init__(self):
        super().__init__()
        self._data = [(False, "asd"), (False, "asd2"), (True, "other task")]

    def data(self, index: QModelIndex, role: int):
        status, name = self._data[index.row()]
        if role == Qt.DisplayRole:
            return name

        elif role == Qt.DecorationRole:
            return QIcon.fromTheme("emblem-default") if status else QIcon.fromTheme("emblem-unreadable")

    def headerData(self, section: int, orientation: Qt.Orientation, role: int):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.HEADERS[section]
            elif orientation == Qt.Vertical:
                return

    def rowCount(self, index: QModelIndex) -> int:
        return len(self._data)

    def columnCount(self, index: QModelIndex) -> int:
        return 1

    def add_task(self, taskname: str):
        self._data.append((False, taskname))
        self.layoutChanged.emit()

    def remove_task(self, row: int):
        if 0 <= row < len(self._data):
            del self._data[row]
            self.layoutChanged.emit()


class ToDoList(QMainWindow):
    # Emit a bool to indicate whether a row is selected or not
    row_selected = Signal(bool)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.model = TableModel()
        self.ui.tableview_tasks.setModel(self.model)

        self.ui.tableview_tasks.selectionModel().selectionChanged.connect(self.selection_changed)

        self.ui.btn_add_task.clicked.connect(self.add_task)
        self.ui.btn_task_done.clicked.connect(self.remove_task)
        self.row_selected.connect(self.ui.btn_task_done.setEnabled)
        self.row_selected.emit(False)

    def selection_changed(self, sel: QItemSelection, dsel: QItemSelection):
        self.row_selected.emit(len(sel.indexes()) != 0)

    def add_task(self):
        taskname, got_input = QInputDialog.getText(self, "Task name", "What is the name of the task?", inputMethodHints=Qt.ImhPreferLatin)
        if got_input:
            self.model.add_task(taskname)

    def remove_task(self):
        indexes = self.ui.tableview_tasks.selectedIndexes()
        if indexes:
            rows = set(ind.row() for ind in indexes)
            tasknames = ", ".join([self.model._data[row][1] for row in rows])
            inp = QMessageBox.information(self, "Remove task?", f"Remove {len(rows)} task(s): {tasknames}?", buttons=QMessageBox.Yes | QMessageBox.No)
            if inp == QMessageBox.Yes:
                # Must delete backwards otherwise they change indices along the way
                for row in sorted(rows, reverse=True):
                    self.model.remove_task(row)
                self.ui.tableview_tasks.clearSelection()
                self.row_selected.emit(False)


if __name__ == '__main__':
    app = QApplication([])
    w = ToDoList()
    w.show()
    sys.exit(app.exec())
