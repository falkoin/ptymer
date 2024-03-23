from unittest import TestCase
from unittest.mock import patch, call
from database import Database
from datetime import datetime, date


class TestDatabase(TestCase):

    def setUp(self) -> None:
        self.filename = ":memory:"

    def tearDown(self) -> None:
        patch.stopall()

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
        patch("database.path.isfile", return_value=True).start()
        sqlite = patch("database.sqlite3").start()
        db = Database(self.filename)
        # when
        db.close()
        # then
        sqlite.assert_has_calls([call.connect().close()])

    def test_db_load(self) -> None:
        # given
        patch("database.path.isfile", return_value=True).start()
        con = patch("database.sqlite3.connect", return_value={}).start()
        # when
        db = Database(self.filename)
        # then
        self.assertEqual({}, db.con)
        con.assert_called_once_with(":memory:")

    def test_create_timestamp(self) -> None:
        # given
        patch("database.path.isfile", return_value=True).start()
        patch("app.Timer._check_valid_timestamp", return_value=True).start()
        con = patch("database.sqlite3").start()
        today = patch("database.date", wraps=date).start()
        today.today.return_value = "2024-01-01"
        time_stamp = datetime.strptime("2024-01-01 17:00:00", "%Y-%m-%d %H:%M:%S")
        db = Database(self.filename)
        expected_call = "INSERT INTO timestamp VALUES ('2024-01-01', 'start', '2024-01-01 17:00:00')"
        con.reset_mock()
        # when
        db.write_timestamp("start", time_stamp)
        # then
        con.assert_has_calls(
            [
                call.connect().cursor(),
                call.connect().cursor().execute(expected_call),
                call.connect().commit(),
            ]
        )

    def test_last_event(self) -> None:
        # given
        today = patch("database.date", wraps=date).start()
        today.today.return_value = "2024-01-01"
        patch("database.path.isfile", return_value=True).start()
        con = patch("database.sqlite3").start()
        db = Database(self.filename)
        expected_call = (
            "SELECT event FROM timestamp WHERE date='2024-01-01' ORDER BY time DESC"
        )
        con.reset_mock()
        # when
        db.get_last_event()
        # then
        con.assert_has_calls(
            [
                call.connect().cursor(),
                call.connect().cursor().execute(expected_call),
                call.connect().cursor().execute().fetchone(),
            ]
        )

    def test_get_times_by(self) -> None:
        # given
        today = patch("database.date", wraps=date).start()
        today.today.return_value = "2024-01-01"
        patch("database.path.isfile", return_value=True).start()
        con = patch("database.sqlite3").start()
        db = Database(self.filename)
        for event in ("start", "stop"):
            with self.subTest(event):
                expected_call = (
                    f"SELECT time FROM timestamp WHERE date='2024-01-01' AND event='{event}' ORDER BY time ASC"
                )
                con.reset_mock()
                # when
                db.get_times_by(event=event)
                # then
                con.assert_has_calls(
                    [
                        call.connect().cursor(),
                        call.connect().cursor().execute(expected_call),
                        call.connect().cursor().execute().fetchall(),
                    ]
                )
