from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from build_tools.loggers_configurator import load_loggers
    from weconnect_id.tools.vehicle_loader import WeConnectVehicleLoader
    import secret_items
import os
import logging
import json
from threading import Event


LOG = logging.getLogger("main")


stop_event = Event()
button_climate = None
scenes = None
email = secret_items.email
passwd = secret_items.passwd
weconnect = None


try:
    with open(secret_items.config_path, "r") as config_file:
        config = json.load(config_file)
except FileNotFoundError as e:
    LOG.exception(e)


load_loggers(config)


from time import sleep
from display.lcd_scene_controller import LCDSceneController
from weconnect.weconnect import WeConnect
from weconnect_id.tools.updater import WeConnectUpdater
from button.push_button import PushButton
import RPi.GPIO as GPIO
from display.custom_scenes.vehicle_selection_scene import VehicleSelectionScene
from display.custom_scenes.options_menu_scene import OptionsMenuScene
from electricity_price.spot_price_provider import SpotPriceProvider
from build_tools.scene_builder import SceneBuilder


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

lcd_scene_controller = LCDSceneController()
lcd_controller = lcd_scene_controller.lcd_controller

lcd_controller.display_message("Welcome To WeConnectLCD")
sleep(2)
lcd_controller.display_message("Made By Ville Einiö")
sleep(2)
lcd_controller.display_message(
    f"WeConnect User: {email.split('@')[0].split('.')[0].title()} {email.split('@')[0].split('.')[1].title()}"
)
sleep(2)

while True:
    try:
        lcd_controller.display_message("Logging In To WeConnect")
        weconnect = WeConnect(email, passwd)
        weconnect.login()
        break
    except Exception as e:
        print(e)
        LOG.exception(e)
        lcd_controller.display_message("Login Failed, Retrying In 5s")
        sleep(5)

lcd_controller.display_message(message="Login Successfull")
sleep(2)

lcd_controller.display_message("Initializing Updater")
weconnect_updater = WeConnectUpdater(weconnect=weconnect, config=config)

selected_vin = config["selected vehicle vin"]
lcd_controller.display_message(
    message="Selected Vehicle: " + str(weconnect.vehicles[selected_vin].nickname)
)
sleep(2)

spot_price_provider = SpotPriceProvider(lcd_scene_controller=lcd_scene_controller)

lcd_controller.display_message("Inititalizing Buttons")
button_up = PushButton(
    pin=config["pin layout"]["button up"],
    id="UP",
    click_callback=lcd_scene_controller.up,
)
button_up.enable()
button_down = PushButton(
    pin=config["pin layout"]["button down"],
    id="DOWN",
    click_callback=lcd_scene_controller.down,
)
button_down.enable()
button_next = PushButton(
    pin=config["pin layout"]["button next"],
    id="NEXT",
    click_callback=lcd_scene_controller.next,
)
button_next.enable()
button_back = PushButton(
    pin=config["pin layout"]["button back"],
    id="BACK",
    click_callback=lcd_scene_controller.back,
)
button_back.enable()

scene_builder = SceneBuilder(
    config=config,
    weconnect_updater=weconnect_updater,
    lcd_scene_controller=lcd_scene_controller,
    spot_price_provider=spot_price_provider,
)

weconnect_vehicle_loader = WeConnectVehicleLoader(
    config=config,
    lcd_scene_controller=lcd_scene_controller,
    weconnect_updater=weconnect_updater,
    scene_builder=scene_builder,
)

vehicle_selection_scene = VehicleSelectionScene(
    id="scene_vehicle_selection",
    lcd_scene_controller=lcd_scene_controller,
    title="Select Vehicle",
    items_selectable=True,
    weconnect_updater=weconnect_updater,
    weconnect_vehicle_loader=weconnect_vehicle_loader,
)

options_menu_scene = OptionsMenuScene(
    close_app_event=stop_event.set,
    vehicle_selection_scene=vehicle_selection_scene,
    id="scene_options_menu",
    title="Options Menu",
    items_selectable=True,
    lcd_scene_controller=lcd_scene_controller,
)

button_wake_screen_and_shutdown = PushButton(
    pin=config["pin layout"]["button display_and_settings"],
    id="DISPLAY_AND_SETTINGS",
    click_callback=lcd_controller.backlight_on,
    long_press_callback=lcd_scene_controller.load_scene,
    long_press_time=5,
    long_press_args=[options_menu_scene],
)
button_wake_screen_and_shutdown.enable()

if selected_vin == "none":
    lcd_scene_controller.load_scene(vehicle_selection_scene)
else:
    weconnect_vehicle_loader.load_vehicle_dependent_items(vin=selected_vin)

stop_event.wait()

lcd_controller.display_message("Exiting...")
lcd_controller.backlight_off()

os._exit(0)
