from threading import Timer
from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
import logging
from weconnect.domain import Domain
from datetime import datetime, time
from led.led_driver import create_led_driver


LOG = logging.getLogger("weconnect_updater")


class WeConnectUpdaterError(Exception):
    pass


class WeConnectUpdater:

    UPDATE_VALUES = [Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]

    def __init__(
        self,
        weconnect: WeConnect,
        config: dict,
        start_on_init=True,
    ) -> None:
        self.__weconnect = weconnect
        self.__update_led = create_led_driver(
            pin=23, id="WECONNECT UPDATE", default_frequency=10
        )

        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()

        self.__config = config["update rate"]
        self.__can_update = True

        self.update_weconnect(update_domains=[Domain.ALL])

        if start_on_init:
            self.start()

    def add_new_scheduler(
        self, id: str, update_values: list, interval: int
    ) -> None:
        LOG.info(f"Adding new update scheduler (ID: {id})")
        try:
            self.__scheduler.add_job(
                self.update_weconnect,
                trigger="interval",
                args=[update_values],
                seconds=interval,
                id=id,
            )
        except ConflictingIdError as e:
            LOG.error(f"Update scheduler (ID: {id}) already exists")
            raise e

    def remove_scheduler(self, id: str) -> None:
        LOG.info(f"Removing update scheduler (ID: {id})")
        try:
            self.__scheduler.remove_job(job_id=id)
        except KeyError as e:
            LOG.error(f"Couldn't find update scheduler (ID: {id})")
            raise e

    def update_weconnect(self, update_domains: list) -> None:
        if not self.__can_update:
            LOG.error("Cannot update WeConnect because updater faced timeout recently")
            self.__update_led.blink(frequency=20)
            Timer(interval=2, function=self.__update_led.turn_on).start()
            return

        self.__update_led.blink()

        try:
            self.__weconnect.update(
                updatePictures=False,
                updateCapabilities=(True if Domain.ALL in update_domains else False),
                selective=update_domains,
            )

        except Exception as e:
            LOG.exception(e)
            self.__can_update = False
            self.__scheduler.remove_all_jobs()
            Timer(function=self.start, interval=60).start()
            self.__update_led.turn_on()
            return

        self.__update_led.stop_blinking()

    def add_daytime_scheduler(self) -> None:
        self.__remove_nighttime_scheduler()
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["day"],
            id="DAYTIME",
            args=[self.UPDATE_VALUES],
        )

    def __remove_daytime_scheduler(self) -> None:
        try:
            self.__scheduler.remove_job(job_id="DAYTIME")
        except KeyError:
            pass

    def add_nighttime_scheduler(self) -> None:
        self.__remove_daytime_scheduler()
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["night"],
            id="NIGHTTIME",
            args=[self.UPDATE_VALUES],
        )

    def __remove_nighttime_scheduler(self) -> None:
        try:
            self.__scheduler.remove_job(job_id="NIGHTTIME")
        except KeyError:
            pass

    def __add_total_update_scheduler(self) -> None:
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

    @property
    def weconnect(self) -> WeConnect:
        return self.__weconnect
