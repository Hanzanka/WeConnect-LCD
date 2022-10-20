from weconnect_id.data_providers.vehicle_data import (
    WeConnectVehicleData,
)
from weconnect.elements.vehicle import Vehicle
from weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
)


class WeConnectReadinessData(WeConnectVehicleData):
    def __init__(self, vehicle: Vehicle) -> None:
        super().__init__(vehicle, vehicle.domains["readiness"])
        self.__import_data()

    def __import_data(self) -> None:
        readiness_data = self._vehicle.domains["readiness"]["readinessStatus"]
        self._data = self.__get_connection_state(readiness_data.connectionState)
        self._data = {
            **self._data,
            **self.__get_warnings(readiness_data.connectionWarning),
        }

    def __get_connection_state(self, connection_status) -> dict:
        connection_data = {}
        weconnect_element = connection_status.isOnline
        connection_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="car online",
            weconnect_element=weconnect_element,
            desc="Car is connected to internet",
            category="readiness",
        )
        weconnect_element = connection_status.isActive
        connection_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="car in use",
            weconnect_element=weconnect_element,
            desc="Car is in use",
            category="readiness",
        )
        return connection_data

    def __get_warnings(self, warnings) -> dict:
        warnings_data = {}
        weconnect_element = warnings.insufficientBatteryLevelWarning
        warnings_data[weconnect_element.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="critical battery level",
            weconnect_element=weconnect_element,
            desc="Car battery is critically low",
            category="readiness",
        )
        return warnings_data
