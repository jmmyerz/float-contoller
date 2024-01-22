import time as T

from components.Config import Config


class Time:
    """
    Time utilities.
    Should always return time.struct_time objects.
    """

    def __init__(self, time=T.gmtime()) -> None:
        self.time = time
        self.Config = Config().get

    def gmtime(self):
        self.time = T.gmtime()
        return self

    def localtime(self):
        self.time = T.localtime(T.time() + (self.Config.time_offset * 3600))
        return self

    def offset_seconds_time(self, offset_seconds):
        self.time = T.localtime(T.mktime(self.time) + offset_seconds)
        return self

    def to_string(self):
        tformat = "{:04d}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}"
        return tformat.format(
            self.time[0],
            self.time[1],
            self.time[2],
            self.time[3],
            self.time[4],
            self.time[5],
        )
