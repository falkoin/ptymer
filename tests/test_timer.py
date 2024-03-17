from unittest import TestCase
from unittest.mock import MagicMock, call, patch
from database import Database
from timer import Timer
from datetime import datetime, timedelta


class TestTimer(TestCase):

    def setUp(self) -> None:
        self.filename = ":memory:"
        self.db = MagicMock(spec=Database)
        now = patch("timer.datetime", wraps=datetime).start()
        now.now.return_value = datetime.strptime(
            "2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S"
        )

    def tearDown(self) -> None:
        patch.stopall()

    def test_create_timestamp(self) -> None:
        # given
        patch("app.Timer._check_valid_timestamp", return_value=True).start()
        db = MagicMock(spec=Database)
        timer = Timer(db)
        # when
        timer.create_timestamp("start")
        # then
        db.assert_has_calls([call.write_timestamp(event="start", time_stamp=datetime(2024, 1, 1, 17, 0))])

    def test_create_timestamp_collision(self) -> None:
        # given
        patch("app.Timer._check_valid_timestamp", return_value=False).start()
        patch("app.Timer._calc_time_stamp").start()
        db = MagicMock(spec=Database)
        timer = Timer(db)
        # when
        with self.assertRaises(Exception) as e:
            timer.create_timestamp("start")
        # then
        self.assertEqual("Timestamp collision", str(e.exception))

    def test_check_state_allowed(self) -> None:
        # given
        db = MagicMock(spec=Database)
        db.get_last_event.side_effect = [("start",), ("start",)]
        timer = Timer(db)
        for event, expected in zip(("start", "stop"), (False, True)):
            with self.subTest(event):
                # when
                result = timer.check_state_allowed(event)
                # then
                self.assertEqual(expected, result)

    def test_calc_time_stamp(self) -> None:
        # given
        db = Database(self.filename)
        timer = Timer(db)
        # when
        time_stamp = timer._calc_time_stamp(delta=10)
        # then
        self.assertEqual(datetime(2024, 1, 1, 16, 50), time_stamp)

    def test_calc_duration(self) -> None:
        # given
        date_ = "2024-01-01"
        times_1 = [(f"{date_} 12:00:00",), (f"{date_} 17:00:00",)]
        times_2 = [(f"{date_} 08:00:00",), (f"{date_} 13:00:00",)]
        db = MagicMock(spec=Database)
        timer = Timer(db)
        # when
        duration = timer.calc_duration(times_1, times_2)
        # then
        self.assertEqual(timedelta(hours=8), duration)

    def test_calc_duration_with_uneven_times(self) -> None:
        # given
        date_ = "2024-01-01"
        times_1 = [(f"{date_} 12:00:00",)]
        times_2 = [(f"{date_} 08:00:00",), (f"{date_} 13:00:00",)]
        db = MagicMock(spec=Database)
        timer = Timer(db)
        # when
        duration = timer.calc_duration(times_1, times_2)
        # then
        self.assertEqual(timedelta(hours=4), duration)

    def test_check_valid_timestamp(self) -> None:
        # given
        timer = Timer(self.db)
        self.db.get_times_by.return_value = [("2024-01-01 17:00:00",)]
        time_stamp = datetime.strptime("2024-01-01 17:10:00", "%Y-%m-%d %H:%M:%S")
        # when
        result = timer._check_valid_timestamp(time_stamp, "start")
        # then
        self.assertTrue(result)

    def test_check_invalid_timestamp(self) -> None:
        # given
        db = MagicMock(spec=Database)
        timer = Timer(db)
        db.get_times_by.return_value = [("2024-01-01 17:00:00",)]
        time_stamp = datetime.strptime("2024-01-01 16:09:00", "%Y-%m-%d %H:%M:%S")
        # when
        result = timer._check_valid_timestamp(time_stamp, "start")
        # then
        self.assertFalse(result)
