from weconnect.elements.vehicle import Vehicle
from weconnect.elements.battery_status import BatteryStatus
from weconnect.elements.charging_status import ChargingStatus
from weconnect.elements.charging_settings import ChargingSettings
from weconnect.elements.plug_status import PlugStatus
from weconnect_id.data_providers.vehicle_data import (
    WeConnectVehicleData,
)
from weconnect_id.data_providers.vehicle_data_property import (
    CalculatedWeConnectVehicleDataProperty,
    WeConnectVehicleDataProperty,
)


class WeConnectBatteryData(WeConnectVehicleData):
    def __init__(self, vehicle: Vehicle) -> None:
        super().__init__(vehicle)
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
        weconnect_element = battery_status.currentSOC_pct
        battery_status_data[weconnect_element.getGlobalAddress()] = []
        battery_status_data[weconnect_element.getGlobalAddress()].append(
            WeConnectVehicleDataProperty(
                id="battery level",
                weconnect_element=weconnect_element,
                category="battery",
                desc="Battery charge percentage",
                unit="%",
            )
        )
        battery_status_data[weconnect_element.getGlobalAddress()].append(
            CalculatedWeConnectVehicleDataProperty(
                id="battery charge",
                weconnect_element=weconnect_element,
                formula=lambda x: round(x / 100 * 58, 2),
                desc="Battery charge in kWh",
                category="battery",
                unit="kWh",
            )
        )
        weconnect_element = battery_status.cruisingRangeElectric_km
        battery_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="range",
            weconnect_element=weconnect_element,
            desc="Range",
            category="battery",
            unit="km",
        )
        return battery_status_data

    def __get_charging_status(self, charging_status: ChargingStatus) -> dict:
        charging_status_data = {}
        weconnect_element = charging_status.remainingChargingTimeToComplete_min
        charging_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charge time remaining",
            weconnect_element=weconnect_element,
            desc="Charge time remaining",
            category="battery",
            unit="min",
        )
        weconnect_element = charging_status.chargingState
        charging_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charge state",
            weconnect_element=weconnect_element,
            desc="Charge state",
            category="battery",
        )
        weconnect_element = charging_status.chargeMode
        charging_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charge mode",
            weconnect_element=weconnect_element,
            desc="Charge mode",
            category="battery",
        )
        weconnect_element = charging_status.chargePower_kW
        charging_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charge power",
            weconnect_element=weconnect_element,
            desc="Charge power in kW",
            category="battery",
            unit="kW",
        )
        weconnect_element = charging_status.chargeRate_kmph
        charging_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charge rate",
            weconnect_element=weconnect_element,
            desc="Charge rate in km/h",
            category="battery",
            unit="km/h",
        )
        weconnect_element = charging_status.chargeType
        charging_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charge type",
            weconnect_element=weconnect_element,
            desc="Charge type",
            category="battery",
        )
        return charging_status_data

    def __get_charging_settings(self, charging_settings: ChargingSettings) -> dict:
        charging_settings_data = {}
        weconnect_element = charging_settings.maxChargeCurrentAC
        charging_settings_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="max ac charge current",
            weconnect_element=weconnect_element,
            desc="Max AC charge current",
            category="battery",
        )
        weconnect_element = charging_settings.autoUnlockPlugWhenCharged
        charging_settings_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="auto unlock charging plug",
            weconnect_element=weconnect_element,
            desc="Auto unlock charging plug when charging is completed",
            category="battery",
        )
        weconnect_element = charging_settings.targetSOC_pct
        charging_settings_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="target battery level",
            weconnect_element=weconnect_element,
            desc="Target battery charge percentage",
            category="battery",
            unit="%",
        )
        weconnect_element = charging_settings.autoUnlockPlugWhenChargedAC
        charging_settings_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="auto unlock charging plug ac",
            weconnect_element=weconnect_element,
            desc="Auto unlock charging plug when charging with AC is completed",
            category="battery",
        )
        return charging_settings_data

    def __get_plug_status(self, plug_status: PlugStatus) -> dict:
        plug_status_data = {}
        weconnect_element = plug_status.plugConnectionState
        plug_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charging plug connection status",
            weconnect_element=weconnect_element,
            desc="Charging plug connection status",
            category="battery",
        )
        weconnect_element = plug_status.plugLockState
        plug_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charging plug lock status",
            weconnect_element=weconnect_element,
            desc="Charging plug locked / unlocked",
            category="battery",
        )
        weconnect_element = plug_status.ledColor
        plug_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="charging led color",
            weconnect_element=weconnect_element,
            desc="Color of the charging indicator LED",
            category="battery",
        )
        weconnect_element = plug_status.externalPower
        plug_status_data[
            weconnect_element.getGlobalAddress()
        ] = WeConnectVehicleDataProperty(
            id="external power",
            weconnect_element=weconnect_element,
            desc="External power status",
            category="battery",
        )
        return plug_status_data
