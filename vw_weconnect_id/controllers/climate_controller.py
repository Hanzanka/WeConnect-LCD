from weconnect.elements.vehicle import Vehicle
from weconnect.elements.control_operation import ControlOperation
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.weconnect import WeConnect
import logging
from weconnect.elements.generic_status import GenericStatus
from threading import Timer
import numpy
from datetime import datetime


class ClimateControllerCompabilityError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
        self.message = message


class ClimateControlAlreadyOnError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
        self.message = message


class NoMatchingIdError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
        self.message = message


class OperationAlreadyRunningError(Exception):
    def __init__(self, message) -> None:
        super.__init__(message)
        self.message = message


class RequestFailedError(Exception):
    def __init__(self, message) -> None:
        super.__init__(message)
        self.message = message


class FailedToSetTemperatureError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
        self.message = message


class FailedToIdentifyRequestError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
        self.message = message


class ClimateController:

    CLIMATE_CONTROL_VALUES_ON = [
        ClimatizationStatus.ClimatizationState.COOLING,
        ClimatizationStatus.ClimatizationState.HEATING,
        ClimatizationStatus.ClimatizationState.VENTILATION,
    ]
    CLIMATE_CONTROL_VALUES_OFF = [
        ClimatizationStatus.ClimatizationState.OFF,
        ClimatizationStatus.ClimatizationState.UNKNOWN,
    ]
    DISALLOWED_CLIMATE_STATES = {
        ControlOperation.START: CLIMATE_CONTROL_VALUES_ON,
        ControlOperation.STOP: CLIMATE_CONTROL_VALUES_OFF,
    }

    SUCCESSFULL_REQUEST = GenericStatus.Request.Status.SUCCESSFULL
    FAILED_REQUESTS = [
        GenericStatus.Request.Status.FAIL_VEHICLE_IS_OFFLINE,
        GenericStatus.Request.Status.FAIL_BATTERY_LOW,
        GenericStatus.Request.Status.FAIL_CHARGE_PLUG_NOT_CONNECTED,
        GenericStatus.Request.Status.FAIL_IGNITION_ON,
        GenericStatus.Request.Status.FAIL_PLUG_ERROR,
        GenericStatus.Request.Status.FAIL,
        GenericStatus.Request.Status.UNKNOWN,
        GenericStatus.Request.Status.POLLING_TIMEOUT,
    ]
    QUEUED_REQUEST = GenericStatus.Request.Status.QUEUED
    IN_PROGRESS_REQUEST = GenericStatus.Request.Status.IN_PROGRESS

    def __init__(self, vehicle: Vehicle) -> None:

        self.__vehicle = vehicle
        self.__weconnect = vehicle.weConnect
        self.__last_update = None

        self.__request_id = None
        self.__request_status = None
        self.__operation_running = False
        self.__call_when_ready = None

    def start(self, call_when_ready: callable) -> None:
        """
        Start climatisation control of the car

        Args:
            call_when_ready (callable): [Call this function when operation is successfull]

        Raises:
            e: [Could be any exception given in this module]
        """
        try:
            self.__call_when_ready = call_when_ready
            self.__make_request(ControlOperation.START)
        except Exception as e:
            raise e

    def stop(self, call_when_ready: callable) -> None:
        """
        Stop climatisation control of the car

        Args:
            call_when_ready (callable): [Call this function when operation is successfull]

        Raises:
            e: [Could be any exception given in this module]
        """
        try:
            self.__call_when_ready = call_when_ready
            self.__make_request(ControlOperation.STOP)
        except Exception as e:
            raise e

    def set_temperature(self, temperature: float) -> None:
        """
        Set climate control temperature

        Args:
            temperature (float): [Target temperature]

        Raises:
            FailedToSetTemperatureError: [Setting temperature failed]
            ValueError: [If temperature is out of acceptable range]
        """

        if temperature < 15.5 or 30 < temperature:
            raise ValueError("Requested temperature is out of range")

        self.__update()

        settings = self.__vehicle.domains["climatisation"]["climatisationSettings"]

        try:
            logging.info("Updating target temperature value")
            if (
                settings.targetTemperature_C is not None
                and settings.targetTemperature_C.enabled
            ):
                settings.targetTemperature_C.value = temperature
            elif (
                settings.targetTemperature_K is not None
                and settings.targetTemperature_K.enabled
            ):
                settings.targetTemperature_K.value = temperature + 273.15
        except Exception:
            raise FailedToSetTemperatureError("Failed to set target temperature")
        else:
            logging.info(
                f"Successfully updated target temperature value -> {temperature}°C"
            )

    def __update(self, bypass_time_check=False) -> None:
        if self.__last_update is not None and not bypass_time_check:
            now = datetime.now()
            time_diff = (now - self.__last_update).total_seconds()
            if time_diff < 10:
                logging.info(
                    "Last update was less than 10 seconds ago. Update will not take place now."
                )
                return

        logging.info("Updating weconnect")
        self.__weconnect.update()
        self.__last_update = datetime.now()

    def __get_climate_control_state(
        self, update=True
    ) -> ClimatizationStatus.ClimatizationState:
        if update:
            self.__vehicle.weConnect.update()
        return self.__vehicle.domains["climatisation"][
            "climatisationStatus"
        ].climatisationState.value

    def __get_current_request_ids(self, update=True) -> list:
        self.__update(bypass_time_check=update)
        requests = self.__get_requests()
        logging.info("Receiving current request ids")
        return [str(request.requestId) for request in requests]

    def __get_request_id(self, ids_before, ids_after) -> str:
        logging.info("Trying to identify our request id")
        new_ids = numpy.setdiff1d(ids_after, ids_before)
        if len(new_ids) != 1:
            raise FailedToIdentifyRequestError(
                f"Failed to identify id of our request, the list containing requestids is {'too long' if len(new_ids) > 1 else 'empty'}"
            )
        self.__request_id = new_ids[0]
        logging.info(f"Found our request id -> {self.__request_id}")
        self.__update_request_state()

    def __check_compability(self):
        logging.info("Checking compability for climate control")
        compatible = (
            self.__vehicle.controls.climatizationControl is not None
            and self.__vehicle.controls.climatizationControl.enabled
        )
        if not compatible:
            raise ClimateControllerCompabilityError(
                "Car is not compatible with climate controller"
            )
        logging.info("Compability check -> Success")

    def __check_climate_state(self, operation: ControlOperation):
        logging.info("Checking if climate control is in acceptable state")
        state = self.__get_climate_control_state(update=True)
        acceptable_state = state not in self.DISALLOWED_CLIMATE_STATES[operation]
        if not acceptable_state:
            raise ClimateControlAlreadyOnError(
                "Climate control is already in requested state"
            )
        logging.info("Climate control state -> Acceptable")

    def __make_request(self, operation: ControlOperation):

        if self.__operation_running:
            raise OperationAlreadyRunningError("Control operation is already running")

        try:
            self.__check_compability()
        except ClimateControllerCompabilityError as e:
            raise e

        try:
            self.__check_climate_state(operation)
        except ClimateControlAlreadyOnError as e:
            raise e

        ids_before = self.__get_current_request_ids(update=False)

        logging.info(f"Creating new request -> {operation}")
        self.__operation_running = True
        self.__vehicle.controls.climatizationControl.value = operation

        ids_after = self.__get_current_request_ids(update=True)

        try:
            self.__get_request_id(ids_before, ids_after)
        except FailedToIdentifyRequestError as e:
            raise e

        self.__update_weconnect()

    def __finish_operation(self, successfull: bool) -> None:
        self.__call_when_ready(successfull)
        self.__request_status = None
        self.__request_id = None
        self.__call_when_ready = None
        self.__operation_running = False

    def __get_requests(self):
        return self.__vehicle.domains["climatisation"]["climatisationStatus"].requests

    def __update_request_state(self) -> None:
        logging.info("Updating request status")
        requests = self.__get_requests()
        try:
            self.__request_status = next(
                request
                for request in requests
                if str(request.requestId) == self.__request_id
            ).status.value
            logging.info(f"Request state updated -> {self.__request_status}")
        except StopIteration:
            raise NoMatchingIdError("There was no matching id found")

    def __update_weconnect(self):

        self.__update()

        try:
            self.__update_request_state()
        except NoMatchingIdError:
            self.__request_status = GenericStatus.Request.Status.FAIL

        if self.__request_status == self.IN_PROGRESS_REQUEST:
            logging.info("Request progess -> Request is in progress")
            Timer(10, self.__update_weconnect).start()
            return

        elif self.__request_status == self.QUEUED_REQUEST:
            logging.info("Request progess -> Request is queued")
            Timer(10, self.__update_weconnect).start()
            return

        if self.__request_status == self.SUCCESSFULL_REQUEST:
            logging.info("Request progess -> Request is successfull")
            self.__finish_operation(successfull=True)

        elif self.__request_status in self.FAILED_REQUESTS:
            logging.error("Request progess -> Request has failed")
            self.__finish_operation(successfull=False)

        else:
            logging.warning("Request is in unknown state")
            Timer(10, self.__update_weconnect).start()


if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    weconnect = WeConnect("username", "passwd")
    weconnect.login()
    vin = ""
    for vin, car in weconnect.vehicles.items():
        vin = vin
        break
    car = weconnect.vehicles[vin]
    car.enableTracker()
    control = ClimateController(car)
    control.stop(
        lambda successfull: print(
            f"Operation is completed, result -> {'Successfull' if successfull else 'Failed'}"
        )
    )
