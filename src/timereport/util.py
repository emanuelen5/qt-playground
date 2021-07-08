from datetime import timedelta, time


def timedelta_to_time(td: timedelta) -> time:
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return time(hours, minutes, seconds, td.microseconds)


def time_to_timedelta(t: time) -> timedelta:
    return timedelta(hours=t.hour, minutes=t.minute, seconds=t.second, microseconds=t.microsecond)
