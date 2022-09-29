import logging
from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem
from display.lcd_scene_controller import LCDSceneController
from display.weconnect_lcd_item import WeConnectLCDItem
from weconnect_id.vehicle import WeConnectVehicle
from display.custom_scenes.climate_controller_temperature_scene import (
    ClimateControllerTemperatureScene,
)
from weconnect_id.tools.weconnect_updater import WeConnectUpdater
from weconnect.domain import Domain


LOG = logging.getLogger("build_tools")


def load_scenes(
    config: dict,
    weconnect_vehicle: WeConnectVehicle,
    lcd_scene_controller: LCDSceneController,
    weconnect_updater: WeConnectUpdater,
) -> dict:
    LOG.debug("Loading LCDScenes from config-file")
    scene_config = config["lcd scenes"]
    item_config = config["lcd items"]

    custom_scenes = {
        "climate temperature": ClimateControllerTemperatureScene(
            lcd_scene_controller=lcd_scene_controller,
            id="climate settings",
            weconnect_vehicle=weconnect_vehicle,
        )
    }
    custom_items = {
        "climate controller starter": LCDItem(
            title="Ilmastointi start",
            id="item_climate_start",
            target=weconnect_vehicle.start_climate_control,
        ),
        "climate controller stopper": LCDItem(
            title="Ilmastointi stop",
            id="item_climate_stop",
            target=weconnect_vehicle.stop_climate_control,
        ),
        "update weconnect": LCDItem(
            title="Päivitä nyt",
            id="item_weconnect_update_now",
            target=weconnect_updater.update_weconnect,
            target_args=[[Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]],
        ),
    }

    scenes = {}
    items = {}

    for scene in scene_config:
        scene_type = scene["type"]
        if scene_type == "normal":
            scenes[scene["id"]] = LCDScene(
                id=scene["id"],
                lcd_scene_controller=lcd_scene_controller,
                title=(scene["title"] if "title" in scene else None),
                items_selectable=scene["items selectable"],
            )
        elif scene_type == "custom":
            scenes[scene["id"]] = custom_scenes[scene["custom scene id"]]

    for item in item_config:
        if item["type"] == "LCDItem":
            items[item["id"]] = LCDItem(
                title=item["title"],
                id=item["id"],
                target=(scenes[item["target"]] if "target" in item else None),
            )
        elif item["type"] == "WeConnectLCDItem":
            items[item["id"]] = WeConnectLCDItem(
                data_provider=weconnect_vehicle.get_data_property(
                    item["data provider id"]
                ),
                title=(item["title"]),
                id=item["id"],
                translate=item["translate"],
            )
        elif item["type"] == "custom":
            items[item["id"]] = custom_items[item["custom item id"]]

    for scene in scene_config:
        if scene["type"] == "custom":
            continue
        for item_id in scene["items"]:
            scenes[scene["id"]].add_item(items[item_id])

    return scenes
