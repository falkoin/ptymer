#!/usr/bin/env python
import typer
from datetime import date
from typing_extensions import Annotated
from database import Database
from constants import InfoText, Event, Format, File
from timer import Timer
from rich import print
from utility import (
    output_with_timestamp,
    db_file_existing,
    output_week,
    output_day,
    check_correct_date_format,
    remove_time_from_date_time,
)


app = typer.Typer()


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
    work_duration = timer.calc_worktime()
    pause_duration = timer.calc_pausetime()
    if pause_duration:
        output_with_timestamp(
            f"Worked for {work_duration} hours, pause [yellow]{pause_duration}[/yellow] hours"
        )
    else:
        output_with_timestamp(f"Worked for {work_duration} hours")

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


@app.command()
def timestamps(
    date_: Annotated[str, typer.Argument()] = date.today().strftime(Format.DATE),
):
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
        print(
            f"{InfoText.WARN_SYMBOL} Incorrect timestamp format. Use: YYYY-MM-DD HH:MM:SS"
        )
        return
    if event not in ("start", "stop"):
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
