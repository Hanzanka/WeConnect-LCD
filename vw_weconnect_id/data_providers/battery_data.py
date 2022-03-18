from weconnect.elements.vehicle import Vehicle
from weconnect.elements.battery_status import BatteryStatus
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.charging_settings import ChargingSettings
from weconnect.elements.plug_status import PlugStatus
from vw_weconnect_id.data_providers.vehicle_data import WeconnectVehicleData
from vw_weconnect_id.data_providers.vehicle_data_property import (
    WeconnectVehicleDataProperty,
)


class WeconnectBatteryData(WeconnectVehicleData):
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
        battery_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "soc_pct", data.value, "Battery", "battery", "%", log_data=True
        )
        data = battery_status.cruisingRangeElectric_km
        battery_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "range", data.value, "Range", "battery", "km", log_data=True
        )
        return battery_status_data

    def __get_charging_status(self, charging_status: ChargingStatus) -> dict:
        charging_status_data = {}
        data = charging_status.remainingChargingTimeToComplete_min
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge time remaining",
            data.value,
            "Charge time",
            "battery",
            "min",
        )
        data = charging_status.chargingState
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge state", data.value, "Charge state", "battery", log_data=True
        )
        data = charging_status.chargeMode
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge mode", data.value, "Charge mode", "battery"
        )
        data = charging_status.chargePower_kW
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge power", data.value, "Charge power", "battery", "kW", log_data=True
        )
        data = charging_status.chargeRate_kmph
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge rate", data.value, "Charge rate", "battery", "km/h", log_data=True
        )
        data = charging_status.chargeType
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge type", data.value, "Charge type", "battery", log_data=True
        )
        return charging_status_data

    def __get_charging_settings(self, charging_settings: ChargingSettings) -> dict:
        charging_settings_data = {}
        data = charging_settings.maxChargeCurrentAC
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "max current", data.value, "Max AC charging current", "battery"
        )
        data = charging_settings.autoUnlockPlugWhenCharged
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "unlock plug",
            data.value,
            "Unlock charging plug",
            "battery",
        )
        data = charging_settings.targetSOC_pct
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "target SoC pct",
            data.value,
            "Target battery",
            "battery",
            "%",
        )
        return charging_settings_data

    def __get_plug_status(self, plug_status: PlugStatus) -> dict:
        plug_status_data = {}
        data = plug_status.plugConnectionState
        plug_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "plug connection status",
            data.value,
            "Plug status",
            "battery",
            log_data=True,
        )
        data = plug_status.plugLockState
        plug_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "plug lock status", data.value, "Plug locked", "battery"
        )
        return plug_status_data
