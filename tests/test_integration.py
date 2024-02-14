from unittest import TestCase
from unittest.mock import patch
from datetime import datetime, date
from app import show


class TestShow(TestCase):

    def setUp(self) -> None:
        self.db_file_existing = patch("app.db_file_existing").start()
        self.today = patch("app.date", wraps=datetime).start()
        self.today.today.return_value = date(2024, 1, 1)
        self.now = patch("app.datetime", wraps=datetime).start()
        self.now.now.return_value = datetime.strptime(
            "2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S"
        )
        self.db_load = patch("app.db_load").start()
        self.std_out = patch("builtins.print").start()

    def test_show_duration(self) -> None:
        # given
        self.db_file_existing.return_value = True
        data = {
            "2024-01-01": [
                {"time": "2024-01-01 08:00:00", "event": "start"},
                {"time": "2024-01-01 16:00:00", "event": "stop"},
            ]
        }
        self.db_load.return_value = data
        # when
        show()
        # then
        self.std_out.assert_called_with("Worked for 8:00:00 hours")

    def test_show_duration_while_state_is_start(self) -> None:
        # given
        self.db_file_existing.return_value = True
        data = {
            "2024-01-01": [
                {"time": "2024-01-01 08:00:00", "event": "start"},
            ]
        }
        self.db_load.return_value = data
        # when
        show()
        # then
        self.std_out.assert_called_with("Worked for 9:00:00 hours")
