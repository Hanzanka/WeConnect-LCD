from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from weconnect.elements.vehicle import Vehicle
    from weconnect.elements.odometer_measurement import OdometerMeasurement
    from weconnect.elements.temperature_battery_status import TemperatureBatteryStatus
from weconnect_id.data_providers.vehicle_data import (
    WeConnectVehicleData,
)
from weconnect_id.data_providers.vehicle_data_property import (
    CalculatedWeConnectVehicleDataProperty,
    WeConnectVehicleDataProperty,
)
import logging


LOG = logging.getLogger("data_properties")


class WeConnectMeasurementData(WeConnectVehicleData):
    def __init__(self, vehicle: Vehicle) -> None:
        """
        Provides data about vehicle's general measurements

        Args:
            vehicle (Vehicle): Used to provide data to the WeConnectDataProperties.
        """
        super().__init__(vehicle)
        self.__import_data()

    def __import_data(self) -> None:
        LOG.debug(f"Importing measurement data (Vehicle: {self._vehicle.nickname})")
        measurement_data = self._vehicle.domains["measurements"]
        self._data.update(self.__get_odometer(odometer=measurement_data["odometerStatus"]))
        self._data.update(self.__get_battery_temperature(battery_temperature=measurement_data["temperatureBatteryStatus"]))

    def __get_odometer(self, odometer: OdometerMeasurement) -> dict:
        LOG.debug(f"Importing ODOMeter data (Vehicle: {self._vehicle.nickname})")
        odometer_data = {}
        weconnect_element = odometer.odometer
        odometer_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="odometer",
                weconnect_element=weconnect_element,
                unit="km",
                desc="Odometer measurement",
                category="measurement",
            )
        )
        return odometer_data

    def __get_battery_temperature(
        self, battery_temperature: TemperatureBatteryStatus
    ) -> None:
        LOG.debug(
            f"Importing battery temperature data (Vehicle: {self._vehicle.nickname})"
        )
        battery_temperature_data = {}
        weconnect_element = battery_temperature.temperatureHvBatteryMin_K
        battery_temperature_data[weconnect_element.getGlobalAddress()] = (
            CalculatedWeConnectVehicleDataProperty(
                id="battery temperature min",
                weconnect_element=weconnect_element,
                formula=lambda x: x - 273.15,
                desc="High voltage battery min temperature",
                category="measurement",
                unit="°C"
            )
        )
        weconnect_element = battery_temperature.temperatureHvBatteryMax_K
        battery_temperature_data[weconnect_element.getGlobalAddress()] = (
            CalculatedWeConnectVehicleDataProperty(
                id="battery temperature max",
                weconnect_element=weconnect_element,
                formula=lambda x: x - 273.15,
                desc="High voltage battery max temperature",
                category="measurement",
                unit="°C"
            )
        )
        return battery_temperature_data
