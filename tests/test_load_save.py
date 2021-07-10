from unittest import TestCase
from tempfile import TemporaryDirectory
from pathlib import Path
from timereport.testdata import test_table_days, load_from_json, save_as_json


class TestSaveLoad(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.dir = TemporaryDirectory(dir=Path(__file__).parent)

    def test_load_save(self):
        db_path = Path(self.dir.name).joinpath("trep.db.json")
        save_as_json(test_table_days, db_path)
        load_from_json(db_path)
