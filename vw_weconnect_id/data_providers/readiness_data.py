from vw_weconnect_id.data_providers.vehicle_data import WeconnectVehicleData
from weconnect.elements.vehicle import Vehicle
from vw_weconnect_id.data_providers.vehicle_data_property import (
    WeconnectVehicleDataProperty,
)


class WeconnectReadinessData(WeconnectVehicleData):
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
        data = connection_status.isOnline
        connection_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "car online", data.value, "Car is connected to internet", "readiness"
        )
        data = connection_status.isActive
        connection_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "car in use", data.value, "Car is in use", "readiness"
        )
        return connection_data

    def __get_warnings(self, warnings) -> dict:
        warnings_data = {}
        data = warnings.insufficientBatteryLevelWarning
        warnings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "critical battery level",
            data.value,
            "Car battery is critically low",
            "readiness",
        )
        return warnings_data
