from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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
import logging


LOG = logging.getLogger("data_properties")


class WeConnectClimateData(WeConnectVehicleData):
    def __init__(self, vehicle: Vehicle) -> None:
        """
        Provides data about climate controller based properties of the vehicle

        Args:
            vehicle (Vehicle): Used to provide data to the WeConnectDataProperties.
        """

        super().__init__(vehicle)
        self.__import_data()

    def __import_data(self) -> dict:
        LOG.debug(f"Importing climate data (Vehicle: {self._vehicle.nickname})")
        climate_data = self._vehicle.domains["climatisation"]
        self._data = self.__get_climate_status(climate_data["climatisationStatus"])
        self._data.update(
            self.__get_climate_settings(climate_data["climatisationSettings"])
        )
        self._data.update(
            self.__get_window_heating_status(climate_data["windowHeatingStatus"])
        )

    def __get_climate_status(self, climate_status: ClimatizationStatus) -> dict:
        LOG.debug(f"Importing climate status data (Vehicle: {self._vehicle.nickname})")
        climate_status_data = {}
        weconnect_element = climate_status.remainingClimatisationTime_min
        climate_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="climateControllerTimeRemaining",
                weconnect_element=weconnect_element,
                desc="Remaining standby climate controller time in minutes",
                category="climate",
                unit="min",
            )
        )
        weconnect_element = climate_status.climatisationState
        climate_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="climateControllerState",
                weconnect_element=weconnect_element,
                desc="Climate controller state",
                category="climate",
            )
        )
        return climate_status_data

    def __get_climate_settings(self, climate_settings: ClimatizationSettings) -> dict:
        LOG.debug(
            f"Importing climate settings data (Vehicle: {self._vehicle.nickname})"
        )
        climate_settings_data = {}
        weconnect_element = climate_settings.targetTemperature_C
        climate_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="climateControllerTargetTemperature",
                weconnect_element=weconnect_element,
                desc="Climate controller target temperature in °C",
                category="climate",
                unit="°C",
            )
        )
        weconnect_element = climate_settings.climatisationWithoutExternalPower
        climate_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="climateControllerWithoutExternalPower",
                weconnect_element=weconnect_element,
                desc="Standby climate controller availability without external power",
                category="climate",
            )
        )
        weconnect_element = climate_settings.climatizationAtUnlock
        climate_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="climateControllerAtUnlock",
                weconnect_element=weconnect_element,
                desc="Start standby climate controller when vehicle is unlocked",
                category="climate",
            )
        )
        weconnect_element = climate_settings.windowHeatingEnabled
        climate_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="windowsHeating",
                weconnect_element=weconnect_element,
                desc="Activate windscreen heater with standby climate controller",
                category="climate",
            )
        )
        weconnect_element = climate_settings.zoneFrontLeftEnabled
        climate_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="heatLeftSeat",
                weconnect_element=weconnect_element,
                desc="Activate driver seat heater with standby climate controller",
                category="climate",
            )
        )
        weconnect_element = climate_settings.zoneFrontRightEnabled
        climate_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="heatRightSeat",
                weconnect_element=weconnect_element,
                desc="Activate passenger seat heater with standby climate controller",
                category="climate",
            )
        )
        return climate_settings_data

    def __get_window_heating_status(
        self, window_heating_status: WindowHeatingStatus
    ) -> dict:
        LOG.debug(f"Importing window data (Vehicle: {self._vehicle.nickname})")
        window_heating_data = {}
        weconnect_element = window_heating_status.windows["rear"]
        window_heating_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="rearWindowHeating",
                weconnect_element=weconnect_element.windowHeatingState,
                desc="Activate rear glass heater with standby climate controller",
                category="climate",
            )
        )
        weconnect_element = window_heating_status.windows["front"]
        window_heating_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="frontWindowHeating",
                weconnect_element=weconnect_element.windowHeatingState,
                desc="Activate windscreen heater with standby climate controller",
                category="climate",
            )
        )
        return window_heating_data
