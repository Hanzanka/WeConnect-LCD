from vw_weconnect_id.vehicle import VolkswagenIdVehicle
from display.lcd_controller import LCDController
import logging


def configure_auto_messages(
    config: dict, vehicle: VolkswagenIdVehicle, lcd_controller: LCDController
) -> None:
    logging.info("Initializing automated messages")
    for message_id in config["automated messages"].keys():
        WeConnectLCDMessage(config, message_id, vehicle, lcd_controller)


class WeConnectLCDMessage:
    def __init__(
        self, config: dict, message_id, vehicle: VolkswagenIdVehicle, lcd_controller: LCDController
    ) -> None:
        message_config = config["automated messages"][message_id]
        self.__lcd_controller = lcd_controller
        self.__selective_messages = "trigger" in message_config
        if self.__selective_messages:
            self.__trigger_value = message_config["trigger"]
        self.__message_base = message_config["message base"]
        self.__message_time = message_config["time"]
        self.__translate = message_config["translate"]
        if self.__translate:
            self.__translation_dict = config["translations"][message_config["data provider id"]]
        self.__data_provider = vehicle.get_data_property(message_config["data provider id"])
        self.__data_provider.add_callback_function(self.on_data_update)

    def on_data_update(self) -> None:
        value = self.__data_provider.get_value_with_unit(self.__translation_dict)
        if self.__selective_messages:
            if self.__data_provider.absolute_value == self.__trigger_value:
                self.__display_message(value)
            return
        self.__display_message(value)

    def __display_message(self, value) -> None:
        self.__lcd_controller.display_message(
            message=self.__message_base.replace("{value}", value),
            time_on_screen=self.__message_time,
        )
