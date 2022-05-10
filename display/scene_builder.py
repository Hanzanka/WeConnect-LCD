import logging
from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem
from display.lcd_scene_controller import LCDSceneController
from display.weconnect_lcd_item import WeConnectLCDItem
from vw_weconnect_id.vehicle import VolkswagenIdVehicle


logger = logging.getLogger("display")


def load_scenes(
    config: dict, vehicle: VolkswagenIdVehicle, lcd_scene_controller: LCDSceneController
) -> dict:
    logger.debug("Loading lcd scenes from config file")
    scene_config = config["lcd scenes"]
    item_config = config["lcd items"]

    scenes = {}
    items = {}

    for scene in scene_config:
        scenes[scene["id"]] = LCDScene(
            id=scene["id"],
            lcd_scene_controller=lcd_scene_controller,
            title=(scene["title"] if "title" in scene else None),
        )

    for item in item_config:
        if item["type"] == "LCDItem":
            items[item["id"]] = LCDItem(
                title=item["title"],
                target=(scenes[item["target"]] if "target" in item else None),
            )
            continue

        items[item["id"]] = WeConnectLCDItem(
            data_provider=vehicle.get_data_property(item["data provider id"]),
            title=(item["title"]),
            second_title=(item["2nd title"] if "2nd title" in item else None),
            translate=item["translate"],
        )

    for scene in scene_config:
        for item_id in scene["items"]:
            scenes[scene["id"]].add_item(items[item_id])

    return scenes
