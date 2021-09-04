from PySide6.QtWidgets import QDialog, QWidget
from .ui.new_project import Ui_Dialog
from datetime import datetime
from typing import Union

RESPONSE = tuple[str, str, str, datetime]


class NewProjectDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

    def exec(self) -> Union[tuple[RESPONSE, bool], tuple[None, bool]]:
        accepted = super().exec()
        if not accepted:
            return None, False
        id_ = self.ui.input_id.text()
        name = self.ui.input_name.text()
        description = self.ui.input_description.text()
        start_date = self.ui.date_start.dateTime().toPython()
        return (id_, name, description, start_date), True
