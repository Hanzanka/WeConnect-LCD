from __future__ import annotations
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from display.lcd_scene import LCDScene
import logging


LOG = logging.getLogger("lcd_item")


class LCDItem:
    def __init__(
        self,
        id: str,
        title: Any,
        second_title: Any = None,
        target=None,
        target_args: list = None,
        content_centering=True,
    ) -> None:
        '''
        Used to display content on the LCD screen.

        Args:
            id (_type_): ID for the LCDItem.
            title (Any): Title for the LCDItem.
                If content centering is disabled title is displayed on the left side of the LCD screen.
                If content centering is enabled title is displayed at the center of the LCD screen with second title separated with space.
            second_title (Any, optional): Second title of the item.
                If content centering is disabled second title is displayed on the right side of the LCD screen.
                Defaults to None.
            target (callable or LCDScene, optional): Determines if scene should be opened or function be ran when pressing enter on this LCDItem.
                Defaults to None.
            target_args (list, optional): Arguments for the function ran when pressing enter on this LCDItem. Defaults to None.
            content_centering (bool, optional): Determines if contents of this LCDItem should be centered. Defaults to False.
        '''
        
        LOG.debug(f"Initializing LCDItem (ID: {id})")
        self._id = id
        self._title = title
        self._second_title = second_title
        self.__target = target
        self.__target_args = target_args
        self.__content_centering = content_centering
        self._scenes = []
        self._selected = False
        self.unselect()
        LOG.debug(f"Successfully initialized LCDItem (ID: {self._id})")

    def update_content(self, title=None, second_title=None) -> None:
        LOG.debug(f"Updated content of LCDItem (ID: {self._id}) (New title: {title}) (New second title: {second_title})")
        if title is not None:
            self._title = title
        if second_title is not None:
            self._second_title = second_title
        if self._selected:
            self.select()
        else:
            self.unselect()
        for scene in self._scenes:
            scene.update()

    def select(self) -> None:
        self._selected = True
        if self.__content_centering:
            self._content = f">{self._title}{' ' + self._second_title if self._second_title is not None else ''}".center(
                20
            )
        else:
            self._content = (
                f">{self._title}{self._second_title:>{19 - len(self._title)}}"
            )

    def unselect(self) -> None:
        self._selected = False
        if self.__content_centering:
            self._content = f"{self._title}{' ' + self._second_title if self._second_title is not None else ''}".center(
                20
            )
        else:
            self._content = (
                f"{self._title}{self._second_title:>{20 - len(self._title)}}"
            )

    def add_scene(self, scene: LCDScene) -> None:
        '''
        Adds new LCDScene to LCDItem's memory.
        When content of the LCDItem is updated, the LCDItem refreshes all added LCDScenes.

        Args:
            scene (LCDScene): LCDScene which should be refreshed when the LCDItem contents are updated.
        '''
        
        self._scenes.append(scene)

    @property
    def content(self) -> str:
        return self._content

    @property
    def target(self):
        if callable(self.__target):
            return self.__target, self.__target_args
        return self.__target

    @property
    def id(self):
        return self._id

    @property
    def content_centering(self) -> bool:
        return self.__content_centering

    @content_centering.setter
    def content_centering(self, content_centering: bool) -> None:
        '''
        Sets if content centering should be enabled or disabled.

        Args:
            content_centering (bool)
        '''
        
        self.__content_centering = content_centering
