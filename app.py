import sqlite3
from sqlite3 import Connection
from typing import Any
import typer
from datetime import datetime, timedelta, date
from os import path
from typing_extensions import Annotated

FILE_NAME = "ptymer.db"
FORMAT = "%Y-%m-%d %H:%M:%S"


class Database:
    filename = FILE_NAME

    def __init__(self):
        if not path.isfile(f"./{self.filename}"):
            self.con = self.create()
        self.con = self.load()
        self.date_today = f"{date.today()}"

    def load(self) -> Connection:
        return sqlite3.connect(self.filename)

    def create(self) -> Connection:
        con = self.load()
        cur = con.cursor()
        cur.execute("CREATE TABLE timestamp(date, event, time)")
        return con

    def close(self) -> None:
        self.con.close()

    def create_timestamp(self, event: str, delta: int = 0) -> None:
        cur = self.con.cursor()
        time_stamp = self._calc_time_stamp(delta)
        cur.execute(
            f"INSERT INTO timestamp VALUES ('{self.date_today}', '{event}', '{time_stamp}')"
        )
        self.con.commit()

    @staticmethod
    def _calc_time_stamp(delta: int) -> str:
        return (datetime.now() - timedelta(minutes=delta)).strftime(FORMAT)

    def get_times_by(self, event: str, ascending: bool = True) -> list[Any]:
        cur = self.con.cursor()
        order = "ASC" if ascending else "DESC"
        return cur.execute(
            f"SELECT time FROM timestamp WHERE date='{self.date_today}' AND event='{event}' ORDER BY time {order}"
        ).fetchall()

    def get_last_event(self) -> str | None:
        cur = self.con.cursor()
        return cur.execute(
            f"SELECT event FROM timestamp WHERE date='{self.date_today}' ORDER BY time DESC"
        ).fetchone()


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
        db.create_timestamp("start", delta)
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
        db.create_timestamp("stop", delta)
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
