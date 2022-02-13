from weconnect.elements.vehicle import Vehicle
from weconnect.elements.control_operation import ControlOperation
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.weconnect import WeConnect
import logging
from time import sleep
from weconnect.elements.generic_status import GenericStatus


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
        super.__init__(message)
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


class Climate_controller:

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
    ]
    QUEUED_REQUEST = GenericStatus.Request.Status.QUEUED
    IN_PROGRESS_REQUEST = GenericStatus.Request.Status.IN_PROGRESS

    def __init__(self, vehicle: Vehicle) -> None:

        self.__vehicle = vehicle
        self.__weconnect = vehicle.weConnect

        self.__request_id = None
        self.__request_state = None
        self.__operation_running = False

    def start(self, call_when_ready: callable) -> None:
        """
        Start climatisation control of the car

        Args:
            call_when_ready (callable): [Call this function when operation is successfull]

        Raises:
            e: [Could be any exception given in this module]
        """
        try:
            self.__make_request(ControlOperation.START)
        except Exception as e:
            raise e
        else:
            logging.info("Climate control is enabled")
            self.__finish_operation()
            call_when_ready()

    def stop(self, call_when_ready: callable) -> None:
        """
        Stop climatisation control of the car

        Args:
            call_when_ready (callable): [Call this function when operation is successfull]

        Raises:
            e: [Could be any exception given in this module]
        """
        try:
            self.__make_request(ControlOperation.STOP)
        except Exception as e:
            raise e
        else:
            logging.info("Climate control is disabled")
            self.__finish_operation()
            call_when_ready()

    def set_temperature(self, temperature: float) -> None:
        """
        Set climate control temperature

        Args:
            temperature (float): [Target temperature]

        Raises:
            FailedToSetTemperatureError: [Setting temperature failed]
            ValueError: [If temperature is out of acceptable range]
        """
        logging.info("Updating weconnect")

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

    def __update(self) -> None:
        logging.info("Updating weconnect")
        self.__weconnect.update()

    def __get_climate_control_state(
        self, update=True
    ) -> ClimatizationStatus.ClimatizationState:
        if update:
            self.__vehicle.weConnect.update()
        return self.__vehicle.domains["climatisation"][
            "climatisationStatus"
        ].climatisationState.value

    def __get_current_request_ids(self, update=True) -> list:
        if update:
            self.__update()
        requests = self.__get_requests()
        logging.info("Receiving current request ids")
        return [str(request.requestId) for request in requests]

    def __get_request_id(self, ids_before, ids_after) -> str:
        logging.info("Trying to identify our request id")
        new_ids = list(set(ids_after) - set(ids_before))
        if len(new_ids) > 1:
            raise Exception(
                "there are more than one new request. Tracking request will not be possible"
            )
        elif len(new_ids) == 0:
            raise Exception(
                "There are zero new requests. Tracking will not be possible"
            )
        else:
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
        except NoMatchingIdError as e:
            raise e

        try:
            self.__update_weconnect()
        except RequestFailedError as e:
            raise e
        else:
            logging.info("Control operation is successfully completed")

    def __finish_operation(self) -> None:
        self.__operation_running = False
        self.__request_state = None
        self.__request_id = None

    def __get_requests(self):
        return self.__vehicle.domains["climatisation"]["climatisationStatus"].requests

    def __update_request_state(self) -> None:
        logging.info("Updating request status")
        requests = self.__get_requests()
        try:
            self.__request_state = next(
                request
                for request in requests
                if str(request.requestId) == self.__request_id
            ).status.value
            logging.info(
                f"Request state updated successfully -> {self.__request_state}"
            )
        except StopIteration:
            logging.warn("There was no matching request in requests list")

    def __update_weconnect(self):
        while True:
            self.__update()

            self.__update_request_state()

            if self.__request_state == self.SUCCESSFULL_REQUEST:
                logging.info("Request progess -> Request is successfull")
                return
            if self.__request_state in self.FAILED_REQUESTS:
                raise RequestFailedError("Request progess -> Request has failed")

            if self.__request_state == self.IN_PROGRESS_REQUEST:
                logging.info("Request progess -> Request is in progress")
            elif self.__request_state == self.QUEUED_REQUEST:
                logging.info("Request progess -> Request is queued")

            sleep(5)


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
    control = Climate_controller(car)
    control.set_temperature(15)
