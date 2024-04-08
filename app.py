#!/usr/bin/env python
from typing import List, Tuple
import typer
from datetime import datetime, timedelta
from os import path
from typing_extensions import Annotated
from database import Database
from constants import InfoText, Event, Format, File
from timer import Timer
from rich.table import Table
from rich.console import Console
from rich import print


def db_file_existing() -> bool:
    return path.isfile(f"./{File.NAME}")


def output_with_timestamp(text: str, delta: int = 0) -> None:
    time_stamp = (datetime.now() - timedelta(minutes=delta)).strftime(Format.TIME)
    print(f"[{time_stamp}]: " + text)


def output_week(timestamps: List[Tuple]) -> None:
    table = Table("Day","Worktime")
    for date_, timestamp in timestamps[::-1]:
        table.add_row(date_.strftime('%A'), str(timestamp))
    console.print(table)


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
        output_week(week_durations)
    else:
        print(f"{InfoText.WARN_SYMBOL} No data to show")
    timer.db.close()


if __name__ == "__main__":
    app()
