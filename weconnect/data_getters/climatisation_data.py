from weconnect.weconnect import WeConnect
from weconnect.elements import vehicle
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.elements.climatization_settings import ClimatizationSettings
from weconnect.elements.window_heating_status import WindowHeatingStatus


class WeConnect_climate_data:
    def __init__(self, vehicle: vehicle) -> None:
        self.__vehicle = vehicle

    def get_data(self) -> dict:
        climate_data = self.__vehicle.domains["climatisation"]
        data = self.__get_climate_status(climate_data["climatisationStatus"])
        data = {
            **data,
            **self.__get_climate_settings(climate_data["climatisationSettings"]),
        }
        data = {
            **data,
            **self.__get_window_heating_status(climate_data["windowHeatingStatus"]),
        }
        return data

    def __get_climate_status(self, climate_status: ClimatizationStatus) -> dict:
        climate_status_data = {}
        climate_status_data["remaining time"] = Climate_data_property(
            climate_status.remainingClimatisationTime_min.value,
            "Time remaining until climate control goes off",
            "min",
        )
        climate_status_data["climate state"] = Climate_data_property(
            climate_status.climatisationState.value.value, "Climate control status"
        )
        return climate_status_data

    def __get_climate_settings(self, climate_settings: ClimatizationSettings) -> dict:
        climate_settings_data = {}
        climate_settings_data["target temp"] = Climate_data_property(
            climate_settings.targetTemperature_C.value,
            "Climate control target temperature",
            "°C",
        )
        climate_settings_data["external power climate control"] = Climate_data_property(
            climate_settings.climatisationWithoutExternalPower.value,
            "Climate control without external power",
        )
        climate_settings_data["climate control on unlock"] = Climate_data_property(
            climate_settings.climatizationAtUnlock.value,
            "Start climate control when unlocked",
        )
        climate_settings_data["windows heating"] = Climate_data_property(
            climate_settings.windowHeatingEnabled.value, "Window heating enabled"
        )
        climate_settings_data["heat left seat"] = Climate_data_property(
            climate_settings.zoneFrontLeftEnabled.value, "Heat left front seat"
        )
        climate_settings_data["heat right seat"] = Climate_data_property(
            climate_settings.zoneFrontRightEnabled.value, "Heat right front seat"
        )
        return climate_settings_data

    def __get_window_heating_status(
        self, window_heating_status: WindowHeatingStatus
    ) -> dict:
        window_heating_data = {}
        window_heating_data["rear window heating"] = Climate_data_property(
            window_heating_status.windows["rear"].windowHeatingState.value.value,
            "Rear window heating",
        )
        window_heating_data["front window heating"] = Climate_data_property(
            window_heating_status.windows["front"].windowHeatingState.value.value,
            "Front window heating",
        )
        return window_heating_data


class Climate_data_property:
    def __init__(self, value, desc, unit=None) -> None:
        self.__value = str(value) if unit is None else f"{value} {unit}"
        self.__desc = desc

    @property
    def value(self) -> str:
        return self.__value

    @property
    def desc(self) -> str:
        return self.__desc

    def __str__(self) -> str:
        return f"{self.__desc:<50}{self.__value}"


if __name__ == "__main__":
    weconnect = WeConnect("email", "passwd")
    weconnect.login()
    vin = ""
    for vin, car in weconnect.vehicles.items():
        vin = vin
        break
    id3 = weconnect.vehicles[vin]
    climate = WeConnect_climate_data(id3)
    for key, item in climate.get_data().items():
        print(item)
