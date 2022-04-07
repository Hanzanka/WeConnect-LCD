from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from config_loader import load_config
from logging import Logger
from weconnect.domain import Domain
from datetime import datetime, time
from led_tools.led_controller import IndicatorLEDController


logger = Logger("main logger")


class WeConnectUpdater:

    UPDATE_VALUES = [Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]

    def __init__(self, weconnect: WeConnect, led_controller: IndicatorLEDController, start_on_init=True) -> None:
        self.__weconnect = weconnect
        self.__update_led = led_controller.create_independent_leddriver(pin=5, led_id="WECONNECT UPDATE", default_frequency=10.0)
        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()
        self.__config = load_config()["update rate"]
        if start_on_init:
            self.start()

    def add_new_scheduler(self, id: str, update_values: list, callback_function: callable) -> None:
        logger.info(f"Adding new update scheduler with id '{id}'")
        self.__scheduler.add_job(
            self.update_weconnect,
            trigger="interval",
            args=[update_values, callback_function],
            seconds=15,
            id=id,
        )

    def remove_scheduler(self, id: str) -> None:
        try:
            logger.info(f"Removing update scheduler with id '{id}'")
            self.__scheduler.remove_job(job_id=id)
        except KeyError:
            logger.error(f"Couldn't find update scheduler with id '{id}'")

    def update_weconnect(self, update_domains: list) -> None:
        logger.info("Updating weconnect data")
        self.__update_led.blink()
        self.__weconnect.update(
            updatePictures=False,
            updateCapabilities=(True if Domain.ALL in update_domains else False),
            selective=update_domains,
        )
        self.__update_led.stop_blinking()

    def add_daytime_scheduler(self) -> None:
        self.__remove_nighttime_scheduler()
        logger.info("Enabling daytime update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["day"],
            id="DAYTIME",
            args=[self.UPDATE_VALUES]
        )

    def __remove_daytime_scheduler(self) -> None:
        logger.info("Disabling daytime update scheduler")
        try:
            self.__scheduler.remove_job(job_id="DAYTIME")
        except KeyError:
            logger.error("DAYTIME update scheduler was not found, this is normal at startup")

    def add_nighttime_scheduler(self) -> None:
        self.__remove_daytime_scheduler()
        logger.info("Enabling nighttime update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["night"],
            id="NIGHTTIME",
            args=[self.UPDATE_VALUES]
        )

    def __remove_nighttime_scheduler(self) -> None:
        logger.info("Disabling nighttime update scheduler")
        try:
            self.__scheduler.remove_job(job_id="NIGHTTIME")
        except KeyError:
            logger.error("NIGHTTIME update scheduler was not found, this is normal at startup")

    def __add_total_update_scheduler(self) -> None:
        logger.info("Enabling total update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            args=[[Domain.ALL]],
            hours=1,
            id="TOTALUPDATE",
        )

    def __add_switcher_schedulers(self) -> None:
        self.__scheduler.add_job(
            self.add_daytime_scheduler,
            trigger="cron",
            minute=0,
            hour=7,
            id="DAYTIME_ENABLER",
        )
        self.__scheduler.add_job(
            self.add_nighttime_scheduler,
            trigger="cron",
            minute=0,
            hour=23,
            id="NIGHTTIME_ENABLER",
        )

    def start(self) -> None:
        start = time(7, 0, 0)
        end = time(23, 00, 0)
        now = datetime.now().time()
        if start <= now and now <= end:
            self.add_daytime_scheduler()
        else:
            self.add_nighttime_scheduler()
        self.__add_total_update_scheduler()
        self.__add_switcher_schedulers()
