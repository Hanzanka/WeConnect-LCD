import logging


LOG = logging.getLogger("lcd_item")


class LCDItem:
    def __init__(
        self, title, item_id, target=None, target_args=None, center=True
    ) -> None:
        LOG.debug(f"Initializing LCDItem (ID: {item_id})")
        self._scenes = []
        self._content = ""
        self._id = item_id
        self._title = title
        self.__target = target
        self.__target_args = target_args
        self.__center = center
        self._selected = False
        if self._title is not None:
            self._update_content()

    def _update_content(self) -> None:
        if self._selected:
            self._content = (
                f">{self._title}".center(20) if self.__center else f">{self._title}"
            )
            return
        self._content = self._title.center(20) if self.__center else self._title

    def select(self) -> None:
        LOG.debug(f"Selected LCDItem (ID: {self._id})")
        self._selected = True
        self._update_content()

    def unselect(self) -> None:
        LOG.debug(f"Unselected LCDItem (ID: {self._id})")
        self._selected = False
        self._update_content()

    def add_scene(self, scene) -> None:
        LOG.debug(f"Adding LCDScene (ID: {scene.id}) to LCDItem (ID: {self._id})")
        self._scenes.append(scene)

    @property
    def content(self) -> str:
        return self._content

    @property
    def target(self):
        if callable(self.__target):
            return self.__target, self.__target_args
        return self.__target

    @target.setter
    def target(self, target) -> None:
        self.__target = target

    @property
    def id(self):
        return self._id
