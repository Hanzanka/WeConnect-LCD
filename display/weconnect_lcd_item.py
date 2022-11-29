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
        self.__data_provider.add_callback_function(self.__on_data_update)

    def __on_data_update(self) -> None:
        self.update_content(
            second_title=self.__data_provider.custom_value_format(
                translate=self.__translate, include_unit=True
            )
        )
