from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from weconnect_id.tools.updater import WeConnectUpdater
    from weconnect_id.vehicle import WeConnectVehicle
    from display.lcd_scene_controller import LCDSceneController
from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem
from display.weconnect_lcd_item import WeConnectLCDItem
from display.lcd_status_bar import LCDStatusBar
from display.custom_scenes.climate_controller_temperature_scene import (
    ClimateControllerTemperatureScene,
)
from electricity_price.spot_price_provider import SpotPriceProvider
from weconnect.domain import Domain
import logging


LOG = logging.getLogger("scene_builder")


class SceneBuilder:
    def __init__(
        self,
        config: dict,
        weconnect_updater: WeConnectUpdater,
        lcd_scene_controller: LCDSceneController,
        spot_price_provider: SpotPriceProvider,
    ) -> None:
        '''
        Builds the scenes used in the user interface.

        Args:
            config (dict): Contains configurations for the created LCDItems and LCDScenes.
            weconnect_updater (WeConnectUpdater): Needed to initialize WeConnectLCDItems.
            lcd_scene_controller (LCDSceneController): Needed to initialize LCDScenes.
            spot_price_provider (SpotPriceProvider): Provides data to the electricity price items.
        '''
        
        self.__config = config
        self.__scene_config = config["lcd scenes"]
        self.__item_config = config["lcd items"]
        self.__weconnect_updater = weconnect_updater
        self.__lcd_scene_controller = lcd_scene_controller
        self.__spot_price_provider = spot_price_provider

    def load_scenes(self, weconnect_vehicle: WeConnectVehicle) -> dict:
        '''
        Builds the scenes for the user interface.

        Args:
            weconnect_vehicle (WeConnectVehicle): Provides necessary objects and functions for the WeConnectLCDItems and some LCDScenes.

        Returns:
            dict: Returns dict where scenes are stored in ID - LCDScene pairs.
        '''
        
        LOG.debug(f"Loading LCDScenes. Selected vehicle: ({weconnect_vehicle.nickname})")
        
        custom_scenes = {
            "climate temperature": ClimateControllerTemperatureScene(
                lcd_scene_controller=self.__lcd_scene_controller,
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
                target=self.__weconnect_updater.update,
                target_args=[[Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]],
            ),
            "spot price now": self.__spot_price_provider.price_now_item,
        }

        scenes = {}
        items = {}

        for scene in self.__scene_config:
            scene_type = scene["type"]
            if scene_type == "normal":
                scenes[scene["id"]] = LCDScene(
                    id=scene["id"],
                    lcd_scene_controller=self.__lcd_scene_controller,
                    title=(scene["title"] if "title" in scene else None),
                    items_selectable=scene["items selectable"],
                )
            elif scene_type == "custom":
                scenes[scene["id"]] = custom_scenes[scene["custom scene id"]]

        for item in self.__item_config:
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
                    content_centering=item["content centering"],
                    target=(scenes[item["target"]] if "target" in item else None),
                )
            elif item["type"] == "custom":
                items[item["id"]] = custom_items[item["custom item id"]]

        for scene in self.__scene_config:
            if scene["type"] == "custom":
                continue
            for item_id in scene["items"]:
                scenes[scene["id"]].add_item(items[item_id])

        self.__lcd_scene_controller.set_home_scene(scenes[self.__config["home scene"]])

        lcd_status_bar = LCDStatusBar(
            weconnect_vehicle=weconnect_vehicle,
            lcd_scene_controller=self.__lcd_scene_controller,
        )
        self.__lcd_scene_controller.set_status_bar(lcd_status_bar)

        LOG.debug("Successfully loaded LCDScenes")
        
        return scenes
