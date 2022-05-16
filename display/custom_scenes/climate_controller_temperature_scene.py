import logging
from display.lcd_scene import LCDScene
from vw_weconnect_id.vehicle import VolkswagenIdVehicle
import numpy


logger = logging.getLogger("lcd_scenes")


class ClimateControllerTemperatureScene(LCDScene):
    
    TEMPERATURES = list(numpy.arange(15.5, 30.5, 0.5))
    
    def __init__(self, scene_id, lcd_scene_controller, vehicle: VolkswagenIdVehicle) -> None:
        super().__init__(scene_id, lcd_scene_controller)
        logger.debug(f"Initializing ClimateControllerTemperatureScene (ID: {scene_id})")
        self.__vehicle = vehicle
        self.__current_temperature = self.__vehicle.get_data_property("target temperature").absolute_value
        self.__selected_temperature = self.__current_temperature
        self.__index = self.TEMPERATURES.index(self.__selected_temperature)
        
    def load(self) -> None:
        logger.debug(f"Loading ClimateControllerTemperatureScene (ID: {self._id})")
        self.__current_temperature = self.__vehicle.get_data_property("target temperature").absolute_value
        self.__selected_temperature = self.__current_temperature
        self.refresh()
        
    def __get_temperatures_list(self) -> list:
        end_index = self.__index + 2
        start_index = self.__index - 1 if self.__index - 1 >= 0 else 0
        temperatures = self.TEMPERATURES[start_index: end_index + 1]
        if self.__index == start_index:
            temperatures.insert(0, "")
        if end_index >= len(self.TEMPERATURES):
            temperatures += ["", ""]
        return temperatures
    
    def refresh(self) -> None:
        temperatures = self.__get_temperatures_list()
        line_1 = f"Aseta{temperatures[3]:>13}"
        line_2 = f"Ilmastoinnin{temperatures[2]:>6}"
        line_3 = f"Lämpötila{f'>{temperatures[1]}<':>10}"
        line_4 = f"{14 * ' '}{temperatures[0]}"
        self._lcd_scene_controller.refresh(self._id, [line_1, line_2, line_3, line_4])
    
    def scroll(self, way: str) -> None:
        if way == "up":
            self._up()
        if way == "down":
            self._down()
        self.refresh()
    
    def _up(self) -> None:
        if self.__index == len(self.TEMPERATURES) - 1:
            return
        self.__index += 1
        self.__selected_temperature = self.TEMPERATURES[self.__index]
    
    def _down(self) -> None:
        if self.__index == 0:
            return
        self.__index -= 1
        self.__selected_temperature = self.TEMPERATURES[self.__index]

    def __set_temperature(self) -> None:
        logger.info(f"Changing vehicle (VIN: {self.__vehicle.vin}) climate controller temperature via ClimateControllerTemperatureScene (ID: {self._id})")
        self._lcd_scene_controller.get_lcd_controller().display_message("Päivitetään lämpötilaa", 2)
        self.__vehicle.set_climate_controller_temperature(self.__selected_temperature)

    def next(self) -> callable:
        return self.__set_temperature
    
    def exit(self) -> None:
        logger.debug(f"Exiting ClimateControllerTemperatureScene (ID: {self._id})")
        pass
