from display.lcd_item import LCDItem
from display.weconnect_lcd_item import WeConnectLCDItem


class LCDScene:
    def __init__(self, id, lcd_scene_controller, items=None, title=None) -> None:
        self.__id = id
        self.__lcd_scene_controller = lcd_scene_controller

        if title is not None:
            self.__title = title.center(20, "_")
        else:
            self.__title = None

        self.__items = [] if items is None else items
        self.__startpoint = 0
        self.__endpoint = 4 if self.__title is None else 3
        self.__selected_index = 0

        if len(self.__items) != 0:
            for item in self.__items:
                item.add_scene(self)

    @property
    def id(self):
        return self.__id

    def add_item(self, item):
        item.add_scene(self)
        self.__items.append(item)

    def get_selected_item(self) -> LCDItem:
        return self.__items[self.__selected_index]

    def load(self) -> None:
        if self.__title is None:
            self.__select_item()
        else:
            for item in self.__items:
                item.set_mode(WeConnectLCDItem.WeConnetLCDItemMode.SECONDARY)
        self.refresh()

    def exit(self) -> None:
        if self.__title is None:
            self.__unselect_item()
        else:
            for item in self.__items:
                item.set_mode(WeConnectLCDItem.WeConnetLCDItemMode.PRIMARY)

    def refresh(self) -> list:
        content = [
            item.content for item in self.__items[self.__startpoint : self.__endpoint]
        ]
        if self.__title is not None:
            content = [self.__title] + content
        self.__lcd_scene_controller.refresh(self.__id, content)

    def __select_item(self) -> None:
        self.__items[self.__selected_index].select()

    def __unselect_item(self) -> None:
        self.__items[self.__selected_index].unselect()

    def scroll(self, way: str) -> None:
        if self.__title is None:
            self.__unselect_item()
        if way == "up":
            self.__up()
        elif way == "down":
            self.__down()
        if self.__title is None:
            self.__select_item()
        self.refresh()

    def __up(self) -> None:
        if self.__title is None:
            self.__selected_index -= 1
        else:
            self.__selected_index = self.__startpoint - 1

        list_lenght = 3 if self.__title is None else 2
        if self.__selected_index < 0:
            self.__selected_index = len(self.__items) - 1
            self.__startpoint = (
                self.__selected_index - list_lenght
                if len(self.__items) >= list_lenght
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

    def __down(self) -> None:
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
