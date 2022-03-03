from enum import Enum
import RPi.GPIO as GPIO
from config_loader import ConfigLoader, ConfigLoaderError
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

        self.parent = led_driver

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
        trigger_value = self.get_trigger_value()
        if isinstance(trigger_value, tuple):
            self.parent.on_trigger_update(trigger_value[0], trigger_value[1])
        else:
            self.parent.on_trigger_update(trigger_value)

    def get_trigger_value(self):

        if self.__compare:
            data_value = float(self.__data_provider.value)
            if self.__compare_operator(float(self.__trigger_value), data_value):
                return self.__trigger_mode
            else:
                return self.__default_mode

        data_value = self.__data_provider.value
        if data_value not in self.__trigger_values:
            return None

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
        self, gpio_pin, LED_id, default_blinker_frequency, trigger, vehicle
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

    def __turn_LED_off(self, looping=True) -> None:
        try:
            GPIO.output(self.__pin, GPIO.LOW)
        except Exception:
            try:
                GPIO.setup(self.__pin, GPIO.OUT)
            except Exception as e:
                raise LEDDriverError(e, fatal=True)
        if looping and not self.__blinker_event.is_set():
            self.__blinker_thread_timer = Timer(
                1 / self.__blinker_frequency / 2, self.__turn_LED_on
            )
            self.__blinker_thread_timer.start()

    def __turn_LED_on(self, looping=True) -> None:
        try:
            GPIO.output(self.__pin, GPIO.HIGH)
        except Exception:
            try:
                GPIO.setup(self.__pin, GPIO.OUT)
            except Exception as e:
                raise LEDDriverError(e, fatal=True)
        if looping:
            self.__blinker_thread_timer = Timer(
                1 / self.__blinker_frequency / 2, self.__turn_LED_off
            )
            self.__blinker_thread_timer.start()

    def blink(self, frequency=None) -> None:
        if self.__status == LEDDriver.LEDState.BLINKING:
            logging.info(f"Blinker on led {self.id} is already on, returning")
            return
        
        logging.info(f"Starting led blinker on led {self.id}")
        override_needed = self.__status == LEDDriver.LEDState.ON
        if override_needed:
            self.turn_off(override_mode=True)

        self.__blinker_event.clear()
        self.__blinker_frequency = (
            self.__default_blinker_frequency if frequency is None else frequency
        )
        self.__status = LEDDriver.LEDState.BLINKING
        self.__turn_LED_on()

    def stop_blinking(self) -> None:
        if (
            self.__status != LEDDriver.LEDState.BLINKING
            and not self.__blinker_thread_timer.is_alive()
        ):
            logging.info(f"Blinker on led {self.id} is already off")
            return
        logging.info(f"Stopping blinker on led {self.id}")
        self.__status = LEDDriver.LEDState.OFF
        self.__blinker_event.set()
        sleep(1 / self.__blinker_frequency)
        if self.__blinker_thread_timer.is_alive():
            logging.info(
                f"Thread timer on led {self.id} is still on, shutting it down manually"
            )
            self.__blinker_thread_timer.cancel()
            if GPIO.input(self.__pin) == 1:
                GPIO.output(self.__pin, GPIO.LOW)
        logging.info(f"Blinker on led {self.id} is successfully shut down")

    def turn_on(self) -> None:
        logging.info(f"Turning on led {self.id}")
        override_needed = self.__status == LEDDriver.LEDState.BLINKING
        if override_needed:
            logging.info(
                f"Blinker on led {self.id} is enabled and override mode is enabled. Shutting it down. "
            )
            self.stop_blinking()
        self.__status = LEDDriver.LEDState.ON
        self.__turn_LED_on(looping=False)

    def turn_off(self) -> None:
        if self.__state == LEDDriver.LEDState.OFF:
            logging.info(f"LED on pin {self.__pin} is already off")
            return
        if self.__status == LEDDriver.LEDState.BLINKING:
            logging.info(
                f"Blinker on led {self.id} is enabled, shutting it down"
            )
            self.stop_blinking()
        logging.info(f"Turning off led {self.id}")
        self.__status = LEDDriver.LEDState.OFF
        self.__turn_LED_off(looping=False)

    def set_frequency(self, frequency) -> None:
        if frequency <= 0:
            raise ValueError("Frequency must be greater than zero")
        self.__blinker_frequency = frequency


class IndicatorLEDController:
    def __init__(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self.__indicator_LEDs = {}
        self.setup_leddrivers(independent_leds_setup=True)

    def setup_leddrivers(self, independent_leds_setup=False, vehicle=None) -> None:
        logging.info(
            f"Initializing {'independent leds' if independent_leds_setup else 'dependent leds'}"
        )

        self.__indicator_LEDs = {
            **self.__indicator_LEDs,
            **self.__import_leddrivers(independent_leds_setup, vehicle),
        }

    def __import_leddrivers(self, independent_leds_setup=False, vehicle=None) -> dict:
        logging.info(
            f"Importing LED configs for {'independent leds' if independent_leds_setup else 'dependent leds'}"
        )
        LEDs = {}
        led_configs = ConfigLoader.load_config()["LED pins"]

        for LED_id, LED_config in led_configs.items():
            if independent_leds_setup:
                if "trigger" in LED_config:
                    continue
            else:
                if "trigger" not in LED_config:
                    continue
            LEDs[LED_id] = self.__initialize_leddriver(LED_config, vehicle)

        return LEDs

    def __initialize_leddriver(self, LED_config, vehicle) -> LEDDriver:

        try:
            LED_id = LED_config["id"]
            LED_pin = LED_config["pin"]
            LED_default_frequency = LED_config["default frequency"]
        except KeyError:
            raise ConfigLoaderError("No led id found", fatal=True)

        logging.info(f"Initializing led: {LED_id}")

        trigger = None if "trigger" not in LED_config else LED_config["trigger"]
        
        driver = LEDDriver(
            gpio_pin=LED_pin,
            LED_id=LED_id,
            default_blinker_frequency=LED_default_frequency,
            trigger=trigger,
            vehicle=vehicle,
        )

        return driver

    def turn_LED_on(self, LED_id) -> None:
        if LED_id not in self.__indicator_LEDs.keys():
            raise ValueError("Given id was not found from LEDs dict keys")
        try:
            self.__indicator_LEDs[LED_id].turn_on()
        except LEDDriverError as e:
            logging.error(f"Couldn't turn on led {LED_id}. Original error: {e}")

    def turn_LED_off(self, LED_id) -> None:
        if LED_id not in self.__indicator_LEDs.keys():
            raise ValueError("Given id was not found from LEDs dict keys")
        try:
            self.__indicator_LEDs[LED_id].turn_off()
        except LEDDriverError as e:
            logging.error(f"Couldn't turn off led {LED_id}. Original error: {e}")

    def blink(self, LED_id, frequency=None) -> None:
        if LED_id not in self.__indicator_LEDs.keys():
            raise ValueError("Given id was not found from LEDs dict keys")
        try:
            self.__indicator_LEDs[LED_id].blink(frequency)
        except LEDDriverError as e:
            logging.error(f"Couldn't turn on blinker on led {LED_id}. Original error: {e}")

    def stop_blinking(self, LED_id) -> None:
        if LED_id not in self.__indicator_LEDs.keys():
            raise ValueError("Given id was not found from LEDs dict keys")
        self.__indicator_LEDs[LED_id].stop_blinking()

    def set_frequency(self, LED_id, frequency) -> None:
        if frequency <= 0:
            raise ValueError("Frequency must be greater than zero")
        self.__indicator_LEDs[LED_id].set_frequency(frequency)
