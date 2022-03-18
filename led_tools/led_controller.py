import RPi.GPIO as GPIO
from config_loader import load_config, ConfigLoaderError
import logging
from led_driver import LEDDriver, LEDDriverError


class IndicatorLEDController:
    def __init__(self) -> None:
        self.__setup_gpio()
        self.__indicator_LEDs = {}
        config = load_config()
        self.__used_pins = config["used pins"]
        self.__used_ids = list(config["LED pins"].keys())

    def __setup_gpio(self) -> None:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

    def setup_vehicle_dependent_leddrivers(self, vehicle) -> None:
        """
        Used to setup leddrivers from config.json-file

        Args:
            vehicle (VolkswagenIdVehicle): Class used to access VehicleDataProperty-objects needed in leddriver setup
        """
        logging.info("Initializing vehicle dependent leds")

        led_configs = load_config()["LED pins"]

        for LED_id, LED_config in led_configs.items():
            self.__indicator_LEDs[LED_id] = self.__initialize_leddriver_from_config(
                LED_config, vehicle
            )

    def __initialize_leddriver_from_config(self, LED_config, vehicle) -> LEDDriver:

        try:
            LED_id = LED_config["id"]
            LED_pin = LED_config["pin"]
            LED_default_frequency = LED_config["default frequency"]
            trigger = LED_config["trigger"]
        except KeyError:
            raise ConfigLoaderError("Failed to load config", fatal=True)

        logging.info(f"Initializing led with id '{LED_id}'")

        driver = LEDDriver(
            gpio_pin=LED_pin,
            LED_id=LED_id,
            default_blinker_frequency=LED_default_frequency,
            trigger=trigger,
            vehicle=vehicle,
        )

        return driver

    def create_independent_leddriver(
        self, pin: int, led_id, default_frequency
    ) -> LEDDriver:
        '''
        Used to create leddriver without triggers

        Args:
            pin (int): Pin where the led is connected
            led_id (Any): Id of the led which is used to access the leddriver from IndicatorLEDController
            default_frequency (Int / float): Default frequency of the led blinker

        Raises:
            ValueError: Raised if trying to use pin which is already in use
            ValueError: Raised if trying to use id which is already in use
            ValueError: Raised if given frequency is not greater than zero

        Returns:
            LEDDriver: Driver which can be used to control the led created
        '''
        if pin in self.__used_pins:
            raise ValueError(
                f"Pin '{pin}' is already in use, try using another. Currently used pins are: {self.__used_pins}"
            )
        if led_id in self.__used_ids:
            raise ValueError(
                f"LED id '{led_id}' is already in use, try using another. Currently used ids are: {self.__used_ids}"
            )
        if default_frequency <= 0:
            raise ValueError(
                f"Given frequency of {default_frequency}Hz is below zero. Frequency must be greater than zero"
            )

        self.__used_ids.append(led_id)
        self.__used_pins.append(pin)

        driver = LEDDriver(
            gpio_pin=pin, LED_id=led_id, default_blinker_frequency=default_frequency
        )

        self.__indicator_LEDs[led_id] = driver
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
            logging.error(
                f"Couldn't turn on blinker on led {LED_id}. Original error: {e}"
            )

    def stop_blinking(self, LED_id) -> None:
        if LED_id not in self.__indicator_LEDs.keys():
            raise ValueError("Given id was not found from LEDs dict keys")
        self.__indicator_LEDs[LED_id].stop_blinking()

    def set_frequency(self, LED_id, frequency) -> None:
        if frequency <= 0:
            raise ValueError("Frequency must be greater than zero")
        self.__indicator_LEDs[LED_id].set_frequency(frequency)
