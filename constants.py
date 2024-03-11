class InfoText:
    HELP_DELTA = "Time delta in minutes to stop in the past."

    WARN_COLLISON = "Timestamp collision with existing one"
    WARN_DURATION = "Couldn't calculate duration for today"


class Event:
    START = "start"
    STOP = "stop"


class Format:
    TIME = "%H:%M:%S"
    DATETIIME = "%Y-%m-%d %H:%M:%S"
