class LCDScene:
    def __init__(
        self,
        id: str,
        lcd_scene_controller: None,
        items: list = None,
        title: str = None,
        items_selectable: bool = True,
    ) -> None:
        self._id = id
        self._lcd_scene_controller = lcd_scene_controller

        if title is not None:
            self.__title = title.center(20, "_")
        else:
            self.__title = None

        self.__items_selectable = items_selectable
        self._items = [] if items is None else items
        self._content = []
        self.__startpoint = 0
        self.__endpoint = 4 if self.__title is None else 3
        self._selected_index = 0

    @property
    def id(self):
        return self._id

    @property
    def next(self):
        return self._items[self._selected_index].target

    @property
    def content(self) -> list:
        self._content = [
            item.content for item in self._items[self.__startpoint : self.__endpoint]
        ]
        if self.__title is not None:
            self._content = [self.__title] + self._content
        return self._content

    @property
    def has_title(self) -> bool:
        return self.__title is not None

    def set_lcd_scene_controller(self, lcd_scene_controller) -> None:
        self._lcd_scene_controller = lcd_scene_controller

    def add_item(self, lcd_item):
        self._items.append(lcd_item)
        lcd_item.add_scene(self)

    def load(self) -> None:
        if self.__items_selectable:
            self.__select_item()
        self.update()

    def exit(self) -> None:
        if self.__items_selectable:
            self.__unselect_item()

    def update(self) -> None:
        self._lcd_scene_controller.refresh(self)

    def __select_item(self) -> None:
        self._items[self._selected_index].select()

    def __unselect_item(self) -> None:
        self._items[self._selected_index].unselect()

    def scroll(self, way: str) -> None:
        if self.__items_selectable:
            self.__unselect_item()
        if way == "up":
            self._up()
        elif way == "down":
            self._down()
        if self.__items_selectable:
            self.__select_item()
        self.update()

    def _up(self) -> None:
        if self.__items_selectable:
            self._selected_index -= 1
        else:
            self._selected_index = self.__startpoint - 1

        list_lenght = 3 if self.__title is None else 2
        if self._selected_index < 0:
            self._selected_index = len(self._items) - 1
            self.__startpoint = (
                self._selected_index - list_lenght
                if len(self._items) >= list_lenght + 1
                else 0
            )
            self.__endpoint = (
                self._selected_index + 1
                if self._selected_index >= list_lenght
                else list_lenght + 1
            )

        elif self._selected_index < self.__startpoint:
            self.__startpoint -= 1
            self.__endpoint = (
                self.__endpoint - 1
                if self.__endpoint - 1 >= list_lenght + 1
                else list_lenght + 1
            )

    def _down(self) -> None:
        if self.__items_selectable:
            self._selected_index += 1
        else:
            self._selected_index = self.__endpoint

        list_lenght = 4 if self.__title is None else 3
        if self._selected_index >= len(self._items):
            self._selected_index = 0
            self.__startpoint = 0
            self.__endpoint = 4 if self.__title is None else 3

        elif self._selected_index >= self.__endpoint:
            self.__startpoint = (
                self.__startpoint + 1
                if self.__startpoint <= len(self._items) - list_lenght
                else len(self._items) - list_lenght
            )
            self.__endpoint += 1
