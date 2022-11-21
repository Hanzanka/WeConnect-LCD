from threading import Timer
from weconnect.elements.control_operation import ControlOperation
from weconnect.elements.climatization_status import ClimatizationStatus
import logging
from weconnect.elements.generic_status import GenericStatus
from display.lcd_controller import LCDController
from weconnect_id.tools.updater import WeConnectUpdater
from weconnect.domain import Domain
from led.led_driver import create_led_driver
from time import sleep
from weconnect.addressable import AddressableLeaf


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

    def __init__(
        self,
        weconnect_vehicle,
        weconnect_updater: WeConnectUpdater,
        lcd_controller: LCDController,
        weconnect_vehicle_loader,
    ) -> None:
        self.__vehicle = weconnect_vehicle.api_vehicle
        self.__weconnect_updater = weconnect_updater
        self.__operation_led = create_led_driver(
            pin=6, id="CLIMATE OPERATION", default_frequency=1
        )
        self.__lcd_controller = lcd_controller
        self.__weconnect_vehicle_loader = weconnect_vehicle_loader

        self.__climate_controls = self.__vehicle.controls.climatizationControl
        self.__climate_state = weconnect_vehicle.get_data_property(
            "climate controller state"
        )
        self.__climate_settings = self.__vehicle.domains["climatisation"][
            "climatisationSettings"
        ]
        self.__climate_requests = self.__vehicle.domains["climatisation"][
            "climatisationStatus"
        ].requests

        self.__request = None
        self.__operation_running = False
        self.__timeout_timer = None

        self.__check_vehicle_compatibility()

    def switch(self) -> None:
        LOG.info("Requested to switch climate controller state")
        self.__weconnect_updater.update_weconnect(update_domains=[Domain.CLIMATISATION])
        if self.__climate_state.value in self.CLIMATE_CONTROL_VALUES_OFF:
            self.start()
        else:
            self.stop()

    def start(self) -> None:
        LOG.info("Requested to start climate controller")
        self.__lcd_controller.display_message(
            message="Käynnistetään Ilmastointia", time_on_screen=3
        )
        self.__start_operation(ControlOperation.START)

    def stop(self) -> None:
        LOG.info("Requested to stop climate controller")
        self.__lcd_controller.display_message(
            message="Pysäytetään Ilmastointia", time_on_screen=3
        )
        self.__start_operation(ControlOperation.STOP)

    def set_temperature(self, temperature: float) -> None:
        LOG.info(
            f"Requested to change climate controller target temperature to {temperature}°C"
        )

        if temperature < 15.5 or 30 < temperature:
            raise TemperatureOutOfRangeError(
                f"Requested temperature of {temperature} is out of accepted range. Target temperature must be between 15.5 and 30"
            )

        try:
            self.__lcd_controller.display_message(
                f"Päivitetään Lämpötila > {temperature}°C", time_on_screen=5
            )

            self.__climate_settings.targetTemperature_C.value = temperature

        except Exception as e:
            LOG.exception(
                "Failed to update climate controller target temperature value", e
            )
            self.__lcd_controller.display_message(
                "Virhe Lämpötilaa Päivittäessä", time_on_screen=5
            )
            raise FailedToSetTemperatureError(e)

    def __start_operation(self, operation: ControlOperation) -> None:
        try:
            self.__post_request(operation=operation)

        except OperationAlreadyRunningError as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Toinen Pyyntö On Vireillä", time_on_screen=5
            )
            raise e

        except ClimateControllerAlreadyInRequestedStateError as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Ilmastointi On Jo Pyydetyssä Tilassa",
                time_on_screen=5,
            )
            raise e

        except FailedToIdentifyRequestError as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Pyyntöä Ei Voida Seurata", time_on_screen=5
            )
            self.__lcd_controller.display_message(
                message=f"Ilmastointi Saattaa Silti {'Käynnistyä' if operation == ControlOperation.START else 'Sammua'}",
                time_on_screen=5,
            )
            raise e

        except Exception as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                message="Ei-Tunnettu Virhe", time_on_screen=5
            )
            self.__lcd_controller.display_message(
                message=f"Ilmastointi Saattaa Silti {'Käynnistyä' if operation == ControlOperation.START else 'Sammua'}",
                time_on_screen=5,
            )
            raise e

    def __get_climate_control_state(self) -> ClimatizationStatus.ClimatizationState:
        self.__weconnect_updater.update_weconnect(update_domains=[Domain.CLIMATISATION])
        return self.__climate_state.value

    def __get_current_requests(self) -> list:
        self.__weconnect_updater.update_weconnect(update_domains=[Domain.CLIMATISATION])
        return list(self.__climate_requests.values())

    def __identify_request(
        self, requests_before, requests_after
    ) -> GenericStatus.Request:
        new_requests = [
            request for request in requests_after if request not in requests_before
        ]
        if len(new_requests) != 1:
            raise FailedToIdentifyRequestError(
                f"Failed to identify ID of the request, the list containing newly added request IDs is {'too long' if len(new_requests) > 1 else 'empty'}"
            )
        return new_requests[0]

    def __check_vehicle_compatibility(self):
        compatible = (
            self.__climate_controls is not None and self.__climate_controls.enabled
        )
        if not compatible:
            raise ClimateControllerCompatibilityError(
                "Car is not compatible with climate controller actions"
            )

    def __check_climate_control_state(self, operation: ControlOperation):
        state = self.__get_climate_control_state()
        acceptable_state = state not in self.DISALLOWED_CLIMATE_STATES[operation]
        if not acceptable_state:
            raise ClimateControllerAlreadyInRequestedStateError(
                f"Climate control is already in requested state of {state}"
            )

    def __post_request(self, operation: ControlOperation):
        if self.__operation_running:
            raise OperationAlreadyRunningError(
                "Other climate controller operation is already running"
            )
        self.__check_climate_control_state(operation)

        self.__weconnect_vehicle_loader.disable_vehicle_change()

        requests_before = self.__get_current_requests()

        self.__operation_running = True
        self.__climate_controls.value = operation

        for tries in range(5):
            requests_after = self.__get_current_requests()
            try:
                self.__request = self.__identify_request(
                    requests_before, requests_after
                )
                self.__request.status.addObserver(
                    observer=self.__on_request_update,
                    flag=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                    priority=AddressableLeaf.ObserverPriority.INTERNAL_FIRST,
                )
                break
            except FailedToIdentifyRequestError as e:
                if tries == 4:
                    raise e
            sleep(5)

        if operation == ControlOperation.START:
            self.__operation_led.turn_on()
        else:
            self.__operation_led.blink(frequency=2)

        self.__weconnect_updater.add_new_scheduler(
            id="CLIMATE", update_values=[Domain.CLIMATISATION], interval=15
        )
        self.__timeout_timer = Timer(
            function=self.__finish_operation,
            args=[False],
            interval=5 * 60,
        )
        self.__timeout_timer.start()

    def __on_request_update(self, element, flags) -> None:
        if self.__request.status.value == self.SUCCESSFULL_REQUEST:
            self.__finish_operation(successfull=True)

        elif self.__request.status.value in self.FAILED_REQUESTS:
            self.__finish_operation(successfull=False)

    def __finish_operation(self, successfull: bool) -> None:
        self.__timeout_timer.cancel()
        self.__request.status.removeObserver(
            observer=self.__on_request_update,
            flag=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
        )

        if successfull:
            self.__operation_led.turn_off()
        else:
            self.__lcd_controller.display_message("Ilmastointi-Pyyntö Epäonnistui")
            self.__operation_led.blink(frequency=10)
            Timer(interval=3, function=self.__operation_led.turn_off).start()

        self.__weconnect_updater.remove_scheduler(id="CLIMATE")
        self.__operation_running = False
        self.__weconnect_vehicle_loader.enable_vehicle_change()
