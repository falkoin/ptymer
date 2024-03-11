from database import Database
from constants import Event, Format, InfoText
from datetime import timedelta, datetime


class Timer:
    
    def __init__(self, db: Database):
        self.db = db

    def check_state_allowed(self, event: str) -> bool:
        last_event = self.db.get_last_event()
        if last_event is not None:
            return last_event[0] != event
        return True

    def calc_worktime(self) -> timedelta:
        times_start = self.db.get_times_by(event=Event.START, ascending=True)
        times_stop = self.db.get_times_by(event=Event.STOP, ascending=True)

        if times_start:
            if len(times_start) > len(times_stop):
                times_stop.append((f"{datetime.now().strftime(Format.DATETIIME)}",))
            return self.calc_duration(times_stop, times_start)
        else:
            raise Exception(InfoText.WARN_DURATION)

    def calc_duration(self, time_1: list[tuple], time_2: list[tuple]) -> timedelta:
        diff_times = [
            datetime.strptime(x[0], Format.DATETIIME)
            - datetime.strptime(y[0], Format.DATETIIME)
            for x, y in zip(time_1, time_2)
        ]

        return sum(diff_times, timedelta())

    def create_timestamp(self, event: str, delta: int = 0) -> None:
        time_stamp = self._calc_time_stamp(delta)
        if not self._check_valid_timestamp(time_stamp, event):
            raise Exception("Timestamp collision")
        self.db.write_timestamp(event=event, time_stamp=time_stamp)

    def _check_valid_timestamp(self, time_stamp: datetime, event: str) -> bool:
        times = self.db.get_times_by(event=event)
        if times:
            latest_time = datetime.strptime(times[0][0], Format.DATETIIME)
            if latest_time > time_stamp:
                return False
        return True


    @staticmethod
    def _calc_time_stamp(delta: int) -> datetime:
        return datetime.now() - timedelta(minutes=delta)
