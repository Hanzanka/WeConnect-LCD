from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from weconnect_id.vehicle import WeConnectVehicle
from enum import Enum
import RPi.GPIO as GPIO
from threading import Timer, Lock
import operator
import logging


LOG = logging.getLogger("led")


def load_automated_leds(config: dict, weconnect_vehicle: WeConnectVehicle) -> None:
    """
    Loads the automated LEDs that are configured in the app configuration file.

    Args:
        config (dict): Configurations for the automated LEDs.
        weconnect_vehicle (WeConnectVehicle): Used to provide data for the LEDTriggers.
    """

    LOG.debug("Initializing automated LEDs")
    led_configs = config["automated leds"]
    for led_config in led_configs:
        LEDDriver(
            pin=led_config["pin"],
            id=led_config["id"],
            default_blinker_frequency=led_config["default frequency"],
            trigger=led_config["trigger"],
            weconnect_vehicle=weconnect_vehicle,
        )
    LOG.debug("Successfully initialized automated LEDs")


class LEDTrigger:
    def __init__(
        self, led_driver: LEDDriver, trigger: dict, weconnect_vehicle: WeConnectVehicle
    ) -> None:
        """
        Used to automatically operate the LED with WeConnectVehicleDataProperty values.

        Args:
            led_driver (LEDDriver): Used to control the LED.
            trigger (_type_): Configurations for the LEDTrigger.
            weconnect_vehicle (WeConnectVehicle): Used to provide data for the LEDTrigger.

        Raises:
            e: Raised when error is detected initializing the trigger.
        """

        LOG.debug(f"Initializing LEDTrigger for LEDDriver (ID: {led_driver.id})")
        self.__led_driver = led_driver

        try:
            self.__default_mode = trigger["default mode"]
            self.__compare = trigger["compare"] == "True"
            if self.__compare:
                self.__trigger_value = trigger["trigger values"]["value"]
                self.__trigger_mode = trigger["trigger values"]["target"]
                self.__compare_operator = {
                    "==": operator.eq,
                    "<=": operator.le,
                    ">=": operator.ge,
                    "<": operator.lt,
                    ">": operator.gt,
                    "!=": operator.ne,
                }[trigger["operator"]]

            else:
                self.__trigger_values = trigger["trigger values"]

            self.__data_provider = weconnect_vehicle.get_data_property(
                trigger["data id"]
            )
            self.__data_provider.add_callback_function(
                id="LED", function=self._on_data_update
            )

        except Exception as e:
            raise e
        LOG.debug(f"Successfully initialized LEDTrigger for LEDDriver (ID: {self.__led_driver.id})")

    def _on_data_update(self) -> None:
        self.__led_driver._on_trigger_update(self.__get_trigger_value())

    def __get_trigger_value(self):
        if self.__compare:
            if self.__compare_operator(
                self.__trigger_value, self.__data_provider.value
            ):
                return self.__trigger_mode
            else:
                return self.__default_mode

        data_value = self.__data_provider.string_value

        if data_value not in self.__trigger_values:
            return self.__default_mode

        target = self.__trigger_values[data_value]["target"]
        if target == "blink":
            frequency = self.__trigger_values[data_value]["frequency"]
            return target, frequency
        return target


