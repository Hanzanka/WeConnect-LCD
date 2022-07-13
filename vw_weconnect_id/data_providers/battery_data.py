from weconnect.elements.vehicle import Vehicle
from weconnect.elements.battery_status import BatteryStatus
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.charging_settings import ChargingSettings
from weconnect.elements.plug_status import PlugStatus
from vw_weconnect_id.data_providers.vehicle_data import WeconnectVehicleData
from vw_weconnect_id.data_providers.vehicle_data_property import (
    CalculatedWeConnectVehicleDataProperty,
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
        battery_status_data[data.getGlobalAddress()] = []
        battery_status_data[data.getGlobalAddress()].append(
            WeconnectVehicleDataProperty(
                "soc pct", data.value, "Battery charge percentage", "battery", "%"
            )
        )
        battery_status_data[data.getGlobalAddress()].append(
            CalculatedWeConnectVehicleDataProperty(
                "battery charge",
                data.value,
                lambda x: round(x / 100 * 58, 2),
                "Battery charge in kWh",
                "battery",
                "kWh",
            )
        )
        data = battery_status.cruisingRangeElectric_km
        battery_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "range", data.value, "Range", "battery", "km"
        )
        return battery_status_data

    def __get_charging_status(self, charging_status: ChargingStatus) -> dict:
        charging_status_data = {}
        data = charging_status.remainingChargingTimeToComplete_min
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge time remaining",
            data.value,
            "Charge time remaining",
            "battery",
            "min",
        )
        data = charging_status.chargingState
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge state", data.value, "Charge state", "battery"
        )
        data = charging_status.chargeMode
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge mode", data.value, "Charge mode", "battery"
        )
        data = charging_status.chargePower_kW
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge power", data.value, "Charge power in kW", "battery", "kW"
        )
        data = charging_status.chargeRate_kmph
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge rate", data.value, "Charge rate in km/h", "battery", "km/h"
        )
        data = charging_status.chargeType
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charge type", data.value, "Charge type", "battery"
        )
        return charging_status_data

    def __get_charging_settings(self, charging_settings: ChargingSettings) -> dict:
        charging_settings_data = {}
        data = charging_settings.maxChargeCurrentAC
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "max ac charge current", data.value, "Max AC charge current", "battery"
        )
        data = charging_settings.autoUnlockPlugWhenCharged
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "auto unlock charging plug",
            data.value,
            "Auto unlock charging plug when charging is completed",
            "battery",
        )
        data = charging_settings.targetSOC_pct
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "target soc pct",
            data.value,
            "Target battery charge percentage",
            "battery",
            "%",
        )
        data = charging_settings.autoUnlockPlugWhenChargedAC
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "auto unlock charging plug ac",
            data.value,
            "Auto unlock charging plug when charging with AC is completed",
            "battery",
        )
        return charging_settings_data

    def __get_plug_status(self, plug_status: PlugStatus) -> dict:
        plug_status_data = {}
        data = plug_status.plugConnectionState
        plug_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charging plug connection status",
            data.value,
            "Charging plug connection status",
            "battery",
        )
        data = plug_status.plugLockState
        plug_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charging plug lock status",
            data.value,
            "Charging plug locked / unlocked",
            "battery",
        )
        data = plug_status.ledColor
        plug_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            "charging led color",
            data.value,
            "Color of the charging indicator LED"
        )
        return plug_status_data
