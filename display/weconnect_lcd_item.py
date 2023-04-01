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
        target=None,
        target_args=None,
        content_centering=False,
    ) -> None:
        '''
        LCD item that is used to display content on the LCD screen.
        This class is used to display vehicle data.

        Args:
            data_provider (WeConnectVehicleDataProperty): Determines which property data of the vehicle the item displays.
            title (_type_): Sets the title of the item.
            id (_type_): Sets the id of the item.
            translate (_type_, optional): Determines if translations should be applied to displayed data. Defaults to None.
            target (_type_, optional): Determines if scene should be opened or function be ran when pressing enter on this item. Defaults to None.
            target_args (_type_, optional): Arguments for the function ran when pressing enter on this item. Defaults to None.
            content_centering (bool, optional): Determines if contents of this item should be centered. Defaults to False.
        '''
        
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

    def __on_data_update(self) -> None:
        self.update_content(
            second_title=self.__data_provider.custom_value_format(
                translate=self.__translate, include_unit=True
            )
        )