class LEDDriver:
    class LEDState(Enum):
        ON = "on"
        OFF = "off"
        BLINKING = "blinking"

    def __init__(
        self,
        pin: int,
        id: str,
        default_blinker_frequency: float,
        trigger: dict = None,
        weconnect_vehicle: WeConnectVehicle = None,
    ) -> None:
        """
        Initializes LED.

        Args:
            pin (int): Pin that the LED is connected to.
            id (str): ID for the LED.
            default_blinker_frequency (float): Default blinking frequency for the LED.
            trigger (dict, optional): Configuration for the LEDTrigger. Defaults to None.
            weconnect_vehicle (WeConnectVehicle, optional): Used to provide data for the LEDTrigger. Defaults to None.
        """

        LOG.debug(f"Initializing LEDDriver (ID: {id})")
        self.__id = id
        self.__pin = pin
        GPIO.setup(self.__pin, GPIO.OUT)
        GPIO.output(self.__pin, GPIO.LOW)
        self.__state = LEDDriver.LEDState.OFF

        self.__default_blinker_frequency = default_blinker_frequency
        self.__blinker_frequency = default_blinker_frequency

        self.__operation_lock = Lock()

        if trigger is not None and weconnect_vehicle is not None:
            self.__trigger_functions = {
                "on": self.turn_on,
                "off": self.turn_off,
                "blink": self.blink,
            }
            self.__trigger = LEDTrigger(
                led_driver=self, trigger=trigger, weconnect_vehicle=weconnect_vehicle
            )
            self.__load_led_mode()
        LOG.debug(f"Successfully initialized LEDDriver (ID: {self.__id})")

    @property
    def id(self):
        return self.__id

    @property
    def state(self) -> Enum:
        return self.__state

    def _on_trigger_update(self, trigger_command) -> None:
        if trigger_command is not None:
            if isinstance(trigger_command, tuple):
                self.__trigger_functions[trigger_command[0]](trigger_command[1])
            else:
                self.__trigger_functions[trigger_command]()

    def __load_led_mode(self) -> None:
        self.__trigger._on_data_update()

    def __turn_LED_off(self) -> None:
        GPIO.output(self.__pin, GPIO.LOW)
        if self.__state == LEDDriver.LEDState.BLINKING:
            timer = Timer(
                interval=1 / self.__blinker_frequency / 2, function=self.__turn_LED_on
            )
            timer.daemon = True
            timer.start()
            return
        if self.__state == LEDDriver.LEDState.ON:
            self.__turn_LED_on()

    def __turn_LED_on(self) -> None:
        GPIO.output(self.__pin, GPIO.HIGH)
        if self.__state == LEDDriver.LEDState.BLINKING:
            timer = Timer(
                interval=1 / self.__blinker_frequency / 2, function=self.__turn_LED_off
            )
            timer.daemon = True
            timer.start()
            return
        if self.__state == LEDDriver.LEDState.OFF:
            self.__turn_LED_off()

    def blink(self, frequency=None) -> None:
        LOG.debug(f"Starting blinker on LEDDriver (ID: {self.__id})")
        if (
            self.__state == LEDDriver.LEDState.BLINKING
            and frequency == self.__blinker_frequency
        ):
            return

        with self.__operation_lock:
            self.__state = LEDDriver.LEDState.BLINKING
            self.__blinker_frequency = (
                self.__default_blinker_frequency if frequency is None else frequency
            )
            self.__turn_LED_on()

    def stop_blinking(self) -> None:
        LOG.debug(f"Stopping blinker on LEDDriver (ID: {self.__id})")
        if self.__state != LEDDriver.LEDState.BLINKING:
            return
        with self.__operation_lock:
            self.__state = LEDDriver.LEDState.OFF

    def turn_on(self) -> None:
        LOG.debug(f"Turning ON LEDDriver (ID: {self.__id})")
        if self.__state == LEDDriver.LEDState.ON:
            return
        with self.__operation_lock:
            state_before = self.__state
            self.__state = LEDDriver.LEDState.ON
            if state_before == LEDDriver.LEDState.OFF:
                self.__turn_LED_on()

    def turn_off(self) -> None:
        LOG.debug(f"Turning OFF LEDDriver (ID: {self.__id})")
        if self.__state == LEDDriver.LEDState.OFF:
            return
        with self.__operation_lock:
            state_before = self.__state
            self.__state = LEDDriver.LEDState.OFF
            if state_before == LEDDriver.LEDState.ON:
                self.__turn_LED_off()

    def set_frequency(self, frequency) -> None:
        LOG.debug(f"Setting default blinker frequency to {frequency} of LEDDriver (ID: {self.__id})")
        if frequency <= 0:
            raise ValueError("Frequency must be greater than zero")
        self.__blinker_frequency = frequency


def create_led_driver(pin: int, id: str, default_frequency: float) -> LEDDriver:
    '''
    Create new LEDDriver without LEDTrigger

    Args:
        pin (int): Pin where the LED is connected.
        id (str): ID for the LEDDriver.
        default_frequency (float): Default blinker frequency for the LEDDriver.

    Returns:
        LEDDriver
    '''
    return LEDDriver(pin=pin, id=id, default_blinker_frequency=default_frequency)
