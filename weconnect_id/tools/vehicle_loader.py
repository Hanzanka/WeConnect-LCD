from display.lcd_scene_controller import LCDSceneController
from weconnect_id.vehicle import WeConnectVehicle
from weconnect_id.tools.updater import WeConnectUpdater
from button.push_button import PushButton
import json
from led.led_driver import load_automated_leds
import logging
from display.weconnect_lcd_message import configure_auto_messages
from build_tools.scene_builder import load_scenes


LOG = logging.getLogger("vehicle")


class WeConnectVehicleLoader:
    def __init__(
        self,
        lcd_scene_controller: LCDSceneController,
        weconnect_updater: WeConnectUpdater,
        config: dict,
    ) -> None:
        self.__lcd_scene_controller = lcd_scene_controller
        self.__lcd_controller = lcd_scene_controller.lcd_controller
        self.__vehicle_change_allowed = True
        self.__weconnect_updater = weconnect_updater
        self.__weconnect = weconnect_updater.weconnect
        self.__config = config

    def load_vehicle_dependent_items(self, vin: str) -> None:

        self.__lcd_controller.display_message("Importing Vehicle Data")
        for vehicle_vin, vehicle in self.__weconnect.vehicles.items():
            if vehicle_vin == vin:
                print(vehicle)
                weconnect_vehicle = WeConnectVehicle(
                    vehicle=vehicle, config=self.__config
                )
                weconnect_vehicle.setup_climate_controller(
                    weconnect_updater=self.__weconnect_updater,
                    lcd_controller=self.__lcd_controller,
                    weconnect_vehicle_loader=self
                )

        try:
            with open(
                "/home/ville/python/WeConnect-LCD/config.json", "w"
            ) as config_file:
                self.__config["selected vehicle vin"] = vin
                json.dump(self.__config, config_file, indent=4)
        except FileNotFoundError as e:
            LOG.exception(e)

        button_climate = PushButton(
            pin=13,
            id="CLIMATE",
            click_callback=weconnect_vehicle.start_climate_control,
            long_press_callback=weconnect_vehicle.stop_climate_control,
            long_press_time=2,
        )
        button_climate.enable()

        self.__lcd_controller.display_message("Loading Scenes")
        scenes = load_scenes(
            config=self.__config,
            weconnect_vehicle=weconnect_vehicle,
            lcd_scene_controller=self.__lcd_scene_controller,
            weconnect_updater=self.__weconnect_updater,
        )

        self.__lcd_controller.display_message("Initializing Automated Leds")
        load_automated_leds(config=self.__config, weconnect_vehicle=weconnect_vehicle)

        self.__lcd_controller.display_message("Initializing Automated Messages")
        configure_auto_messages(self.__config, weconnect_vehicle, self.__lcd_controller)

        self.__lcd_scene_controller.set_home_scene(scene=scenes["scene_menu"])
        self.__lcd_scene_controller.load_scene(scene=scenes["scene_menu"])
        
        _ = input("press enter to start a/c")
        weconnect_vehicle.start_climate_control()

    @property
    def vehicle_change_allowed(self) -> bool:
        return self.__vehicle_change_allowed

    def disable_vehicle_change(self) -> None:
        self.__vehicle_change_allowed = False

    def enable_vehicle_change(self) -> bool:
        self.__vehicle_change_allowed = True
