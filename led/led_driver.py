from enum import Enum
import RPi.GPIO as GPIO
from threading import Timer, Event
import logging
import operator
from weconnect_id.weconnect_vehicle import WeConnectVehicle


LOG = logging.getLogger("led")


def load_automated_leds(config: dict, vehicle: WeConnectVehicle) -> None:
    LOG.debug("Loading automated LEDDrivers")
    led_configs = config["automated leds"]
    for led_config in led_configs:
        LEDDriver(
            pin=led_config["pin"],
            id=led_config["id"],
            default_blinker_frequency=led_config["default frequency"],
            trigger=led_config["trigger"],
            vehicle=vehicle,
        )


class LEDDriverError(Exception):
    pass


class LEDTrigger:
    def __init__(self, led_driver, trigger, vehicle: WeConnectVehicle) -> None:
        LOG.debug(f"Initializing LEDTrigger for LEDDriver (ID: {led_driver.id})")
        self.driver = led_driver

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
            self.__data_provider = vehicle.get_data_property(trigger["data id"])
            self.__data_provider.add_callback_function(self.on_data_update)
        except Exception as e:
            raise LEDDriverError(e, True)

    def on_data_update(self) -> None:
        self.driver.on_trigger_update(self.get_trigger_value())

    def get_trigger_value(self):
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
        self, pin, id, default_blinker_frequency, trigger=None, vehicle=None
    ) -> None:
        LOG.debug(f"Creating new LEDDriver (ID: {id}) (PIN: {pin})")

        self.__id = id

        self.__pin = pin
        GPIO.setup(self.__pin, GPIO.OUT)
        GPIO.output(self.__pin, GPIO.LOW)
        self.__state = LEDDriver.LEDState.OFF

        self.__default_blinker_frequency = default_blinker_frequency
        self.__blinker_frequency = default_blinker_frequency
        self.__blinker_event = Event()
        self.__blinker_event.set()

        self.__operation_event = Event()
        self.__operation_event.set()

        if trigger is not None and vehicle is not None:
            self.__trigger_functions = {
                "on": self.turn_on,
                "off": self.turn_off,
                "blink": self.blink,
            }
            self.__trigger = LEDTrigger(self, trigger, vehicle)
            self.__load_led_mode()

    @property
    def id(self):
        return self.__id

    @property
    def state(self) -> Enum:
        return self.__state

    def on_trigger_update(self, trigger_command) -> None:
        LOG.debug(f"LEDDriver (ID: {self.__id}) got update from LEDTrigger")
        if trigger_command is not None:
            try:
                if isinstance(trigger_command, tuple):
                    self.__trigger_functions[trigger_command[0]](trigger_command[1])
                else:
                    self.__trigger_functions[trigger_command]()
            except LEDDriverError as e:
                LOG.exception(e)

    def __load_led_mode(self) -> None:
        self.__trigger.on_data_update()

    def __start_operation(self) -> None:
        self.__operation_event.wait()
        self.__operation_event.clear()

    def __finish_operation(self) -> None:
        self.__operation_event.set()

    def __turn_LED_off(self, looping=True) -> None:
        if self.__state != LEDDriver.LEDState.ON:
            GPIO.output(self.__pin, GPIO.LOW)
        if looping and not self.__blinker_event.is_set():
            Timer(1 / self.__blinker_frequency / 2, self.__turn_LED_on).start()

    def __turn_LED_on(self, looping=True) -> None:
        if self.__state != LEDDriver.LEDState.OFF:
            GPIO.output(self.__pin, GPIO.HIGH)
        if looping and not self.__blinker_event.is_set():
            Timer(1 / self.__blinker_frequency / 2, self.__turn_LED_off).start()

    def blink(self, frequency=None) -> None:
        LOG.info(f"Starting blinker on LEDDriver (ID: {self.__id})")
        if self.__state == LEDDriver.LEDState.BLINKING:
            LOG.debug(f"Blinker on LEDDriver (ID: {self.__id}) is already on")
            return

        self.__start_operation()
        self.__state = LEDDriver.LEDState.BLINKING
        self.__blinker_frequency = (
            self.__default_blinker_frequency if frequency is None else frequency
        )
        self.__blinker_event.clear()
        self.__turn_LED_on()
        self.__finish_operation()

    def stop_blinking(self) -> None:
        LOG.info(f"Shutting down blinker on LEDDriver (ID: {self.__id})")
        if self.__blinker_event.is_set():
            LOG.debug(f"Blinker on LEDDriver (ID: {self.__id}) is already off")
            return

        self.__start_operation()
        self.__state = LEDDriver.LEDState.OFF
        self.__blinker_event.set()
        self.__turn_LED_off()
        self.__finish_operation()

    def turn_on(self) -> None:
        LOG.info(f"Turning on LEDDriver (ID: {self.__id})")
        if self.__state == LEDDriver.LEDState.ON:
            LOG.debug(f"LEDDriver (ID: {self.__id}) is already on")
            return

        self.__start_operation()
        if self.__state == LEDDriver.LEDState.BLINKING:
            LOG.debug(
                f"Blinker on LEDDriver (ID: {self.__id}) is enabled. Shutting it down"
            )
            self.__blinker_event.set()
        self.__state = LEDDriver.LEDState.ON
        self.__turn_LED_on(looping=False)
        self.__finish_operation()

    def turn_off(self) -> None:
        LOG.info(f"Turning off LEDDriver (ID: {self.__id})")
        if self.__state == LEDDriver.LEDState.OFF:
            LOG.debug(f"LEDDriver (ID: {self.__id}) is already off")
            return

        self.__start_operation()
        if self.__state == LEDDriver.LEDState.BLINKING:
            LOG.debug(
                f"Blinker on LEDDriver (ID: {self.__id}) is enabled, shutting it down"
            )
            self.__blinker_event.set()
        self.__state = LEDDriver.LEDState.OFF
        self.__turn_LED_off(looping=False)
        self.__finish_operation()

    def set_frequency(self, frequency) -> None:
        LOG.info(
            f"Setting default frequency of LEDDRiver (ID: {self.__id}) to {frequency}Hz"
        )
        if frequency <= 0:
            LOG.error("Frequency must be greater than zero")
            raise ValueError("Frequency must be greater than zero")
        self.__blinker_frequency = frequency


def create_led_driver(pin: int, id, default_frequency) -> LEDDriver:
    LOG.info(f"Creating new LEDDriver (ID: {id})")
    return LEDDriver(pin=pin, id=id, default_blinker_frequency=default_frequency)
