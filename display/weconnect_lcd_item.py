from weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
)
from display.lcd_item import LCDItem


class WeConnectLCDItem(LCDItem):
    def __init__(
        self,
        data_provider: WeConnectVehicleDataProperty,
        title,
        id,
        translate=None,
    ) -> None:
        super().__init__(title=None, id=id)
        self._title = title
        self.__translate = translate
        self.__data_provider = data_provider
        self.__data_provider.add_callback_function(self.on_data_update)
        self.update_content()

    def update_content(self) -> None:
        value = self.__data_provider.custom_value_format(
            translate=self.__translate, include_unit=True
        )
        self._content = f"{self._title}{value:>{20 - len(self._title)}}"


    def on_data_update(self) -> None:
        self.update_content()
        for scene in self._scenes:
            scene.update()
