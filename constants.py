class InfoText:
    HELP_DELTA = "Time delta in minutes to stop in the past."

    WARN_COLLISON = "Timestamp collision with existing one"
    WARN_DURATION = "Couldn't calculate duration for today"
    WARN_SYMBOL = "[red]⏱[/red]"
    CONFIRM_SYMBOL = "[green]⏱[/green]"


class Event:
    START = "start"
    STOP = "stop"


class Format:
    TIME = "%H:%M:%S"
    DATETIME = "%Y-%m-%d %H:%M:%S"
    DATE = "%Y-%m-%d"


class File:
    NAME = "ptymer.db"
