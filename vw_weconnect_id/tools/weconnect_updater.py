from threading import Timer
from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
from build_tools.config_loader import load_config
import logging
from weconnect.domain import Domain
from datetime import datetime, time
from display.lcd_controller import LCDController
from led.led_driver import create_led_driver


LOG = logging.getLogger("weconnect_updater")


class WeConnectUpdaterError(Exception):
    pass


class WeConnectUpdater:

    UPDATE_VALUES = [Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]

    def __init__(
        self, weconnect: WeConnect, lcd_controller: LCDController, start_on_init=True
    ) -> None:
        LOG.debug("Initializing WeConnectUpdater")
        self.__weconnect = weconnect
        self.__lcd_controller = lcd_controller
        self.__update_led = create_led_driver(
            led_pin=5, led_id="WECONNECT UPDATE", default_frequency=10
        )
        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()
        self.__config = load_config()["update rate"]
        self.__can_update = True
        if start_on_init:
            self.start()

    def add_new_scheduler(
        self,
        scheduler_id: str,
        update_values: list,
        interval: int,
        callback_function: callable
    ) -> None:
        LOG.info(f"Adding new update scheduler (ID: {scheduler_id})")
        try:
            self.__scheduler.add_job(
                self.update_weconnect,
                trigger="interval",
                args=[update_values, callback_function],
                seconds=interval,
                id=scheduler_id,
            )
        except ConflictingIdError as e:
            LOG.error(f"Update scheduler (ID: {scheduler_id}) already exists")
            raise e

    def remove_scheduler(self, scheduler_id: str, called_from) -> None:
        LOG.info(f"Removing update scheduler (ID: {scheduler_id})")
        try:
            self.__scheduler.remove_job(job_id=scheduler_id)
        except KeyError as e:
            LOG.error(f"Couldn't find update scheduler (ID: {scheduler_id})")
            raise e

    def __update(self, update_domains: list) -> None:
        try:
            self.__weconnect.update(
                updatePictures=False,
                updateCapabilities=(True if Domain.ALL in update_domains else False),
                selective=update_domains,
            )
        except Exception as e:
            LOG.exception(e)

    def update_weconnect(self, update_domains: list, callback_function=None) -> None:
        LOG.debug("Updating WeConnect data from server")

        if not self.__can_update:
            LOG.error("Cannot update weconnect because updater faced timeout recently")
            self.__update_led.blink(frequency=20)
            Timer(interval=2, function=self.__update_led.turn_on).start()
            self.__lcd_controller.display_message(
                "Cannot update WeConnect right now", time_on_screen=3
            )
            return

        self.__update_led.blink()

        try:
            self.__weconnect.update(
                updatePictures=False,
                updateCapabilities=(True if Domain.ALL in update_domains else False),
                selective=update_domains,
            )
        except Exception:
            self.__can_update = False
            self.__scheduler.remove_all_jobs()

            Timer(function=self.start, interval=60).start()
            self.__update_led.turn_on()

            self.__lcd_controller.display_message(
                message="Failed to update weconnect data", time_on_screen=5
            )
            self.__lcd_controller.display_message(
                message="Trying again in 1 minute", time_on_screen=5
            )
            return

        LOG.debug("Successfully updated WeConnect data")
        self.__update_led.stop_blinking()
        if callback_function is not None:
            callback_function()

    def add_daytime_scheduler(self) -> None:
        self.__remove_nighttime_scheduler()
        LOG.debug("Enabling daytime update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["day"],
            id="DAYTIME",
            args=[self.UPDATE_VALUES],
        )

    def __remove_daytime_scheduler(self) -> None:
        LOG.debug("Disabling daytime update scheduler")
        try:
            self.__scheduler.remove_job(job_id="DAYTIME")
        except KeyError:
            LOG.exception(
                "'DAYTIME' update scheduler was not found, this is normal at startup"
            )

    def add_nighttime_scheduler(self) -> None:
        self.__remove_daytime_scheduler()
        LOG.debug("Enabling nighttime update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["night"],
            id="NIGHTTIME",
            args=[self.UPDATE_VALUES],
        )

    def __remove_nighttime_scheduler(self) -> None:
        LOG.debug("Disabling nighttime update scheduler")
        try:
            self.__scheduler.remove_job(job_id="NIGHTTIME")
        except KeyError:
            LOG.exception(
                "'NIGHTTIME' update scheduler was not found, this is normal at startup"
            )

    def __add_total_update_scheduler(self) -> None:
        LOG.debug("Enabling total update scheduler")
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            args=[[Domain.ALL]],
            hours=1,
            id="TOTALUPDATE",
        )

    def __add_switcher_schedulers(self) -> None:
        LOG.debug("Enabling switcher schedulers")
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
        LOG.debug("Starting weconnect updater")
        if not self.__can_update:
            self.__can_update = True
        start = time(7, 0, 0)
        end = time(23, 00, 0)
        now = datetime.now().time()
        if start <= now and now <= end:
            self.add_daytime_scheduler()
        else:
            self.add_nighttime_scheduler()
        self.__add_total_update_scheduler()
        self.__add_switcher_schedulers()
