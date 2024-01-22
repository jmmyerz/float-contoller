"""
Float pod external light / audio controller firmware
"""

import asyncio, machine

from components.App import BaseApp
from drivers.Logger import Logger

Logger = Logger(module_name="main")
GLOBAL_DEBUG = False


def set_global_exception():
    def handle_exception(loop, context):
        import sys

        sys.print_exception(context["exception"])
        sys.exit()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(handle_exception)


class FloatPodController(BaseApp):
    def __init__(self, *args, **kwargs):
        kwargs["app_name"] = "FloatPodController"

        self._status_code = 0

        self._light_longpress = False
        self._audio_longpress = False

        self.Logger = Logger

        # Initialize parent class
        super().__init__(*args, **kwargs)

    @property
    def status_code(self):
        """
        Get the current status code.
        """
        return self._status_code

    @status_code.setter
    def status_code(self, status_code: int):
        """
        Set the current status code.
        """
        self._status_code = status_code

    def _longpress_flag(self, button, state):
        """
        Set the longpress flag for a button.
        """
        flag = getattr(self, "_" + button + "_longpress")

        if flag != state:
            Logger.debug(f"Setting {button} longpress flag to {state}")
            setattr(self, "_" + button + "_longpress", state)

    async def _longpress_watchdog(self):
        """
        Watchdog for longpresses.
        """
        while True:
            if self._light_longpress and self._audio_longpress:
                self.Logger.info("Longpress detected on both buttons, resetting")
                machine.reset()
            await asyncio.sleep_ms(100)

    async def setup(self):
        """
        App setup sequence.
        """
        self.Logger.info("Running setup")

        # Initialize the StatusLED before we change the status code
        from drivers.StatusLED import StatusLED

        self.StatusLED = StatusLED(self)

        # Set the status code to 1 (setup active)
        self.status_code = 1

        if GLOBAL_DEBUG:
            from drivers.Logger import Levels

            for level in Levels:
                getattr(self.Logger, level.lower())("Testing log level " + level)

        # Initialize the TaskStore
        self.load_module("components.TaskStore", "TaskStore")

        # Initialize the Wifi driver
        from drivers.Wifi import WifiDriver

        self.Wifi = WifiDriver(self)

        # Initialize the IO pins
        self.POD_LIGHT_CTRL_NO = machine.Pin(15, machine.Pin.IN)
        self.POD_AUDIO_CTRL_NO = machine.Pin(12, machine.Pin.IN)
        self.POD_AUDIO_CTRL_NC = machine.Pin(14, machine.Pin.IN)
        self.POD_LIGHT_CTRL_NC = machine.Pin(13, machine.Pin.IN)

        self.EXT_LIGHT_CTRL = machine.Pin(32, machine.Pin.IN)
        self.EXT_AUDIO_CTRL = machine.Pin(33, machine.Pin.IN)

        self.AUDIO_CH1_OUT = machine.Pin(25, machine.Pin.OUT)
        self.AUDIO_CH2_OUT = machine.Pin(26, machine.Pin.OUT)
        self.LIGHT_OUT = machine.Pin(27, machine.Pin.OUT)

        from components.hardware import Switch, PushButton, Relay

        Switch = Switch.Switch
        Pushbutton = PushButton.Pushbutton
        Relay = Relay.Relay

        # Create relay objects for the light and audio relays
        self.LightRelay = Relay(self.LIGHT_OUT)
        self.AudioRelays = Relay([self.AUDIO_CH1_OUT, self.AUDIO_CH2_OUT])

        # Create switch objects for the pod light and audio controls
        self.PodLightSwitch = Switch(self.POD_LIGHT_CTRL_NO)
        self.PodAudioSwitch = Switch(self.POD_AUDIO_CTRL_NO)

        # Setup the open_func and close_func for the pod light and audio controls to toggle the light and audio relays
        self.PodLightSwitch.open_func(self.LightRelay.toggle)
        self.PodLightSwitch.close_func(self.LightRelay.toggle)
        self.PodAudioSwitch.open_func(self.AudioRelays.toggle)
        self.PodAudioSwitch.close_func(self.AudioRelays.toggle)

        # Create pushbutton objects for the external light and audio controls
        self.ExtLightButton = Pushbutton(self.EXT_LIGHT_CTRL)
        self.ExtAudioButton = Pushbutton(self.EXT_AUDIO_CTRL)

        # Setup press_func for the external light and audio controls to toggle the light and audio relays
        self.ExtLightButton.press_func(self.LightRelay.toggle)
        self.ExtAudioButton.press_func(self.AudioRelays.toggle)

        # Setup longpress_func for the external light and audio controls
        # The longpress_func should set a flag to enable functionality of longpressing both buttons at the same time to soft reset the program
        self.ExtLightButton.long_func(self._longpress_flag, ["light", True])
        self.ExtAudioButton.long_func(self._longpress_flag, ["audio", True])

        # Set release_func for the external light and audio controls to clear the longpress flag
        self.ExtLightButton.release_func(self._longpress_flag, ["light", False])
        self.ExtAudioButton.release_func(self._longpress_flag, ["audio", False])

        # Set the initial state of the light and audio relays based on the state of the pod light and audio controls
        # Note that a state of 0 means the switch is "on" and a state of 1 means the switch is "off"
        self.LightRelay.state = not self.PodLightSwitch()
        self.AudioRelays.state = not self.PodAudioSwitch()

        # Create a watchdog task to reset the program if both buttons are longpressed at the same time
        self._reset_watchdog = asyncio.create_task(self._longpress_watchdog())

        # Loop until wifi is connected or the timeout is reached
        self.Logger.info("Waiting for wifi connection to continue setup")
        while self.Wifi.status_code not in [1, 2]:
            await asyncio.sleep_ms(100)

        # Initialize NTPTime sync
        from drivers.NTPTime import NTPTime

        self.NTPTime = NTPTime(self)

        self.Logger.info("Waiting for NTP sync to continue setup")
        while self.NTPTime.status_code not in [1, 2]:
            await asyncio.sleep_ms(100)

        Logger.info("Application setup complete")
        self.status_code = 2

    async def run(self):
        # Set up the app
        await self.setup()

        # Run the main loop
        await super()._loop()


if __name__ == "__main__":
    # Instantiate the app
    main = FloatPodController()

    # Run the app
    asyncio.run(main.run())
