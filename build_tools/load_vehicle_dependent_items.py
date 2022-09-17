from display.lcd_scene_controller import LCDSceneController
from weconnect_id.weconnect_vehicle import WeConnectVehicle
from weconnect_id.tools.weconnect_updater import WeConnectUpdater
from button.push_button import PushButton
import json
from led.led_driver import load_automated_leds
import logging
from display.weconnect_lcd_message import configure_auto_messages
from build_tools.scene_builder import load_scenes


LOG = logging.getLogger("build_tools")


def load_vehicle_dependent_items(
    vin: str,
    lcd_scene_controller: LCDSceneController,
    weconnect_updater: WeConnectUpdater,
    config: dict,
) -> None:
    lcd_controller = lcd_scene_controller.lcd_controller
    weconnect = weconnect_updater.weconnect

    lcd_controller.display_message("Importing Vehicle Data")
    for vehicle_vin, vehicle in weconnect.vehicles.items():
        if vehicle_vin == vin:
            weconnect_vehicle = WeConnectVehicle(vehicle=vehicle, config=config)
            weconnect_vehicle.setup_climate_controller(
                weconnect_updater=weconnect_updater,
                lcd_scene_controller=lcd_scene_controller,
            )

    try:
        with open("/home/ville/python/WeConnect-LCD/config.json", "w") as config_file:
            config["selected vehicle vin"] = vin
            json.dump(config, config_file, indent=4)
    except FileNotFoundError as e:
        LOG.exception(e)

    button_climate = PushButton(
        pin=21,
        id="CLIMATE",
        double_click_prevention_time=5,
        click_callback=weconnect_vehicle.start_climate_control,
        long_press_callback=weconnect_vehicle.stop_climate_control,
        long_press_time=2,
    )
    button_climate.enable()

    lcd_controller.display_message("Loading Scenes")
    scenes = load_scenes(
        config=config,
        vehicle=weconnect_vehicle,
        lcd_scene_controller=lcd_scene_controller,
        updater=weconnect_updater,
    )

    lcd_controller.display_message("Initializing Automated Leds")
    load_automated_leds(config=config, vehicle=weconnect_vehicle)

    lcd_controller.display_message("Initializing Automated Messages")
    configure_auto_messages(config, weconnect_vehicle, lcd_controller)

    lcd_scene_controller.set_home_scene(scene=scenes["scene_menu"])
    lcd_scene_controller.load_scene(scene=scenes["scene_menu"])
