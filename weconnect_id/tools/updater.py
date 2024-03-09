from threading import Timer
from weconnect.weconnect import WeConnect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
import logging
from weconnect.domain import Domain
from led.led_driver import create_led_driver, LEDDriver
import os


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

        self.__base_job_running = {}
        self.__executions_skipped = 0
        self.__job_restarts = 0

        self.__scheduler = BackgroundScheduler(timezone="Europe/Helsinki")
        self.__scheduler.start()

        self.__update_rate = config["update rate"]
        self.__silent_main_update = config["silent main update"]

        self.update(domains=[Domain.ALL])

        self.__start_main_update_scheduler()
        self.__start_total_update_scheduler()

    def add_scheduler(
        self,
        id: str,
        domains: list,
        interval: int,
        silent: bool,
        run_immediately: bool = True,
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

    def update(self, domains: list, silent: bool = False, job_id: str = None) -> None:
        LOG.debug(f"Updating WeConnect data (Domains: {domains})")
        if job_id is not None:
            if self.__base_job_running[job_id]:
                self.__on_max_instances_reached(job_id=job_id)
                return
            self.__base_job_running[job_id] = True

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

            if job_id is not None:
                self.__base_job_running[job_id] = False

            self.__scheduler.pause()
            Timer(function=self.__scheduler.resume, interval=60).start()
            self.__update_led.turn_on()
            raise e

        if not silent:
            self.__update_led.stop_blinking()

        if self.__scheduler.state == 2:
            self.__scheduler.resume()

        if job_id is not None:
            self.__base_job_running[job_id] = False

        LOG.debug(f"Successfully updated WeConnect data (Domains: {domains})")

    def __start_main_update_scheduler(self) -> None:
        self.__base_job_running["MAIN_UPDATE_SCHEDULER"] = False
        self.__scheduler.add_job(
            id="MAIN_UPDATE_SCHEDULER",
            func=self.update,
            args=[self.DOMAINS, self.__silent_main_update, "MAIN_UPDATE_SCHEDULER"],
            trigger="interval",
            seconds=self.__update_rate,
            max_instances=999,
            replace_existing=True,
        )

    def __start_total_update_scheduler(self) -> None:
        self.__base_job_running["TOTALUPDATE"] = False
        self.__scheduler.add_job(
            id="TOTALUPDATE",
            func=self.update,
            args=[[Domain.ALL], self.__silent_main_update, "TOTALUPDATE"],
            trigger="interval",
            hours=1,
            max_instances=999,
            replace_existing=True,
        )

    def __on_max_instances_reached(self, job_id: str) -> None:
        self.__executions_skipped += 1
        LOG.error(
            f"Other WeConnectUpdater job with (ID: {job_id})"
            + f" was running (Skipped executions: {self.__executions_skipped})"
            + f" (Job restarts: {self.__job_restarts})"
        )
        if self.__executions_skipped >= 5:
            LOG.info(
                "Restarting WeConnectUpdater jobs"
            )
            self.__scheduler.remove_job(job_id="MAIN_UPDATE_SCHEDULER")
            self.__scheduler.remove_job(job_id="TOTALUPDATE")
            self.__start_main_update_scheduler()
            self.__start_total_update_scheduler()

            self.__executions_skipped = 0
            self.__job_restarts += 1

        if self.__job_restarts >= 5:
            LOG.info("Rebooting system due too many restarted jobs")
            os.system("sudo reboot")

    @property
    def weconnect(self) -> WeConnect:
        return self.__weconnect
