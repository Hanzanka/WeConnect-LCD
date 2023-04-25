from __future__ import annotations
from weconnect_id.vehicle import WeConnectVehicle
from weconnect_id.tools.updater import WeConnectUpdater
from button.push_button import PushButton
import json
from led.led_driver import load_automated_leds
import logging
from display.weconnect_lcd_message import configure_auto_messages
from build_tools.scene_builder import SceneBuilder
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from display.lcd_scene_controller import LCDSceneController


LOG = logging.getLogger("vehicle")


class WeConnectVehicleLoader:
    def __init__(
        self,
        lcd_scene_controller: LCDSceneController,
        weconnect_updater: WeConnectUpdater,
        config: dict,
        scene_builder: SceneBuilder,
    ) -> None:
        """
        Used to load vehicle based items.

        Args:
            lcd_scene_controller (LCDSceneController): Used to provide new scenes and set home screen.
            weconnect_updater (WeConnectUpdater): Used to initialize new objects for the app.
            config (dict): Used to initialize new objects for the app.
            scene_builder (SceneBuilder): Used to build new scenes.
        """

        LOG.debug("Initializing WeConnectVehicleLoader")
        self.__lcd_scene_controller = lcd_scene_controller
        self.__lcd_controller = lcd_scene_controller.lcd_controller
        self.__vehicle_change_allowed = True
        self.__weconnect_updater = weconnect_updater
        self.__weconnect = weconnect_updater.weconnect
        self.__config = config
        self.__scene_builder = scene_builder

    def load_vehicle_dependent_items(self, vin: str) -> None:
        LOG.debug(f"Loading vehicle dependent items (Vehicle VIN: {vin})")
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
                    weconnect_vehicle_loader=self,
                )

        try:
            with open(self.__config["paths"]["config"], "w") as config_file:
                self.__config["selected vehicle vin"] = vin
                json.dump(self.__config, config_file, indent=4)
        except FileNotFoundError as e:
            LOG.exception(e)

        button_climate = PushButton(
            pin=self.__config["pin layout"]["button climate"],
            id="CLIMATE",
            click_callback=weconnect_vehicle.start_climate_control,
            long_press_callback=weconnect_vehicle.stop_climate_control,
            long_press_time=2,
        )
        button_climate.enable()

        self.__lcd_controller.display_message("Loading Scenes")
        scenes = self.__scene_builder.load_scenes(weconnect_vehicle=weconnect_vehicle)

        self.__lcd_controller.display_message("Initializing Automated Leds")
        load_automated_leds(config=self.__config, weconnect_vehicle=weconnect_vehicle)

        self.__lcd_controller.display_message("Initializing Automated Messages")
        configure_auto_messages(self.__config, weconnect_vehicle, self.__lcd_controller)

        self.__lcd_scene_controller.set_home_scene(scene=scenes["SCENE_MENU"])
        self.__lcd_scene_controller.load_scene(scene=scenes["SCENE_MENU"])

    @property
    def vehicle_change_allowed(self) -> bool:
        return self.__vehicle_change_allowed

    def disable_vehicle_change(self) -> None:
        LOG.info("Disabled vehicle changing")
        self.__vehicle_change_allowed = False

    def enable_vehicle_change(self) -> bool:
        LOG.info("Enabling vehicle changing")
        self.__vehicle_change_allowed = True
