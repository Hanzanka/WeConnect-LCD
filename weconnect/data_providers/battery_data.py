from time import sleep
from weconnect.weconnect import WeConnect
from weconnect.elements.vehicle import Vehicle
from weconnect.elements.battery_status import BatteryStatus
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.charging_settings import ChargingSettings
from weconnect.elements.plug_status import PlugStatus
from vehicle_data import Weconnect_vehicle_data
from vehicle_data_property import Weconnect_vehicle_data_property


class Weconnect_battery_data(Weconnect_vehicle_data):
    def __init__(self, vehicle: Vehicle) -> None:
        super().__init__(vehicle, vehicle.domains["charging"])
        self.__import_data()

    def __import_data(self) -> None:
        battery_data = self._vehicle.domains["charging"]
        self._data = {
            **{},
            **self.__get_battery_status(battery_data["batteryStatus"]),
        }
        self._data = {
            **self._data,
            **self.__get_charging_status(battery_data["chargingStatus"]),
        }
        self._data = {
            **self._data,
            **self.__get_charging_settings(battery_data["chargingSettings"]),
        }
        self._data = {
            **self._data,
            **self.__get_plug_status(battery_data["plugStatus"]),
        }

    def __get_battery_status(self, battery_status: BatteryStatus) -> dict:
        battery_status_data = {}
        data = battery_status.currentSOC_pct
        battery_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "Soc_pct", data.value, "Battery charge level", "%"
        )
        data = battery_status.cruisingRangeElectric_km
        battery_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "Range", data.value, "Range", "km"
        )
        return battery_status_data

    def __get_charging_status(self, charging_status: ChargingStatus) -> dict:
        charging_status_data = {}
        data = charging_status.remainingChargingTimeToComplete_min
        charging_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "charge time remaining",
            data.value,
            "Time until charge is complete",
            "min",
        )
        data = charging_status.chargingState
        charging_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "charge state", data.value.value, "Charging state"
        )
        data = charging_status.chargeMode
        charging_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "charge mode", data.value.value, "Charging mode"
        )
        data = charging_status.chargePower_kW
        charging_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "charge power", data.value, "Charge power", "kW"
        )
        data = charging_status.chargeRate_kmph
        charging_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "charge rate", data.value, "Charge rate", "km/h"
        )
        return charging_status_data

    def __get_charging_settings(self, charging_settings: ChargingSettings) -> dict:
        charging_settings_data = {}
        data = charging_settings.maxChargeCurrentAC
        charging_settings_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "max current", data.value.value, "Max AC charging current"
        )
        data = charging_settings.autoUnlockPlugWhenCharged
        charging_settings_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "unlock plug",
            data.value.value,
            "Automatically unlock charging plug",
        )
        data = charging_settings.targetSOC_pct
        charging_settings_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "target SoC pct",
            data.value,
            "Target battery charge level percentage",
            "%",
        )
        return charging_settings_data

    def __get_plug_status(self, plug_status: PlugStatus) -> dict:
        plug_status_data = {}
        data = plug_status.plugConnectionState
        plug_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "plug connection status", data.value.value, "Plug connection status"
        )
        data = plug_status.plugLockState
        plug_status_data[data.getGlobalAddress()] = Weconnect_vehicle_data_property(
            "plug lock status", data.value.value, "Charge plug lock status"
        )
        return plug_status_data


if __name__ == "__main__":
    weconnect = WeConnect("username", "passwd")
    weconnect.login()
    vin = ""
    for vin, car in weconnect.vehicles.items():
        vin = vin
        break
    car = weconnect.vehicles[vin]
    battery = Weconnect_battery_data(car)
    battery.add_update_function(lambda data: print(f"\nUpdate:\n{data}"))
    for key, item in battery.get_data().items():
        print(item)
    while True:
        weconnect.update()
        sleep(10)
