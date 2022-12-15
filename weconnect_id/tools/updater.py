from threading import Timer
from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
import logging
from weconnect.domain import Domain
from datetime import datetime
from led.led_driver import create_led_driver


LOG = logging.getLogger("weconnect_updater")


class WeConnectUpdaterError(Exception):
    pass


class WeConnectUpdater:

    DOMAINS = [Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]

    def __init__(self, weconnect: WeConnect, config: dict) -> None:
        self.__weconnect = weconnect
        self.__update_led = create_led_driver(
            pin=config["pin layout"]["led updater"],
            id="WECONNECT UPDATE",
            default_frequency=10,
        )

        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()

        self.__config = config["update rate"]
        self.__nighttime = datetime.strptime(config["nighttime"], "%H.%M.%S")
        self.__daytime = datetime.strptime(config["daytime"], "%H.%M.%S")

        self.update_weconnect(domains=[Domain.ALL])

        self.__start()

    def add_scheduler(self, id: str, domains: list, interval: int) -> None:
        try:
            self.__scheduler.add_job(
                self.update_weconnect,
                trigger="interval",
                args=[domains],
                seconds=interval,
                id=id,
            )
        except ConflictingIdError as e:
            raise e

    def remove_scheduler(self, id: str) -> None:
        try:
            self.__scheduler.remove_job(job_id=id)
        except KeyError as e:
            raise e

    def update_weconnect(self, domains: list) -> None:

        self.__update_led.blink()

        try:
            self.__weconnect.update(
                updatePictures=False,
                updateCapabilities=(True if Domain.ALL in domains else False),
                selective=domains,
            )

        except Exception as e:
            LOG.exception(e)
            self.__scheduler.pause()
            Timer(function=self.__scheduler.resume, interval=60).start()
            self.__update_led.turn_on()
            raise e

        if self.__scheduler.state == 2:
            self.__scheduler.resume()

        self.__update_led.stop_blinking()

    def __add_daytime_scheduler(self) -> None:
        self.__remove_nighttime_scheduler()
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["day"],
            id="DAYTIME",
            args=[self.DOMAINS],
        )

    def __remove_daytime_scheduler(self) -> None:
        try:
            self.__scheduler.remove_job(job_id="DAYTIME")
        except KeyError:
            pass

    def __add_nighttime_scheduler(self) -> None:
        self.__remove_daytime_scheduler()
        self.__scheduler.add_job(
            self.update_weconnect,
            "interval",
            seconds=self.__config["night"],
            id="NIGHTTIME",
            args=[self.DOMAINS],
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
            self.__add_daytime_scheduler,
            trigger="cron",
            hour=self.__daytime.hour,
            minute=self.__daytime.minute,
            second=self.__daytime.second,
            id="DAYTIME_ENABLER",
        )
        self.__scheduler.add_job(
            self.__add_nighttime_scheduler,
            trigger="cron",
            hour=self.__nighttime.hour,
            minute=self.__nighttime.minute,
            second=self.__nighttime.second,
            id="NIGHTTIME_ENABLER",
        )

    def __start(self) -> None:
        start = self.__daytime.time()
        end = self.__nighttime.time()
        now = datetime.now().time()
        if start <= now and now <= end:
            self.__add_daytime_scheduler()
        else:
            self.__add_nighttime_scheduler()
        self.__add_total_update_scheduler()
        self.__add_switcher_schedulers()

    @property
    def weconnect(self) -> WeConnect:
        return self.__weconnect
