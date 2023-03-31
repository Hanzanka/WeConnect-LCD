import logging
from RPLCD.i2c import CharLCD
from threading import Timer, Lock
import textwrap
from queue import Queue


LOG = logging.getLogger("lcd_controller")


class LCDController:
    def __init__(self, lcd_scene_controller) -> None:
        self.__lcd = CharLCD(
            i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4
        )

        self.__backlight_timer = Timer(30, self.backlight_off)

        self.__load_custom_characters()

        self.__print_lock = Lock()

        self.__message_timer = None
        self.__message_on_screen = False
        self.__message_queue = Queue()

        self.__lcd_scene_controller = lcd_scene_controller
        self.__interactions_enabled = True

        self.display_message("WeConnect-LCD Is Starting")

    def __content_into_string(self, content) -> str:
        content_string = "".join(item + (20 - len(item)) * " " for item in content)
        if len(content) == 4:
            return content_string
        content_string += "".join(" " * 20 for _ in range(4 - len(content)))
        return content_string

    def update_lcd(self, content: list) -> None:
        """
        Used to update content of the LCD screen

        Args:
            content (list): List containing contents for each line on the LCD screen.
                Max lenght for the list is same as the line count on the LCD screen.
                Max lenght for the items on the list is same as the character count on each line of the LCD screen.

        Raises:
            ValueError: If given content exceeds the LCD screen dimensions.
        """

        if len(content) > 4:
            error_string = (
                "Given content list is too long. "
                "Max lenght is 4. "
                f"Given content list lenght was {len(content)}. Items on the content list: {content}"
            )
            LOG.error(error_string)
            raise ValueError(error_string)

        if len(max(content, key=len)) > 20:
            error_string = (
                "One or more items on the content list were too long. "
                "Max lenght is 20. "
                f"First item which was too long was {next(s for s in content if len(s) > 20)}. "
                f"Items on the content list: {content}"
            )
            LOG.error(error_string)
            raise ValueError(error_string)

        if not self.__message_on_screen:
            with self.__print_lock:
                try:
                    self.__lcd.cursor_pos = (0, 0)
                    self.__lcd.write_string(self.__content_into_string(content))
                except Exception as e:
                    LOG.exception(e)

    def backlight_on(self) -> None:
        """
        Turns on the backlight of the LCD screen and restarts the 30 second timer before backlight turns off.
        """

        if self.__backlight_timer.is_alive():
            self.__backlight_timer.cancel()
        self.__lcd.backlight_enabled = True
        self.__start_darkmode_timer()

    def backlight_off(self) -> None:
        """
        Turns off the backlight of the LCD screen.
        """

        self.__lcd.backlight_enabled = False

    def __start_darkmode_timer(self, time=None) -> None:
        if self.__backlight_timer.is_alive():
            self.__backlight_timer.cancel()
        self.__backlight_timer = Timer(
            (30 if time is None else time), self.backlight_off
        )
        self.__backlight_timer.start()

    def __load_custom_characters(self) -> None:
        battery_empty = [0x0E, 0x1B, 0x11, 0x11, 0x11, 0x11, 0x11, 0x1F]
        battery_20 = [0x0E, 0x1B, 0x11, 0x11, 0x11, 0x11, 0x1F, 0x1F]
        battery_50 = [0x0E, 0x1B, 0x11, 0x11, 0x1F, 0x1F, 0x1F, 0x1F]
        battery_80 = [0x0E, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F, 0x1F]
        charging = [0x0A, 0x0A, 0x1F, 0x1F, 0x0E, 0x04, 0x04, 0x04]
        plug_connected = [0x04, 0x04, 0x04, 0x0E, 0x1F, 0x1F, 0x0A, 0x0A]
        charge_complete = [0x00, 0x01, 0x03, 0x16, 0x1C, 0x08, 0x00, 0x00]
        climate = [0x04, 0x0A, 0x0A, 0x0E, 0x0E, 0x1F, 0x1F, 0x0E]
        self.__lcd.create_char(0, battery_empty)
        self.__lcd.create_char(1, battery_20)
        self.__lcd.create_char(2, battery_50)
        self.__lcd.create_char(3, battery_80)
        self.__lcd.create_char(4, charging)
        self.__lcd.create_char(5, plug_connected)
        self.__lcd.create_char(6, charge_complete)
        self.__lcd.create_char(7, climate)

    def clear_message(self) -> None:
        """
        Clears the current displayed message off the LCD screen and displays the next queued message if there is one.
        """

        self.__message_on_screen = False
        if self.__message_queue.empty():
            self.__interactions_enabled = True
            self.__lcd_scene_controller.restore_last_view()
        else:
            queued_msg = self.__message_queue.get()
            self.display_message(queued_msg[0], queued_msg[1])

    def display_message(self, message: str, time_on_screen=None) -> None:
        """
        Displays message on the LCD screen.

        Args:
            message (str): Message that will be displayed on the LCD screen.
                Message should fit on block with 18x2 characters or some contents will get cut off.
            time_on_screen (_type_, optional): Time when the message will be cleared off the LCD screen.
                If time is not given the message will clear off automatically next time when the LCD screen is updated.
                Defaults to None.
        """

        if not self.__message_on_screen:
            self.backlight_on()
            with self.__print_lock:
                if time_on_screen is not None:
                    self.__interactions_enabled = False
                    self.__message_on_screen = True

                splitted = textwrap.wrap(message, 19)
                if len(splitted) == 1:
                    splitted.append(" " * 18)
                for i in range(0, len(splitted)):
                    splitted[i] = splitted[i].center(18)

                self.__lcd.clear()

                try:
                    for i in range(0, 2):
                        self.__lcd.cursor_pos = (1 + i, 1)
                        self.__lcd.write_string(splitted[i])
                except Exception as e:
                    LOG.exception(e)

            if time_on_screen is not None:
                self.__message_timer = Timer(
                    interval=time_on_screen, function=self.clear_message
                )
                self.__message_timer.start()

        else:
            if time_on_screen is not None:
                self.__message_queue.put((message, time_on_screen))

    @property
    def can_interact(self) -> bool:
        self.backlight_on()
        return self.__interactions_enabled
