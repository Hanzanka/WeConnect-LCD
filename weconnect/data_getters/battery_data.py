from heapq import merge
from weconnect.weconnect import WeConnect
from weconnect.elements import vehicle
from weconnect.elements.battery_status import BatteryStatus
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.charging_settings import ChargingSettings
from weconnect.elements.plug_status import PlugStatus



class WeConnect_battery_data:
    def __init__(self, vehicle: vehicle) -> None:
        self.__vehicle = vehicle

    def get_data(self):
        battery_data = self.__vehicle.domains["charging"]
        data = {**{}, **self.__get_battery_status(battery_data["batteryStatus"])}
        data = {**data, **self.__get_charging_status(battery_data["chargingStatus"])}
        data = {
            **data,
            **self.__get_charging_settings(battery_data["chargingSettings"]),
        }
        data = {**data, **self.__get_plug_status(battery_data["plugStatus"])}
        for key, item in data.items():
            print(item)

    def __get_battery_status(self, battery_status: BatteryStatus) -> dict:
        battery_status_data = {}
        battery_status_data["SoC_pct"] = Battery_data_property(
            battery_status.currentSOC_pct.value, "Battery charge level", "%"
        )
        battery_status_data["Range"] = Battery_data_property(
            battery_status.cruisingRangeElectric_km.value, "Range", "km"
        )
        return battery_status_data

    def __get_charging_status(self, charging_status: ChargingStatus) -> dict:
        charging_status_data = {}
        charging_status_data["time remaining"] = Battery_data_property(
            charging_status.remainingChargingTimeToComplete_min.value,
            "Time until charge is complete",
            "min",
        )
        charging_status_data["charge state"] = Battery_data_property(
            charging_status.chargingState.value.value, "Charging state"
        )
        charging_status_data["charge mode"] = Battery_data_property(
            charging_status.chargeMode.value.value, "Charging mode"
        )
        charging_status_data["charge power"] = Battery_data_property(
            charging_status.chargePower_kW.value, "Charge power", "kW"
        )
        charging_status_data["charge rate"] = Battery_data_property(
            charging_status.chargeRate_kmph.value, "Charge rate", "km/h"
        )
        return charging_status_data

    def __get_charging_settings(self, charging_settings: ChargingSettings) -> dict:
        charging_settings_data = {}
        charging_settings_data["max current"] = Battery_data_property(
            charging_settings.maxChargeCurrentAC.value.value, "Max AC charging current"
        )
        charging_settings_data["unlock plug"] = Battery_data_property(
            charging_settings.autoUnlockPlugWhenCharged.value.value,
            "Automatically unlock charging plug",
        )
        charging_settings_data["target SoC pct"] = Battery_data_property(
            charging_settings.targetSOC_pct.value,
            "Target battery charge level percentage", "%"
        )
        return charging_settings_data

    def __get_plug_status(self, plug_status: PlugStatus) -> dict:
        plug_status_data = {}
        plug_status_data["plug connection status"] = Battery_data_property(
            plug_status.plugConnectionState.value.value, "Plug connection status"
        )
        plug_status_data["plug lock status"] = Battery_data_property(
            plug_status.plugLockState.value.value, "Charge plug lock status"
        )
        return plug_status_data

class Battery_data_property:
    def __init__(self, value, desc, unit=None) -> None:
        self.__value = str(value) if unit is None else f"{value} {unit}"
        self.__desc = desc

    @property
    def value(self) -> str:
        return self.__value

    @property
    def desc(self) -> str:
        return self.desc

    def __str__(self) -> str:
        return f"{self.__desc:<50}{self.__value}"

if __name__ == "__main__":
    weconnect = WeConnect("username", "password")
    weconnect.login()
    id3 = weconnect.vehicles["vin"]
    battery = WeConnect_battery_data(id3)
    battery.get_data()
