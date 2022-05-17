from enum import Enum
import RPi.GPIO as GPIO
from threading import Timer, Event
import logging
from time import sleep
import operator


logger = logging.getLogger("led")


def load_automated_leds(config: dict, vehicle) -> None:
    logger.debug("Loading automated leddrivers")
    led_configs = config["automated leds"]
    for led_config in led_configs:
        LEDDriver(
            gpio_pin=led_config["pin"],
            led_id=led_config["id"],
            default_blinker_frequency=led_config["default frequency"],
            trigger=led_config["trigger"],
            vehicle=vehicle
        )


class LEDDriverError(Exception):
    pass


class LEDTrigger:
    def __init__(self, led_driver, trigger, vehicle) -> None:
        logger.debug(f"Initializing LEDTrigger for LEDDriver (ID: {led_driver.id})")
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
            if self.__compare_operator(self.__trigger_value, self.__data_provider.absolute_value):
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
        self, gpio_pin, led_id, default_blinker_frequency, trigger=None, vehicle=None
    ) -> None:
        logger.debug(f"Creating new LEDDriver (ID: {led_id}) (PIN: {gpio_pin})")
        
        self.__id = led_id
        
        self.__pin = gpio_pin
        GPIO.setup(self.__pin, GPIO.OUT)
        GPIO.output(self.__pin, GPIO.LOW)
        self.__state = LEDDriver.LEDState.OFF

        self.__default_blinker_frequency = default_blinker_frequency
        self.__blinker_frequency = default_blinker_frequency
        self.__blinker_event = Event()
        self.__blinker_thread_timer = None

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
        logger.debug(f"LEDDriver (ID: {self.__id}) got update from LEDTrigger")
        if trigger_command is not None:
            try:
                if isinstance(trigger_command, tuple):
                    self.__trigger_functions[trigger_command[0]](trigger_command[1])
                else:
                    self.__trigger_functions[trigger_command]()
            except LEDDriverError as e:
                logger.exception(e)

    def __load_led_mode(self) -> None:
        self.__trigger.on_data_update()

    def __start_operation(self) -> None:
        self.__operation_event.wait()
        self.__operation_event.clear()
    
    def __finish_operation(self) -> None:
        self.__operation_event.set()

    def __turn_LED_off(self, looping=True) -> None:
        GPIO.output(self.__pin, GPIO.LOW)
        if looping and not self.__blinker_event.is_set():
            self.__blinker_thread_timer = Timer(
                1 / self.__blinker_frequency / 2, self.__turn_LED_on
            )
            self.__blinker_thread_timer.start()

    def __turn_LED_on(self, looping=True) -> None:
        GPIO.output(self.__pin, GPIO.HIGH)
        if looping:
            self.__blinker_thread_timer = Timer(
                1 / self.__blinker_frequency / 2, self.__turn_LED_off
            )
            self.__blinker_thread_timer.start()

    def blink(self, frequency=None) -> None:
        logger.info(f"Starting blinker on LEDDriver (ID: {self.__id})")
        if self.__state == LEDDriver.LEDState.BLINKING:
            logger.debug(f"Blinker on LEDDriver (ID: {self.__id}) is already on")
            return
        
        self.__start_operation()
        override_needed = self.__state == LEDDriver.LEDState.ON
        if override_needed:
            self.turn_off(override_mode=True)

        self.__blinker_event.clear()
        self.__blinker_frequency = (
            self.__default_blinker_frequency if frequency is None else frequency
        )
        self.__state = LEDDriver.LEDState.BLINKING
        self.__turn_LED_on()
        self.__finish_operation()

    def stop_blinking(self, called_from_turn_off=False) -> None:
        logger.info(f"Shuttingdown blinker on LEDDriver (ID: {self.__id})")
        if self.__blinker_thread_timer is None:
            logger.debug(f"Blinker on LEDDriver (ID: {self.__id}) is already off")
            return
        if (
            self.__state != LEDDriver.LEDState.BLINKING
            and not self.__blinker_thread_timer.is_alive()
        ):
            logger.debug(f"Blinker on LEDDriver (ID: {self.__id}) is already off")
            return
        if not called_from_turn_off:
            self.__start_operation()
        self.__state = LEDDriver.LEDState.OFF
        self.__blinker_event.set()
        sleep(1 / self.__blinker_frequency)
        if self.__blinker_thread_timer.is_alive():
            logger.debug(
                f"Thread timer on LEDDriver (ID: {self.__id}) is still on, shutting it down manually"
            )
            self.__blinker_thread_timer.cancel()
            if GPIO.input(self.__pin) == 1:
                GPIO.output(self.__pin, GPIO.LOW)
        if not called_from_turn_off:
            self.__finish_operation()

    def turn_on(self) -> None:
        logger.info(f"Turning on LEDDriver (ID: {self.__id})")
        if self.__state == LEDDriver.LEDState.ON:
            logger.debug(f"LEDDriver (ID: {self.__id}) is already on")
            return
        
        self.__start_operation()
        override_needed = self.__state == LEDDriver.LEDState.BLINKING
        if override_needed:
            logger.debug(
                f"Blinker on LEDDriver (ID: {self.__id}) is enabled. Shutting it down"
            )
            self.stop_blinking()
        self.__state = LEDDriver.LEDState.ON
        self.__turn_LED_on(looping=False)
        self.__finish_operation()

    def turn_off(self) -> None:
        logger.info(f"Turning off LEDDriver (ID: {self.__id})")
        if self.__state == LEDDriver.LEDState.OFF:
            logger.debug(f"LEDDriver (ID: {self.__id}) is already off")
            return
        self.__start_operation()
        if self.__state == LEDDriver.LEDState.BLINKING:
            logger.debug(
                f"Blinker on LEDDriver (ID: {self.__id}) is enabled, shutting it down"
            )
            self.stop_blinking(called_from_turn_off=True)
        self.__state = LEDDriver.LEDState.OFF
        self.__turn_LED_off(looping=False)
        self.__finish_operation()

    def set_frequency(self, frequency) -> None:
        logger.info(f"Setting default frequency of LEDDRiver (ID: {self.__id}) to {frequency}Hz")
        if frequency <= 0:
            logger.error("Frequency must be greater than zero")
            raise ValueError("Frequency must be greater than zero")
        self.__blinker_frequency = frequency
        

def create_led_driver(led_pin: int, led_id, default_frequency) -> LEDDriver:
    logger.info(f"Creating new LEDDriver (ID: {led_id})")
    return LEDDriver(gpio_pin=led_pin, led_id=led_id, default_blinker_frequency=default_frequency)
