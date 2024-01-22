"""
Float pod external light / audio controller firmware
Author: jmyers
File: Drivers/StatusLED.py

Driver for the onboard status LED.
"""

# Import modules
import machine, asyncio

from utilities import type_coro as tc

from . import BaseDriver
from components.Config import Config
from drivers.Logger import Logger

# Get relevant config
Config = Config().get.status_led
Logger = Logger(module_name="StatusLED")

# Define the effect that corresponds to each status code
StatusCodes = {
    "0": ["off", [], {}],
    "1": ["blink", [2, 300, 200, 1000], {"loop": True}],
    "2": ["breathe", [], {"steps": 4}],
    "3": ["blink", [3, 300, 200, 500], {"loop": True}],
}


# StatusLED class
class StatusLED(BaseDriver):
    # Initialize
    def __init__(
        self,
        context,
        pin=Config.pin,
        freq=Config.pwm_frequency,
        duty=0,
        fade_steps=Config.fade_steps,
    ):
        Logger.debug("Initializing StatusLED driver")

        # Initialize parent class
        super().__init__(context=context)

        # Get the app context
        self._context = context

        # Set up LED pin and PWM
        self.led = machine.Pin(pin, machine.Pin.OUT)
        self.pwm = machine.PWM(self.led, freq=freq, duty=duty)

        # Setup initial fade direction for breathing effect
        self.fade_direction = 1

        # Set fade steps for breathing effect
        self.fade_steps = fade_steps

        # Initialize the status code from the app context
        self._status_code = self._context.status_code

        self._current_task = None
        self._run = asyncio.create_task(self._check_status_code())

    async def _check_status_code(self):
        Logger.debug("Starting status code watchdog")
        while True:
            # Get the current status code from the app context
            status_code = self._context.status_code

            # If the status code has changed, update the LED
            if self._status_code != status_code:
                Logger.debug("Status code changed to " + str(status_code))
                self._status_code = status_code

                self.set(
                    StatusCodes[str(status_code)][0],
                    args=StatusCodes[str(status_code)][1],
                    kwargs=StatusCodes[str(status_code)][2],
                )

            # Sleep for 100ms
            await asyncio.sleep_ms(100)

    def deinit(self):
        self._run.cancel()

    def set(self, effect, args=[], kwargs={}):
        """
        This function sets the LED to a specific effect.
        """

        # Delete (cancel) any running LED tasks
        if hasattr(self._current_task, "cancel"):
            self._current_task.cancel()
        else:
            self._current_task = None

        # Verify the requested effect exists
        if not hasattr(self, effect):
            raise ValueError("Invalid effect: " + str(effect))

        # If the requested effect is async, create a task
        func = getattr(self, effect)(*args, **kwargs)
        if isinstance(func, tc):
            self._current_task = asyncio.create_task(
                getattr(self, effect)(*args, **kwargs)
            )

    async def breathe(self, steps=None):
        """
        This function breathes the LED.
        """

        # Set fade steps
        steps = steps if steps != None else self.fade_steps

        while True:
            # Get current duty cycle
            current_duty = self.pwm.duty()

            # If duty cycle is 0, set direction to 1
            if current_duty == 0:
                self.fade_direction = 1
            # If duty cycle is 1023, set direction to -1
            elif current_duty == 1023:
                self.fade_direction = -1

            # Calculate new duty cycle ensuring it is between 0 and 1023
            new_duty = current_duty + (self.fade_direction * steps)
            if new_duty > 1023:
                new_duty = 1023
            elif new_duty < 0:
                new_duty = 0

            # Set duty cycle
            self.pwm.duty(new_duty)

            # Sleep for 1ms
            await asyncio.sleep_ms(10)

    async def blink(
        self,
        flashes=1,
        flash_duration=100,
        flash_interval=0,
        pause_duration=0,
        loop=True,
    ):
        """
        This function blinks the LED.

        flashes: The number of times to blink the LED.
        flash_duration: The duration in milliseconds of each blink.
        flash_interval: The interval in milliseconds between blinks.
        pause_duration: The duration in milliseconds of the pause between blink cycles.
        loop: Whether or not to loop the blink cycle.
        """

        async def _blink():
            # Blink the LED
            for i in range(flashes):
                self.pwm.duty(1023)
                await asyncio.sleep_ms(flash_duration)
                self.pwm.duty(0)
                await asyncio.sleep_ms(flash_interval)
            await asyncio.sleep_ms(pause_duration)

        while loop:
            await _blink()

        await _blink()

    # Turn off
    def off(self):
        self.pwm.duty(0)

    # Turn on
    def on(self):
        self.pwm.duty(1023)

    # Set frequency
    def set_freq(self, freq):
        self.pwm.freq(freq)

    # Get frequency
    def get_freq(self):
        return self.pwm.freq()

    # Get duty cycle
    def get_duty(self):
        return self.pwm.duty()

    # Set duty cycle
    def set_duty(self, duty):
        self.pwm.duty(duty)
