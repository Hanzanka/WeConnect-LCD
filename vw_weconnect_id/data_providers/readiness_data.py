from vehicle_data import Weconnect_vehicle_data
from weconnect.elements.vehicle import Vehicle
from vehicle_data_property import Weconnect_vehicle_data_property
from weconnect.weconnect import WeConnect
from time import sleep


class Weconnect_readiness_data(Weconnect_vehicle_data):
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
        connection_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "car online", data.value, "Car is connected to internet"
        )
        data = connection_status.isActive
        connection_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "car active", data.value, "Car is in use"
        )
        return connection_data

    def __get_warnings(self, warnings) -> dict:
        warnings_data = {}
        data = warnings.insufficientBatteryLevelWarning
        warnings_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "critical battery level", data.value, "Car battery is critically low"
        )
        return warnings_data


if __name__ == "__main__":
    weconnect = WeConnect("username", "passwd")
    weconnect.login()
    vin = ""
    for vin, car in weconnect.vehicles.items():
        vin = vin
        break
    car = weconnect.vehicles[vin]
    readiness = Weconnect_readiness_data(car)
    readiness.add_update_function(lambda data: print(f"\nUpdate:\n{data}"))
    for key, item in readiness.get_data().items():
        print(item)
    while True:
        weconnect.update()
        sleep(10)
