from threading import Timer
from weconnect.elements.control_operation import ControlOperation
from weconnect.elements.climatization_status import ClimatizationStatus
import logging
from weconnect.elements.generic_status import GenericStatus
import numpy
from vw_weconnect_id.tools.weconnect_updater import WeConnectUpdater
from weconnect.domain import Domain
from led.led_driver import create_led_driver
from display.lcd_controller import LCDController
from time import sleep


LOG = logging.getLogger("climate")


class ClimateControllerCompatibilityError(Exception):
    pass


class ClimateControllerAlreadyInRequestedStateError(Exception):
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

    def __init__(
        self, vehicle, updater: WeConnectUpdater, lcd_controller: LCDController
    ) -> None:
        LOG.debug("Initializing ClimateController")
        self.__vehicle = vehicle.get_weconnect_vehicle()
        self.__updater = updater
        self.__lcd_controller = lcd_controller
        self.__operation_led = create_led_driver(
            led_pin=26, led_id="CLIMATE OPERATION", default_frequency=1
        )
        self.__climate_state = vehicle.get_data_property("climate controller state")
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

    def switch(self) -> None:
        LOG.info("Requested to switch climate controller state")
        self.__updater.update_weconnect(update_domains=[Domain.CLIMATISATION])
        if self.__climate_state.value in self.CLIMATE_CONTROL_VALUES_OFF:
            self.start()
        else:
            self.stop()

    def start(self) -> None:
        """
        Make request to start climatisation control of the car
        """
        LOG.info("Requested to start climate control")
        self.__lcd_controller.display_message(
            message="K??ynnistet????n Ilmastointia", time_on_screen=3
        )
        self.__start_operation(ControlOperation.START)

    def stop(self) -> None:
        """
        Make request to stop climatisation control of the car
        """
        LOG.info("Requested to stop climate control")
        self.__lcd_controller.display_message(
            message="Pys??ytet????n Ilmastointia", time_on_screen=3
        )
        self.__start_operation(ControlOperation.STOP)

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
            LOG.info(
                f"Requested to change climate controller target temperature to {temperature}??C"
            )
            if temperature < 15.5 or 30 < temperature:
                error_string = f"Requested temperature of {temperature} is out of accepted range. Target temperature must be between 15.5??C and 30??C"
                LOG.error(error_string)
                raise TemperatureOutOfRangeError(error_string)

            self.__updater.update_weconnect(update_domains=[Domain.CLIMATISATION])

            try:
                LOG.debug(
                    f"Updating climate controller target temperature value to {temperature}??C"
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
            except Exception as e:
                LOG.exception(e)
                raise FailedToSetTemperatureError(e)
            else:
                LOG.info(
                    f"Successfully updated climate controller target temperature to {temperature}??C"
                )
        except Exception as e:
            logging.getLogger("exception").exception(
                "Failed to update climate controller target temperature value"
            )
            raise e

    def __start_operation(self, operation: ControlOperation) -> None:
        try:
            self.__make_request(operation=operation)

        except OperationAlreadyRunningError as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Error: Other Request Is Pending", time_on_screen=5
            )
            raise e

        except ClimateControllerCompatibilityError as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Error: Car Is Not Compatible", time_on_screen=5
            )
            raise e

        except ClimateControllerAlreadyInRequestedStateError as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Climate Already In Requested State", time_on_screen=5
            )
            raise e

        except FailedToIdentifyRequestError as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Error: Failed To Track Request", time_on_screen=5
            )
            self.__lcd_controller.display_message(
                message=f"Climate May Still Switch {'Off' if operation == ControlOperation.STOP else 'On'}",
                time_on_screen=5,
            )
            raise e

        except Exception as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Error: Unknown Error Occurred", time_on_screen=5
            )
            self.__lcd_controller.display_message(
                message=f"Climate May Still Switch {'Off' if operation == ControlOperation.STOP else 'On'}",
                time_on_screen=5,
            )
            raise e

    def __get_climate_control_state(self) -> ClimatizationStatus.ClimatizationState:
        LOG.debug("Checking current climate controller status")
        self.__updater.update_weconnect(update_domains=[Domain.CLIMATISATION])
        return self.__climate_state.value

    def __get_current_request_ids(self) -> list:
        LOG.debug("Receiving current climate operation request IDs")
        self.__updater.update_weconnect(update_domains=[Domain.CLIMATISATION])
        return [str(request_id) for request_id in self.__climate_requests.keys()]

    def __get_request_id(self, ids_before, ids_after) -> str:
        LOG.debug("Trying to identify request ID of the request")
        new_ids = numpy.setdiff1d(ids_after, ids_before)
        if len(new_ids) != 1:
            raise FailedToIdentifyRequestError(
                f"Failed to identify ID of the request, the list containing newly added request IDs is {'too long' if len(new_ids) > 1 else 'empty'}"
            )
        self.__request_id = new_ids[0]
        LOG.debug(f"Found the ID of the request (ID: {self.__request_id})")
        self.__update_request_state()

    def __check_compatibility(self):
        LOG.debug("Checking vehicle compatibility for climate controller actions")
        compatible = (
            self.__climate_controls is not None and self.__climate_controls.enabled
        )
        if not compatible:
            raise ClimateControllerCompatibilityError(
                "Car is not compatible with climate controller actions"
            )

    def __check_climate_state(self, operation: ControlOperation):
        LOG.debug(
            "Checking if climate control of the car is in acceptable state for the request"
        )
        state = self.__get_climate_control_state()
        acceptable_state = state not in self.DISALLOWED_CLIMATE_STATES[operation]
        if not acceptable_state:
            raise ClimateControllerAlreadyInRequestedStateError(
                f"Climate control is already in requested state of {state}"
            )

    def __make_request(self, operation: ControlOperation):
        LOG.debug(
            "Checking requirements for the request and the vehicle to be able to continue"
        )
        if self.__operation_running:
            raise OperationAlreadyRunningError(
                "Other climate controller operation is already running"
            )
        self.__check_compatibility()
        self.__check_climate_state(operation)
        LOG.debug(
            f"Vehicle (VIN: {self.__vehicle.vin}) passed all compatibility checks"
        )

        if operation == ControlOperation.START:
            self.__operation_led.turn_on()
        else:
            self.__operation_led.blink(frequency=2)

        ids_before = self.__get_current_request_ids()

        LOG.debug(
            f"Creating new request for operation (OPERATION TYPE: {operation})"
        )
        self.__operation_running = True
        self.__climate_controls.value = operation

        for tries in range(5):
            ids_after = self.__get_current_request_ids()
            try:
                self.__get_request_id(ids_before, ids_after)
                break
            except FailedToIdentifyRequestError as e:
                if tries == 4:
                    LOG.error(
                        "Couldn't identify request ID within 5 tries, climate controller operation will be terminated!"
                    )
                    raise e
                else:
                    LOG.warning(
                        f"Couldn't identify request ID within try number {tries + 1}, trying again in 5 seconds"
                    )
            sleep(5)

        self.__updater.add_new_scheduler(
            scheduler_id="CLIMATE",
            update_values=[Domain.CLIMATISATION],
            interval=15,
            callback_function=self.__update_request_state
        )
        Timer(function=self.__finish_operation, args=[False, self.__request_id], interval=5 * 60).start()

    def __finish_operation(self, successfull: bool, request_id=None) -> None:
        if request_id is not None and request_id != self.__request_id:
            return
            
        LOG.debug(
            f"Finishing climate controller operation (ID: {self.__request_id})"
        )
        if successfull:
            self.__lcd_controller.display_message(
                message=f"Ilmastoinnin Tila: {self.__climate_state.custom_value_format(translate=True, include_unit=False)}",
                time_on_screen=5,
            )
            self.__operation_led.turn_off()
        else:
            self.__lcd_controller.display_message(
                message="Error: Operation Failed", time_on_screen=5
            )
            self.__operation_led.blink(frequency=10)
            Timer(interval=3, function=self.__operation_led.turn_off).start()
        self.__updater.remove_scheduler(scheduler_id="CLIMATE", called_from=self)
        self.__operation_running = False
        self.__request_status = None
        self.__request_id = None

    def __update_request_state(self) -> None:
        if not self.__operation_running:
            LOG.error(
                "There were no climate controller operations running, but update_request_state was still called"
            )
            self.__updater.remove_scheduler(scheduler_id="CLIMATE", called_from=self)
            return
        LOG.debug(f"Updating request (ID: {self.__request_id}) status")
        try:
            self.__request_status = self.__climate_requests[
                self.__request_id
            ].status.value
        except KeyError as e:
            LOG.exception(e)
            self.__finish_operation(successfull=False)
            raise NoMatchingIdError(
                f"Updating climate controller request (ID: {self.__request_id}) status failed because request with same ID wasn't found"
            )

        LOG.debug(f"Successfully updated request (ID: {self.__request_id}) status to '{self.__request_status}'")
        
        if self.__request_status == self.SUCCESSFULL_REQUEST:
            LOG.info(
                f"Climate controller operation request (ID: {self.__request_id}) is successfull"
            )
            self.__finish_operation(successfull=True)

        elif self.__request_status in self.FAILED_REQUESTS:
            LOG.error(
                f"Climate controller operation request (ID: {self.__request_id}) has failed"
            )
            self.__finish_operation(successfull=False)
