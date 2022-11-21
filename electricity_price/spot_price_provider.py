import urllib.request
import json
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from display.lcd_item import LCDItem
from display.lcd_scene import LCDScene
from display.lcd_scene_controller import LCDSceneController


class SpotPriceProvider:
    def __init__(self, lcd_scene_controller: LCDSceneController) -> None:
        self.__prices = {}
        self.__price_now = None
        self.__price_now_item = None
        self.__price_items = None
        self.__prices_scene = LCDScene(
            id="scene_spot_price_list",
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
            id="spot price updater",
        )

    def __update(self) -> None:
        print("updating spot data")
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

    def __create_items(self) -> None:
        self.__price_items = {}
        hours = [str(i) if i > 9 else "0" + str(i) for i in range(24)]
        for hour in hours:
            self.__price_items[hour] = LCDItem(
                id=f"item_spot_price_{hour}",
                title=f"Tunti {hour}:",
                content_centering=False,
                second_title=str(self.__prices[hour]["PriceWithTax"]) + "C/kWh",
            )
            self.__prices_scene.add_item(self.__price_items[hour])

        self.__price_now_item = LCDItem(
            title="Hinta Nyt",
            id="item_spot_price_now",
            content_centering=False,
            second_title=str(self.__price_now) + "C",
            target=self.__prices_scene,
        )
        self.__items_created = True

    def __update_items(self) -> None:
        hours = [str(i) if i > 9 else "0" + str(i) for i in range(24)]
        for hour in hours:
            self.__price_items[hour].update_content(
                second_title=str(self.__prices[hour]["PriceWithTax"]) + "C/kWh",
            )
        self.__price_now_item.update_content(second_title=str(self.__price_now) + "C")

    @property
    def prices(self) -> dict:
        return self.__prices

    @property
    def scene(self) -> LCDScene:
        return self.__prices_scene

    @property
    def price_now_item(self) -> LCDItem:
        return self.__price_now_item
