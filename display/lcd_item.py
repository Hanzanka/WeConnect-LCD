import logging


logger = logging.getLogger("lcd_item")


class LCDItem:
    def __init__(self, title, item_id, target=None, center=True) -> None:
        logger.debug(f"Initializing LCDItem (ID: {item_id})")
        self._scenes = []
        self._content = ""
        self._id = item_id
        self._title = title
        self.__target = target
        self.__center = center
        self._selected = False
        if issubclass(LCDItem, self.__class__):
            self._convert_to_string()

    def _convert_to_string(self) -> None:
        if self._selected:
            self._content = (
                f">{self._title}".center(20) if self.__center else f">{self._title}"
            )
            return
        self._content = self._title.center(20) if self.__center else self._title

    def select(self) -> None:
        logger.debug(f"Selected LCDItem (ID: {self._id})")
        self._selected = True
        self._convert_to_string()

    def unselect(self) -> None:
        logger.debug(f"Unselected LCDItem (ID: {self._id})")
        self._selected = False
        self._convert_to_string()

    @property
    def target(self):
        return self.__target

    @target.setter
    def target(self, scene) -> None:
        self.__target = scene

    @property
    def content(self) -> str:
        return self._content

    @property
    def id(self):
        return self._id
