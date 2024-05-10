from unittest import TestCase
from unittest.mock import patch, call
from utility import (
    db_file_existing,
    output_with_timestamp,
    output_week,
    remove_date_from_date_time,
    check_correct_date_format,
    output_day,
    remove_time_from_date_time,
    _format_timedelta,
)
from datetime import datetime, date, timedelta


class TestUtility(TestCase):

    def setUp(self) -> None:
        self.db_file_existing = patch("utility.db_file_existing").start()
        now = patch("utility.datetime", wraps=datetime).start()
        now.now.return_value = datetime.strptime(
            "2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S"
        )

    def tearDown(self) -> None:
        patch.stopall()

    def test_db_file_existing(self) -> None:
        # given
        db_file = patch("utility.path.isfile", return_value=True).start()
        # when
        result = db_file_existing()
        # then
        db_file.assert_called_with("./ptymer.db")
        self.assertEqual(True, result)

    def test_db_file_not_existing(self) -> None:
        # given
        db_file = patch("utility.path.isfile", return_value=False).start()
        # when
        result = db_file_existing()
        # then
        db_file.assert_called_with("./ptymer.db")
        self.assertEqual(False, result)

    def test_output_with_timestamp(self) -> None:
        # given
        std_out = patch("utility.print").start()
        today = patch("database.date", wraps=datetime).start()
        today.today.return_value = date(2024, 1, 1)
        text = "text"
        # when
        output_with_timestamp(text)
        # then
        std_out.assert_called_once_with(f"[17:00:00]: {text}")

    def test_output_week(self) -> None:
        # given
        with patch("utility.Table") as mock:
            console = patch("utility.console.print").start()
            data = [
                (datetime.strptime("2024-01-03", "%Y-%m-%d"), timedelta(hours=8)),
                (datetime.strptime("2024-01-02", "%Y-%m-%d"), timedelta(hours=8)),
                (datetime.strptime("2024-01-01", "%Y-%m-%d"), timedelta(hours=8)),
            ]
            expected_calls = [
                call("Day", "Worktime"),
                call().add_row("Monday", "8:00:00"),
                call().add_row("Tuesday", "8:00:00"),
                call().add_row("Wednesday", "8:00:00"),
                call().add_section(),
                call().add_row("Overall", "24:00:00"),
            ]
            # when
            output_week(data)
            # then
            console.assert_called_once()
            mock.assert_has_calls(expected_calls)

    def test_remove_date_from_date_time(self) -> None:
        # given
        date_time = "2024-01-01 22:22:22"
        # when
        result = remove_date_from_date_time(date_time)
        # then
        self.assertEqual("22:22:22", result)

    def test_output_day(self) -> None:
        # given
        with patch("utility.Table") as mock:
            console = patch("utility.console.print").start()
            data = [
                (54, "2024-01-03 12:00:12", "start"),
                (55, "2024-01-03 22:22:22", "stop"),
                (56, "2024-01-03 23:23:42", "start"),
            ]
            expected_calls = [
                call("Index", "Time", "Event"),
                call().add_row("54", "12:00:12", "start"),
                call().add_row("55", "22:22:22", "stop"),
                call().add_row("56", "23:23:42", "start"),
            ]
            # when
            output_day(data)
            # then
            console.assert_called_once()
            mock.assert_has_calls(expected_calls)

    def test_check_correct_date_format_with_correct_input(self) -> None:
        # given
        date = "2024-01-01"
        # when
        result = check_correct_date_format(date, "%Y-%m-%d")
        # then
        self.assertEqual(True, result)

    def test_check_correct_date_format_with_incorrect_input(self) -> None:
        # given
        date = "20240101"
        # when
        result = check_correct_date_format(date, "%Y-%m-%d")
        # then
        self.assertEqual(False, result)

    def test_remove_time_from_date_time(self) -> None:
        # given
        date_time = "2024-01-01 23:42:05"
        # when
        result = remove_time_from_date_time(date_time)
        # then
        self.assertEqual("2024-01-01", result)

    def test_format_timedetla(self) -> None:
        # given
        timedelta_ = timedelta(hours=25)
        # when
        result = _format_timedelta(timedelta_)
        # then
        self.assertEqual("25:00:00", result)
