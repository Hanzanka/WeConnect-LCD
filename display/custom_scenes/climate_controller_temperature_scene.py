import logging
from display.lcd_scene import LCDScene
from weconnect_id.vehicle import WeConnectVehicle
import numpy


LOG = logging.getLogger("lcd_scene")


class ClimateControllerTemperatureScene(LCDScene):

    TEMPERATURES = list(numpy.arange(15.5, 30.5, 0.5))

    def __init__(
        self, id, lcd_scene_controller, weconnect_vehicle: WeConnectVehicle
    ) -> None:
        '''
        Initializes scene for changing the target temperature of the climate controller.

        Args:
            id (_type_): ID for the scene.
            lcd_scene_controller (_type_): LCDSceneController-object used to control the scenes of the LCD screen.
            weconnect_vehicle (WeConnectVehicle): WeConnectVehicle-object where the temperature should be applied.
        '''
        
        super().__init__(id=id, lcd_scene_controller=lcd_scene_controller)
        LOG.debug(f"Initializing ClimateControllerTemperatureScene (ID: {id})")
        self.__weconnect_vehicle = weconnect_vehicle
        self.__current_temperature = self.__weconnect_vehicle.get_data_property(
            "climate controller target temperature"
        ).value
        self.__selected_temperature = self.__current_temperature
        self.__index = self.TEMPERATURES.index(self.__selected_temperature)

    @property
    def content(self) -> list:
        return self._content

    def load(self) -> None:
        LOG.debug(f"Loading ClimateControllerTemperatureScene (ID: {self._id})")
        self.__current_temperature = self.__weconnect_vehicle.get_data_property(
            "climate controller target temperature"
        ).value
        self.__selected_temperature = self.__current_temperature
        self.update()

    def __get_temperatures_list(self) -> list:
        end_index = self.__index + 2
        start_index = self.__index - 1 if self.__index - 1 >= 0 else 0
        temperatures = self.TEMPERATURES[start_index : end_index + 1]
        if self.__index == start_index:
            temperatures.insert(0, "")
        if end_index >= len(self.TEMPERATURES):
            temperatures += ["", ""]
        return temperatures

    def update(self) -> None:
        temperatures = self.__get_temperatures_list()
        line_1 = f"Aseta{temperatures[3]:>13}"
        line_2 = f"Ilmastoinnin{temperatures[2]:>6}"
        line_3 = f"Lämpötila{f'>{temperatures[1]}<':>10}"
        line_4 = f"{14 * ' '}{temperatures[0]}"
        self._content = [line_1, line_2, line_3, line_4]
        self._lcd_scene_controller.refresh(self)

    def scroll(self, way: str) -> None:
        if way == "up":
            self._up()
        if way == "down":
            self._down()
        self.update()

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
        self.__weconnect_vehicle.set_climate_controller_temperature(
            self.__selected_temperature
        )

    @property
    def next(self) -> tuple:
        return self.__set_temperature, None

    def exit(self) -> None:
        LOG.debug(f"Exiting ClimateControllerTemperatureScene (ID: {self._id})")
        pass
