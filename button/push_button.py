from enum import Enum
import logging
from threading import Event, Lock, Timer
import RPi.GPIO as GPIO
from threading import Thread


LOG = logging.getLogger("button")


class PushButton:
    class ButtonAction(Enum):
        HOLD = "hold"
        CLICK = "click"
        INVALID = "invalid"

    def __init__(
        self,
        pin: int,
        id,
        click_callback: callable,
        click_args: list = None,
        long_press_callback: callable = None,
        long_press_time: float = None,
        long_press_args: list = None
    ) -> None:
        LOG.debug(f"Initializing PushButton (ID: {id})")
        self.__id = id
        self.__pin = pin

        self.__click_callback = click_callback
        self.__click_args = [] if click_args is None else click_args

        self.__long_press_callback = long_press_callback
        if long_press_time is not None and long_press_time < 1:
            raise ValueError("Long press time must be equal or greater than one second")
        self.__long_press_time = long_press_time
        self.__long_press_args = [] if long_press_args is None else long_press_args

        self.__press_lock = Lock()
        self.__release_lock = Lock()
        self.__release_lock.acquire()

        self.__press_thread = Thread()
        self.__button_event = Event()

        GPIO.setup(self.__pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def enable(self) -> None:
        GPIO.remove_event_detect(self.__pin)
        GPIO.add_event_detect(self.__pin, GPIO.BOTH, callback=self.__on_button_event)

    def disable(self) -> None:
        GPIO.remove_event_detect(self.__pin)

    def __on_button_event(self, pin) -> None:
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
            Timer(0.2, self.__release_press_lock).start()

    def __release_press_lock(self) -> None:
        if GPIO.input(self.__pin) == 1:
            if self.__release_lock.locked():
                self.__release_lock.release()
            return
        self.__press_lock.release()

    def __wait_for_release(self) -> ButtonAction:
        self.__button_event.wait(
            timeout=(0.2 if self.__long_press_time is None else self.__long_press_time)
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
        LOG.info(f"PushButton (ID: {self.__id}) was released")
        self.__button_event.set()

    def __pressed(self) -> None:
        LOG.info(f"PushButton (ID: {self.__id}) was pressed")
        self.__button_event.clear()

        button_action = self.__wait_for_release()

        if button_action == PushButton.ButtonAction.INVALID:
            LOG.info(f"PushButton (ID: {self.__id}) got invalid action")
            return

        if button_action == PushButton.ButtonAction.CLICK:
            LOG.info(f"PushButton (ID: {self.__id}) was clicked")
            try:
                self.__click_callback(*self.__click_args)
            except Exception as e:
                LOG.exception(e)
            return

        if button_action == PushButton.ButtonAction.HOLD:
            LOG.info(f"PushButton (ID: {self.__id}) was long pressed")
            try:
                self.__long_press_callback(*self.__long_press_args)
            except Exception as e:
                LOG.exception(e)
