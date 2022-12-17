from threading import Timer
from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
import logging
from weconnect.domain import Domain
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

        self.__update_rate = config["update rate"]
        self.__silent_main_update = config["silent main update"]

        self.update(domains=[Domain.ALL])

        self.__start_main_update_scheduler()
        self.__start_total_update_scheduler()

    def add_scheduler(self, id: str, domains: list, interval: int, silent: bool) -> None:
        try:
            self.__scheduler.add_job(
                id=id,
                func=self.update,
                args=[domains, silent],
                trigger="interval",
                seconds=interval,
            )
        except ConflictingIdError as e:
            raise e

    def remove_scheduler(self, id: str) -> None:
        try:
            self.__scheduler.remove_job(job_id=id)
        except KeyError as e:
            raise e

    def update(self, domains: list, silent: bool = False) -> None:

        if not silent:
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

        if not silent:
            self.__update_led.stop_blinking()

        if self.__scheduler.state == 2:
            self.__scheduler.resume()

    def __start_main_update_scheduler(self) -> None:
        self.__scheduler.add_job(
            id="MAIN UPDATE SCHEDULER",
            func=self.update,
            args=[self.DOMAINS, self.__silent_main_update],
            trigger="interval",
            seconds=self.__update_rate,
        )

    def __start_total_update_scheduler(self) -> None:
        self.__scheduler.add_job(
            id="TOTALUPDATE",
            func=self.update,
            args=[[Domain.ALL], self.__silent_main_update],
            trigger="interval",
            hours=1,
        )

    @property
    def weconnect(self) -> WeConnect:
        return self.__weconnect
