import sqlite3
from sqlite3 import Connection
from typing import Any
from datetime import date, datetime, timedelta
from os import path
from constants import Format

FILE_NAME = "ptymer.db"


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
        if not self._check_valid_timestamp(time_stamp, event):
            raise Exception("Timestamp collision")
        cur.execute(
            f"INSERT INTO timestamp VALUES ('{self.date_today}', '{event}', '{time_stamp.strftime(Format.DATETIIME)}')"
        )
        self.con.commit()

    def _check_valid_timestamp(self, time_stamp: datetime, event: str) -> bool:
        times = self.get_times_by(event=event)
        if times:
            latest_time = datetime.strptime(times[0][0], Format.DATETIIME)
            if latest_time > time_stamp:
                return False
        return True

    @staticmethod
    def _calc_time_stamp(delta: int) -> datetime:
        return datetime.now() - timedelta(minutes=delta)

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
