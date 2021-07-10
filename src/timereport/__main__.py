from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
from PySide6.QtCore import Signal, QItemSelection
from PySide6.QtGui import QCloseEvent, QResizeEvent
from datetime import datetime, date
from pathlib import Path
import sys
from logging import getLogger
from typing import Union
from .model import TableModel, TimeDelegate
from .session import TimeViewType
from . import testdata
from .testdata import load_from_json, save_as_json
from .ui.task_view import Ui_MainWindow

logger = getLogger(__name__)


class TimeReportOverview(QMainWindow):
    # Emit a bool to indicate whether a row is selected or not
    row_selected = Signal(bool)

    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.model = TableModel()
        self.delegate = TimeDelegate()
        self.dirty: bool = False
        self.filepath: Path = None
        self.ui.tableview_days.setModel(self.model)
        self.ui.tableview_days.setItemDelegateForColumn(self.model.HEADERS.index("came"), self.delegate)
        self.ui.tableview_days.setItemDelegateForColumn(self.model.HEADERS.index("went"), self.delegate)

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
        self.ui.actionOpen.triggered.connect(lambda: self.open_db_from_file())
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
        save_as_json(testdata.test_table_days, filepath)
        self.ui.statusbar.showMessage("Saved database", 2000)

    def open_db_from_file(self):
        filepath, ending = QFileDialog.getOpenFileName(self, "Select trep db", filter="trep DB (*.json)")
        if filepath == "":
            self.ui.statusbar.showMessage("Canceled", 2000)
            return

        testdata.test_table_days = load_from_json(Path(filepath))
        self.model.fetch_data()
        self.ui.statusbar.showMessage(f"Opened database {filepath}", 4000)

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
        testdata.test_table_days[dt.date()] = {k: getattr(row, k) for k in row.__dataclass_fields__.keys()}
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
