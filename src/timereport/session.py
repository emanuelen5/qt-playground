from PySide6.QtCore import QSize
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import auto, Enum, unique
from logging import getLogger
from pathlib import Path
import json

logger = getLogger(__name__)


@unique
class TimeViewType(Enum):
    DAY = auto()
    WEEK = auto()
    MONTH = auto()
    AROUND_DAY = auto()


@dataclass
class SessionSettings:
    # Default value
    time_view_type: TimeViewType = TimeViewType.MONTH
    view_date: date = date.today()
    window_size: QSize = QSize(300, 600)
    recent_files: list[Path] = field(default_factory=lambda: [])

    # Serialize function, Deserialize function
    serdes = {
        "time_view_type": (lambda v: v.name, lambda s: TimeViewType[s]),
        "view_date": (lambda v: v.strftime("%Y-%m-%d"), lambda s: datetime.strptime(s, "%Y-%m-%d").date()),
        "window_size": (lambda v: dict(w=v.width(), h=v.height()), lambda s: QSize(s["w"], s["h"])),
        "recent_files": (lambda v: [str(f.absolute()) for f in v], lambda s: [Path(f) for f in s])
    }

    def load(self, filepath: Path):
        if not filepath.exists():
            logger.info(f"The session file {filepath.absolute()} does not exist. No changes.")
            return

        with open(filepath, 'r') as f:
            file_dict = json.loads(f.read())
        for prop in self.__dataclass_fields__.keys():
            if prop not in self.serdes:
                logger.warning(f"Missing deserializer for property {prop}.")
                continue

            _, deserialize = self.serdes[prop]
            try:
                value = deserialize(file_dict[prop])
                setattr(self, prop, value)
            except KeyError:
                logger.warning(f"Key {prop} missing in session file. Skipping.")
            except BaseException as e:
                logger.exception(f"Error while serializing {prop}.")
                continue

    def save(self, filepath: Path):
        kwargs = dict()
        for prop in self.__dataclass_fields__.keys():
            if prop not in self.serdes:
                logger.warning(f"Missing serializer for property {prop}.")
                continue
            value = getattr(self, prop)
            serialize, _ = self.serdes[prop]
            try:
                value = serialize(getattr(self, prop))
            except KeyError:
                logger.error(f"Key {prop} missing in session setting. Skipping.")
            except BaseException as e:
                logger.warning(f"Error while serializing {prop}. Got the following error: {e}")
                continue
            kwargs[prop] = value

        with open(filepath, 'w') as f:
            f.write(json.dumps(kwargs, sort_keys=True, indent=4))
