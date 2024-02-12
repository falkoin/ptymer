from copy import deepcopy

import typer
import json
from datetime import datetime, timedelta, date
from os import path

FILE_NAME = "data.json"
FORMAT = "%Y-%m-%d %H:%M:%S"


def db_file_existing() -> bool:
    return path.isfile(f"./{FILE_NAME}")


def db_load() -> dict:
    with open(FILE_NAME, "r") as file:
        return json.load(file)


def create_entry(data: dict, today: str) -> dict:
    if not data.get(today):
        data[today] = []
    return data


def create_timestamp(data: dict, date_today: str, event: str) -> dict:
    data[date_today].append({"event": event, "time": datetime.now().strftime(FORMAT)})
    return data


def save_data(data: dict) -> None:
    with open(FILE_NAME, "w+") as file:
        file.seek(0)
        json.dump(data, file)


def check_state_allowed(data: dict, date_today: str, event: str) -> bool:
    if data_today := data.get(date_today):
        last_event = data_today[-1].get("event")
        return last_event != event
    return True

def calc_duration(data: dict, date_today: str) -> None:
    data_for_date = data.get(date_today)
    if data_for_date:
        all_times = [entry.get("time") for entry in data_for_date]
        diff_times = [
            datetime.strptime(x, FORMAT) - datetime.strptime(y, FORMAT)
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
        data = create_timestamp({date_today: []}, date_today, "start")
        save_data(data)
        return
    data = db_load()
    if check_state_allowed(data, date_today, "start"):
        create_entry(data, date_today)
        data = create_timestamp(data, date_today, "start")
        save_data(data)
    else:
        print("Session already running.")


@app.command()
def stop():
    if not db_file_existing():
        print("No session started, yet")
        return
    data = db_load()
    date_today = f"{date.today()}"
    if check_state_allowed(data, date_today, "stop"):
        create_entry(data, date_today)
        data = create_timestamp(data, date_today, "stop")
        save_data(data)
        calc_duration(data, date_today)
    else:
        print("Session already stopped.")


@app.command()
def show():
    if not db_file_existing():
        print("No data to show")
        return
    data = db_load()
    date_today = f"{date.today()}"
    if check_state_allowed(data, date_today, "stop"):
        data = create_timestamp(data, date_today, "stop")
    calc_duration(data, date_today)


if __name__ == "__main__":
    app()
