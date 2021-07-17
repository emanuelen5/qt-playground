from datetime import timedelta, date, datetime, time
from random import randint
from .util import timedelta_to_time
from pathlib import Path
import json
from copy import deepcopy


# A test database with some came and went times
test_table_days = {
    date.today() + timedelta(days=i): {
        "came": timedelta_to_time(timedelta(hours=8, minutes=30) + timedelta(seconds=randint(-60*60, 60*60))),
        "went": timedelta_to_time(timedelta(hours=17, minutes=00) + timedelta(seconds=randint(-60*60, 60*60))),
        "note": ""
    } for i in range(-2, 3)
}

test_table_days[sorted(test_table_days.keys())[0]]["note"] = "Here is a testnote with some details about the specific date"


def save_as_json(db: dict[date, dict], filename: Path):
    db = deepcopy(db)  # To avoid editing in the original dict

    def time_to_str(t: time):
        return t.strftime("%H:%M:%S")

    # Transform data into JSON serializable format
    transformed_data = {}
    for k, d in db.items():
        k = k.strftime("%Y-%m-%d")
        d["came"] = time_to_str(d["came"])
        d["went"] = time_to_str(d["went"])
        transformed_data[k] = d

    jsonified_data = json.dumps(transformed_data)
    with open(filename, 'w') as f:
        f.write(jsonified_data)


def load_from_json(filename: Path) -> dict[date, dict]:
    with open(filename) as f:
        jsonified_data = f.read()
    data: dict[str, dict[str, str]] = json.loads(jsonified_data)

    # Interpret from JSON strings to native format
    db = dict()
    for k, d in data.items():
        k = datetime.strptime(k, "%Y-%m-%d").date()
        d["came"] = datetime.strptime(d["came"], "%H:%M:%S").time()
        d["went"] = datetime.strptime(d["went"], "%H:%M:%S").time()
        db[k] = d
    return db
