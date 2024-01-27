from threading import Timer
from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
import logging
from weconnect.domain import Domain
from led.led_driver import create_led_driver, LEDDriver


LOG = logging.getLogger("weconnect_updater")


class WeConnectUpdaterError(Exception):
    pass


class WeConnectUpdater:
    DOMAINS = [Domain.CHARGING, Domain.CLIMATISATION, Domain.READINESS]

    def __init__(self, weconnect: WeConnect, config: dict) -> None:
        """
        Used to update the data for the app from the server.

        Args:
            weconnect (WeConnect): WeConnect-API instance which is used to update data from server.
            config (dict): Configuration dict for the updater.
        """

        LOG.debug("Initializing WeConnectUpdater")
        self.__weconnect = weconnect
        self.__update_led = create_led_driver(
            pin=config["pin layout"]["led updater"],
            id="LED_WECONNECT_UPDATE",
            default_frequency=10,
        )

        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()

        self.__update_rate = config["update rate"]
        self.__silent_main_update = config["silent main update"]

        self.update(domains=[Domain.ALL])

        self.__start_main_update_scheduler()
        self.__start_total_update_scheduler()

    def add_scheduler(
        self, id: str, domains: list, interval: int, silent: bool, run_immediately: bool = True
    ) -> None:
        LOG.debug(f"Adding WeConnectUpdater scheduler (ID: {id})")
        try:
            self.__scheduler.add_job(
                id=id,
                func=self.update,
                args=[domains, silent],
                trigger="interval",
                seconds=interval,
                max_instances=1,
            )
        except ConflictingIdError as e:
            LOG.exception(f"WeConnectUpdater scheduler with (ID: {id}) already exists")
            raise e
        if run_immediately:
            self.update(domains=domains, silent=silent)

    def remove_scheduler(self, id: str) -> None:
        LOG.debug(f"Removing WeConnectUpdater scheduler (ID: {id})")
        try:
            self.__scheduler.remove_job(job_id=id)
        except KeyError as e:
            LOG.exception(f"WeConnectUpdater scheduler (ID: {id}) doesn't exist")
            raise e

    def update(self, domains: list, silent: bool = False) -> None:
        LOG.debug(f"Updating WeConnect data (Domains: {domains})")
        if not silent:
            self.__update_led.blink()

        try:
            self.__weconnect.update(
                updatePictures=False,
                updateCapabilities=(True if Domain.ALL in domains else False),
                selective=domains,
            )
            if self.__update_led.state == LEDDriver.LEDState.ON:
                self.__update_led.turn_off()

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
            
        LOG.debug(f"Successfully updated WeConnect data (Domains: {domains})")

    def __start_main_update_scheduler(self) -> None:
        self.__scheduler.add_job(
            id="MAIN_UPDATE_SCHEDULER",
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
