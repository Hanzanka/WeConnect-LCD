from weconnect.elements.vehicle import Vehicle
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.elements.climatization_settings import ClimatizationSettings
from weconnect.elements.window_heating_status import WindowHeatingStatus
from vw_weconnect_id.data_providers.vehicle_data import WeconnectVehicleData
from vw_weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
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
        climate_status_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller time remaining",
            value=data.value,
            desc="Remaining climate controller time",
            category="climate",
            unit="min",
        )
        data = climate_status.climatisationState
        climate_status_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller state",
            value=data.value,
            desc="Climate controller state",
            category="climate",
        )
        return climate_status_data

    def __get_climate_settings(self, climate_settings: ClimatizationSettings) -> dict:
        climate_settings_data = {}
        data = climate_settings.targetTemperature_C
        climate_settings_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller target temperature",
            value=data.value,
            desc="Climate controller target temperature",
            category="climate",
            unit="°C",
        )
        data = climate_settings.climatisationWithoutExternalPower
        climate_settings_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller without external power",
            value=data.value,
            desc="Climate control without external power",
            category="climate",
        )
        data = climate_settings.climatizationAtUnlock
        climate_settings_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller at unlock",
            value=data.value,
            desc="Start climate control when unlocked",
            category="climate",
        )
        data = climate_settings.windowHeatingEnabled
        climate_settings_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="windows heating",
            value=data.value,
            desc="Window heating enabled",
            category="climate",
        )
        data = climate_settings.zoneFrontLeftEnabled
        climate_settings_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="heat left seat",
            value=data.value,
            desc="Heat left front seat",
            category="climate",
        )
        data = climate_settings.zoneFrontRightEnabled
        climate_settings_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="heat right seat",
            value=data.value,
            desc="Heat right front seat",
            category="climate",
        )
        return climate_settings_data

    def __get_window_heating_status(
        self, window_heating_status: WindowHeatingStatus
    ) -> dict:
        window_heating_data = {}
        data = window_heating_status.windows["rear"]
        window_heating_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="rear window heating",
            value=data.windowHeatingState.value,
            desc="Rear window heating",
            category="climate",
        )
        data = window_heating_status.windows["front"]
        window_heating_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="front window heating",
            value=data.windowHeatingState.value,
            desc="Front window heating",
            category="climate",
        )
        return window_heating_data
