import typer
from datetime import datetime, timedelta
from os import path
from typing_extensions import Annotated
from database import Database

FILE_NAME = "ptymer.db"
FORMAT = "%Y-%m-%d %H:%M:%S"


def db_file_existing() -> bool:
    return path.isfile(f"./{FILE_NAME}")


def check_state_allowed(db: Database, event: str) -> bool:
    last_event = db.get_last_event()
    if last_event is not None:
        return last_event[0] != event
    return True


def output_with_timestamp(text: str, delta: int = 0) -> None:
    FORMAT_TIME = "%H:%M:%S"
    time_stamp = (datetime.now() - timedelta(minutes=delta)).strftime(FORMAT_TIME)
    print(f"[{time_stamp}]: " + text)


def calc_worktime(db: Database) -> timedelta:
    times_start = db.get_times_by(event="start", ascending=True)
    times_stop = db.get_times_by(event="stop", ascending=True)

    if times_start:
        if len(times_start) > len(times_stop):
            times_stop.append((f"{datetime.now().strftime(FORMAT)}",))
        return calc_duration(times_stop, times_start)
    else:
        raise Exception("Couldn't calculate duration for today")


def calc_duration(time_1: list[tuple], time_2: list[tuple]) -> timedelta:
    diff_times = [
        datetime.strptime(x[0], FORMAT) - datetime.strptime(y[0], FORMAT)
        for x, y in zip(time_1, time_2)
    ]

    return sum(diff_times, timedelta())


app = typer.Typer()


@app.command()
def start(
    delta: Annotated[
        int, typer.Option(help="Time delta in minutes to start in the past.")
    ] = 0
):
    db = Database()
    if check_state_allowed(db, "start"):
        try:
            db.create_timestamp("start", delta)
        except Exception:
            print("Timestamp collision with existing one")
        output_with_timestamp("Started working", delta)
    else:
        print("Session already running.")
    db.close()


@app.command()
def stop(
    delta: Annotated[
        int, typer.Option(help="Time delta in minutes to stop in the past.")
    ] = 0
):
    if not db_file_existing():
        print("No session started, yet")
        return
    db = Database()
    if check_state_allowed(db, "stop"):
        try:
            db.create_timestamp("stop", delta)
        except Exception:
            print("Timestamp collision with existing one")
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
