#!/usr/bin/env python
from typing import Any, Dict, List, Tuple
import typer
from datetime import datetime, timedelta, date
from os import path
from typing_extensions import Annotated
from database import Database
from constants import InfoText, Event, Format, File
from timer import Timer
from rich.table import Table
from rich.console import Console
from rich import print
import re


def db_file_existing() -> bool:
    return path.isfile(f"./{File.NAME}")


def output_with_timestamp(text: str, delta: int = 0) -> None:
    time_stamp = (datetime.now() - timedelta(minutes=delta)).strftime(Format.TIME)
    print(f"[{time_stamp}]: " + text)


def output_week(timestamps: List[Tuple], config: Dict[str, Any]) -> None:
    table = Table("Day", "Worktime")
    hours = []
    for date_, timestamp in timestamps[::-1]:
        table.add_row(date_.strftime("%A"), str(timestamp))
        hours.append(timestamp)
    if config:
        goal_hours = sum([hour for hour in config["hours"].values()])

        table.add_row("", str(timedelta(hours=goal_hours) - sum(hours, timedelta())))
    console.print(table)


def output_day(timestamps: List[Tuple]) -> None:
    table = Table("Index", "Time", "Event")
    for index, time, event in timestamps:
        table.add_row(
            str(index), remove_date_from_date_time(time), event
        )
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
    except:
        return False
    return True


app = typer.Typer()
console = Console()


@app.command()
def start(delta: Annotated[int, typer.Option(help=InfoText.HELP_DELTA)] = 0):
    db = Database(File.NAME)
    timer = Timer(db)
    if timer.check_state_allowed(Event.START):
        try:
            timer.create_timestamp(Event.START, delta)
        except Exception:
            print(InfoText.WARN_COLLISON)
            return
        output_with_timestamp("Started working", delta)
    else:
        print(f"{InfoText.WARN_SYMBOL} Session already running.")
    timer.db.close()


@app.command()
def stop(delta: Annotated[int, typer.Option(help=InfoText.HELP_DELTA)] = 0):
    if not db_file_existing():
        print(f"{InfoText.WARN_SYMBOL} No session started, yet")
        return
    db = Database(File.NAME)
    timer = Timer(db)
    if timer.check_state_allowed(Event.STOP):
        try:
            timer.create_timestamp(Event.STOP, delta)
        except Exception:
            print(InfoText.WARN_COLLISON)
            return
        duration = timer.calc_worktime()
        output_with_timestamp(f"Worked for {duration} hours", delta)
    else:
        print(f"{InfoText.WARN_SYMBOL} Session already stopped.")
    timer.db.close()


@app.command()
def show():
    if not db_file_existing():
        print(f"{InfoText.WARN_SYMBOL} No data to show")
        return
    db = Database(File.NAME)
    if not db.get_last_event():
        print(f"{InfoText.WARN_SYMBOL} No session existing for today, yet")
        return
    timer = Timer(db)
    duration = timer.calc_worktime()
    output_with_timestamp(f"Worked for {duration} hours")
    timer.db.close()


@app.command()
def week():
    if not db_file_existing():
        print(f"{InfoText.WARN_SYMBOL} No data to show")
        return
    db = Database(File.NAME)
    timer = Timer(db)
    week_durations = timer.calc_week()
    if week_durations:
        output_week(week_durations, timer.config)
    else:
        print(f"{InfoText.WARN_SYMBOL} No data to show")
    timer.db.close()


@app.command()
def timestamps(date_: Annotated[str, typer.Argument()] = date.today().strftime(Format.DATE)):
    if not check_correct_date_format(date_, Format.DATE):
        print(f"{InfoText.WARN_SYMBOL} Incorrect date format. Use: YYYY-MM-DD")
        return
    if not db_file_existing():
        print(f"{InfoText.WARN_SYMBOL} No data to show")
        return
    db = Database(File.NAME)
    entries = db.get_data_by_date(date_)
    if entries:
        output_day(entries)
    else:
        print(f"{InfoText.WARN_SYMBOL} No entries for today")


@app.command()
def delete(rowid: int):
    if not db_file_existing():
        print(f"{InfoText.WARN_SYMBOL} No data to show")
        return
    db = Database(File.NAME)
    if db.delete_row(rowid):
        print(f"{InfoText.CONFIRM_SYMBOL} Timestamp successfully removed.")
    else:
        print(f"{InfoText.WARN_SYMBOL} Removal of timestamp not possible.")


@app.command()
def add(date_time: str, event: str):
    if not check_correct_date_format(date_time, Format.DATETIME):
        print(f"{InfoText.WARN_SYMBOL} Incorrect timestamp format. Use: YYYY-MM-DD HH:MM:SS")
        return
    if not event in ("start", "stop"):
        print(f"{InfoText.WARN_SYMBOL} Incorrect event")
        return
    if not db_file_existing():
        print(f"{InfoText.WARN_SYMBOL} No data to show")
        return
    db = Database(File.NAME)
    db.write_timestamp(event, date_time, remove_time_from_date_time(date_time))
    print(f"{InfoText.CONFIRM_SYMBOL} Timestamp successfully added.")


if __name__ == "__main__":
    app()
