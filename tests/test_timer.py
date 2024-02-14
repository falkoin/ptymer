from unittest import TestCase
from unittest.mock import patch
from app import check_state_allowed, create_entry, db_file_existing


class TestCreateEntry(TestCase):

    def setUp(self) -> None:
        self.data = {"2024-01-01": [{"some_key": "some_value"}]}

    def test_create_entry(self) -> None:
        # when
        result = create_entry(self.data, "2024-01-01")
        # then
        self.assertEqual(self.data, result)

    def test_create_entry_new_day(self) -> None:
        # when
        today = "2024-12-12"
        result = create_entry(self.data, today)
        # then
        self.assertEqual(self.data | {today: []}, result)


class TestDb(TestCase):

    def setUp(self) -> None:
        self.db_file = patch("os.path.isfile").start()

    def test_db_file_existing(self) -> None:
        # given
        self.db_file.return_value = True
        # when
        result = db_file_existing()
        # then
        self.db_file.assert_called_with("./data.json")
        self.assertEqual(True, result)

    def test_db_file_not_existing(self) -> None:
        # given
        self.db_file.return_value = False
        # when
        result = db_file_existing()
        # then
        self.db_file.assert_called_with("./data.json")
        self.assertEqual(False, result)


class TestState(TestCase):

    def setUp(self) -> None:
        self.date_today = "2024-01-01"

    def test_check_state_allowed(self):
        # given
        data = {self.date_today: [{"event": "start"}, {"event": "stop"}]}
        # when
        for event, expected in zip(("start", "stop"), (True, False)):
            with self.subTest(f"event: {event}"):
                result = check_state_allowed(data, self.date_today, event)
                # then
                self.assertEqual(expected, result)

    def test_check_state_allowed_date_not_found(self):
        # given
        data = {"1999-01-01": []}
        # when
        with self.assertRaises(Exception) as error:
            check_state_allowed(data, self.date_today, "start")
        # then
        self.assertEqual(
            "Couldn't find date entry in data file.", error.exception.args[0]
        )
