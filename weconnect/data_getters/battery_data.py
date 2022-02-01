from enum import Enum
from time import sleep
from weconnect.weconnect import WeConnect
from weconnect.elements import vehicle
from weconnect.elements.battery_status import BatteryStatus
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.charging_settings import ChargingSettings
from weconnect.elements.plug_status import PlugStatus
from weconnect.addressable import AddressableLeaf, AddressableAttribute


class WeConnect_battery_data:
    def __init__(self, vehicle: vehicle, call_on_update: callable) -> None:
        self.__vehicle = vehicle

        self.__battery_data = {}
        self.__import_data()

        self.__call_on_update = call_on_update
        
        self.__add_observer()

        self.__addresses = (
            f"/vehicles/{self.__vehicle.vin}/domains/charging/batteryStatus/charging/",
            f"/vehicles/{self.__vehicle.vin}/domains/charging/batteryStatus/batteryStatus/",
            f"/vehicles/{self.__vehicle.vin}/domains/charging/batteryStatus/chargingStatus/",
            f"/vehicles/{self.__vehicle.vin}/domains/charging/batteryStatus/chargingSettings/",
            f"/vehicles/{self.__vehicle.vin}/domains/charging/batteryStatus/plugStatus/",
        )

    def __import_data(self) -> None:
        battery_data = self.__vehicle.domains["charging"]
        self.__battery_data = {
            **{},
            **self.__get_battery_status(battery_data["batteryStatus"]),
        }
        self.__battery_data = {
            **self.__battery_data,
            **self.__get_charging_status(battery_data["chargingStatus"]),
        }
        self.__battery_data = {
            **self.__battery_data,
            **self.__get_charging_settings(battery_data["chargingSettings"]),
        }
        self.__battery_data = {
            **self.__battery_data,
            **self.__get_plug_status(battery_data["plugStatus"]),
        }

    def get_data(self) -> dict:
        data = {}
        for key, item in self.__battery_data.items():
            data[item.name] = item
        return data

    def __get_battery_status(self, battery_status: BatteryStatus) -> dict:
        battery_status_data = {}
        data = battery_status.currentSOC_pct
        battery_status_data[data.getGlobalAddress()] = Battery_data_property(
            "Soc_pct", data.value, "Battery charge level", "%"
        )
        data = battery_status.cruisingRangeElectric_km
        battery_status_data[data.getGlobalAddress()] = Battery_data_property(
            "Range", data.value, "Range", "km"
        )
        return battery_status_data

    def __get_charging_status(self, charging_status: ChargingStatus) -> dict:
        charging_status_data = {}
        data = charging_status.remainingChargingTimeToComplete_min
        charging_status_data[data.getGlobalAddress()] = Battery_data_property(
            "charge time remaining",
            data.value,
            "Time until charge is complete",
            "min",
        )
        data = charging_status.chargingState
        charging_status_data[data.getGlobalAddress()] = Battery_data_property(
            "charge mode", data.value.value, "Charging state"
        )
        data = charging_status.chargeMode
        charging_status_data[data.getGlobalAddress()] = Battery_data_property(
            "charge mode", data.value.value, "Charging mode"
        )
        data = charging_status.chargePower_kW
        charging_status_data[data.getGlobalAddress()] = Battery_data_property(
            "charge power", data.value, "Charge power", "kW"
        )
        data = charging_status.chargeRate_kmph
        charging_status_data[data.getGlobalAddress()] = Battery_data_property(
            "charge rate", data.value, "Charge rate", "km/h"
        )
        return charging_status_data

    def __get_charging_settings(self, charging_settings: ChargingSettings) -> dict:
        charging_settings_data = {}
        data = charging_settings.maxChargeCurrentAC
        charging_settings_data[data.getGlobalAddress()] = Battery_data_property(
            "max current", data.value.value, "Max AC charging current"
        )
        data = charging_settings.autoUnlockPlugWhenCharged
        charging_settings_data[data.getGlobalAddress()] = Battery_data_property(
            "unlock plug",
            data.value.value,
            "Automatically unlock charging plug",
        )
        data = charging_settings.targetSOC_pct
        charging_settings_data[data.getGlobalAddress()] = Battery_data_property(
            "target SoC pct",
            data.value,
            "Target battery charge level percentage",
            "%",
        )
        return charging_settings_data

    def __get_plug_status(self, plug_status: PlugStatus) -> dict:
        plug_status_data = {}
        data = plug_status.plugConnectionState
        plug_status_data[data.getGlobalAddress()] = Battery_data_property(
            "plug connection status", data.value.value, "Plug connection status"
        )
        data = plug_status.plugLockState
        plug_status_data[data.getGlobalAddress()] = Battery_data_property(
            "plug lock status", data.value.value, "Charge plug lock status"
        )
        return plug_status_data

    def __update_value(self, element: AddressableAttribute) -> None:
        value = element.value
        address = element.getGlobalAddress()
        print(value.getGlobalAddress())
        print(address)
        self.__battery_data[address].value = (
            value.value if isinstance(value, Enum) else value
        )
        self.__call_on_update(self.__battery_data[address])

    def __add_observer(self) -> None:
        self.__vehicle.weConnect.addObserver(
            self.__on_weconnect_event,
            AddressableLeaf.ObserverEvent.ENABLED
            | AddressableLeaf.ObserverEvent.DISABLED
            | AddressableLeaf.ObserverEvent.VALUE_CHANGED,
        )

    def __on_weconnect_event(self, element, flags) -> None:
        print(element.getGlobalAddress())
        if isinstance(element, AddressableAttribute):
            if flags and element.getGlobalAddress().startswith(self.__addresses):
                self.__update_value(element)


class Battery_data_property:
    def __init__(self, name, value, desc, unit=None) -> None:
        self.__name = name
        self.__value = str(value)
        self.__unit = unit
        self.__desc = desc

    @property
    def value(self) -> str:
        return self.__value

    @property
    def name(self) -> str:
        return self.__name

    @value.setter
    def value(self, value) -> None:
        self.__value = str(value)

    def __str__(self) -> str:
        return (
            f"{self.__desc:<50}{self.__value}"
            if self.__unit is None
            else f"{self.__desc:<50}{self.__value}{self.__unit}"
        )


def test22(data: Battery_data_property):
    print(data)


if __name__ == "__main__":
    weconnect = WeConnect("username", "passwd")
    weconnect.login()
    vin = ""
    for vin, car in weconnect.vehicles.items():
        vin = vin
        break
    id3 = weconnect.vehicles[vin]
    battery = WeConnect_battery_data(id3, test22)
    for key, item in battery.get_data().items():
        print(item)
    while True:
        weconnect.update()
        sleep(10)
