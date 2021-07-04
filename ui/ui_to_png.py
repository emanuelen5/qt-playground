from PySide6.QtWidgets import QApplication
from PySide6.QtUiTools import QUiLoader
from argparse import ArgumentParser
from pathlib import Path
import sys

parser = ArgumentParser("Takes in .ui-files, renders them and saves them as .png-files")
parser.add_argument("ui_files", nargs="+", help="Path to a .ui-file")
args = parser.parse_args()

app = QApplication([])
loader = QUiLoader()

for ui_file in args.ui_files:
    filepath = Path(ui_file)
    if not filepath.is_file():
        print(f"{filepath} is not a file. Skipping...", file=sys.stdout)
        continue

    ui = loader.load(str(filepath))
    ui.grab().save(filepath.stem + ".png")
