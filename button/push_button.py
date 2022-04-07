import logging
from threading import Event
import RPi.GPIO as GPIO
from datetime import datetime, timedelta, timezone
from threading import Thread


class PushButton:
    def __init__(
        self,
        pin: int,
        id,
        double_click_prevention_time: int,
        click_callback: callable,
        hold_callback=None,
        long_press_time=None,
    ) -> None:
        self.__id = id

        self.__pin = pin
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(pin, GPIO.BOTH, callback=self.on_button_event)

        self.__click_callback = click_callback
        self.__long_press_callback = hold_callback
        self.__long_press_time = long_press_time

        self.__double_click_prevention = double_click_prevention_time
        self.__timezone = timezone(timedelta(hours=+2), "HEL")
        self.__last_press = datetime.now(self.__timezone)
        self.__last_release = datetime.now(self.__timezone)

        self.__press_thread = Thread()
        self.__button_event = Event()

    def on_button_event(self, channel) -> None:
        if GPIO.input(self.__pin):
            if (
                datetime.now(self.__timezone) - self.__last_press
            ).total_seconds() >= self.__double_click_prevention:
                self.__last_press = datetime.now(self.__timezone)
                if not self.__press_thread.isAlive():
                    self.__press_thread = Thread(target=self.__pressed)
                    self.__press_thread.start()

        else:
            if (
                datetime.now(self.__timezone) - self.__last_release
            ).total_seconds() >= self.__double_click_prevention:
                self.__last_release = datetime.now(self.__timezone)
                self.__released()

    def __wait_for_release(self) -> float:
        self.__button_event.wait(timeout=self.__long_press_time)
        if not self.__button_event.is_set():
            self.__button_event.clear()
            return self.__long_press_time
        self.__button_event.clear()
        return (self.__last_release - self.__last_press).total_seconds()

    def __released(self) -> None:
        logging.info(f"Button '{self.__id}' was released")
        self.__button_event.set()

    def __pressed(self) -> None:
        print(self.__last_press)
        logging.info(f"Button '{self.__id}' was pressed")

        self.__button_event.clear()
        time_diff = self.__wait_for_release()

        if self.__long_press_callback is None:
            self.__click_callback()
            return

        if time_diff < self.__long_press_time:
            self.__click_callback()
        else:
            self.__long_press_callback()
