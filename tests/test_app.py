from unittest import TestCase
from unittest.mock import patch
from app import db_file_existing, output_with_timestamp
from datetime import datetime, date


class TestApp(TestCase):

    def setUp(self) -> None:
        self.db_file = patch("app.path.isfile").start()

    def tearDown(self) -> None:
        patch.stopall()

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
