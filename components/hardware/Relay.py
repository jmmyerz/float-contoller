import asyncio, machine


class Relay:
    def __init__(self, pin: machine.Pin or tuple or list):
        self._pin = pin
        self._state = self._get_pin(pin)

    def _get_pin(self, pin) -> bool:
        if isinstance(pin, tuple) or isinstance(pin, list):
            return all([self._get_pin(p) for p in pin])
        else:
            return bool(pin.value())

    def _set_pin(self, pin, state):
        self._state = bool(state)
        if isinstance(pin, tuple) or isinstance(pin, list):
            for p in pin:
                self._set_pin(p, state)
        else:
            pin.value(state)

    def on(self):
        self._set_pin(self._pin, True)

    def off(self):
        self._set_pin(self._pin, False)

    def toggle(self):
        self._set_pin(self._pin, not self._state)

    @property
    def state(self) -> bool:
        return self._state

    @state.setter
    def state(self, state: bool):
        self._set_pin(self._pin, state)
