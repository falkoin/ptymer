import sqlite3
from sqlite3 import Connection
import typer
from datetime import datetime, timedelta, date
from os import path
from typing_extensions import Annotated

FILE_NAME = "ptymer.db"
FORMAT = "%Y-%m-%d %H:%M:%S"


def db_file_existing() -> bool:
    return path.isfile(f"./{FILE_NAME}")


def db_create() -> None:
    con = sqlite3.connect(FILE_NAME)
    cur = con.cursor()
    cur.execute("CREATE TABLE timestamp(date, event, time)")


def db_load() -> Connection:
    return sqlite3.connect(FILE_NAME)


def create_timestamp(con: Connection, date_today: str, event: str, delta: int) -> None:
    time_stamp = (datetime.now() - timedelta(minutes=delta)).strftime(FORMAT)
    cur = con.cursor()
    cur.execute(
        f"INSERT INTO timestamp VALUES ('{date_today}', '{event}', '{time_stamp}')"
    )
    con.commit()


def check_state_allowed(con: Connection, date_today: str, event: str) -> bool:
    cur = con.cursor()
    last_event = cur.execute(
        f"SELECT event FROM timestamp WHERE date='{date_today}' ORDER BY time DESC"
    )
    if last_event:
        return last_event != event
    return True


def output_with_timestamp(text: str, delta: int = 0) -> None:
    FORMAT_TIME = "%H:%M:%S"
    time_stamp = (datetime.now() - timedelta(minutes=delta)).strftime(FORMAT_TIME)
    print(f"[{time_stamp}]: " + text)


def calc_worktime(con: Connection, date_today: str) -> timedelta:
    cur = con.cursor()
    times_start = cur.execute(
        f"SELECT time FROM timestamp WHERE date='{date_today}' AND event='start' ORDER BY time ASC"
    ).fetchall()

    times_stop = cur.execute(
        f"SELECT time FROM timestamp WHERE date='{date_today}' AND event='stop' ORDER BY time ASC"
    ).fetchall()

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
def start(delta: Annotated[int, typer.Option(help="Time delta in minutes to start in the past.")] = 0):
    if not db_file_existing():
        db_create()
    date_today = f"{date.today()}"
    con = db_load()
    if check_state_allowed(con, date_today, "start"):
        create_timestamp(con, date_today, "start", delta)
        output_with_timestamp("Started working", delta)
    else:
        print("Session already running.")
    con.close()


@app.command()
def stop(delta: Annotated[int, typer.Option(help="Time delta in minutes to start in the past.")] = 0):
    if not db_file_existing():
        print("No session started, yet")
        return
    date_today = f"{date.today()}"
    con = db_load()
    if check_state_allowed(con, date_today, "stop"):
        create_timestamp(con, date_today, "stop", delta)
        duration = calc_worktime(con, date_today)
        output_with_timestamp(f"Worked for {duration} hours", delta)
    else:
        print("Session already stopped.")
    con.close()


@app.command()
def show():
    if not db_file_existing():
        print("No data to show")
        return
    date_today = f"{date.today()}"
    con = db_load()
    duration = calc_worktime(con, date_today)
    output_with_timestamp(f"Worked for {duration} hours")
    con.close()


if __name__ == "__main__":
    app()
