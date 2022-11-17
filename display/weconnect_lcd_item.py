import logging
from weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
)
from display.lcd_item import LCDItem


LOG = logging.getLogger("lcd_item")


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
        self._update_content()

    def _update_content(self) -> None:
        value = self.__data_provider.custom_value_format(
            translate=self.__translate, include_unit=True
        )
        indentation = 20 - len(self._title)
        self._content = f"{self._title}{value:>{indentation}}"

    def on_data_update(self) -> None:
        LOG.debug(f"Updating WeConnectLCDItem (ID: {self._id}) value")
        self._update_content()
        for scene in self._scenes:
            scene.update()
