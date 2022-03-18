from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from config_loader import load_config
import logging
from weconnect.domain import Domain
from datetime import datetime, time
from led_tools.led_controller import IndicatorLEDController, LEDDriverError


class WeConnectUpdater:

    UPDATE_VALUES = [Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]

    def __init__(self, weconnect: WeConnect, led_controller: IndicatorLEDController, start_on_init=True) -> None:
        self.__weconnect = weconnect
        self.__update_led = led_controller.create_independent_leddriver(pin=5, led_id="WECONNECT UPDATE", default_frequency=10.0)
        self.update_weconnect([Domain.ALL])
        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()
        self.__config = load_config()["update rate"]
        if start_on_init:
            self.start()

    def add_new_scheduler(self, id: str, update_values: list, callback_function: callable) -> None:
        logging.info("Enabling climatecontroller scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            trigger="interval",
            args=[update_values, callback_function],
            seconds=15,
            id=id,
        )

    def remove_scheduler(self, id: str) -> None:
        logging.info("Enabling climatecontroller scheduler")
        try:
            self.__scheduler.remove_job(job_id=id)
        except KeyError:
            logging.error("Couldn't find job with key 'CLIMATE'")

    def update_weconnect(self, update_domains: list, callback_function=None) -> None:
        logging.info("Updating weconnect")
        try:
            self.__update_led.blink()
        except LEDDriverError as e:
            logging.error(e.message)
        self.__weconnect.update(
            updatePictures=False,
            updateCapabilities=(True if Domain.ALL in update_domains else False),
            selective=update_domains,
        )
        try:
            self.__update_led.stop_blinking()
        except LEDDriverError as e:
            logging.error(e.message)
        if callback_function is not None:
            callback_function()

    def __add_daytime_scheduler(self) -> None:
        self.__remove_nighttime_scheduler()
        logging.info("Enabling daytime scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["day"],
            id="DAYTIME",
            args=[self.UPDATE_VALUES]
        )

    def __remove_daytime_scheduler(self) -> None:
        logging.info("Disabling daytime scheduler")
        try:
            self.__scheduler.remove_job(job_id="DAYTIME")
        except KeyError:
            logging.error("DAYTIME job was not found, this is normal at startup")

    def __add_nighttime_scheduler(self) -> None:
        self.__remove_daytime_scheduler()
        logging.info("Enabling nighttime scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["night"],
            id="NIGHTTIME",
            args=[self.UPDATE_VALUES]
        )

    def __remove_nighttime_scheduler(self) -> None:
        logging.info("Disabling nighttime scheduler")
        try:
            self.__scheduler.remove_job(job_id="NIGHTTIME")
        except KeyError:
            logging.error("NIGHTTIME job was not found, this is normal at startup")

    def __add_total_update_scheduler(self) -> None:
        logging.info("Enabling total update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            args=[[Domain.ALL]],
            hours=1,
            id="TOTALUPDATE",
        )

    def __add_switcher_schedulers(self) -> None:
        self.__scheduler.add_job(
            self.__add_daytime_scheduler,
            trigger="cron",
            minute=0,
            hour=7,
            id="DAYTIME_ENABLER",
        )
        self.__scheduler.add_job(
            self.__add_nighttime_scheduler,
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
            self.__add_daytime_scheduler()
        else:
            self.__add_nighttime_scheduler()
        self.__add_total_update_scheduler()
        self.__add_switcher_schedulers()
