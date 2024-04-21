from unittest import TestCase
from unittest.mock import call, patch

from app import check_correct_date_format, db_file_existing, output_day, output_week, output_with_timestamp, remove_date_from_date_time, remove_time_from_date_time
from app import app
from datetime import datetime, date
from typer.testing import CliRunner


class TestApp(TestCase):

    def setUp(self) -> None:
        self.runner = CliRunner()
        self.db_file_existing = patch("app.db_file_existing").start()

    def tearDown(self) -> None:
        patch.stopall()

    def test_db_file_existing(self) -> None:
        # given
        db_file = patch("app.path.isfile", return_value=True).start()
        # when
        result = db_file_existing()
        # then
        db_file.assert_called_with("./ptymer.db")
        self.assertEqual(True, result)

    def test_db_file_not_existing(self) -> None:
        # given
        db_file = patch("app.path.isfile", return_value=False).start()
        # when
        result = db_file_existing()
        # then
        db_file.assert_called_with("./ptymer.db")
        self.assertEqual(False, result)

    def test_output_with_timestamp(self) -> None:
        # given
        std_out = patch("app.print").start()
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

    def test_app_with_start(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=True).start()
        patch("app.Timer.create_timestamp").start()
        # when
        result = self.runner.invoke(app, ["start"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("Started working" in result.stdout)

    def test_app_with_start_has_collision(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=True).start()
        patch("app.Timer.create_timestamp", side_effect=Exception()).start()
        # when
        with self.assertRaises(Exception):
            result = self.runner.invoke(app, ["start"])
            # then
            self.assertEqual(0, result.exit_code)
            self.assertTrue("Timestamp collision with exisiting one" in result.stdout)

    def test_app_with_start_already_started(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=False).start()
        # when
        result = self.runner.invoke(app, ["start"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("Session already running." in result.stdout)

    def test_app_show(self) -> None:
        # given
        patch("app.Timer.calc_worktime", return_value=1337).start()
        patch("app.Database.get_last_event", return_value="start").start()
        patch("app.Timer.create_timestamp", side_effect=Exception()).start()
        # when
        self.runner.invoke(app, ["start"])
        result = self.runner.invoke(app, ["show"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("Worked for 1337 hours" in result.stdout)

    def test_app_show_without_start(self) -> None:
        # given
        patch("app.Database.get_last_event", return_value=[]).start()
        # when
        result = self.runner.invoke(app, ["show"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("No session existing for today, yet" in result.stdout)

    def test_app_show_without_database(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["show"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("No data to show" in result.stdout)

    def test_app_stop_no_db_file(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["stop"])
        # then
        self.assertTrue("No session started, yet", result.stdout)

    def test_app_stop_already_stopped(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=False).start()
        # when
        result = self.runner.invoke(app, ["stop"])
        # then
        self.assertTrue("Session already stopped.", result.stdout)

    def test_app_stop_with_collision(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=True).start()
        patch("app.Timer.create_timestamp", side_effect=Exception()).start()
        # when
        with self.assertRaises(Exception):
            result = self.runner.invoke(app, ["start"])
            # then
            self.assertEqual(0, result.exit_code)
            self.assertTrue("Timestamp collision with exisiting one" in result.stdout)
        # when
        result = self.runner.invoke(app, ["stop"])
        # then
        self.assertTrue("Session already stopped.", result.stdout)

    def test_app_with_stop(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=True).start()
        patch("app.Timer.create_timestamp").start()
        patch("app.Timer.calc_worktime", return_value="01:33:07").start()
        # when
        result = self.runner.invoke(app, ["stop"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("Worked for 01:33:07 hours" in result.stdout)

    def test_app_week_without_database(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["week"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("No data to show" in result.stdout)

    def test_app_week_without_data(self) -> None:
        # given
        patch("app.Timer.calc_week", return_value=[]).start()
        # when
        result = self.runner.invoke(app, ["week"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("No data to show" in result.stdout)

    def test_app_week(self) -> None:
        # given
        datetime_ = datetime.strptime("2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S")
        patch("app.Timer.calc_week", return_value=[(datetime_, "something")]).start()
        output_week = patch("app.output_week").start()
        # when
        result = self.runner.invoke(app, ["week"])
        # then
        self.assertEqual(0, result.exit_code)
        output_week.assert_called_with([(datetime_, "something")])

    def test_output_week(self) -> None:
        # given
        with patch("app.Table") as mock:
            console = patch("app.console.print").start()
            data = [
                (datetime.strptime("2024-01-03", "%Y-%m-%d"), 1),
                (datetime.strptime("2024-01-02", "%Y-%m-%d"), 2),
                (datetime.strptime("2024-01-01", "%Y-%m-%d"), 3),
            ]
            expected_calls = [
                call("Day", "Worktime"),
                call().add_row("Monday", "3"),
                call().add_row("Tuesday", "2"),
                call().add_row("Wednesday", "1"),
            ]
            # when
            output_week(data)
            # then
            console.assert_called_once()
            mock.assert_has_calls(expected_calls)

    def test_app_timestamps(self) -> None:
        # given
        date_ = "2024-01-01 17:00:00"
        patch("app.Database.get_data_by_date", return_value=[(date_, "start")]).start()
        output_day = patch("app.output_day").start()
        # when
        result = self.runner.invoke(app, ["timestamps", "2024-01-01"])
        # then
        self.assertEqual(0, result.exit_code)
        output_day.assert_called_with([(date_, "start")])

    def test_app_timestamps_no_db_file(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["timestamps", "2024-01-01"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("No data to show" in result.stdout)

    def test_app_timestamps_no_entries(self) -> None:
        # given
        patch("app.Database.get_data_by_date", return_value=[]).start()
        # when
        result = self.runner.invoke(app, ["timestamps", "2024-01-01"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("No entries for today" in result.stdout)

    def test_app_timestamps_with_default(self) -> None:
        # given
        output_day = patch("app.output_day").start()
        today = patch("database.date", wraps=datetime).start()
        today.today.return_value = date(2024, 1, 1)
        date_ = "2024-01-01 17:00:00"
        patch("app.Database.get_data_by_date", return_value=[(date_, "start")]).start()
        # when
        result = self.runner.invoke(app, ["timestamps"])
        # then
        self.assertEqual(0, result.exit_code)
        output_day.assert_called_with([(date_, "start")])

    def test_app_timestamps_incorrect_date(self) -> None:
        # given
        patch("app.check_correct_date_format", return_value=False).start()
        # when
        result = self.runner.invoke(app, ["timestamps", "20240101"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertTrue("Incorrect date format. Use: YYYY-MM-DD" in result.stdout)

    def test_remove_date_from_date_time(self) -> None:
        # given
        date_time = "2024-01-01 22:22:22"
        # when
        result = remove_date_from_date_time(date_time)
        # then
        self.assertEqual("22:22:22", result)

    def test_output_day(self) -> None:
        # given
        with patch("app.Table") as mock:
            console = patch("app.console.print").start()
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

    def test_delete_deletes_successfully(self) -> None:
        # given
        write_timestamp = patch("app.Database.delete_row").start()
        # whe
        result = self.runner.invoke(app, ["delete", "42"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_called_with(42)
        self.assertIn("Timestamp successfully removed", result.stdout)

    def test_delete_deletes_not_successfully(self) -> None:
        # given
        write_timestamp = patch("app.Database.delete_row", return_value=False).start()
        # whe
        result = self.runner.invoke(app, ["delete", "42"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_called_with(42)
        self.assertIn("Removal of timestamp not possible", result.stdout)

    def test_delete_deletes_no_database(self) -> None:
        # given
        self.db_file_existing.return_value = False
        result = self.runner.invoke(app, ["delete", "42"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No data to show", result.stdout)

    def test_date_time_is_successful(self) -> None:
        # given
        write_timestamp = patch("app.Database.write_timestamp").start()
        # whe
        result = self.runner.invoke(app, ["add", "2024-01-01 22:23:42", "start"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_called_with("start", "2024-01-01 22:23:42", "2024-01-01")
        self.assertIn("Timestamp successfully added", result.stdout)

    def test_date_time_incorrect_format(self) -> None:
        # given
        write_timestamp = patch("app.Database.write_timestamp").start()
        # whe
        result = self.runner.invoke(app, ["add", "2024+01+01 22:23:42", "start"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_not_called()
        self.assertIn("Incorrect timestamp format. Use: YYYY-MM-DD HH:MM:SS", result.stdout)

    def test_date_time_incorrect_event(self) -> None:
        # given
        write_timestamp = patch("app.Database.write_timestamp").start()
        # whe
        result = self.runner.invoke(app, ["add", "2024-01-01 22:23:42", "woop"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_not_called()
        self.assertIn("Incorrect event", result.stdout)

    def test_date_time_no_database(self) -> None:
        # given
        self.db_file_existing.return_value= False
        # whe
        result = self.runner.invoke(app, ["add", "2024-01-01 22:23:42", "start"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No data to show", result.stdout)
