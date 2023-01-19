from __future__ import annotations
from typing import TYPE_CHECKING
from weconnect.elements.plug_status import PlugStatus
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.climatization_status import ClimatizationStatus

if TYPE_CHECKING:
    from weconnect_id.vehicle import WeConnectVehicle
    from display.lcd_scene_controller import LCDSceneController


class LCDStatusBar:
    def __init__(
        self,
        weconnect_vehicle: WeConnectVehicle,
        lcd_scene_controller: LCDSceneController,
    ) -> None:
        self.__weconnect_vehicle = weconnect_vehicle
        self.__lcd_scene_controller = lcd_scene_controller

        self.__battery_empty = "\x00"
        self.__battery_20 = "\x01"
        self.__battery_50 = "\x02"
        self.__battery_80 = "\x03"
        self.__charging = "\x04"
        self.__plug_connected = "\x05"
        self.__charge_complete = "\x06"
        self.__climate_on = "\x07"

        self.__battery_icon = None
        self.__charging_icon = None
        self.__climate_icon = None

        self.__climate_on_states = [
            ClimatizationStatus.ClimatizationState.HEATING,
            ClimatizationStatus.ClimatizationState.COOLING,
            ClimatizationStatus.ClimatizationState.VENTILATION,
        ]

        self.__weconnect_vehicle.get_data_property(
            "battery level"
        ).add_callback_function(id="STATUS_BAR", function=self.__update_battery_icon)
        self.__weconnect_vehicle.get_data_property(
            "charge state"
        ).add_callback_function(id="STATUS_BAR", function=self.__update_charging_icon)
        self.__weconnect_vehicle.get_data_property(
            "target battery level"
        ).add_callback_function(id="STATUS_BAR", function=self.__update_charging_icon)
        self.__weconnect_vehicle.get_data_property(
            "charging plug connection status"
        ).add_callback_function(id="STATUS_BAR", function=self.__update_charging_icon)
        self.__weconnect_vehicle.get_data_property(
            "climate controller state"
        ).add_callback_function(id="STATUS_BAR", function=self.__update_climate_icon)

        self.__update_battery_icon()
        self.__update_charging_icon()
        self.__update_climate_icon()

    @property
    def icons(self) -> list:
        icons_string = ""
        if self.__climate_icon is not None:
            icons_string += self.__climate_icon
        if self.__charging_icon is not None:
            icons_string += self.__charging_icon
        icons_string += self.__battery_icon
        return icons_string

    def __update_battery_icon(self) -> None:
        battery = self.__weconnect_vehicle.get_data_property("battery level").value
        if battery >= 80:
            self.__battery_icon = self.__battery_80
        elif battery >= 50:
            self.__battery_icon = self.__battery_50
        elif battery >= 20:
            self.__battery_icon = self.__battery_20
        else:
            self.__battery_icon = self.__battery_empty
        self.__lcd_scene_controller.update_status_bar()

    def __update_charging_icon(self) -> None:
        charging_status = self.__weconnect_vehicle.get_data_property(
            "charge state"
        ).value
        
        if charging_status == ChargingStatus.ChargingState.CHARGING:
            self.__charging_icon = self.__charging
            self.__lcd_scene_controller.update_status_bar()
            return

        plug_status = self.__weconnect_vehicle.get_data_property(
            "charging plug connection status"
        ).value
        target_soc_pct = self.__weconnect_vehicle.get_data_property(
            "target battery level"
        ).value
        battery = self.__weconnect_vehicle.get_data_property("battery level").value
        
        if battery >= target_soc_pct and plug_status == PlugStatus.PlugConnectionState.CONNECTED:
            self.__charging_icon = self.__charge_complete
            self.__lcd_scene_controller.update_status_bar()
            return

        if plug_status == PlugStatus.PlugConnectionState.CONNECTED:
            self.__charging_icon = self.__plug_connected
            self.__lcd_scene_controller.update_status_bar()
            return

        self.__charging_icon = None
        self.__lcd_scene_controller.update_status_bar()

    def __update_climate_icon(self) -> None:
        climate_state = self.__weconnect_vehicle.get_data_property(
            "climate controller state"
        ).value
        if climate_state in self.__climate_on_states:
            self.__climate_icon = self.__climate_on
        else:
            self.__climate_icon = None
        self.__lcd_scene_controller.update_status_bar()
