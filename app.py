import sqlite3
from sqlite3 import Connection
import typer
from datetime import datetime, timedelta, date
from os import path

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


def create_timestamp(con: Connection, date_today: str, event: str) -> None:
    cur = con.cursor()
    cur.execute(
        f"""
        INSERT INTO timestamp VALUES
            ('{date_today}', '{event}', '{datetime.now().strftime(FORMAT)}')
    """
    )
    con.commit()


def check_state_allowed(con: Connection, date_today: str, event: str) -> bool:
    cur = con.cursor()
    last_event = cur.execute(
        f"""
                             SELECT event FROM timestamp WHERE date='{date_today}' ORDER BY time DESC
                             """
    )
    if last_event:
        return last_event != event
    return True


def output_with_timestamp(text: str) -> None:
    FORMAT_TIME = "%H:%M:%S"
    print(f"[{datetime.now().strftime(FORMAT_TIME)}]: " + text)


def calc_duration(con: Connection, date_today: str) -> None:
    cur = con.cursor()
    times_start = cur.execute(
        f"""
                             SELECT time FROM timestamp WHERE date='{date_today}' AND event='start' ORDER BY time ASC
                             """
    ).fetchall()

    times_stop = cur.execute(
        f"""
                             SELECT time FROM timestamp WHERE date='{date_today}' AND event='stop' ORDER BY time ASC
                             """
    ).fetchall()

    if times_start:
        if len(times_start) > len(times_stop):
            times_stop.append((f"{datetime.now().strftime(FORMAT)}",))
        diff_times = [
            datetime.strptime(x[0], FORMAT) - datetime.strptime(y[0], FORMAT)
            for x, y in zip(times_stop, times_start)
        ]

        output_with_timestamp(f"Worked for {sum(diff_times, timedelta())} hours")
    else:
        raise Exception("Couldn't calculate duration for today")


app = typer.Typer()


@app.command()
def start():
    if not db_file_existing():
        db_create()
    date_today = f"{date.today()}"
    con = db_load()
    if check_state_allowed(con, date_today, "start"):
        create_timestamp(con, date_today, "start")
        output_with_timestamp("Started working")
    else:
        print("Session already running.")
    con.close()


@app.command()
def stop():
    if not db_file_existing():
        print("No session started, yet")
        return
    date_today = f"{date.today()}"
    con = db_load()
    if check_state_allowed(con, date_today, "stop"):
        create_timestamp(con, date_today, "stop")
        calc_duration(con, date_today)
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
    calc_duration(con, date_today)
    con.close()


if __name__ == "__main__":
    app()
