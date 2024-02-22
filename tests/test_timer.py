from unittest import TestCase
from unittest.mock import call, MagicMock, patch
from app import db_create, check_state_allowed, db_file_existing
import sqlite3


class TestDb(TestCase):

    def setUp(self) -> None:
        self.db_file = patch("os.path.isfile").start()
        self.conn = sqlite3.connect(":memory:")
        self.filename = "ptymer.db"

    def tearDown(self):
        self.conn.close()

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
                [call.connect(self.filename),
                 call.connect().cursor(),
                 call.connect().cursor().execute(
                     'CREATE TABLE timestamp(date, event, time)'
                     )
                 ]
                )
