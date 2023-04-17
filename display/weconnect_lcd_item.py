from weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
)
from display.lcd_item import LCDItem
from typing import Any
import logging


LOG = logging.getLogger("lcd_item")


class WeConnectLCDItem(LCDItem):
    def __init__(
        self,
        data_provider: WeConnectVehicleDataProperty,
        title: Any,
        id: str,
        translate: bool = None,
        target=None,
        target_args: list = None,
        content_centering=False,
    ) -> None:
        '''
        LCD item that is used to display content on the LCD screen.
        This class is used to display vehicle data.

        Args:
            data_provider (WeConnectVehicleDataProperty): Used to provide data for the WeConnectLCDItem.
            title (Any): Title for the LCDItem.
            id (str): ID for the LCDItem.
            translate (bool, optional): Enables or disables translations for the WeConnectLCDItem. Defaults to None.
            target (LCDScene or callable, optional): Determines if scene should be opened or function be ran when pressing enter on this item. Defaults to None.
            target_args (list, optional): Arguments for the function ran when pressing enter on this item. Defaults to None.
            content_centering (bool, optional): Determines if contents of this item should be centered. Defaults to False.
        '''
        
        LOG.debug(f"Initializing WeConnectLCDItem (ID: f{id})")
        super().__init__(
            title=title,
            id=id,
            content_centering=content_centering,
            target=target,
            target_args=target_args,
            second_title=data_provider.custom_value_format(
                translate=translate, include_unit=True
            ),
        )
        self.__translate = translate
        self.__data_provider = data_provider
        self.__data_provider.add_callback_function(id="LCD_ITEMS", function=self.__on_data_update)
        LOG.debug(f"Successfully initialized WeConnectLCDItem (ID: f{self._id})")

    def __on_data_update(self) -> None:
        self.update_content(
            second_title=self.__data_provider.custom_value_format(
                translate=self.__translate, include_unit=True
            )
        )
