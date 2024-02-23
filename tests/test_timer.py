from unittest import TestCase
from unittest.mock import MagicMock, call, patch
from app import (
    calc_duration,
    db_create,
    check_state_allowed,
    db_file_existing,
    db_load,
    create_timestamp,
    output_with_timestamp,
)
from datetime import datetime, date, timedelta
from sqlite3 import Connection


class TestDb(TestCase):

    def setUp(self) -> None:
        self.db_file = patch("os.path.isfile").start()
        self.filename = "ptymer.db"

    def test_db_file_existing(self) -> None:
        # given
        self.db_file.return_value = True
        # when
        result = db_file_existing()
        # then
        self.db_file.assert_called_with(f"./{self.filename}")
        self.assertEqual(True, result)

    def test_db_file_not_existing(self) -> None:
        # given
        self.db_file.return_value = False
        # when
        result = db_file_existing()
        # then
        self.db_file.assert_called_with(f"./{self.filename}")
        self.assertEqual(False, result)

    def test_db_create(self) -> None:
        # given
        sqlite = patch("app.sqlite3").start()
        # when
        db_create()
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

    def test_db_load(self) -> None:
        # given
        con = patch("app.sqlite3.connect", return_value={}).start()
        # when
        result = db_load()
        # then
        self.assertEqual({}, result)
        con.assert_called_once_with("ptymer.db")

    def test_create_timestamp(self) -> None:
        # given
        con = patch("app.sqlite3.connect").start()
        now = patch("app.datetime", wraps=datetime).start()
        now.now.return_value = datetime.strptime(
            "2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S"
        )
        date_today = "2024-01-01"
        expected_call = "INSERT INTO timestamp VALUES ('2024-01-01', 'start', '2024-01-01 17:00:00')"
        # when
        create_timestamp(con, date_today, "start")
        # then
        con.assert_has_calls([call.cursor(), call.cursor().execute(expected_call)])

    def test_check_state_allowed(self) -> None:
        # given
        mock_con = MagicMock(spec=Connection)
        mock_con.cursor.return_value.execute.return_value = "start"
        date_today = "2024-01-01"
        for event, expected in zip(("start", "stop"), (False, True)):
            with self.subTest(event):
                # when
                result = check_state_allowed(mock_con, date_today, event)
                # then
                self.assertEqual(expected, result)

    def test_ouput_with_timestamp(self) -> None:
        # given
        std_out = patch("builtins.print").start()
        today = patch("app.date", wraps=datetime).start()
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
        # when
        duration = calc_duration(times_1, times_2)
        # then
        self.assertEqual(timedelta(hours=8), duration)

    def test_calc_duration_with_uneven_times(self) -> None:
        # given
        date_ = "2024-01-01"
        times_1 = [(f"{date_} 12:00:00",)]
        times_2 = [(f"{date_} 08:00:00",), (f"{date_} 13:00:00",)]
        # when
        duration = calc_duration(times_1, times_2)
        # then
        self.assertEqual(timedelta(hours=4), duration)
