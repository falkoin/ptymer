from contextlib import suppress
from typing import List, Literal, Optional
from database import Database
from constants import Event, Format, InfoText
from datetime import timedelta, datetime


class Timer:

    def __init__(self, db: Database):
        self.db = db

    def check_state_allowed(self, event: Literal["start", "stop", None]) -> bool:
        last_event = self.db.get_last_event()
        if last_event is None and event == "stop":
            return False
        if last_event is not None:
            return last_event[0] != event
        return True

    def calc_worktime(self) -> timedelta:
        times_start = self.db.get_times_by(event=Event.START, ascending=True)
        times_stop = self.db.get_times_by(event=Event.STOP, ascending=True)

        if times_start:
            if self._timer_not_stopped(times_start, times_stop):
                current_time = self._calc_time_stamp()
                current_time = (current_time.strftime(Format.DATETIME),)

                times_stop.append(current_time)
            return self.calc_duration(times_stop, times_start)
        else:
            raise Exception(InfoText.WARN_DURATION)

    @staticmethod
    def _timer_not_stopped(times_start: list, times_stop: list) -> bool:
        if len(times_start) > len(times_stop):
            return True
        else:
            return False

    def calc_pausetime(self) -> Optional[timedelta]:
        times_start = self.db.get_times_by(event=Event.START, ascending=True)
        times_stop = self.db.get_times_by(event=Event.STOP, ascending=True)
        if len(times_stop) == 0:
            return None
        if times_start:
            return self.calc_duration(times_start[1:], times_stop)

    def calc_duration(self, time_1: list[tuple], time_2: list[tuple]) -> timedelta:
        diff_times = [
            datetime.strptime(x[0], Format.DATETIME)
            - datetime.strptime(y[0], Format.DATETIME)
            for x, y in zip(time_1, time_2)
        ]

        return sum(diff_times, timedelta())

    def create_timestamp(self, event: str, delta: int = 0) -> None:
        time_stamp = self._calc_time_stamp(delta)
        if not self._check_valid_timestamp(time_stamp, event):
            raise Exception("Timestamp collision")
        time_stamp = time_stamp.strftime(Format.DATETIME)
        self.db.write_timestamp(event=event, time_stamp=time_stamp)

    def _check_valid_timestamp(self, time_stamp: datetime, event: str) -> bool:
        times = self.db.get_times_by(event=event)
        if times:
            latest_time = datetime.strptime(times[0][0], Format.DATETIME)
            return latest_time < time_stamp
        return True

    @staticmethod
    def _calc_time_stamp(delta: int = 0) -> datetime:
        return datetime.now() - timedelta(minutes=delta)

    def calc_week(self) -> List:
        week_durations = []
        current_week = datetime.strptime(self.db.date_today, Format.DATE)
        for date_delta in range(0, 7):
            new_date = current_week - timedelta(days=date_delta)
            self.db.date_today = new_date.strftime(Format.DATE)
            if current_week.strftime("%V") == new_date.strftime("%V"):
                with suppress(Exception):
                    week_durations.append((new_date, self.calc_worktime()))
            else:
                break
        return week_durations
