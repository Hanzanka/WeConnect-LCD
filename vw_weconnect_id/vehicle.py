import logging
from weconnect.elements.vehicle import Vehicle
from vw_weconnect_id.controllers.climate_controller import ClimateController
from vw_weconnect_id.data_providers.battery_data import WeconnectBatteryData
from vw_weconnect_id.data_providers.climatisation_data import WeconnectClimateData
from vw_weconnect_id.data_providers.readiness_data import WeconnectReadinessData
from vw_weconnect_id.data_providers.vehicle_data_property import WeconnectVehicleDataProperty
from vw_weconnect_id.tools.weconnect_updater import WeConnectUpdater


logger = logging.getLogger("vehicle")


class VolkswagenIdVehicle:

    CAR_BRANDS = {"WCAR": "Volkswagen"}

    def __init__(self, vehicle: Vehicle, updater: WeConnectUpdater, config: dict) -> None:
        logger.debug(f"Initializing vehicle (VIN: {vehicle.vin})")
        self.__import_vehicle_properties(vehicle)
        self.__setup_vehicle()

        self.__battery_data_provider = WeconnectBatteryData(vehicle)
        self.__climatisation_data_provider = WeconnectClimateData(vehicle)
        self.__readiness_data_provider = WeconnectReadinessData(vehicle)

        self.__data = {}
        self.__import_vehicle_data()
        
        self.__add_data_property_translations(config=config)
        self.__add_data_property_logger_paths(config=config)
        
        self.__climate_controller = ClimateController(vehicle=self, updater=updater)

    def __import_vehicle_properties(self, vehicle: Vehicle) -> None:
        logger.debug("Importing vehicle properties")
        self.__weconnect_vehicle = vehicle
        self.__brand = self.CAR_BRANDS[vehicle.devicePlatform.value.value]
        self.__model = vehicle.model
        self.__vin = vehicle.vin

    def __setup_vehicle(self) -> None:
        logger.debug("Enabling request tracker for climate controller")
        self.__weconnect_vehicle.enableTracker()

    def __import_vehicle_data(self) -> None:
        logger.debug("Importing vehicle data")
        self.__data.update(self.__battery_data_provider.get_data())
        self.__data.update(self.__climatisation_data_provider.get_data())
        self.__data.update(self.__readiness_data_provider.get_data())

    def __add_data_property_translations(self, config: dict) -> None:
        logger.debug("Adding translations for WeconnectVehicleDataProperties")
        for data_id, translations in config["translations"].items():
            self.get_data_property(data_id=data_id).add_translations(translations=translations)

    def __add_data_property_logger_paths(self, config: dict) -> None:
        logger.debug("Setting logging path for WeconnectVehicleDataProperties that log their data")
        for data_property in self.__data.values():
            if data_property.logging_enabled:
                data_property.set_logger_path(config["paths"]["data_logs"])

    def start_climate_control(self) -> None:
        if self.__climate_controller is None:
            return
        try:
            logger.info(f"Starting vehicle (VIN: {self.__vin}) climate controller")
            self.__climate_controller.start()
        except Exception as e:
            logger.exception(e)

    def stop_climate_control(self) -> None:
        if self.__climate_controller is None:
            return
        try:
            logger.info(f"Stopping vehicle (VIN: {self.__vin}) climate controller")
            self.__climate_controller.stop()
        except Exception as e:
            logger.exception(e)

    def set_climate_controller_temperature(self, temperature: float) -> None:
        if self.__climate_controller is None:
            return
        try:
            logger.info(f"Updating vehicle (VIN: {self.__vin}) climate controller target temperature")
            self.__climate_controller.set_temperature(temperature)
        except Exception as e:
            logger.exception(e)

    def get_data_property(self, data_id: str) -> WeconnectVehicleDataProperty:
        return self.__data[data_id]

    def add_callback_function(self, data_id: str, function: callable) -> None:
        logger.info(f"Adding callback function {function.__name__} to WeconnectVehicleDataProperty (ID: {data_id})")
        self.get_data_property(data_id).add_callback_function(function)

    def get_weconnect_vehicle(self) -> Vehicle:
        return self.__weconnect_vehicle

    @property
    def vin(self) -> str:
        return self.__vin
    
    @property
    def model(self) -> str:
        return self.__model
    
    @property
    def brand(self) -> str:
        return self.__brand
