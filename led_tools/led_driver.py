from enum import Enum
import RPi.GPIO as GPIO
from threading import Timer, Event
import logging
from time import sleep
from general_exception import GeneralException
import operator


class LEDDriverError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


class LEDTrigger:
    def __init__(self, led_driver, trigger, vehicle) -> None:

        self.driver = led_driver

        try:
            self.__compare = trigger["compare"] == "True"
            if self.__compare:
                self.__trigger_value = trigger["trigger values"]["value"]
                self.__trigger_mode = trigger["trigger values"]["target"]
                self.__default_mode = trigger["default mode"]
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
            return

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
        self, gpio_pin, LED_id, default_blinker_frequency, trigger=None, vehicle=None
    ) -> None:

        self.id = LED_id
        
        self.__pin = gpio_pin
        GPIO.setup(self.__pin, GPIO.OUT)
        GPIO.output(self.__pin, GPIO.LOW)
        self.__status = LEDDriver.LEDState.OFF

        self.__default_blinker_frequency = default_blinker_frequency
        self.__blinker_frequency = default_blinker_frequency
        self.__blinker_event = Event()
        self.__blinker_thread_timer = None

        self.__operation_event = Event()

        if trigger is not None and vehicle is not None:
            self.__trigger_functions = {
                "on": self.turn_on,
                "off": self.turn_off,
                "blink": self.blink,
            }
            self.__trigger = LEDTrigger(self, trigger, vehicle)
            self.__load_led_mode()

    def on_trigger_update(self, trigger_command) -> None:
        if trigger_command is not None:
            try:
                if isinstance(trigger_command, tuple):
                    self.__trigger_functions[trigger_command[0]](trigger_command[1])
                else:
                    self.__trigger_functions[trigger_command]()
            except LEDDriverError as e:
                logging.error(e)

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
        if self.__status == LEDDriver.LEDState.BLINKING:
            logging.info(f"Blinker on led '{self.id}' is already on")
            return
        
        logging.info(f"Starting blinker on led '{self.id}'")
        self.__start_operation()
        override_needed = self.__status == LEDDriver.LEDState.ON
        if override_needed:
            self.turn_off(override_mode=True)

        self.__blinker_event.clear()
        self.__blinker_frequency = (
            self.__default_blinker_frequency if frequency is None else frequency
        )
        self.__status = LEDDriver.LEDState.BLINKING
        self.__turn_LED_on()
        self.__finish_operation()

    def stop_blinking(self) -> None:
        if self.__blinker_thread_timer is None:
            logging.info(f"Blinker on led '{self.id}' is already off")
            return
        if (
            self.__status != LEDDriver.LEDState.BLINKING
            and not self.__blinker_thread_timer.is_alive()
        ):
            logging.info(f"Blinker on led '{self.id}' is already off")
            return
        logging.info(f"Stopping blinker on led '{self.id}'")
        self.__start_operation()
        self.__status = LEDDriver.LEDState.OFF
        self.__blinker_event.set()
        sleep(1 / self.__blinker_frequency)
        if self.__blinker_thread_timer.is_alive():
            logging.info(
                f"Thread timer on led '{self.id}' is still on, shutting it down manually"
            )
            self.__blinker_thread_timer.cancel()
            if GPIO.input(self.__pin) == 1:
                GPIO.output(self.__pin, GPIO.LOW)
        logging.info(f"Blinker on led '{self.id}' is successfully shut down")
        self.__finish_operation()

    def turn_on(self) -> None:
        if self.__status == LEDDriver.LEDState.ON:
            logging.info(f"Led '{self.id}' is already on")
            return
        
        logging.info(f"Turning on led '{self.id}'")
        self.__start_operation()
        override_needed = self.__status == LEDDriver.LEDState.BLINKING
        if override_needed:
            logging.info(
                f"Blinker on led '{self.id}' is enabled. Shutting it down"
            )
            self.stop_blinking()
        self.__status = LEDDriver.LEDState.ON
        self.__turn_LED_on(looping=False)
        self.__finish_operation()

    def turn_off(self) -> None:
        if self.__status == LEDDriver.LEDState.OFF:
            logging.info(f"LED on pin '{self.__pin}' is already off")
            return
        logging.info(f"Turning off led '{self.id}'")
        self.__start_operation()
        if self.__status == LEDDriver.LEDState.BLINKING:
            logging.info(
                f"Blinker on led '{self.id}' is enabled, shutting it down"
            )
            self.stop_blinking()
        self.__status = LEDDriver.LEDState.OFF
        self.__turn_LED_off(looping=False)
        self.__finish_operation()

    def set_frequency(self, frequency) -> None:
        if frequency <= 0:
            raise ValueError("Frequency must be greater than zero")
        self.__blinker_frequency = frequency
