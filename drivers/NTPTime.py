import asyncio
import time as T, ntptime  # type: ignore (assume imports are available in micropython)

from components.Config import Config
from drivers.Logger import Logger
from drivers.Time import Time

Config = Config().get.ntp
Logger = Logger(module_name="NTPTime")


class NTPTime:
    """
    Driver for synchronizing time with NTP server.

    :param ntp_sync_interval: The interval in seconds between NTP syncs. Defaults to 86400 (1 day).
    :param ntp_timeout: The timeout in seconds for NTP syncs. Defaults to 10.
    :param ntp_max_retries: The maximum number of times to retry NTP syncs before giving up. Defaults to 5.
    """

    def __init__(
        self,
        context,  # This is here for backwards compatibility
        ntp_sync_interval: int = (
            Config.sync_interval if hasattr(Config, "sync_interval") else 86400
        ),
        ntp_timeout: int = (Config.timeout if hasattr(Config, "timeout") else 10),
        ntp_max_retries: int = (
            Config.max_retries if hasattr(Config, "max_retries") else 5
        ),
    ):
        Logger.debug("Initializing NTP time driver")
        Logger.debug("NTP sync interval: " + str(ntp_sync_interval))

        # Initialize private variables
        self._last_sync = 0
        self._initial_sync = False
        self._sync_interval = ntp_sync_interval
        self._ntp_timeout = ntp_timeout
        self._max_retries = ntp_max_retries
        self._status_code = 0

        # After init, call self.run()
        self._watchdog = asyncio.create_task(self._run())

    @property
    def last_sync(self) -> int:
        """
        Get the last time time was synced with NTP server.

        :return: The last time time was synced with NTP server.
        """
        return self._last_sync

    @property
    def status_code(self) -> int:
        """
        Get the current status code.

        :return: The current status code.
        """
        return self._status_code

    async def _run(self) -> None:
        while True:
            # If time has not been synced, or it has been more than _sync_interval seconds since last sync, sync time
            if not self._initial_sync or T.ticks_diff(T.ticks_ms(), self._last_sync) > (
                self._sync_interval * 1000
            ):
                Logger.debug(
                    f"Last sync was {T.ticks_diff(T.ticks_ms(), self._last_sync) / 1000:.0f}s ago"
                )
                await self.sync_time()

            # Yield to other tasks
            await asyncio.sleep_ms(100)

    def _cancel_watchdog(self) -> None:
        """
        Cancel the watchdog task.
        """
        self._watchdog.cancel()

    async def sync_time(self, failures=0) -> bool:
        """
        Sync time with NTP server.
        Will retry up to _max_failures times before giving up until next sync interval.

        :param failures: Number of times sync has failed
        """

        try:
            Logger.info("Synchronizing time with NTP server...")

            self._initial_sync = True
            ntptime.timeout = self._ntp_timeout
            ntptime.settime()

            self._last_sync = T.ticks_ms()
            self._status_code = 1

            # Create a time object representing a future time when we will sync again
            next_sync = (
                Time().localtime().offset_seconds_time(self._sync_interval).to_string()
            )

            Logger.info("Synchronized time with NTP server")
            Logger.debug(f"Will resync at approximately {next_sync}")

            return True

        except Exception as e:
            Logger.error(f"Failed to synchronize time with NTP server ({str(e)})")

            if failures < self._max_retries - 1:
                Logger.info("Retrying in 5 seconds...")
                await asyncio.sleep(5)
                await self.sync_time(failures=failures + 1)
            else:
                Logger.error(
                    f"Failed to synchronize time with NTP server after {str(self._max_retries)} attempts, continuing with system time until next sync interval"
                )
                self._last_sync = T.ticks_ms()
                self._status_code = 2

                return False
