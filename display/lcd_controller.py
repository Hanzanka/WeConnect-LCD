import logging
import traceback
from RPLCD.i2c import CharLCD
from threading import Event, Timer
import textwrap
from queue import Queue


logger = logging.getLogger("lcd_controller")


class LCDController:

    """
    Used to control and print data on lcd display
    """

    def __init__(self, lcd_scene_controller) -> None:
        logger.debug("Initializing LCDController")
        self.__lcd = CharLCD(
            i2c_expander="PCF8574", address=0x27, port=1, charmap="A00", cols=20, rows=4
        )

        self.__darkmode_timer = Timer(30, self.backlight_off)

        self.__load_custom_characters()

        self.__print_event = Event()
        self.__print_event.set()

        self.__message_timer = None
        self.__message_on_screen = False
        self.__message_queue = Queue()

        self.__lcd_scene_controller = lcd_scene_controller
        self.__interactions_enabled = True

        self.display_message("WeConnect-LCD Is Starting")

    def __ready(self) -> None:
        self.__print_event.set()

    def __wait(self) -> None:
        self.__print_event.wait()
        self.__print_event.clear()

    def __content_into_string(self, content) -> str:
        if len(max(content, key=len)) > 20:
            raise ValueError("One of the items given is too long")
        content_string = "".join(item + (20 - len(item)) * " " for item in content)
        if len(content) == 4:
            return content_string
        content_string += "".join(" " * 20 for _ in range(4 - len(content)))
        return content_string

    def update_lcd(self, content: list) -> None:
        
        if len(content) > 4:
            self.display_message("Content list is too long!")
            logger.error(f"Given content list is too long (Content: {content})")
            return

        if not self.__message_on_screen:
            self.__wait()
            try:
                self.__lcd.cursor_pos = (0, 0)
                self.__lcd.write_string(self.__content_into_string(content))
            except Exception as e:
                logger.exception(e)
            self.__ready()

    def backlight_on(self) -> None:
        if self.__darkmode_timer.is_alive():
            self.__darkmode_timer.cancel()
        self.__lcd.backlight_enabled = True
        self.__start_darkmode_timer()

    def backlight_off(self) -> None:
        self.__lcd.backlight_enabled = False
        
    def __start_darkmode_timer(self, time=None) -> None:
        if self.__darkmode_timer.is_alive():
            self.__darkmode_timer.cancel()
        self.__darkmode_timer = Timer(
            (30 if time is None else time), self.backlight_off
        )
        self.__darkmode_timer.start()

    def __load_custom_characters(self) -> None:
        logger.debug("Creating custom lcd characters")
        upper_left_corner = [0x00, 0x00, 0x00, 0x00, 0x0F, 0x08, 0x08, 0x08]
        bottom_left_corner = [0x08, 0x08, 0x08, 0x0F, 0x00, 0x00, 0x00, 0x00]
        upper_right_corner = [0x00, 0x00, 0x00, 0x00, 0x1E, 0x02, 0x02, 0x02]
        bottom_right_corner = [0x02, 0x02, 0x02, 0x1E, 0x00, 0x00, 0x00, 0x00]
        top = [0x00, 0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00]
        bottom = [0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00, 0x00]
        right_side = [0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02, 0x02]
        left_side = [0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08]
        self.__lcd.create_char(0, upper_left_corner)
        self.__lcd.create_char(1, top)
        self.__lcd.create_char(2, upper_right_corner)
        self.__lcd.create_char(3, right_side)
        self.__lcd.create_char(4, bottom_right_corner)
        self.__lcd.create_char(5, bottom)
        self.__lcd.create_char(6, bottom_left_corner)
        self.__lcd.create_char(7, left_side)

    def __print_message_square(self) -> None:
        try:
            self.__lcd.home()
            self.__lcd.write_string(
                "\x00"
                + 18 * "\x01"
                + "\x02"
                + 2 * ("\x07" + 18 * " " + "\x03")
                + "\x06"
                + 18 * "\x05"
                + "\x04"
            )
        except Exception:
            logging.error(traceback.print_exc())

    def clear_message(self) -> None:
        self.__message_on_screen = False
        if self.__message_queue.empty():
            self.__interactions_enabled = True
            self.__lcd_scene_controller.restore_last_view()
        else:
            queued_msg = self.__message_queue.get()
            self.display_message(queued_msg[0], queued_msg[1])

    def display_message(self, message, time_on_screen=None) -> None:
        logger.debug(f"Queued new message (Content: {message})")
        if not self.__message_on_screen:
            
            self.backlight_on()
            self.__wait()
            if time_on_screen is not None:
                self.__interactions_enabled = False
                self.__message_on_screen = True
            
            self.__print_message_square()
            splitted = textwrap.wrap(message, 16)
            if len(splitted) == 1:
                splitted.append(" " * 18)
            for i in range(0, len(splitted)):
                splitted[i] = splitted[i].center(18)

            try:
                for i in range(0, 2):
                    self.__lcd.cursor_pos = (1 + i, 1)
                    self.__lcd.write_string(splitted[i])
            except Exception:
                logging.error(traceback.print_exc())
            self.__ready()

            if time_on_screen is not None:
                self.__message_timer = Timer(time_on_screen, self.clear_message)
                self.__message_timer.start()

        else:
            if time_on_screen is not None:
                self.__message_queue.put((message, time_on_screen))
                logger.debug("Message added to message queue")
            else:
                logger.debug("Cannot queue messages with no onscreen time")

    @property
    def can_interact(self) -> bool:
        self.backlight_on()
        return self.__interactions_enabled
