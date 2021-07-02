import sys
from typing import Union

from PySide6.QtWidgets import (
    QApplication, QMessageBox, QMainWindow, QPushButton,
    QTreeView, QHBoxLayout, QVBoxLayout, QWidget, QInputDialog, QTableView
)
from PySide6.QtCore import QSize, QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt


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

        self.tree = QTableView()
        self.model = TableModel()
        self.tree.setModel(self.model)

        self.button_add_task = QPushButton(text="Add task")
        self.button_add_task.clicked.connect(self.add_task)
        self.button_remove_task = QPushButton(text="Remove task")
        self.button_remove_task.clicked.connect(self.remove_task)

        self.tree.selectionModel().selectionChanged.connect(self.selection_changed)

        widget = QWidget()
        add_remove_layout = QHBoxLayout()
        widget.setLayout(add_remove_layout)
        add_remove_layout.addWidget(self.button_add_task)
        add_remove_layout.addWidget(self.button_remove_task)

        self.vlayout = QVBoxLayout()
        self.vlayout.addWidget(self.tree)
        self.vlayout.addWidget(widget)

        widget = QWidget()
        widget.setLayout(self.vlayout)

        self.setCentralWidget(widget)

    def selection_changed(self, sel, dsel):
        print(self.tree.selectionModel().selectedRows())
        print("Selection changed to: ", sel, dsel)
        # self.button_remove_task.setEnabled

    def add_task(self):
        taskname, got_input = QInputDialog.getText(self, "Task name", "What is the name of the task?", inputMethodHints=Qt.ImhPreferLatin)
        if got_input:
            self.model.add_task(taskname)

    def remove_task(self):
        indexes = self.tree.selectedIndexes()
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
