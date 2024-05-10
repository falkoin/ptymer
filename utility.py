from datetime import datetime, timedelta
from typing import List, Tuple
from rich.table import Table
import re
from os import path
from constants import File, Format
from rich.console import Console
from rich import print


console = Console()


def db_file_existing() -> bool:
    return path.isfile(f"./{File.NAME}")


def output_with_timestamp(text: str, delta: int = 0) -> None:
    time_stamp = (datetime.now() - timedelta(minutes=delta)).strftime(Format.TIME)
    print(f"[{time_stamp}]: " + text)


def output_week(timestamps: List[Tuple]) -> None:
    table = Table("Day", "Worktime")
    hours = []
    for date_, timestamp in timestamps[::-1]:
        hours.append(timestamp)
        table.add_row(date_.strftime("%A"), str(timestamp))
    table.add_section()
    table.add_row("Overall", _format_timedelta(sum(hours, timedelta())))
    console.print(table)


def _format_timedelta(timedelta_: timedelta):
    DAYS_2_SECONDS = 86400
    minutes, seconds = divmod(timedelta_.seconds + timedelta_.days * DAYS_2_SECONDS, 60)
    hours, minutes = divmod(minutes, 60)
    return "{:d}:{:02d}:{:02d}".format(hours, minutes, seconds)


def output_day(timestamps: List[Tuple]) -> None:
    table = Table("Index", "Time", "Event")
    for index, time, event in timestamps:
        table.add_row(str(index), remove_date_from_date_time(time), event)
    console.print(table)


def remove_date_from_date_time(date_time: str) -> str:
    pattern = r"\d{4}-\d{2}-\d{2}\s"
    return re.sub(pattern, "", date_time)


def remove_time_from_date_time(date_time: str) -> str:
    pattern = r"\s\d{2}:\d{2}:\d{2}$"
    return re.sub(pattern, "", date_time)


def check_correct_date_format(date: str, format: str) -> bool:
    try:
        datetime.strptime(date, format)
    except ValueError:
        return False
    return True
