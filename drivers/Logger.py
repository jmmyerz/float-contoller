"""
Float pod external light / audio controller firmware
Author: jmyers
File: logger.py

"""
from components.Config import Config
from drivers.Time import Time

Config = Config().get.log
time = Time()

# Log levels (enumerated)
Levels = {
    "DEBUG": 0,
    "INFO": 1,
    "WARN": 2,
    "ERROR": 3,
    "CRITICAL": 4,
}


class bcolors:
    WHITE = "\033[39m"
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    CRITICAL = "\033[91m\033[1m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    DEBUG = OKBLUE
    INFO = WHITE
    WARN = WARNING
    ERROR = FAIL
    CRITICAL = CRITICAL


class Logger:
    # Initialize
    def __init__(
        self,
        module_name: str = "Logger",
        conf_level: str = (Config.level if hasattr(Config, "level") else "INFO"),
    ):
        self._module = module_name
        self._conf_level = conf_level.upper()
        self._conf_level_int = Levels[self._conf_level]

        # Dynamically create log level functions
        for lvl, rank in Levels.items():
            setattr(
                self,
                lvl.lower(),
                lambda message, lvl=lvl: self._log(self._module, message, lvl),
            )

    @property
    def configured_level(self):
        """
        Get the configured log level.
        """
        return self._conf_level

    # Log a message with a timestamp, the module, the level, and the message
    def _log(self, module, message, level: str):
        # Retrun without printing if the level is not valid
        if level not in Levels:
            return

        # Get the rank of the level and return without printing if it is below the configured level
        rank = Levels[level]
        if rank < self._conf_level_int:
            return

        try:
            print(
                f"{bcolors.BOLD}[{time.localtime().to_string()}]"
                + f"[{str(module)}] "
                + f"{getattr(bcolors, level.upper())}{str(level)}:{bcolors.ENDC} "
                + f"{getattr(bcolors, level.upper())}{message}{bcolors.ENDC}"
            )
        except Exception as e:
            print(
                f"{bcolors.CRITICAL}[{time.localtime().to_string()}][LOGGER] ERROR: Failed to print message, error: {str(e)}{bcolors.ENDC}"
            )

    def log(self, message, level: str = None):
        """
        Generic log function. Must be called with a valid level.

        :param message: The message to log.
        :param level: The level of the message. Must be one of the following:
            DEBUG, INFO, WARN, ERROR, CRITICAL
        """
        self._log(self._module, message, level)
