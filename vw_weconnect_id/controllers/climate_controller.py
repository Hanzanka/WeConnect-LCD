from threading import Timer
from weconnect.elements.control_operation import ControlOperation
from weconnect.elements.climatization_status import ClimatizationStatus
import logging
from weconnect.elements.generic_status import GenericStatus
import numpy
from vw_weconnect_id.tools.weconnect_updater import WeConnectUpdater
from weconnect.domain import Domain
from led.led_driver import create_led_driver


logger = logging.getLogger("climate")


class ClimateControllerCompabilityError(Exception):
    pass


class ClimateControlAlreadyOnError(Exception):
    pass


class NoMatchingIdError(Exception):
    pass


class OperationAlreadyRunningError(Exception):
    pass


class RequestFailedError(Exception):
    pass


class FailedToSetTemperatureError(Exception):
    pass


class FailedToIdentifyRequestError(Exception):
    pass


class NoOperationRunningError(Exception):
    pass


class TemperatureOutOfRangeError(Exception):
    pass


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

    def __init__(self, vehicle, updater: WeConnectUpdater) -> None:
        logger.debug("Initializing climate controller")
        self.__vehicle = vehicle.get_weconnect_vehicle()
        self.__updater = updater
        self.__operation_led = create_led_driver(
            led_pin=26, led_id="CLIMATE OPERATION", default_frequency=1
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

    def start(self) -> None:
        """
        Start climatisation control of the car
        """
        logger.info("Requested to start climate control")
        self.__make_request(ControlOperation.START)

    def stop(self) -> None:
        """
        Stop climatisation control of the car
        """
        logger.info("Requested to stop climate control")
        self.__make_request(ControlOperation.STOP)

    def set_temperature(self, temperature: float) -> None:
        """
        Set climate controller target temperature

        Args:
            temperature (float): [Target temperature, must be between 15.5 and 30]

        Raises:
            FailedToSetTemperatureError: [Setting target temperature failed]
            TemperatureOutOfRangeError: [Given temperature is out of acceptable range]
        """
        try:
            logger.info(
                f"Requested to change climate control target temperature to {temperature}°C"
            )
            if temperature < 15.5 or 30 < temperature:
                error_string = f"Requested temperature of {temperature} is out of accepted range. Target temperature must be between 15.5 and 30"
                logger.error(error_string)
                raise TemperatureOutOfRangeError(error_string)

            self.__updater.update_weconnect([Domain.CLIMATISATION])

            try:
                logger.debug(
                    f"Updating climate controller target temperature value to {temperature}°C"
                )
                if (
                    self.__climate_settings.targetTemperature_C is not None
                    and self.__climate_settings.targetTemperature_C.enabled
                ):
                    self.__climate_settings.targetTemperature_C.value = temperature
                elif (
                    self.__climate_settings.targetTemperature_K is not None
                    and self.__climate_settings.targetTemperature_K.enabled
                ):
                    self.__climate_settings.targetTemperature_K.value = (
                        temperature + 273.15
                    )
            except Exception:
                error_string = "Failed to set climate controller target temperature"
                logger.error(error_string)
                raise FailedToSetTemperatureError(error_string)
            else:
                logger.info(
                    f"Successfully updated climate controller target temperature to {temperature}°C"
                )
        except Exception as e:
            logging.getLogger("exception").exception(
                "Failed to update climate controller target temperature value"
            )
            raise e

    def __get_climate_control_state(self) -> ClimatizationStatus.ClimatizationState:
        logger.debug("Checking current climate control status")
        self.__updater.update_weconnect([Domain.CLIMATISATION])
        return self.__climate_state.absolute_value

    def __get_current_request_ids(self) -> list:
        logger.debug("Receiving current climate request ids")
        self.__updater.update_weconnect([Domain.CLIMATISATION])
        return [str(request_id) for request_id in self.__climate_requests.keys()]

    def __get_request_id(self, ids_before, ids_after) -> str:
        logger.debug("Trying to identify request id of the request")
        new_ids = numpy.setdiff1d(ids_after, ids_before)
        if len(new_ids) != 1:
            raise FailedToIdentifyRequestError(
                f"Failed to identify id of our request, the list containing newly added request ids is {'too long' if len(new_ids) > 1 else 'empty'}"
            )
        self.__request_id = new_ids[0]
        logger.debug(f"Id of the request is {self.__request_id}")
        self.__update_request_state()

    def __check_compability(self):
        logger.debug("Checking vehicle compability for climate controller actions")
        compatible = (
            self.__climate_controls is not None and self.__climate_controls.enabled
        )
        if not compatible:
            raise ClimateControllerCompabilityError(
                "Car is not compatible with climate controller actions"
            )
        logger.debug("Car is compitable with climate controller actions")

    def __check_climate_state(self, operation: ControlOperation):
        logger.debug(
            "Checking if climate control of the car is in acceptable state for the request"
        )
        state = self.__get_climate_control_state()
        acceptable_state = state not in self.DISALLOWED_CLIMATE_STATES[operation]
        if not acceptable_state:
            raise ClimateControlAlreadyOnError(
                f"Climate control is already in requested state of {state}"
            )
        logger.debug("Climate control of the car is in acceptable state")

    def __make_request(self, operation: ControlOperation):
        logger.debug("Checking requirements for the request to be able to continue")
        if self.__operation_running:
            raise OperationAlreadyRunningError(
                "Other climate controller operation is already running"
            )
        self.__check_compability()
        self.__check_climate_state(operation)

        if operation == ControlOperation.START:
            self.__operation_led.turn_on()
        else:
            self.__operation_led.blink(frequency=2)

        ids_before = self.__get_current_request_ids()

        logger.debug(f"Creating new request for operation {operation}")
        self.__operation_running = True
        self.__climate_controls.value = operation

        ids_after = self.__get_current_request_ids()
        self.__get_request_id(ids_before, ids_after)

        self.__updater.add_new_scheduler(
            scheduler_id="CLIMATE",
            update_values=[Domain.CLIMATISATION],
            interval=15,
            callback_function=self.__update_request_state,
            called_from=self,
            at_lost_connection=self.__at_connection_failure,
        )

    def __finish_operation(self, successfull: bool) -> None:
        logger.debug(
            f"Finishing climate controller operation with ID {self.__request_id}"
        )
        if successfull:
            self.__operation_led.turn_off()
        else:
            self.__operation_led.blink(frequency=10)
            Timer(interval=3, function=self.__operation_led.turn_off).start()
        self.__updater.remove_scheduler(scheduler_id="CLIMATE", called_from=self)
        self.__operation_running = False
        self.__request_status = None
        self.__request_id = None

    def __at_connection_failure(self) -> None:
        if self.__operation_running:
            self.__finish_operation(successfull=False)

    def __update_request_state(self) -> None:
        if not self.__operation_running:
            logger.error(
                "There are no climate controller operations running, but update_request_state was still called"
            )
            self.__updater.remove_scheduler(scheduler_id="CLIMATE", called_from=self)
            return
        logger.debug("Updating request status")
        try:
            self.__request_status = self.__climate_requests[
                self.__request_id
            ].status.value
        except KeyError as e:
            logger.exception(e)
            self.__finish_operation(successfull=False)
            raise NoMatchingIdError(
                f"Updating climate controller operation status with request ID {self.__request_id} failed because request with same ID wasn't found"
            )

        if self.__request_status == self.SUCCESSFULL_REQUEST:
            logger.info(
                f"Climate controller operation with request ID {self.__request_id} is successfull"
            )
            self.__finish_operation(successfull=True)

        elif self.__request_status in self.FAILED_REQUESTS:
            logger.error(
                f"Climate controller operation with request ID {self.__request_id} has failed"
            )
            self.__finish_operation(successfull=False)
