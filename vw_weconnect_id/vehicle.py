import logging
from weconnect.elements.vehicle import Vehicle
from led_tools.led_controller import IndicatorLEDController
from vw_weconnect_id.controllers.climate_controller import ClimateController
from vw_weconnect_id.data_providers.battery_data import WeconnectBatteryData
from vw_weconnect_id.data_providers.climatisation_data import WeconnectClimateData
from vw_weconnect_id.data_providers.readiness_data import WeconnectReadinessData
from vw_weconnect_id.data_providers.vehicle_data_property import WeconnectVehicleDataProperty
from vw_weconnect_id.tools.weconnect_updater import WeConnectUpdater


class VolkswagenIdVehicle:

    CAR_BRANDS = {"WCAR": "Volkswagen"}

    def __init__(self, vehicle: Vehicle, updater: WeConnectUpdater, led_controller: IndicatorLEDController) -> None:
        
        self.__import_vehicle_properties(vehicle)
        self.__setup_vehicle()

        self.__climate_controller = None

        self.__battery_data_provider = WeconnectBatteryData(vehicle)
        self.__climatisation_data_provider = WeconnectClimateData(vehicle)
        self.__readiness_data_provider = WeconnectReadinessData(vehicle)

        self.__data = {}
        self.__import_vehicle_data()
        
        led_controller.setup_vehicle_dependent_leddrivers(self)
        
        self.__climate_controller = ClimateController(vehicle=self, updater=updater, led_controller=led_controller)

    def __import_vehicle_properties(self, vehicle: Vehicle) -> None:
        logging.info("Importing vehicle properties")
        self.__weconnect_vehicle = vehicle
        self.__brand = self.CAR_BRANDS[vehicle.devicePlatform.value.value]
        self.__model = vehicle.model
        self.__vin = vehicle.vin

    def __setup_vehicle(self) -> None:
        logging.info("Enabling request tracker for climatisation control")
        self.__weconnect_vehicle.enableTracker()

    def __import_vehicle_data(self) -> None:
        logging.info("Importing vehicle data")
        self.__data.update(self.__battery_data_provider.get_data())
        self.__data.update(self.__climatisation_data_provider.get_data())
        self.__data.update(self.__readiness_data_provider.get_data())

    def start_climate_control(self) -> None:
        if self.__climate_controller is None:
            return
        try:
            self.__climate_controller.start(call_when_ready=lambda x: print(x))
        except Exception as e:
            logging.error(e)

    def stop_climate_control(self) -> None:
        if self.__climate_controller is None:
            return
        try:
            self.__climate_controller.stop(call_when_ready=lambda x: print(x))
        except Exception as e:
            logging.error(e)

    def get_data_property(self, data_id) -> WeconnectVehicleDataProperty:
        return self.__data[data_id]

    def add_callback_function(self, data_id, function: callable) -> None:
        self.get_data_property(data_id).add_callback_function(function)

    def get_weconnect_vehicle(self) -> Vehicle:
        return self.__weconnect_vehicle
