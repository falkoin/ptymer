from unittest import TestCase
from unittest.mock import patch

from app import app
from datetime import datetime, date
from typer.testing import CliRunner


class TestApp(TestCase):

    def setUp(self) -> None:
        self.runner = CliRunner()
        self.db_file_existing = patch("app.db_file_existing").start()
        now = patch("utility.datetime", wraps=datetime).start()
        now.now.return_value = datetime.strptime(
            "2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S"
        )

    def tearDown(self) -> None:
        patch.stopall()

    def test_app_with_start(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=True).start()
        patch("app.Timer.create_timestamp").start()
        # when
        result = self.runner.invoke(app, ["start"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("Started working", result.stdout)

    def test_app_with_start_has_collision(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=True).start()
        patch("app.Timer.create_timestamp", side_effect=Exception()).start()
        # when
        result = self.runner.invoke(app, ["start"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("Timestamp collision with existing one", result.stdout)

    def test_app_with_start_already_started(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=False).start()
        # when
        result = self.runner.invoke(app, ["start"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("Session already running.", result.stdout)

    def test_app_show_with_pause(self) -> None:
        # given
        patch("app.Timer.calc_worktime", return_value=1337).start()
        patch("app.Timer.calc_pausetime", return_value=42).start()
        patch("app.Database.get_last_event", return_value="start").start()
        patch("app.Timer.create_timestamp", side_effect=Exception()).start()
        # when
        self.runner.invoke(app, ["start"])
        result = self.runner.invoke(app, ["show"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("Worked for 1337 hours, pause 42 hours", result.stdout)

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
        self.assertIn("Worked for 1337 hours", result.stdout)

    def test_app_show_without_start(self) -> None:
        # given
        patch("app.Database.get_last_event", return_value=[]).start()
        # when
        result = self.runner.invoke(app, ["show"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No session existing for today, yet", result.stdout)

    def test_app_show_without_database(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["show"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No data to show", result.stdout)

    def test_app_stop_no_db_file(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["stop"])
        # then
        self.assertIn("No session started, yet", result.stdout)

    def test_app_stop_already_stopped(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=False).start()
        # whe
        result = self.runner.invoke(app, ["stop"])
        # then
        self.assertIn("Session already stopped.", result.stdout)

    def test_app_stop_with_collision(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=True).start()
        patch("app.Timer.create_timestamp", side_effect=Exception()).start()
        # when
        result = self.runner.invoke(app, ["stop"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("Timestamp collision with existing one", result.stdout)

    def test_app_with_stop(self) -> None:
        # given
        patch("app.Timer.check_state_allowed", return_value=True).start()
        patch("app.Timer.create_timestamp").start()
        patch("app.Timer.calc_worktime", return_value="01:33:07").start()
        # when
        result = self.runner.invoke(app, ["stop"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("Worked for 01:33:07 hours", result.stdout)

    def test_app_week_without_database(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["week"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No data to show", result.stdout)

    def test_app_week_without_data(self) -> None:
        # given
        patch("app.Timer.calc_week", return_value=[]).start()
        # when
        result = self.runner.invoke(app, ["week"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No data to show", result.stdout)

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
        self.assertIn("No data to show", result.stdout)

    def test_app_timestamps_no_entries(self) -> None:
        # given
        patch("app.Database.get_data_by_date", return_value=[]).start()
        # when
        result = self.runner.invoke(app, ["timestamps", "2024-01-01"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No entries for today", result.stdout)

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
        patch("utility.check_correct_date_format", return_value=False).start()
        # when
        result = self.runner.invoke(app, ["timestamps", "20240101"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("Incorrect date format. Use: YYYY-MM-DD", result.stdout)

    def test_delete_deletes_successfully(self) -> None:
        # given
        write_timestamp = patch("app.Database.delete_row").start()
        # when
        result = self.runner.invoke(app, ["delete", "42"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_called_with(42)
        self.assertIn("Timestamp successfully removed", result.stdout)

    def test_delete_deletes_not_successfully(self) -> None:
        # given
        write_timestamp = patch("app.Database.delete_row", return_value=False).start()
        # when
        result = self.runner.invoke(app, ["delete", "42"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_called_with(42)
        self.assertIn("Removal of timestamp not possible", result.stdout)

    def test_delete_deletes_no_database(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["delete", "42"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No data to show", result.stdout)

    def test_date_time_is_successful(self) -> None:
        # given
        write_timestamp = patch("app.Database.write_timestamp").start()
        # when
        result = self.runner.invoke(app, ["add", "2024-01-01 22:23:42", "start"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_called_with("start", "2024-01-01 22:23:42", "2024-01-01")
        self.assertIn("Timestamp successfully added", result.stdout)

    def test_date_time_incorrect_format(self) -> None:
        # given
        write_timestamp = patch("app.Database.write_timestamp").start()
        # when
        result = self.runner.invoke(app, ["add", "2024+01+01 22:23:42", "start"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_not_called()
        self.assertIn(
            "Incorrect timestamp format. Use: YYYY-MM-DD HH:MM:SS", result.stdout
        )

    def test_date_time_incorrect_event(self) -> None:
        # given
        write_timestamp = patch("app.Database.write_timestamp").start()
        # when
        result = self.runner.invoke(app, ["add", "2024-01-01 22:23:42", "woop"])
        # then
        self.assertEqual(0, result.exit_code)
        write_timestamp.assert_not_called()
        self.assertIn("Incorrect event", result.stdout)

    def test_date_time_no_database(self) -> None:
        # given
        self.db_file_existing.return_value = False
        # when
        result = self.runner.invoke(app, ["add", "2024-01-01 22:23:42", "start"])
        # then
        self.assertEqual(0, result.exit_code)
        self.assertIn("No data to show", result.stdout)
