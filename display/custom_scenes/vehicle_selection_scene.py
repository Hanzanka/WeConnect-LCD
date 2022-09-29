from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem
from weconnect_id.tools.weconnect_updater import WeConnectUpdater
from weconnect_id.tools.weconnect_vehicle_loader import WeConnectVehicleLoader


class VehicleSelectionScene(LCDScene):
    def __init__(
        self,
        id: str,
        lcd_scene_controller,
        weconnect_updater: WeConnectUpdater,
        config: dict,
        weconnect_vehicle_loader: WeConnectVehicleLoader,
        items: list = None,
        title: str = None,
        items_selectable: bool = True
    ) -> None:
        super().__init__(id, lcd_scene_controller, items, title, items_selectable)

        self.__weconnect_vehicle_loader = weconnect_vehicle_loader
        self.__weconnect_updater = weconnect_updater
        vin_list = list(self.__weconnect_updater.weconnect.vehicles.keys())
        self.__config = config

        for vin in vin_list:
            self.add_item(
                LCDItem(
                    title=vin,
                    id=f"item_{vin}",
                    target=self.__select_vehicle,
                    target_args=[vin],
                )
            )

    def __select_vehicle(self, vin: str) -> None:
        self.__weconnect_vehicle_loader.load_vehicle_dependent_items(
            vin=vin,
            lcd_scene_controller=self._lcd_scene_controller,
            updater=self.__weconnect_updater,
            config=self.__config,
        )

    @property
    def vehicle_change_allowed(self) -> bool:
        return self.__weconnect_vehicle_loader.vehicle_change_allowed
