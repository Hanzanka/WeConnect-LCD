from __future__ import annotations
from typing import TYPE_CHECKING
from enum import Enum
import RPi.GPIO as GPIO
from threading import Timer, Lock
import operator

if TYPE_CHECKING:
    from weconnect_id.vehicle import WeConnectVehicle


def load_automated_leds(config: dict, weconnect_vehicle: WeConnectVehicle) -> None:
    led_configs = config["automated leds"]
    for led_config in led_configs:
        LEDDriver(
            pin=led_config["pin"],
            id=led_config["id"],
            default_blinker_frequency=led_config["default frequency"],
            trigger=led_config["trigger"],
            weconnect_vehicle=weconnect_vehicle,
        )


class LEDTrigger:
    def __init__(
        self, led_driver: LEDDriver, trigger, weconnect_vehicle: WeConnectVehicle
    ) -> None:
        self.__driver = led_driver

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
                id="LED", function=self.__on_data_update
            )

        except Exception as e:
            raise e

    def __on_data_update(self) -> None:
        self.__driver.on_trigger_update(self.__get_trigger_value())

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
        pin,
        id,
        default_blinker_frequency,
        trigger=None,
        weconnect_vehicle: WeConnectVehicle = None,
    ) -> None:

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
            self.__trigger = LEDTrigger(self, trigger, weconnect_vehicle)
            self.__load_led_mode()

    @property
    def id(self):
        return self.__id

    @property
    def state(self) -> Enum:
        return self.__state

    def on_trigger_update(self, trigger_command) -> None:
        if trigger_command is not None:
            if isinstance(trigger_command, tuple):
                self.__trigger_functions[trigger_command[0]](trigger_command[1])
            else:
                self.__trigger_functions[trigger_command]()

    def __load_led_mode(self) -> None:
        self.__trigger.__on_data_update()

    def __start_operation(self) -> None:
        self.__operation_lock.acquire()

    def __finish_operation(self) -> None:
        self.__operation_lock.release()

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
        if self.__state == LEDDriver.LEDState.BLINKING:
            return

        self.__start_operation()
        self.__state = LEDDriver.LEDState.BLINKING
        self.__blinker_frequency = (
            self.__default_blinker_frequency if frequency is None else frequency
        )
        self.__turn_LED_on()
        self.__finish_operation()

    def stop_blinking(self) -> None:
        if self.__state != LEDDriver.LEDState.BLINKING:
            return
        self.__start_operation()
        self.__state = LEDDriver.LEDState.OFF
        self.__finish_operation

    def turn_on(self) -> None:
        if self.__state == LEDDriver.LEDState.ON:
            return
        self.__start_operation()
        state_before = self.__state
        self.__state = LEDDriver.LEDState.ON
        if state_before == LEDDriver.LEDState.OFF:
            self.__turn_LED_on()
        self.__finish_operation()

    def turn_off(self) -> None:
        if self.__state == LEDDriver.LEDState.OFF:
            return
        self.__start_operation()
        state_before = self.__state
        self.__state = LEDDriver.LEDState.OFF
        if state_before == LEDDriver.LEDState.ON:
            self.__turn_LED_off()
        self.__finish_operation()

    def set_frequency(self, frequency) -> None:
        if frequency <= 0:
            raise ValueError("Frequency must be greater than zero")
        self.__blinker_frequency = frequency


def create_led_driver(pin: int, id, default_frequency) -> LEDDriver:
    return LEDDriver(pin=pin, id=id, default_blinker_frequency=default_frequency)
