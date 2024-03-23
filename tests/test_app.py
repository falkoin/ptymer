from unittest import TestCase
from unittest.mock import patch
from app import db_file_existing, output_with_timestamp
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
