from vw_weconnect_id.data_providers.vehicle_data import WeconnectVehicleData
from weconnect.elements.vehicle import Vehicle
from vw_weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
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
        connection_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="car online",
            value=data.value,
            desc="Car is connected to internet",
            category="readiness",
        )
        data = connection_status.isActive
        connection_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="car in use",
            value=data.value,
            desc="Car is in use",
            category="readiness",
        )
        return connection_data

    def __get_warnings(self, warnings) -> dict:
        warnings_data = {}
        data = warnings.insufficientBatteryLevelWarning
        warnings_data[data.getGlobalAddress()] = WeConnectVehicleDataProperty(
            id="critical battery level",
            value=data.value,
            desc="Car battery is critically low",
            category="readiness",
        )
        return warnings_data
