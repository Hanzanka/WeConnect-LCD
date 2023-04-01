from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem
from weconnect_id.tools.updater import WeConnectUpdater
from weconnect_id.tools.vehicle_loader import WeConnectVehicleLoader


class VehicleSelectionScene(LCDScene):
    def __init__(
        self,
        id: str,
        lcd_scene_controller,
        weconnect_updater: WeConnectUpdater,
        weconnect_vehicle_loader: WeConnectVehicleLoader,
        items: list = None,
        title: str = None,
        items_selectable: bool = True
    ) -> None:
        '''
        Selects the vehicle used to display data.

        Args:
            id (str): ID of the scene.
            lcd_scene_controller (_type_): LCDSceneController-object used to control the scenes of the LCD screen.
            weconnect_updater (WeConnectUpdater): WeConnectUpdater-object which is used to update data.
            weconnect_vehicle_loader (WeConnectVehicleLoader): WeConnectVehicleLoader-object which is used to load items for the specified vehicle.
            items (list, optional): Keep as None. Defaults to None.
            title (str, optional): Title for the scene. Defaults to None.
            items_selectable (bool, optional): Keep as True. Defaults to True.
        '''
        
        super().__init__(id, lcd_scene_controller, items, title, items_selectable)

        self.__weconnect_vehicle_loader = weconnect_vehicle_loader
        self.__weconnect_updater = weconnect_updater
        vehicle_list = self.__weconnect_updater.weconnect.vehicles

        for vin, vehicle in vehicle_list.items():
            self.add_item(
                LCDItem(
                    title=vehicle.nickname,
                    id=f"item_{vin}",
                    target=self.__select_vehicle,
                    target_args=[vin],
                )
            )

    def __select_vehicle(self, vin: str) -> None:
        self.__weconnect_vehicle_loader.load_vehicle_dependent_items(
            vin=vin
        )

    @property
    def vehicle_change_allowed(self) -> bool:
        return self.__weconnect_vehicle_loader.vehicle_change_allowed
