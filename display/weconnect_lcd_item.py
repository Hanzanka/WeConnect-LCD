from vw_weconnect_id.data_providers.vehicle_data_property import (
    WeconnectVehicleDataProperty,
)
from display.lcd_item import LCDItem
from enum import Enum


class WeConnectLCDItem(LCDItem):
    class WeConnetLCDItemMode(Enum):
        SECONDARY = "secondary"
        PRIMARY = "primary"

    def __init__(
        self,
        data_provider: WeconnectVehicleDataProperty,
        title,
        second_title=None,
        translate=None,
    ) -> None:
        super().__init__(title)
        self.__second_title = second_title
        self.__mode = WeConnectLCDItem.WeConnetLCDItemMode.PRIMARY
        self.__translate = translate
        self.__data_provider = data_provider
        self.__data_provider.add_callback_function(self.on_data_update)
        self._convert_to_string()

    def _convert_to_string(self) -> None:
        title = (
            (self.__second_title if self.__second_title is not None else self._title)
            if self.__mode == WeConnectLCDItem.WeConnetLCDItemMode.SECONDARY
            else self._title
        )
        value = self.__data_provider.get_value_with_unit(
            translate=self.__translate
        )
        indentation = (19 if self._selected else 20) - len(title)
        self._content = f"{'>' if self._selected else ''}{title}{value:>{indentation}}"

    def on_data_update(self) -> None:
        self._convert_to_string()
        for scene in self._scenes:
            scene.refresh()

    def set_mode(self, mode: WeConnetLCDItemMode) -> None:
        self.__mode = mode
        self._convert_to_string()
