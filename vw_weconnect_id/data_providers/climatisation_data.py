from weconnect.elements.vehicle import Vehicle
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.elements.climatization_settings import ClimatizationSettings
from weconnect.elements.window_heating_status import WindowHeatingStatus
from vw_weconnect_id.data_providers.vehicle_data import WeconnectVehicleData
from vw_weconnect_id.data_providers.vehicle_data_property import (
    WeconnectVehicleDataProperty,
)


class WeconnectClimateData(WeconnectVehicleData):
    def __init__(self, vehicle: Vehicle) -> None:
        super().__init__(vehicle, vehicle.domains["climatisation"])
        self.__import_data()

    def __import_data(self) -> dict:
        climate_data = self._vehicle.domains["climatisation"]
        self._data = self.__get_climate_status(climate_data["climatisationStatus"])
        self._data = {
            **self._data,
            **self.__get_climate_settings(climate_data["climatisationSettings"]),
        }
        self._data = {
            **self._data,
            **self.__get_window_heating_status(climate_data["windowHeatingStatus"]),
        }

    def __get_climate_status(self, climate_status: ClimatizationStatus) -> dict:
        climate_status_data = {}
        data = climate_status.remainingClimatisationTime_min
        climate_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "remaining time",
            data.value,
            "Climate control time remaining",
            "climate",
            "min",
        )
        data = climate_status.climatisationState
        climate_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "climate state", data.value, "Climate control status", "climate"
        )
        return climate_status_data

    def __get_climate_settings(self, climate_settings: ClimatizationSettings) -> dict:
        climate_settings_data = {}
        data = climate_settings.targetTemperature_C
        climate_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "target temperature",
            data.value,
            "Climate control target temperature",
            "climate",
            "°C",
        )
        data = climate_settings.climatisationWithoutExternalPower
        climate_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "no external power climate control",
            data.value,
            "Climate control without external power",
            "climate",
        )
        data = climate_settings.climatizationAtUnlock
        climate_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "climate control at unlock",
            data.value,
            "Start climate control when unlocked",
            "climate",
        )
        data = climate_settings.windowHeatingEnabled
        climate_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "windows heating", data.value, "Window heating enabled", "climate"
        )
        data = climate_settings.zoneFrontLeftEnabled
        climate_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "heat left seat", data.value, "Heat left front seat", "climate"
        )
        data = climate_settings.zoneFrontRightEnabled
        climate_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "heat right seat", data.value, "Heat right front seat", "climate"
        )
        return climate_settings_data

    def __get_window_heating_status(
        self, window_heating_status: WindowHeatingStatus
    ) -> dict:
        window_heating_data = {}
        data = window_heating_status.windows["rear"]
        window_heating_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "rear window heating",
            data.windowHeatingState.value.value,
            "Rear window heating",
            "climate",
        )
        data = window_heating_status.windows["front"]
        window_heating_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "front window heating",
            data.windowHeatingState.value.value,
            "Front window heating",
            "climate",
        )
        return window_heating_data
