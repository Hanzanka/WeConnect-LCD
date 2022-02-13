import logging
from time import sleep
from weconnect.elements.vehicle import Vehicle
from weconnect.weconnect import WeConnect
from vw_weconnect_id.controllers.climate_controller import ClimateController
from vw_weconnect_id.data_providers.battery_data import WeconnectBatteryData
from vw_weconnect_id.data_providers.climatisation_data import WeconnectClimateData
from vw_weconnect_id.data_providers.readiness_data import WeconnectReadinessData
from vw_weconnect_id.data_providers.vehicle_data_property import WeconnectVehicleDataProperty


class VolkswagenIdVehicle:

    CAR_BRANDS = {"WCAR": "Volkswagen"}

    def __init__(self, vehicle: Vehicle) -> None:
        self.__import_vehicle_properties(vehicle)
        self.__setup_vehicle()

        self.__climate_controller = ClimateController(vehicle=self.__weconnect_vehicle)

        self.__battery_data_provider = WeconnectBatteryData(vehicle)
        self.__climatisation_data_provider = WeconnectClimateData(vehicle)
        self.__readiness_data_provider = WeconnectReadinessData(vehicle)

        self.__data = {}
        self.__import_vehicle_data()

        self.__on_update_callback_functions = {}

    def __import_vehicle_properties(self, vehicle: Vehicle) -> None:
        logging.info("Importing vehicle data")
        self.__weconnect_vehicle = vehicle
        self.__brand = self.CAR_BRANDS[vehicle.devicePlatform.value.value]
        self.__model = vehicle.model
        self.__vin = vehicle.vin

    def __setup_vehicle(self) -> None:
        logging.info("Enabling request tracker for climatisation control")
        self.__weconnect_vehicle.enableTracker()

    def __import_vehicle_data(self) -> None:
        self.__data["battery"] = self.__battery_data_provider.get_data()
        self.__data["climate"] = self.__climatisation_data_provider.get_data()
        self.__data["readiness"] = self.__readiness_data_provider.get_data()

        self.__battery_data_provider.add_update_function(self.on_vehicleproperty_update)
        self.__climatisation_data_provider.add_update_function(self.on_vehicleproperty_update)
        self.__readiness_data_provider.add_update_function(self.on_vehicleproperty_update)

    def on_vehicleproperty_update(self, data: WeconnectVehicleDataProperty) -> None:
        logging.info(f"Update:\n{self.__data[data.category][data.name]}")
        self.__call_callback_functions(data.name)

    def __call_callback_functions(self, name) -> None:
        if name in self.__on_update_callback_functions.keys():
            for function in self.__on_update_callback_functions[name]:
                function()

    def start_climate_control(self) -> None:
        try:
            self.__climate_controller.start(call_when_ready=lambda x: print(x))
        except Exception as e:
            logging.error(e)

    def stop_climate_control(self) -> None:
        try:
            self.__climate_controller.stop(call_when_ready=lambda x: print(x))
        except Exception as e:
            logging.error(e)

    def add_callback_function(self, name: str, function: callable) -> None:
        """
        [Adds a callback function that will be called when given vehicle data property changes]

        Args:
            name (str): [Name of the VehicleDataProperty-object]
            function (callable): [Function to call]
        """
        if name not in self.__on_update_callback_functions.keys():
            self.__on_update_callback_functions[name] = []
        self.__on_update_callback_functions[name].append(function)


if __name__ == "__main__":
    weconnect = WeConnect("username", "passwd")
    weconnect.login()
    weconnect.update()
    vin = ""
    for vin, car in weconnect.vehicles.items():
        vin = vin
        break
    car = weconnect.vehicles[vin]
    vehicle = VolkswagenIdVehicle(car)
    while True:
        weconnect.update()
        sleep(30)
