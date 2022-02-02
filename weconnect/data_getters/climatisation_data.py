from weconnect.weconnect import WeConnect
from weconnect.elements import vehicle
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.elements.climatization_settings import ClimatizationSettings
from weconnect.elements.window_heating_status import WindowHeatingStatus
from vehicle_data import Vehicle_data
from vehicle_data_property import Vehicle_data_property
from time import sleep


class WeConnect_climate_data(Vehicle_data):
    def __init__(self, vehicle: vehicle, call_on_update: callable) -> None:
        super().__init__(vehicle, call_on_update)
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
        climate_status_data[data.getGlobalAddress()] = Vehicle_data_property(
            "remaining time",
            data.value,
            "Time remaining until climate control goes off",
            "min",
        )
        data = climate_status.climatisationState
        climate_status_data[data.getGlobalAddress()] = Vehicle_data_property(
            "climate state", data.value.value, "Climate control status"
        )
        return climate_status_data

    def __get_climate_settings(self, climate_settings: ClimatizationSettings) -> dict:
        climate_settings_data = {}
        data = climate_settings.targetTemperature_C
        climate_settings_data[data.getGlobalAddress()] = Vehicle_data_property(
            "target temperature",
            data.value,
            "Climate control target temperature",
            "°C",
        )
        data = climate_settings.climatisationWithoutExternalPower
        climate_settings_data[data.getGlobalAddress()] = Vehicle_data_property(
            "no external power climate control",
            data.value,
            "Climate control without external power",
        )
        data = climate_settings.climatizationAtUnlock
        climate_settings_data[data.getGlobalAddress()] = Vehicle_data_property(
            "climate control at unlock",
            data.value,
            "Start climate control when unlocked",
        )
        data = climate_settings.windowHeatingEnabled
        climate_settings_data[data.getGlobalAddress()] = Vehicle_data_property(
            "windows heating", data.value, "Window heating enabled"
        )
        data = climate_settings.zoneFrontLeftEnabled
        climate_settings_data[data.getGlobalAddress()] = Vehicle_data_property(
            "heat left seat", data.value, "Heat left front seat"
        )
        data = climate_settings.zoneFrontRightEnabled
        climate_settings_data[data.getGlobalAddress()] = Vehicle_data_property(
            "heat right seat", data.value, "Heat right front seat"
        )
        return climate_settings_data

    def __get_window_heating_status(
        self, window_heating_status: WindowHeatingStatus
    ) -> dict:
        window_heating_data = {}
        data = window_heating_status.windows["rear"]
        window_heating_data[data.getGlobalAddress()] = Vehicle_data_property(
            "rear window heating",
            data.windowHeatingState.value.value,
            "Rear window heating",
        )
        data = window_heating_status.windows["front"]
        window_heating_data[data.getGlobalAddress()] = Vehicle_data_property(
            "front window heating",
            data.windowHeatingState.value.value,
            "Front window heating",
        )
        return window_heating_data


def test22(data: Vehicle_data_property):
    print(data)


if __name__ == "__main__":
    weconnect = WeConnect("username", "passwd")
    weconnect.login()
    vin = ""
    for vin, car in weconnect.vehicles.items():
        vin = vin
        break
    id3 = weconnect.vehicles[vin]
    climate = WeConnect_climate_data(id3, test22)
    for key, item in climate.get_data().items():
        print(item)
    while True:
        weconnect.update()
        sleep(10)
