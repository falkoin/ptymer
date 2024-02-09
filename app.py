import typer
import json
from datetime import datetime, timedelta, date
from os import path

FILE_NAME = "data.json"


def db_file_existing() -> bool:
    return path.isfile(f"./{FILE_NAME}")


def create_file() -> None:
    with open(FILE_NAME, "w") as file:
        json.dump({f"{date.today()}": []}, file)


def db_load() -> dict:
    with open(FILE_NAME, "r") as file:
        return json.load(file)


def create_entry(data: dict, today: str) -> dict:
    if not data.get(today):
        data[today] = []
    return data


def create_timestamp(data: dict, date_today: str, event: str) -> None:
    data[date_today].append({"event": event, "time": f"{datetime.now()}"})
    with open(FILE_NAME, "w+") as file:
        file.seek(0)
        json.dump(data, file)


def check_state_allowed(data: dict, date_today: str, event: str) -> bool:
    if data_today := data.get(date_today):
        last_event = data_today[-1].get("event")
        return last_event != event
    raise Exception("Couldn't find date entry in data file.")


def calc_duration(data: dict, date_today: str) -> None:
    data_for_date = data.get(date_today)
    if data_for_date:
        all_times = [entry.get("time") for entry in data_for_date]
        format_ = "%Y-%m-%d %H:%M:%S.%f"
        diff_times = [
            datetime.strptime(x, format_) - datetime.strptime(y, format_)
            for x, y in zip(all_times[1::2], all_times[::2])
        ]

        print(f"Worked for {sum(diff_times, timedelta())} hours")
    else:
        raise Exception("Couldn't calculate duration for today")


app = typer.Typer()


@app.command()
def start():
    date_today = f"{date.today()}"
    if not db_file_existing():
        create_timestamp({date_today: []}, date_today, "start")
        return
    data = db_load()
    if check_state_allowed(data, date_today, "start"):
        create_entry(data, date_today)
        create_timestamp(data, date_today, "start")
    else:
        print("Session already running.")


@app.command()
def stop():
    if not db_file_existing():
        print("No session started, yet")
    data = db_load()
    date_today = f"{date.today()}"
    if check_state_allowed(data, date_today, "stop"):
        create_entry(data, date_today)
        create_timestamp(data, date_today, "stop")
        calc_duration(data, date_today)
    else:
        print("Session already stopped.")


if __name__ == "__main__":
    app()
