from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from weconnect.elements.vehicle import Vehicle
    from weconnect.elements.battery_status import BatteryStatus
    from weconnect.elements.charging_status import ChargingStatus
    from weconnect.elements.charging_settings import ChargingSettings
    from weconnect.elements.plug_status import PlugStatus
    from weconnect.elements.charge_mode import ChargeMode
    from weconnect.elements.charging_care_settings import ChargingCareSettings
from weconnect_id.data_providers.vehicle_data import (
    WeConnectVehicleData,
)
from weconnect_id.data_providers.vehicle_data_property import (
    CalculatedWeConnectVehicleDataProperty,
    WeConnectVehicleDataProperty,
)
import logging


LOG = logging.getLogger("data_properties")


class WeConnectBatteryData(WeConnectVehicleData):
    def __init__(self, vehicle: Vehicle) -> None:
        """
        Provides data about battery based properties of the vehicle

        Args:
            vehicle (Vehicle): Used to provide data to the WeConnectDataProperties.
        """

        super().__init__(vehicle)
        self.__import_data()

    def __import_data(self) -> None:
        LOG.debug(f"Importing battery data (Vehicle: {self._vehicle.nickname})")
        battery_data = self._vehicle.domains["charging"]
        self._data.update(self.__get_battery_status(battery_data["batteryStatus"]))
        self._data.update(self.__get_charging_status(battery_data["chargingStatus"]))
        self._data.update(
            self.__get_charging_settings(battery_data["chargingSettings"])
        )
        self._data.update(self.__get_plug_status(battery_data["plugStatus"]))
        self._data.update(self.__get_charge_mode(battery_data["chargeMode"]))
        self._data.update(
            self.__get_charging_care_settings(battery_data["chargingCareSettings"])
        )

    def __get_battery_status(self, battery_status: BatteryStatus) -> dict:
        LOG.debug(f"Importing battery status data (Vehicle: {self._vehicle.nickname})")
        battery_status_data = {}
        weconnect_element = battery_status.currentSOC_pct
        battery_status_data[weconnect_element.getGlobalAddress()] = []
        battery_status_data[weconnect_element.getGlobalAddress()].append(
            WeConnectVehicleDataProperty(
                id="batteryLevel",
                weconnect_element=weconnect_element,
                category="battery",
                desc="Battery level as percentage",
                unit="%",
            )
        )
        battery_status_data[weconnect_element.getGlobalAddress()].append(
            CalculatedWeConnectVehicleDataProperty(
                id="batteryCharge",
                weconnect_element=weconnect_element,
                formula=lambda x: round(x / 100 * 58, 2),
                desc="Battery charge in kWh",
                category="battery",
                unit="kWh",
            )
        )
        weconnect_element = battery_status.cruisingRangeElectric_km
        battery_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="range",
                weconnect_element=weconnect_element,
                desc="Estimated electric range in km",
                category="battery",
                unit="km",
            )
        )
        return battery_status_data

    def __get_charging_status(self, charging_status: ChargingStatus) -> dict:
        LOG.debug(f"Importing charging data (Vehicle: {self._vehicle.nickname})")
        charging_status_data = {}
        weconnect_element = charging_status.remainingChargingTimeToComplete_min
        charging_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargeTimeRemaining",
                weconnect_element=weconnect_element,
                desc="Remaining charging time in minutes",
                category="battery",
                unit="min",
            )
        )
        weconnect_element = charging_status.chargingState
        charging_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargeState",
                weconnect_element=weconnect_element,
                desc="Charging state",
                category="battery",
            )
        )
        weconnect_element = charging_status.chargeMode
        charging_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargeMode",
                weconnect_element=weconnect_element,
                desc="Charging mode",
                category="battery",
            )
        )
        weconnect_element = charging_status.chargePower_kW
        charging_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargePower",
                weconnect_element=weconnect_element,
                desc="Charging power in kWs",
                category="battery",
                unit="kW",
            )
        )
        weconnect_element = charging_status.chargeRate_kmph
        charging_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargeRate",
                weconnect_element=weconnect_element,
                desc="Charging rate in km/h",
                category="battery",
                unit="km/h",
            )
        )
        weconnect_element = charging_status.chargeType
        charging_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargeType",
                weconnect_element=weconnect_element,
                desc="Charging type",
                category="battery",
            )
        )
        return charging_status_data

    def __get_charging_settings(self, charging_settings: ChargingSettings) -> dict:
        LOG.debug(
            f"Importing charging settings data (Vehicle: {self._vehicle.nickname})"
        )
        charging_settings_data = {}
        weconnect_element = charging_settings.maxChargeCurrentAC
        charging_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="maxACChargeCurrent",
                weconnect_element=weconnect_element,
                desc="Maximum AC charging current",
                category="battery",
            )
        )
        weconnect_element = charging_settings.autoUnlockPlugWhenCharged
        charging_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="autoUnlockChargingPlug",
                weconnect_element=weconnect_element,
                desc="Automatically unlock charging plug after charging is completed",
                category="battery",
            )
        )
        weconnect_element = charging_settings.targetSOC_pct
        charging_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="targetBatteryLevel",
                weconnect_element=weconnect_element,
                desc="Target battery level as percentage",
                category="battery",
                unit="%",
            )
        )
        weconnect_element = charging_settings.autoUnlockPlugWhenChargedAC
        charging_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="autoUnlockChargingPlugAC",
                weconnect_element=weconnect_element,
                desc="Automatically unlock charging plug after charging with AC is completed",
                category="battery",
            )
        )
        return charging_settings_data

    def __get_plug_status(self, plug_status: PlugStatus) -> dict:
        LOG.debug(f"Importing plug status data (Vehicle: {self._vehicle.nickname})")
        plug_status_data = {}
        weconnect_element = plug_status.plugConnectionState
        plug_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargingPlugConnectionStatus",
                weconnect_element=weconnect_element,
                desc="Connection status of charging plug",
                category="battery",
            )
        )
        weconnect_element = plug_status.plugLockState
        plug_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargingPlugLockStatus",
                weconnect_element=weconnect_element,
                desc="Charging plug locked / unlocked",
                category="battery",
            )
        )
        weconnect_element = plug_status.ledColor
        plug_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="chargingLedColor",
                weconnect_element=weconnect_element,
                desc="Color of the charging indicator LED",
                category="battery",
            )
        )
        weconnect_element = plug_status.externalPower
        plug_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="externalPower",
                weconnect_element=weconnect_element,
                desc="External power status",
                category="battery",
            )
        )
        return plug_status_data

    def __get_charge_mode(self, charge_mode: ChargeMode) -> dict:
        LOG.debug(f"Importing  data (Vehicle: {self._vehicle.nickname})")
        charge_mode_data = {}
        weconnect_element = charge_mode.preferredChargeMode
        charge_mode_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="preferredChargingMode",
                weconnect_element=weconnect_element,
                desc="Preferred charging mode",
                category="battery",
            )
        )
        return charge_mode_data

    def __get_charging_care_settings(
        self, charging_care_settings: ChargingCareSettings
    ) -> dict:
        LOG.debug(f"Importing charging care data (Vehicle: {self._vehicle.nickname})")
        charging_care_settings_data = {}
        weconnect_element = charging_care_settings.batteryCareMode
        charging_care_settings_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="batteryCareMode",
                weconnect_element=weconnect_element,
                desc="Battery care mode activated / deactivatedg",
                category="battery",
            )
        )
        return charging_care_settings_data
