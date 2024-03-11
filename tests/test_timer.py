import unittest
from unittest import TestCase
from unittest.mock import MagicMock, call, patch
from database import Database
from timer import Timer
from app import (
    db_file_existing,
    output_with_timestamp,
)
from datetime import datetime, date, timedelta


class TestDb(TestCase):

    def setUp(self) -> None:
        self.db_file = patch("os.path.isfile").start()
        self.filename = ":memory:"
        self.db = MagicMock(spec=Database)

    def test_db_file_existing(self) -> None:
        # given
        self.db_file.return_value = True
        # when
        result = db_file_existing()
        # then
        self.db_file.assert_called_with("./ptymer.db")
        self.assertEqual(True, result)

    def test_db_file_not_existing(self) -> None:
        # given
        self.db_file.return_value = False
        # when
        result = db_file_existing()
        # then
        self.db_file.assert_called_with("./ptymer.db")
        self.assertEqual(False, result)

    def test_db_create(self) -> None:
        # given
        sqlite = patch("database.sqlite3").start()
        patch("database.path.isfile", return_value=False).start()
        # when
        _ = Database(self.filename)
        # then
        sqlite.assert_has_calls(
            [
                call.connect(self.filename),
                call.connect().cursor(),
                call.connect()
                .cursor()
                .execute("CREATE TABLE timestamp(date, event, time)"),
            ]
        )

    def test_db_close(self) -> None:
        # given
        sqlite = patch("database.sqlite3").start()
        db = Database(self.filename)
        # when
        db.close()
        # then
        sqlite.assert_has_calls([call.connect().close()])

    def test_db_load(self) -> None:
        # given
        con = patch("database.sqlite3.connect", return_value={}).start()
        # when
        db = Database(self.filename)
        # then
        self.assertEqual({}, db.con)
        con.assert_called_once_with(":memory:")

    def test_create_timestamp(self) -> None:
        # given
        patch("app.Timer._check_valid_timestamp", return_value=True).start()
        con = patch("database.sqlite3").start()
        today = patch("database.date", wraps=date).start()
        today.today.return_value = "2024-01-01"
        now = patch("database.datetime", wraps=datetime).start()
        now.now.return_value = datetime.strptime(
            "2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S"
        )
        db = Database(self.filename)
        timer = Timer(db)
        expected_call = "INSERT INTO timestamp VALUES ('2024-01-01', 'start', '2024-01-01 17:00:00')"
        # when
        timer.create_timestamp("start")
        # then
        con.assert_has_calls(
            [
                call.connect(":memory:"),
                call.connect().cursor(),
                call.connect().cursor().execute(expected_call),
                call.connect().commit(),
            ]
        )

    def test_create_timestamp_collision(self) -> None:
        # given
        patch("app.Timer._check_valid_timestamp", return_value=False).start()
        patch("database.sqlite3").start()
        patch("app.Timer._calc_time_stamp").start()
        db = Database(self.filename)
        timer = Timer(db)
        # when
        with self.assertRaises(Exception) as e:
            timer.create_timestamp("start")
        # then
        self.assertEqual("Timestamp collision", str(e.exception))

    def test_check_state_allowed(self) -> None:
        # given
        mock_db = MagicMock(spec=Database)
        mock_db.get_last_event.side_effect = [("start",), ("start",)]
        timer = Timer(mock_db)
        for event, expected in zip(("start", "stop"), (False, True)):
            with self.subTest(event):
                # when
                result = timer.check_state_allowed(event)
                # then
                self.assertEqual(expected, result)

    def test_calc_time_stamp(self) -> None:
        # given
        now = patch("timer.datetime", wraps=datetime).start()
        now.now.return_value = datetime.strptime(
            "2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S"
        )
        db = Database(self.filename)
        timer = Timer(db)
        # when
        time_stamp = timer._calc_time_stamp(delta=10)
        # then
        self.assertEqual(datetime(2024, 1, 1, 16, 50), time_stamp)

    def test_output_with_timestamp(self) -> None:
        # given
        std_out = patch("builtins.print").start()
        today = patch("database.date", wraps=datetime).start()
        today.today.return_value = date(2024, 1, 1)
        now = patch("app.datetime", wraps=datetime).start()
        now.now.return_value = datetime.strptime(
            "2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S"
        )
        text = "text"
        # when
        output_with_timestamp(text)
        # then
        std_out.assert_called_once_with(f"[17:00:00]: {text}")

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
        db = Database(self.filename)
        timer = Timer(db)
        patch(
            "app.Database.get_times_by", return_value=[("2024-01-01 17:00:00",)]
        ).start()
        time_stamp = datetime.strptime("2024-01-01 17:10:00", "%Y-%m-%d %H:%M:%S")
        # when
        result = timer._check_valid_timestamp(time_stamp, "start")
        # then
        self.assertTrue(result)

    def test_check_invalid_timestamp(self) -> None:
        # given
        db = Database(self.filename)
        timer = Timer(db)
        patch(
            "app.Database.get_times_by", return_value=[("2024-01-01 17:00:00",)]
        ).start()
        time_stamp = datetime.strptime("2024-01-01 16:9:00", "%Y-%m-%d %H:%M:%S")
        # when
        result = timer._check_valid_timestamp(time_stamp, "start")
        # then
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
