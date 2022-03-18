from weconnect.elements.control_operation import ControlOperation
from weconnect.elements.climatization_status import ClimatizationStatus
from weconnect.weconnect import WeConnect
import logging
from weconnect.elements.generic_status import GenericStatus
import numpy
from vw_weconnect_id.tools.weconnect_updater import WeConnectUpdater
from weconnect.domain import Domain
from general_exception import GeneralException
from led_tools.led_controller import IndicatorLEDController


class ClimateControllerCompabilityError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


class ClimateControlAlreadyOnError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


class NoMatchingIdError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


class OperationAlreadyRunningError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


class RequestFailedError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


class FailedToSetTemperatureError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


class FailedToIdentifyRequestError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


class NoOperationRunningError(GeneralException):
    def __init__(self, message, fatal) -> None:
        super().__init__(message, fatal)


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

    def __init__(
        self, vehicle, updater: WeConnectUpdater, led_controller: IndicatorLEDController
    ) -> None:

        self.__vehicle = vehicle.get_weconnect_vehicle()
        self.__updater = updater
        self.__operation_led = led_controller.create_independent_leddriver(
            pin=26, led_id="CLIMATE OPERATION", default_frequency=1
        )
        self.__climate_state = vehicle.get_data_property("climate state")
        self.__climate_settings = self.__vehicle.domains["climatisation"][
            "climatisationSettings"
        ]
        self.__climate_requests = self.__vehicle.domains["climatisation"][
            "climatisationStatus"
        ].requests
        self.__climate_controls = self.__vehicle.controls.climatizationControl

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

        self.__updater.update_weconnect([Domain.CLIMATISATION])

        try:
            logging.info("Updating target temperature value")
            if (
                self.__climate_settings.targetTemperature_C is not None
                and self.__climate_settings.targetTemperature_C.enabled
            ):
                self.__climate_settings.targetTemperature_C.value = temperature
            elif (
                self.__climate_settings.targetTemperature_K is not None
                and self.__climate_settings.targetTemperature_K.enabled
            ):
                self.__climate_settings.targetTemperature_K.value = temperature + 273.15
        except Exception:
            raise FailedToSetTemperatureError("Failed to set target temperature")
        else:
            logging.info(
                f"Successfully updated target temperature value -> {temperature}°C"
            )

    def __get_climate_control_state(
        self, update=True
    ) -> ClimatizationStatus.ClimatizationState:
        if update:
            self.__updater.update_weconnect([Domain.CLIMATISATION])
        return self.__climate_state.absolute_value

    def __get_current_request_ids(self, update=True) -> list:
        if update:
            self.__updater.update_weconnect([Domain.CLIMATISATION])
        logging.info("Receiving current request ids")
        return [str(requestId) for requestId in self.__climate_requests.keys()]

    def __get_request_id(self, ids_before, ids_after) -> str:
        logging.info("Trying to identify our request id")
        new_ids = numpy.setdiff1d(ids_after, ids_before)
        if len(new_ids) != 1:
            raise FailedToIdentifyRequestError(
                f"Failed to identify id of our request, the list containing requestids is {'too long' if len(new_ids) > 1 else 'empty'}"
            )
        self.__request_id = new_ids[0]
        logging.info(f"Found our request id -> {self.__request_id}")
        self.update_request_state()

    def __check_compability(self):
        logging.info("Checking compability for climate control")
        compatible = (
            self.__climate_controls is not None and self.__climate_controls.enabled
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

        self.__operation_led.turn_on()
        ids_before = self.__get_current_request_ids(update=True)

        logging.info(f"Creating new request -> {operation}")
        self.__operation_running = True
        self.__climate_controls.value = operation

        ids_after = self.__get_current_request_ids(update=True)

        try:
            self.__get_request_id(ids_before, ids_after)
        except FailedToIdentifyRequestError as e:
            raise e

        self.__updater.add_new_scheduler(id="CLIMATE", update_values=[Domain.CLIMATISATION], callback_function=self.update_request_state)

    def __finish_operation(self, successfull: bool) -> None:
        logging.info("Finishing climate controller operation")
        self.__updater.remove_scheduler()
        self.__operation_running = False
        self.__operation_led.turn_off()
        self.__call_when_ready(successfull)
        self.__request_status = None
        self.__request_id = None
        self.__call_when_ready = None

    def update_request_state(self) -> None:
        if not self.__operation_running:
            logging.error(
                "There are no climate controller operations running, but update_request_state was still called"
            )
            self.__updater.remove_scheduler(id="CLIMATE")
            return
        logging.info("Updating request status")
        try:
            self.__request_status = self.__climate_requests[
                self.__request_id
            ].status.value
        except KeyError:
            self.__finish_operation(successfull=False)
            raise NoMatchingIdError("There was no matching id found")

        if self.__request_status == self.SUCCESSFULL_REQUEST:
            logging.info("Request progess -> Request is successfull")
            self.__finish_operation(successfull=True)

        elif self.__request_status in self.FAILED_REQUESTS:
            logging.error("Request progess -> Request has failed")
            self.__finish_operation(successfull=False)


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
