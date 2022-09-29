import os
from threading import Event
from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem


class OptionsMenuScene(LCDScene):
    def __init__(
        self,
        id: str,
        lcd_scene_controller,
        vehicle_selection_scene: LCDScene,
        close_app_event: Event,
        items: list = None,
        title: str = None,
        items_selectable: bool = True,
    ) -> None:
        super().__init__(id, lcd_scene_controller, items, title, items_selectable)

        self.__vehicle_selection_scene = vehicle_selection_scene

        self.add_item(
            LCDItem(
                content_centering=True,
                id="item_return",
                title="Return",
                target=lcd_scene_controller.home,
            )
        )
        self.add_item(
            LCDItem(
                content_centering=True,
                id="item_select_vehicle",
                title="Select Vehicle",
                target=self.__vehicle_selection_scene,
            )
        )
        self.add_item(
            LCDItem(
                content_centering=True,
                id="item_reboot",
                title="Reboot System",
                target=self.__reboot,
            )
        )
        self.add_item(
            LCDItem(
                content_centering=True,
                id="item_shutdown",
                title="Shutdown System",
                target=self.__shutdown,
            )
        )
        self.add_item(
            LCDItem(
                content_centering=True,
                id="item_close_app",
                title="Close App",
                target=close_app_event,
            )
        )

    @property
    def next(self):
        selected_item = self._items[self._selected_index]
        if selected_item.id == "item_select_vehicle":
            if self.__vehicle_selection_scene.vehicle_change_allowed:
                return self.__vehicle_selection_scene
            return None
        return selected_item.target

    def __reboot(self) -> None:
        self._lcd_scene_controller.lcd_controller.display_message("Rebooting System...")
        os.system("sudo reboot")

    def __shutdown(self) -> None:
        self._lcd_scene_controller.lcd_controller.display_message("Shutting Down...")
        os.system("sudo shutdown -h now")
