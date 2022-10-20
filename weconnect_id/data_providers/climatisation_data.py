from weconnect.elements.vehicle import Vehicle
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.elements.climatization_settings import ClimatizationSettings
from weconnect.elements.window_heating_status import WindowHeatingStatus
from weconnect_id.data_providers.vehicle_data import (
    WeConnectVehicleData,
)
from weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
)


class WeConnectClimateData(WeConnectVehicleData):
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
        weconnect_element = climate_status.remainingClimatisationTime_min
        climate_status_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller time remaining",
            weconnect_element=weconnect_element,
            desc="Remaining climate controller time",
            category="climate",
            unit="min",
        )
        weconnect_element = climate_status.climatisationState
        climate_status_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller state",
            weconnect_element=weconnect_element,
            desc="Climate controller state",
            category="climate",
        )
        return climate_status_data

    def __get_climate_settings(self, climate_settings: ClimatizationSettings) -> dict:
        climate_settings_data = {}
        weconnect_element = climate_settings.targetTemperature_C
        climate_settings_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller target temperature",
            weconnect_element=weconnect_element,
            desc="Climate controller target temperature",
            category="climate",
            unit="°C",
        )
        weconnect_element = climate_settings.climatisationWithoutExternalPower
        climate_settings_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller without external power",
            weconnect_element=weconnect_element,
            desc="Climate control without external power",
            category="climate",
        )
        weconnect_element = climate_settings.climatizationAtUnlock
        climate_settings_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="climate controller at unlock",
            weconnect_element=weconnect_element,
            desc="Start climate control when unlocked",
            category="climate",
        )
        weconnect_element = climate_settings.windowHeatingEnabled
        climate_settings_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="windows heating",
            weconnect_element=weconnect_element,
            desc="Window heating enabled",
            category="climate",
        )
        weconnect_element = climate_settings.zoneFrontLeftEnabled
        climate_settings_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="heat left seat",
            weconnect_element=weconnect_element,
            desc="Heat left front seat",
            category="climate",
        )
        weconnect_element = climate_settings.zoneFrontRightEnabled
        climate_settings_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="heat right seat",
            weconnect_element=weconnect_element,
            desc="Heat right front seat",
            category="climate",
        )
        return climate_settings_data

    def __get_window_heating_status(
        self, window_heating_status: WindowHeatingStatus
    ) -> dict:
        window_heating_data = {}
        weconnect_element = window_heating_status.windows["rear"]
        window_heating_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="rear window heating",
            weconnect_element=weconnect_element.windowHeatingState,
            desc="Rear window heating",
            category="climate",
        )
        weconnect_element = window_heating_status.windows["front"]
        window_heating_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="front window heating",
            weconnect_element=weconnect_element.windowHeatingState,
            desc="Front window heating",
            category="climate",
        )
        return window_heating_data
