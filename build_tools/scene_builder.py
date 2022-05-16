import logging
from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem
from display.lcd_scene_controller import LCDSceneController
from display.weconnect_lcd_item import WeConnectLCDItem
from vw_weconnect_id.vehicle import VolkswagenIdVehicle
from display.custom_scenes.climate_controller_temperature_scene import (
    ClimateControllerTemperatureScene,
)


logger = logging.getLogger("build_tools")


def load_scenes(
    config: dict, vehicle: VolkswagenIdVehicle, lcd_scene_controller: LCDSceneController
) -> dict:
    logger.debug("Loading LCDScenes from config-file")
    scene_config = config["lcd scenes"]
    item_config = config["lcd items"]

    custom_scenes = {
        "climate temperature": ClimateControllerTemperatureScene(
            lcd_scene_controller=lcd_scene_controller,
            scene_id="climate settings",
            vehicle=vehicle,
        )
    }
    scenes = {}
    items = {}

    for scene in scene_config:
        scene_type = scene["type"]
        if scene_type == "normal":
            scenes[scene["id"]] = LCDScene(
                scene_id=scene["id"],
                lcd_scene_controller=lcd_scene_controller,
                title=(scene["title"] if "title" in scene else None),
            )
            continue
        if scene_type == "custom":
            scenes[scene["id"]] = custom_scenes[scene["custom scene id"]]

    for item in item_config:
        if item["type"] == "LCDItem":
            items[item["id"]] = LCDItem(
                title=item["title"],
                item_id=item["id"],
                target=(scenes[item["target"]] if "target" in item else None),
            )
            continue

        items[item["id"]] = WeConnectLCDItem(
            data_provider=vehicle.get_data_property(item["data provider id"]),
            title=(item["title"]),
            item_id=item["id"],
            second_title=(item["2nd title"] if "2nd title" in item else None),
            translate=item["translate"],
        )

    for scene in scene_config:
        for item_id in scene["items"]:
            scenes[scene["id"]].add_item(items[item_id])

    return scenes
