from __future__ import annotations
from typing import TYPE_CHECKING
import logging
from weconnect.elements.vehicle import Vehicle
from display.lcd_controller import LCDController
from weconnect_id.controllers.climate_controller import ClimateController
from weconnect_id.data_providers.battery_data import WeConnectBatteryData
from weconnect_id.data_providers.climatisation_data import WeConnectClimateData
from weconnect_id.data_providers.readiness_data import WeConnectReadinessData
from weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
)
from weconnect_id.tools.updater import WeConnectUpdater

if TYPE_CHECKING:
    from weconnect_id.tools.vehicle_loader import WeConnectVehicleLoader


LOG = logging.getLogger("vehicle")


class WeConnectVehicle:

    CAR_BRANDS = {"WCAR": "Volkswagen"}

    def __init__(self, vehicle: Vehicle, config: dict) -> None:
        '''
        Contains all data related to the selected vehicle and used to interact with climate controls.

        Args:
            vehicle (Vehicle): Used to provide data to the WeConnectVehicleDataProperties, to enable features and interact with climate controller.
            config (dict): Provides configurations for WeConnectVehicleDataProperties.
        '''
        
        LOG.debug(f"Initializing WeConnectVehicle (Vehicle: {vehicle.nickname})")
        self.__import_vehicle_properties(vehicle=vehicle)
        self.__api_vehicle.enableTracker()

        self.__battery_data_provider = WeConnectBatteryData(vehicle=vehicle)
        self.__climatisation_data_provider = WeConnectClimateData(vehicle=vehicle)
        self.__readiness_data_provider = WeConnectReadinessData(vehicle=vehicle)

        self.__import_vehicle_data()

        self.__add_data_property_translations(config=config)
        self.__setup_data_property_loggers(config=config)

        self.__climate_controller = None

    def setup_climate_controller(
        self,
        weconnect_updater: WeConnectUpdater,
        lcd_controller: LCDController,
        weconnect_vehicle_loader: WeConnectVehicleLoader,
    ) -> None:
        '''
        Used to setup the ClimateController.

        Args:
            weconnect_updater (WeConnectUpdater): Used in ClimateController setup.
            lcd_controller (LCDController): Used in ClimateController setup.
            weconnect_vehicle_loader (WeConnectVehicleLoader): Used in ClimateController setup.
        '''
        
        LOG.debug(f"Setting up climate controller (Vehicle: {self.nickname})")
        self.__climate_controller = ClimateController(
            weconnect_vehicle=self,
            weconnect_updater=weconnect_updater,
            lcd_controller=lcd_controller,
            weconnect_vehicle_loader=weconnect_vehicle_loader,
        )

    def __import_vehicle_properties(self, vehicle: Vehicle) -> None:
        LOG.debug(f"Importing vehicle properties (Vehicle: {vehicle.nickname})")
        self.__api_vehicle = vehicle
        self.__brand = self.CAR_BRANDS[vehicle.devicePlatform.value.value]
        self.__model = vehicle.model
        self.__vin = vehicle.vin
        self.__brand_code = vehicle.brandCode
        self.__nickname = vehicle.nickname

    def __import_vehicle_data(self) -> None:
        LOG.debug(f"Importing vehicle data (Vehicle: {self.nickname})")
        self.__data = {}
        self.__data.update(self.__battery_data_provider.get_data())
        self.__data.update(self.__climatisation_data_provider.get_data())
        self.__data.update(self.__readiness_data_provider.get_data())

    def __add_data_property_translations(self, config: dict) -> None:
        for data_id, translations in config["translations"].items():
            self.__data[data_id].add_translations(translations=translations)

    def __setup_data_property_loggers(self, config: dict) -> None:
        for data_id in config["log data"]:
            self.__data[data_id].set_logging(True, config["paths"]["data_logs"])

    def start_climate_control(self) -> None:
        '''
        Starts the climate controller of the vehicle.
        '''
        
        if self.__climate_controller is None:
            return
        try:
            LOG.info(f"Starting vehicle (VIN: {self.__vin}) climate controller")
            self.__climate_controller.start()
        except Exception as e:
            LOG.exception(e)

    def stop_climate_control(self) -> None:
        '''
        Stops the climate controller of the vehicle.
        '''
        
        if self.__climate_controller is None:
            return
        try:
            LOG.info(f"Stopping vehicle (VIN: {self.__vin}) climate controller")
            self.__climate_controller.stop()
        except Exception as e:
            LOG.exception(e)

    def switch_climate_control(self) -> None:
        '''
        Switches the climate controller state of the vehicle.
        '''
        
        if self.__climate_controller is None:
            return
        try:
            LOG.info(f"Switching vehicle (VIN: {self.__vin}) climate controller mode")
            self.__climate_controller.switch()
        except Exception as e:
            LOG.exception(e)

    def set_climate_controller_temperature(self, temperature: float) -> None:
        '''
        Sets the climate controller temperature of the vehicle.

        Args:
            temperature (float): Target temperature of the climate controller.
        '''
        
        if self.__climate_controller is None:
            return
        try:
            LOG.info(
                f"Updating vehicle (VIN: {self.__vin}) climate controller target temperature"
            )
            self.__climate_controller.set_temperature(temperature)
        except Exception as e:
            LOG.exception(e)

    def get_data_property(self, data_property_id: str) -> WeConnectVehicleDataProperty:
        '''
        Get WeConnectVehicleDataProperty using it's ID.

        Args:
            data_property_id (str): ID of the WeConnectVehicleDataProperty.

        Returns:
            WeConnectVehicleDataProperty
        '''
        
        return self.__data[data_property_id]

    @property
    def api_vehicle(self) -> Vehicle:
        return self.__api_vehicle

    @property
    def nickname(self) -> str:
        return self.__nickname

    @property
    def vin(self) -> str:
        return self.__vin

    @property
    def model(self) -> str:
        return self.__model

    @property
    def brand(self) -> str:
        return self.__brand

    @property
    def brand_code(self) -> str:
        return self.__brand_code
