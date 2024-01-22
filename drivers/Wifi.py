import asyncio, network, time
from components.Config import Config
from drivers.Logger import Logger

Config = Config().get.network
Logger = Logger(module_name="WLAN")

SecurityModes = {
    "open": 0,
    "wep": 1,
    "wpa-psk": 2,
    "wpa2-psk": 3,
    "wpa/wpa2-psk": 4,
}


class WifiDriver:
    def __init__(
        self,
        context,
        mode: str = (Config.mode if hasattr(Config, "mode") else "ap"),
        ssid: str = (Config.ssid if hasattr(Config, "ssid") else "pod_controller"),
        password: str = (Config.password if hasattr(Config, "password") else ""),
        security: str = (Config.security if hasattr(Config, "security") else "open"),
        hostname: str = (
            Config.hostname if hasattr(Config, "hostname") else "pod_controller"
        ),
        retry_interval: int = (
            Config.retry_interval if hasattr(Config, "retry_interval") else 5
        ),
        timeout: int = (Config.timeout if hasattr(Config, "timeout") else 10),
        max_failures: int = (
            Config.max_failures if hasattr(Config, "max_failures") else 5
        ),
        backoff_interval: int = (
            Config.backoff_interval if hasattr(Config, "backoff_interval") else 300
        ),
    ):
        Logger.debug("Initializing WLAN driver")

        self._context = context

        # Initialize private variables
        self._mode = mode
        self._was_connected = False
        self._ssid = ssid
        self._password = password
        self._security = SecurityModes[security]
        self._hostname = hostname
        self._retry_interval = retry_interval
        self._timeout = timeout
        self._max_failures = max_failures
        self._backoff_interval = backoff_interval

        self._status_code = 0

        # Register events in the runtime
        # self._context.eventstore.create_event("wifi_connected_event")
        # self._context.eventstore.create_event("wifi_connected_init_event")
        # self._context.eventstore.create_event("wifi_disconnected_event")

        # Create the WLAN interface
        self._interface = network.WLAN(
            (network.STA_IF if self._mode == "sta" else network.AP_IF)
        )

        # Add the last 4 of the mac to the ssid if in AP mode and default ssid is used
        if self._mode == "ap" and self._ssid == "pod_controller":
            self._ssid += "_" + self._interface.config("mac").hex(":")[-5:]

        # Configure the AP interface (if in AP mode)
        if self._mode == "ap":
            self._interface.config(
                ssid=self._ssid,
                key=self._password,
                security=self._security,
            )

        # Set hostname to the provided hostname or add the last 4 of the mac to the default hostname
        if self._hostname == "pod_controller":
            self._hostname += "_" + self._interface.config("mac").hex(":")[-5:]
        network.hostname(self._hostname)

        Logger.debug("WLAN hostname: " + self._hostname)

        # Activate the interface
        self._interface.active(True)

        # If this is a sta, run the watchdog
        if self._mode == "sta":
            Logger.debug("WLAN interface is in station mode, starting watchdog...")
            self._watchdog = asyncio.create_task(self._wifi_watchdog())

    @property
    def ssid(self) -> str:
        """
        Get the SSID of the wifi network.

        :return: SSID of the wifi network.
        """
        return self._ssid

    @property
    def hostname(self) -> str:
        """
        Get the hostname of the device.

        :return: Hostname of the device.
        """
        return self._hostname

    @property
    def status_code(self) -> int:
        """
        Get the current status code.

        :return: The current status code. Values are:
            0: Not connected or not in station mode
            1: Connected
            2: Failed to connect, waiting to retry
        """
        return self._status_code

    def cancel_watchdog(self) -> None:
        """
        Cancel the watchdog task.
        """
        self._watchdog.cancel()

    async def _wifi_watchdog(self) -> None:
        """
        Run the wifi watchdog. Only called on a station interface.
        """
        while True:
            if not self._interface.isconnected():
                if self._was_connected:
                    Logger.info("Disconnected from network " + self._ssid)
                await self.connect()

            # Edge case: a soft reboot may maintain the WLAN connection but will reset _was_connected and the status code
            if self._interface.isconnected() and not self._was_connected:
                Logger.info("Soft reset detected, network is still connected")
                Logger.info("Network details: " + str(self._interface.ifconfig()))
                self._was_connected = True
                self._status_code = 1

            # Yield to other tasks
            await asyncio.sleep_ms(100)

    async def _do_connect(self) -> None:
        """
        Connect to wifi.
        """
        # Get the interface
        sta_if = self._interface

        # Log that we are connecting
        Logger.info("Connecting to network " + self._ssid + "...")

        # Store time ticks in ms for timeout, attempt to connect, and wait for connection
        start = time.ticks_ms()
        sta_if.connect(self._ssid, self._password)

        while not sta_if.isconnected() and time.ticks_diff(time.ticks_ms(), start) < (
            self._timeout * 1000
        ):
            await asyncio.sleep_ms(100)

        if time.ticks_diff(time.ticks_ms(), start) >= (self._timeout * 1000):
            raise Exception("Connection timed out")

        # Log success and the network details
        Logger.info("Connected to network " + self._ssid)
        Logger.info("Network details: " + str(sta_if.ifconfig()))

        self._was_connected = True
        self._status_code = 1

    async def connect(self, failures: int = 0) -> bool:
        """
        Connect to wifi unless max_failures has been reached.

        :return: True if connected, False otherwise.
        """

        # Try establishing connection, or log the error and wait _retry_interval seconds
        try:
            await self._do_connect()
            return True

        except Exception as e:
            # If max_failures has not been reached, log the error and wait _retry_interval seconds
            if failures < self._max_failures:
                Logger.error(
                    "Failed to connect to network " + self._ssid + "(" + str(e) + ")"
                )
                Logger.info("Retrying in " + str(self._retry_interval) + " seconds...")
                await asyncio.sleep(self._retry_interval)
                await self.connect(failures=failures + 1)
            else:
                # If max_failures has been reached, log the error, wait _backoff_interval seconds, and return False
                # This will cause the self.run() function to try again
                Logger.error(
                    "Failed to connect to network " + self._ssid + "(" + str(e) + ")"
                )
                Logger.info(
                    "Retry limit reached, restarting in "
                    + str(self._backoff_interval)
                    + " seconds..."
                )
                self._status_code = 2
                await asyncio.sleep(self._backoff_interval)
                return False
