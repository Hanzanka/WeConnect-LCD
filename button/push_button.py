from enum import Enum
import logging
from threading import Event, Lock, Timer
import RPi.GPIO as GPIO
from threading import Thread


logger = logging.getLogger("button")


class PushButton:

    class ButtonAction(Enum):
        HOLD = "hold"
        CLICK = "click"
        INVALID = "invalid"

    def __init__(
        self,
        pin: int,
        button_id,
        double_click_prevention_time: float,
        click_callback: callable,
        long_press_callback=None,
        long_press_time=None,
    ) -> None:
        logger.debug(f"Initializing button with ID {button_id}")
        self.__button_id = button_id
        self.__pin = pin

        self.__click_callback = click_callback
        self.__long_press_callback = long_press_callback
        self.__long_press_time = long_press_time

        self.__double_click_prevention_time = double_click_prevention_time

        self.__press_lock = Lock()
        self.__release_lock = Lock()
        self.__release_lock.acquire()

        self.__press_thread = Thread()
        self.__button_event = Event()

        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.add_event_detect(pin, GPIO.BOTH, callback=self.on_button_event)

    def on_button_event(self, channel) -> None:
        if GPIO.input(self.__pin) == 1:
            if not self.__press_lock.acquire(blocking=False):
                return
            Timer(0.02, self.__release_lock.release).start()
            self.__press_thread = Thread(target=self.__pressed)
            self.__press_thread.start()

        if GPIO.input(self.__pin) != 1:
            if not self.__release_lock.acquire(blocking=False):
                return
            self.__released()
            Timer(self.__double_click_prevention_time, self.__release_press_lock).start()

    def __release_press_lock(self) -> None:
        if GPIO.input(self.__pin) == 1:
            if self.__release_lock.locked():
                self.__release_lock.release()
            return
        logger.debug(f"Released press lock from button ID {self.__button_id}")
        self.__press_lock.release()

    def __wait_for_release(self) -> ButtonAction:
        self.__button_event.wait(
            timeout=(
                self.__double_click_prevention_time
                if self.__long_press_time is None
                else self.__long_press_time
            )
        )

        if not self.__button_event.is_set():
            if self.__long_press_callback is None:
                if GPIO.input(self.__pin) != 1:
                    return PushButton.ButtonAction.CLICK
                if GPIO.input(self.__pin) == 1:
                    return PushButton.ButtonAction.INVALID
                
            return PushButton.ButtonAction.HOLD

        return PushButton.ButtonAction.CLICK

    def __released(self) -> None:
        logger.debug(f"Button with ID {self.__button_id} was released")
        self.__button_event.set()

    def __pressed(self) -> None:
        logger.debug(f"Button with ID {self.__button_id} was pressed")
        self.__button_event.clear()

        button_action = self.__wait_for_release()

        if button_action == PushButton.ButtonAction.INVALID:
            logger.debug(f"Button ID {self.__button_id} got invalid action")
            return

        if button_action == PushButton.ButtonAction.CLICK:
            logger.debug(f"Button ID {self.__button_id} was pressed")
            self.__click_callback()
            return

        if button_action == PushButton.ButtonAction.HOLD:
            logger.debug(f"Button ID {self.__button_id} was long pressed")
            self.__long_press_callback()
