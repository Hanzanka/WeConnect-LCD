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
                data_property_id="soc pct", value=data.value, category="battery", desc="Battery charge percentage", unit="%"
            )
        )
        battery_status_data[data.getGlobalAddress()].append(
            CalculatedWeConnectVehicleDataProperty(
                data_property_id="battery charge",
                value=data.value,
                formula=lambda x: round(x / 100 * 58, 2),
                desc="Battery charge in kWh",
                category="battery",
                unit="kWh",
            )
        )
        data = battery_status.cruisingRangeElectric_km
        battery_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="range", value=data.value, desc="Range", category="battery", unit="km"
        )
        return battery_status_data

    def __get_charging_status(self, charging_status: ChargingStatus) -> dict:
        charging_status_data = {}
        data = charging_status.remainingChargingTimeToComplete_min
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charge time remaining",
            value=data.value,
            desc="Charge time remaining",
            category="battery",
            unit="min",
        )
        data = charging_status.chargingState
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charge state", value=data.value, desc="Charge state", category="battery"
        )
        data = charging_status.chargeMode
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charge mode", value=data.value, desc="Charge mode", category="battery"
        )
        data = charging_status.chargePower_kW
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charge power", value=data.value, desc="Charge power in kW", category="battery", unit="kW"
        )
        data = charging_status.chargeRate_kmph
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charge rate", value=data.value, desc="Charge rate in km/h", category="battery", unit="km/h"
        )
        data = charging_status.chargeType
        charging_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charge type", value=data.value, desc="Charge type", category="battery"
        )
        return charging_status_data

    def __get_charging_settings(self, charging_settings: ChargingSettings) -> dict:
        charging_settings_data = {}
        data = charging_settings.maxChargeCurrentAC
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="max ac charge current", value=data.value, desc="Max AC charge current", category="battery"
        )
        data = charging_settings.autoUnlockPlugWhenCharged
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="auto unlock charging plug",
            value=data.value,
            desc="Auto unlock charging plug when charging is completed",
            category="battery",
        )
        data = charging_settings.targetSOC_pct
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="target soc pct",
            value=data.value,
            desc="Target battery charge percentage",
            category="battery",
            unit="%",
        )
        data = charging_settings.autoUnlockPlugWhenChargedAC
        charging_settings_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="auto unlock charging plug ac",
            value=data.value,
            desc="Auto unlock charging plug when charging with AC is completed",
            category="battery",
        )
        return charging_settings_data

    def __get_plug_status(self, plug_status: PlugStatus) -> dict:
        plug_status_data = {}
        data = plug_status.plugConnectionState
        plug_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charging plug connection status",
            value=data.value,
            desc="Charging plug connection status",
            category="battery",
        )
        data = plug_status.plugLockState
        plug_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charging plug lock status",
            value=data.value,
            desc="Charging plug locked / unlocked",
            category="battery",
        )
        data = plug_status.ledColor
        plug_status_data[data.getGlobalAddress()] = WeconnectVehicleDataProperty(
            data_property_id="charging led color",
            value=data.value,
            desc="Color of the charging indicator LED",
            category="battery"
        )
        return plug_status_data
