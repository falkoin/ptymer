import typer
from datetime import datetime, timedelta
from os import path
from typing_extensions import Annotated
from database import Database
from constants import InfoText, Event, Format, File
from timer import Timer


def db_file_existing() -> bool:
    return path.isfile(f"./{File.NAME}")


def output_with_timestamp(text: str, delta: int = 0) -> None:
    time_stamp = (datetime.now() - timedelta(minutes=delta)).strftime(Format.TIME)
    print(f"[{time_stamp}]: " + text)


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
        print("Session already running.")
    timer.db.close()


@app.command()
def stop(delta: Annotated[int, typer.Option(help=InfoText.HELP_DELTA)] = 0):
    if not db_file_existing():
        print("No session started, yet")
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
        print("Session already stopped.")
    timer.db.close()


@app.command()
def show():
    if not db_file_existing():
        print("No data to show")
        return
    db = Database(File.NAME)
    timer = Timer(db)
    duration = timer.calc_worktime()
    output_with_timestamp(f"Worked for {duration} hours")
    timer.db.close()


if __name__ == "__main__":
    app()
