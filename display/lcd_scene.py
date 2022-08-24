import logging


LOG = logging.getLogger("lcd_scene")


class LCDScene:
    def __init__(self, id, lcd_scene_controller, items=None, title=None) -> None:
        LOG.debug(f"Initializing LCDScene (ID: {id})")
        self._id = id
        self._lcd_scene_controller = lcd_scene_controller

        if title is not None:
            self.__title = title.center(20, "_")
        else:
            self.__title = None

        self.__items = [] if items is None else items
        self._content = []
        self.__startpoint = 0
        self.__endpoint = 4 if self.__title is None else 3
        self.__selected_index = 0

    @property
    def id(self):
        return self._id

    @property
    def next(self):
        return self.__items[self.__selected_index].target

    @property
    def content(self) -> list:
        return self._content

    def add_item(self, lcd_item):
        LOG.debug(f"Adding item (ID: {lcd_item.id}) to LCDScene (ID: {self._id})")
        self.__items.append(lcd_item)
        lcd_item.add_scene(self)

    def load(self) -> None:
        LOG.debug(f"Loading LCDScene (ID: {self._id})")
        if self.__title is None:
            self.__select_item()
        self.update_content()

    def exit(self) -> None:
        LOG.debug(f"Exiting LCDScene (ID: {self._id})")
        if self.__title is None:
            self.__unselect_item()

    def update_content(self) -> None:
        self._content = [
            item.content for item in self.__items[self.__startpoint : self.__endpoint]
        ]
        if self.__title is not None:
            self._content = [self.__title] + self._content
        self._lcd_scene_controller.refresh(self)

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
        self.update_content()

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
