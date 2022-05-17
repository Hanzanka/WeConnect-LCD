from threading import Thread, Timer
from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
from build_tools.config_loader import load_config
import logging
from weconnect.domain import Domain
from datetime import datetime, time
from display.lcd_controller import LCDController
from led.led_driver import create_led_driver


logger = logging.getLogger("weconnect_updater")


class WeConnectUpdater:

    UPDATE_VALUES = [Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]

    def __init__(
        self, weconnect: WeConnect, lcd_controller: LCDController, start_on_init=True
    ) -> None:
        logger.debug("Initializing WeConnectUpdater")
        self.__weconnect = weconnect
        self.__lcd_controller = lcd_controller
        self.__update_led = create_led_driver(
            led_pin=5, led_id="WECONNECT UPDATE", default_frequency=10
        )
        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()
        self.__config = load_config()["update rate"]
        self.__updater_related_objects = {}
        if start_on_init:
            self.start()

    def add_new_scheduler(
        self,
        scheduler_id: str,
        update_values: list,
        interval: int,
        callback_function: callable,
        called_from: object,
        at_lost_connection: callable,
    ) -> None:
        logger.info(f"Adding new update scheduler (ID: {scheduler_id})")
        if called_from not in self.__updater_related_objects:
            self.__updater_related_objects[called_from] = at_lost_connection
        try:
            self.__scheduler.add_job(
                self.update_weconnect,
                trigger="interval",
                args=[update_values, callback_function],
                seconds=interval,
                id=scheduler_id,
            )
        except ConflictingIdError as e:
            logger.error(f"Update scheduler (ID: {scheduler_id}) already exists")
            raise e

    def remove_scheduler(self, scheduler_id: str, called_from) -> None:
        logger.info(f"Removing update scheduler (ID: {scheduler_id})")
        try:
            self.__scheduler.remove_job(job_id=scheduler_id)
            if called_from in self.__updater_related_objects:
                self.__updater_related_objects.pop(called_from)
        except KeyError as e:
            logger.error(f"Couldn't find update scheduler (ID: {scheduler_id})")
            raise e

    def update_weconnect(self, update_domains: list, callback_function=None) -> None:
        logger.debug("Updating weconnect data from server")
        self.__update_led.blink()
        try:
            self.__weconnect.update(
                updatePictures=False,
                updateCapabilities=(True if Domain.ALL in update_domains else False),
                selective=update_domains,
            )
        except Exception:
            logger.exception(
                "Could not update weconnect data due to timeout, trying again in five minutes"
            )
            for function in self.__updater_related_objects.values():
                Thread(target=function).start()
            self.__updater_related_objects.clear()
            self.__scheduler.remove_all_jobs()
            Timer(target=self.start, interval=5 * 60).start()
            self.__update_led.turn_on()
            self.__lcd_controller.display_message(
                "Failed to update weconnect!", time_on_screen=5
            )
            self.__lcd_controller.display_message("Trying again in five minutes")
        self.__update_led.stop_blinking()
        if callback_function is not None:
            callback_function()

    def add_daytime_scheduler(self) -> None:
        self.__remove_nighttime_scheduler()
        logger.debug("Enabling daytime update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["day"],
            id="DAYTIME",
            args=[self.UPDATE_VALUES],
        )

    def __remove_daytime_scheduler(self) -> None:
        logger.debug("Disabling daytime update scheduler")
        try:
            self.__scheduler.remove_job(job_id="DAYTIME")
        except KeyError:
            logger.exception(
                "'DAYTIME' update scheduler was not found, this is normal at startup"
            )

    def add_nighttime_scheduler(self) -> None:
        self.__remove_daytime_scheduler()
        logger.debug("Enabling nighttime update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["night"],
            id="NIGHTTIME",
            args=[self.UPDATE_VALUES],
        )

    def __remove_nighttime_scheduler(self) -> None:
        logger.debug("Disabling nighttime update scheduler")
        try:
            self.__scheduler.remove_job(job_id="NIGHTTIME")
        except KeyError:
            logger.exception(
                "'NIGHTTIME' update scheduler was not found, this is normal at startup"
            )

    def __add_total_update_scheduler(self) -> None:
        logger.debug("Enabling total update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            args=[[Domain.ALL]],
            hours=1,
            id="TOTALUPDATE",
        )

    def __add_switcher_schedulers(self) -> None:
        logger.debug("Enabling switcher schedulers")
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
        logger.debug("Starting weconnect updater")
        start = time(7, 0, 0)
        end = time(23, 00, 0)
        now = datetime.now().time()
        if start <= now and now <= end:
            self.add_daytime_scheduler()
        else:
            self.add_nighttime_scheduler()
        self.__add_total_update_scheduler()
        self.__add_switcher_schedulers()
