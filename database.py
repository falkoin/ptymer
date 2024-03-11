import sqlite3
from sqlite3 import Connection
from typing import Any
from datetime import date, datetime
from os import path
from constants import Format


class Database:

    def __init__(self, filename):
        self.filename = filename
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

    def write_timestamp(self, event: str, time_stamp: datetime):
        cur = self.con.cursor()
        cur.execute(
            f"INSERT INTO timestamp VALUES ('{self.date_today}', '{event}', '{time_stamp.strftime(Format.DATETIIME)}')"
        )
        self.con.commit()

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
