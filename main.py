import sys

from PySide6.QtWidgets import (
    QApplication, QMessageBox, QMainWindow, QPushButton,
    QTreeView, QHBoxLayout, QVBoxLayout, QWidget, QInputDialog, QTableView
)
from PySide6.QtCore import QSize, QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt
from ui.task_view import Ui_MainWindow


class TableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self._data = [(False, "asd"), (False, "asd2")]

    def data(self, index: QModelIndex, role: int):
        if role == Qt.DisplayRole:
            return self._data[index.row()][index.column()]

    def rowCount(self, index: QModelIndex) -> int:
        return len(self._data)

    def columnCount(self, index: QModelIndex) -> int:
        return 2

    def add_task(self, taskname: str):
        self._data.append((False, taskname))
        self.layoutChanged.emit()

    def remove_task(self, row: int):
        if 0 <= row < len(self._data):
            del self._data[row]
            self.layoutChanged.emit()


class ToDoList(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.model = TableModel()
        self.ui.tableview_tasks.setModel(self.model)

        self.ui.tableview_tasks.selectionModel().selectionChanged.connect(self.selection_changed)

        self.ui.btn_add_task.clicked.connect(self.add_task)
        self.ui.btn_task_done.clicked.connect(self.remove_task)

    def selection_changed(self, sel, dsel):
        print(self.ui.tableview_tasks.selectionModel().selectedRows())
        print("Selection changed to: ", sel, dsel)
        # self.button_remove_task.setEnabled

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
                for row in sorted(rows, reverse=True):
                    self.model.remove_task(row)


if __name__ == '__main__':
    app = QApplication([])
    w = ToDoList()
    w.show()
    sys.exit(app.exec())
