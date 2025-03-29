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
        timer = Timer(self.db)
        # when
        timer.create_timestamp("start")
        # then
        self.db.assert_has_calls(
            [call.write_timestamp(event="start", time_stamp="2024-01-01 17:00:00")]
        )

    def test_create_timestamp_collision(self) -> None:
        # given
        patch("app.Timer._check_valid_timestamp", return_value=False).start()
        patch("app.Timer._calc_time_stamp").start()
        timer = Timer(self.db)
        # when
        with self.assertRaises(Exception) as e:
            timer.create_timestamp("start")
        # then
        self.assertEqual("Timestamp collision", str(e.exception))

    def test_check_state_allowed(self) -> None:
        # given
        self.db.get_last_event.side_effect = [("start",), ("start",), None, None]
        timer = Timer(self.db)
        for event, expected in zip(
            ("start", "stop", "start", "stop"), (False, True, True, False)
        ):
            with self.subTest(event):
                # when
                result = timer.check_state_allowed(event)
                # then
                self.assertEqual(expected, result)

    def test_calc_time_stamp(self) -> None:
        # given
        timer = Timer(self.db)
        # when
        time_stamp = timer._calc_time_stamp(delta=10)
        # then
        self.assertEqual(datetime(2024, 1, 1, 16, 50), time_stamp)

    def test_calc_duration(self) -> None:
        # given
        date_ = "2024-01-01"
        times_1 = [(f"{date_} 12:00:00",), (f"{date_} 17:00:00",)]
        times_2 = [(f"{date_} 08:00:00",), (f"{date_} 13:00:00",)]
        timer = Timer(self.db)
        # when
        duration = timer.calc_duration(times_1, times_2)
        # then
        self.assertEqual(timedelta(hours=8), duration)

    def test_calc_duration_with_uneven_times(self) -> None:
        # given
        date_ = "2024-01-01"
        times_1 = [(f"{date_} 12:00:00",)]
        times_2 = [(f"{date_} 08:00:00",), (f"{date_} 13:00:00",)]
        timer = Timer(self.db)
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

    def test_check_timestamp_without_entries(self) -> None:
        # given
        timer = Timer(self.db)
        self.db.get_times_by.return_value = None
        time_stamp = datetime.strptime("2024-01-01 17:10:00", "%Y-%m-%d %H:%M:%S")
        # when
        result = timer._check_valid_timestamp(time_stamp, "start")
        # then
        self.assertTrue(result)

    def test_check_invalid_timestamp(self) -> None:
        # given
        timer = Timer(self.db)
        self.db.get_times_by.return_value = [("2024-01-01 17:00:00",)]
        time_stamp = datetime.strptime("2024-01-01 16:09:00", "%Y-%m-%d %H:%M:%S")
        # when
        result = timer._check_valid_timestamp(time_stamp, "start")
        # then
        self.assertFalse(result)

    def test_calc_worktime_no_times(self) -> None:
        # given
        self.db.get_times_by.side_effect = ([], [])
        timer = Timer(self.db)
        # when
        with self.assertRaises(Exception) as e:
            timer.calc_worktime()
        # then
        self.assertEqual("Couldn't calculate duration for today", str(e.exception))

    def test_calc_worktime(self) -> None:
        # given
        patch("timer.Timer.calc_duration", return_value={}).start()
        self.db.get_times_by.side_effect = ([("t1",)], [("t2",)])
        timer = Timer(self.db)
        # when
        result = timer.calc_worktime()
        # then
        self.assertEqual({}, result)

    def test_calc_worktime_more_start_times(self) -> None:
        # given
        test = patch("timer.Timer.calc_duration", return_value={}).start()
        self.db.get_times_by.side_effect = ([("t1",), ("t2",)], [("t3",)])
        timer = Timer(self.db)
        # when
        result = timer.calc_worktime()
        # then
        self.assertEqual({}, result)
        test.assert_called_with([("t3",), ("2024-01-01 17:00:00",)], [("t1",), ("t2",)])

    def test_calc_pausetime_no_times(self) -> None:
        # given
        self.db.get_times_by.side_effect = ([], [])
        timer = Timer(self.db)
        # when
        result = timer.calc_pausetime()
        # then
        self.assertEqual(None, result)

    def test_calc_pausetime(self) -> None:
        # given
        patch("timer.Timer.calc_duration", return_value={}).start()
        self.db.get_times_by.side_effect = (("t1",), ("t2",))
        timer = Timer(self.db)
        # when
        result = timer.calc_pausetime()
        # then
        self.assertEqual({}, result)

    def test_calc_week(self) -> None:
        # gicen
        self.db.date_today = "2024-01-02"
        patch("timer.Timer.calc_worktime", side_effect=["1", "2", "3"]).start()
        timer = Timer(self.db)
        expected_date_1 = datetime.strptime(self.db.date_today, "%Y-%m-%d")
        expected_date_2 = datetime.strptime("2024-01-01", "%Y-%m-%d")
        # when
        result = timer.calc_week()
        # then
        self.assertEqual([(expected_date_1, "1"), (expected_date_2, "2")], result)
