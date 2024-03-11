import typer
from datetime import datetime, timedelta
from os import path
from typing_extensions import Annotated
from database import Database
from constants import InfoText, Event, Format

FILE_NAME = "ptymer.db"


def db_file_existing() -> bool:
    return path.isfile(f"./{FILE_NAME}")


def check_state_allowed(db: Database, event: str) -> bool:
    last_event = db.get_last_event()
    if last_event is not None:
        return last_event[0] != event
    return True


def output_with_timestamp(text: str, delta: int = 0) -> None:
    time_stamp = (datetime.now() - timedelta(minutes=delta)).strftime(Format.TIME)
    print(f"[{time_stamp}]: " + text)


def calc_worktime(db: Database) -> timedelta:
    times_start = db.get_times_by(event=Event.START, ascending=True)
    times_stop = db.get_times_by(event=Event.STOP, ascending=True)

    if times_start:
        if len(times_start) > len(times_stop):
            times_stop.append((f"{datetime.now().strftime(Format.DATETIIME)}",))
        return calc_duration(times_stop, times_start)
    else:
        raise Exception(InfoText.WARN_DURATION)


def calc_duration(time_1: list[tuple], time_2: list[tuple]) -> timedelta:
    diff_times = [
        datetime.strptime(x[0], Format.DATETIIME)
        - datetime.strptime(y[0], Format.DATETIIME)
        for x, y in zip(time_1, time_2)
    ]

    return sum(diff_times, timedelta())


app = typer.Typer()


@app.command()
def start(delta: Annotated[int, typer.Option(help=InfoText.HELP_DELTA)] = 0):
    db = Database()
    if check_state_allowed(db, Event.START):
        try:
            db.create_timestamp(Event.START, delta)
        except Exception:
            print(InfoText.WARN_COLLISON)
        output_with_timestamp("Started working", delta)
    else:
        print("Session already running.")
    db.close()


@app.command()
def stop(delta: Annotated[int, typer.Option(help=InfoText.HELP_DELTA)] = 0):
    if not db_file_existing():
        print("No session started, yet")
        return
    db = Database()
    if check_state_allowed(db, Event.STOP):
        try:
            db.create_timestamp(Event.STOP, delta)
        except Exception:
            print(InfoText.WARN_COLLISON)
            return
        duration = calc_worktime(db)
        output_with_timestamp(f"Worked for {duration} hours", delta)
    else:
        print("Session already stopped.")
    db.close()


@app.command()
def show():
    if not db_file_existing():
        print("No data to show")
        return
    db = Database()
    duration = calc_worktime(db)
    output_with_timestamp(f"Worked for {duration} hours")
    db.close()


if __name__ == "__main__":
    app()
