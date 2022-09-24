from weconnect_id.weconnect_vehicle import WeConnectVehicle
from display.lcd_controller import LCDController
import logging


LOG = logging.getLogger("lcd_message")


def configure_auto_messages(
    config: dict, weconnect_vehicle: WeConnectVehicle, lcd_controller: LCDController
) -> None:
    LOG.debug("Initializing WeConnectLCDMessages")
    for message_config in config["automated messages"]:
        WeConnectLCDMessage(message_config, weconnect_vehicle, lcd_controller)


class WeConnectLCDMessage:
    def __init__(
        self,
        message_config: dict,
        weconnect_vehicle: WeConnectVehicle,
        lcd_controller: LCDController,
    ) -> None:
        self.__id = message_config["id"]
        LOG.debug(f"Initializing WeConnectLCDMessage (ID: {self.__id})")
        self.__lcd_controller = lcd_controller
        self.__selective_messages = "trigger" in message_config
        if self.__selective_messages:
            self.__trigger_value = message_config["trigger"]
        self.__message_base = message_config["message base"]
        self.__message_time = message_config["time"]
        self.__translate = message_config["translate"]
        self.__data_provider = weconnect_vehicle.get_data_property(
            message_config["data provider id"]
        )
        self.__data_provider.add_callback_function(self.on_data_update)

    def on_data_update(self) -> None:
        value = self.__data_provider.custom_value_format(
            translate=self.__translate, include_unit=True
        )
        if self.__selective_messages:
            if self.__data_provider.value == self.__trigger_value:
                self.__display_message(value)
            return
        self.__display_message(value)

    def __display_message(self, value) -> None:
        message_content = self.__message_base.replace("{value}", value)
        LOG.debug(
            f"Queueing WeConnectLCDMessage (ID: {self.__id}) with content ({message_content})"
        )
        self.__lcd_controller.display_message(
            message=message_content,
            time_on_screen=self.__message_time,
        )
