from PySide6.QtWidgets import QApplication, QMainWindow
from .ui.projects import Ui_MainWindow
import sys


class ProjectWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)


def main():
    app = QApplication(sys.argv)
    projects = ProjectWindow()
    projects.show()
    app.exec()


if __name__ == "__main__":
    main()