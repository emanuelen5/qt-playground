from datetime import timedelta, date
from random import randint
from .util import timedelta_to_time


# A test database with some came and went times
test_table_days = {
    date.today() + timedelta(days=i): {
        "came": timedelta_to_time(timedelta(hours=8, minutes=30) + timedelta(seconds=randint(-60*60, 60*60))),
        "went": timedelta_to_time(timedelta(hours=17, minutes=00) + timedelta(seconds=randint(-60*60, 60*60))),
        "note": ""
    } for i in range(-2, 3)
}

test_table_days[sorted(test_table_days.keys())[0]]["note"] = "Here is a testnote with some details about the specific date"
