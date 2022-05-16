import logging
from display.weconnect_lcd_item import WeConnectLCDItem


logger = logging.getLogger("lcd_scenes")


class LCDScene:
    
    def __init__(self, scene_id, lcd_scene_controller, items=None, title=None) -> None:
        logger.debug(f"Initializing LCDScene (ID: {scene_id})")
        self._id = scene_id
        self._lcd_scene_controller = lcd_scene_controller

        if title is not None:
            self.__title = title.center(20, "_")
        else:
            self.__title = None

        self.__items = [] if items is None else items
        self.__startpoint = 0
        self.__endpoint = 4 if self.__title is None else 3
        self.__selected_index = 0

    @property
    def id(self):
        return self._id

    def add_item(self, lcd_item):
        logger.debug(f"Adding item (ID: {lcd_item.id}) to LCDScene (ID: {self._id})")
        self.__items.append(lcd_item)

    def next(self):
        return self.__items[self.__selected_index].target

    def load(self) -> None:
        logger.debug(f"Loading LCDScene (ID: {self._id})")
        if self.__title is None:
            self.__select_item()
        else:
            for item in self.__items:
                item.set_mode(WeConnectLCDItem.WeConnetLCDItemMode.SECONDARY)
        self.refresh()

    def exit(self) -> None:
        logger.debug(f"Exiting LCDScene (ID: {self._id})")
        if self.__title is None:
            self.__unselect_item()
        else:
            for item in self.__items:
                item.set_mode(WeConnectLCDItem.WeConnetLCDItemMode.PRIMARY)

    def refresh(self) -> None:
        content = [
            item.content for item in self.__items[self.__startpoint : self.__endpoint]
        ]
        if self.__title is not None:
            content = [self.__title] + content
        self._lcd_scene_controller.refresh(self._id, content)

    def __select_item(self) -> None:
        self.__items[self.__selected_index].select()

    def __unselect_item(self) -> None:
        self.__items[self.__selected_index].unselect()

    def scroll(self, way: str) -> None:
        if self.__title is None:
            self.__unselect_item()
        if way == "up":
            self._up()
        elif way == "down":
            self._down()
        if self.__title is None:
            self.__select_item()
        self.refresh()

    def _up(self) -> None:
        if self.__title is None:
            self.__selected_index -= 1
        else:
            self.__selected_index = self.__startpoint - 1

        list_lenght = 3 if self.__title is None else 2
        if self.__selected_index < 0:
            self.__selected_index = len(self.__items) - 1
            self.__startpoint = (
                self.__selected_index - list_lenght
                if len(self.__items) >= list_lenght + 1
                else 0
            )
            self.__endpoint = (
                self.__selected_index + 1
                if self.__selected_index >= list_lenght
                else list_lenght + 1
            )

        elif self.__selected_index < self.__startpoint:
            self.__startpoint -= 1
            self.__endpoint = (
                self.__endpoint - 1
                if self.__endpoint - 1 >= list_lenght + 1
                else list_lenght + 1
            )

    def _down(self) -> None:
        if self.__title is None:
            self.__selected_index += 1
        else:
            self.__selected_index = self.__endpoint

        list_lenght = 4 if self.__title is None else 3
        if self.__selected_index >= len(self.__items):
            self.__selected_index = 0
            self.__startpoint = 0
            self.__endpoint = 4 if self.__title is None else 3

        elif self.__selected_index >= self.__endpoint:
            self.__startpoint = (
                self.__startpoint + 1
                if self.__startpoint <= len(self.__items) - list_lenght
                else len(self.__items) - list_lenght
            )
            self.__endpoint += 1
