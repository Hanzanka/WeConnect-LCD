from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from display.lcd_scene_controller import LCDSceneController
from display.lcd_scene import LCDScene
from display.lcd_item import LCDItem
import urllib.request
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import logging


LOG = logging.getLogger("spot_price_provider")


class SpotPriceProvider:
    def __init__(self, lcd_scene_controller: LCDSceneController) -> None:
        '''
        Gets current electricity prices in Finland.

        Args:
            lcd_scene_controller (LCDSceneController): Used to display electricity prices on the LCD screen.
        '''
        
        LOG.debug("Initializing SpotPriceProvider")
        self.__prices = {}
        self.__price_now = None
        self.__price_now_item = None
        self.__price_items = None
        self.__prices_scene = LCDScene(
            id="SCENE_SPOT_PRICE_LIST",
            items_selectable=False,
            lcd_scene_controller=lcd_scene_controller,
        )
        self.__items_created = False
        self.__update()
        self.__create_items()
        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()
        self.__scheduler.add_job(
            func=self.__update,
            trigger="cron",
            minute="0, 15, 30, 45",
            id="SPOT_PRICE_UPDATER",
        )
        LOG.debug("Successfully initialized SpotPriceProvider")

    def __update(self) -> None:
        LOG.debug("Updating SpotPriceProvider data")
        with urllib.request.urlopen("https://api.spot-hinta.fi/Today") as url:
            data = json.loads(url.read().decode())

        for item in data:
            item["PriceWithTax"] = round(item["PriceWithTax"] * 100, 2)
            item["PriceNoTax"] = round(item["PriceNoTax"] * 100, 2)
            self.__prices[
                datetime.strptime(item["DateTime"], "%Y-%m-%dT%H:%M:%S%z").strftime(
                    "%H"
                )
            ] = item

        self.__price_now = self.__prices[datetime.now().strftime("%H")]["PriceWithTax"]
        if self.__items_created:
            self.__update_items()
        LOG.debug("Successfully updated SpotPriceProvider data")

    def __create_items(self) -> None:
        self.__price_items = {}
        hours = [str(i) if i > 9 else "0" + str(i) for i in range(24)]
        for hour in hours:
            self.__price_items[hour] = LCDItem(
                id=f"ITEM_SPOT_PRICE_{hour}",
                title=f"Tunti {hour}:",
                content_centering=False,
                second_title=str(self.__prices[hour]["PriceWithTax"]) + "C/kWh",
            )
            self.__prices_scene.add_item(self.__price_items[hour])

        self.__price_now_item = LCDItem(
            title="Hinta Nyt",
            id="ITEM_SPOT_PRICE_NOW",
            content_centering=False,
            second_title=str(self.__price_now) + "C/kWh",
            target=self.__prices_scene,
        )
        self.__items_created = True

    def __update_items(self) -> None:
        hours = [str(i) if i > 9 else "0" + str(i) for i in range(24)]
        for hour in hours:
            self.__price_items[hour].update_content(
                second_title=str(self.__prices[hour]["PriceWithTax"]) + "C/kWh",
            )
        self.__price_now_item.update_content(second_title=str(self.__price_now) + "C/kWh")

    @property
    def prices(self) -> dict:
        return self.__prices

    @property
    def scene(self) -> LCDScene:
        return self.__prices_scene

    @property
    def price_now_item(self) -> LCDItem:
        return self.__price_now_item
