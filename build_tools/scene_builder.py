import logging
from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem
from display.lcd_scene_controller import LCDSceneController
from display.weconnect_lcd_item import WeConnectLCDItem
from vw_weconnect_id.vehicle import VolkswagenIdVehicle
from display.custom_scenes.climate_controller_temperature_scene import (
    ClimateControllerTemperatureScene,
)
from vw_weconnect_id.tools.weconnect_updater import WeConnectUpdater
from weconnect.domain import Domain


LOG = logging.getLogger("build_tools")


def load_scenes(
    config: dict,
    vehicle: VolkswagenIdVehicle,
    lcd_scene_controller: LCDSceneController,
    updater: WeConnectUpdater,
) -> dict:
    LOG.debug("Loading LCDScenes from config-file")
    scene_config = config["lcd scenes"]
    item_config = config["lcd items"]

    custom_scenes = {
        "climate temperature": ClimateControllerTemperatureScene(
            lcd_scene_controller=lcd_scene_controller,
            scene_id="climate settings",
            vehicle=vehicle,
        )
    }
    custom_items = {
        "climate controller starter": LCDItem(
            title="Ilmastointi start",
            item_id="item_climate_start",
            target=vehicle.start_climate_control,
        ),
        "climate controller stopper": LCDItem(
            title="Ilmastointi stop",
            item_id="item_climate_stop",
            target=vehicle.stop_climate_control,
        ),
        "update weconnect": LCDItem(
            title="Päivitä nyt",
            item_id="item_weconnect_update_now",
            target=updater.update_weconnect,
            target_args=[[Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]],
        ),
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
        elif scene_type == "custom":
            scenes[scene["id"]] = custom_scenes[scene["custom scene id"]]

    for item in item_config:
        if item["type"] == "LCDItem":
            items[item["id"]] = LCDItem(
                title=item["title"],
                item_id=item["id"],
                target=(scenes[item["target"]] if "target" in item else None),
            )
        elif item["type"] == "WeConnectLCDItem":
            items[item["id"]] = WeConnectLCDItem(
                data_provider=vehicle.get_data_property(item["data provider id"]),
                title=(item["title"]),
                item_id=item["id"],
                translate=item["translate"],
            )
        elif item["type"] == "custom":
            items[item["id"]] = custom_items[item["custom item id"]]

    for scene in scene_config:
        for item_id in scene["items"]:
            scenes[scene["id"]].add_item(items[item_id])

    return scenes
