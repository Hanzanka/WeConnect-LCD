from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from weconnect_id.tools.updater import WeConnectUpdater, WeConnectUpdaterError
    from display.lcd_controller import LCDController
    from weconnect_id.tools.vehicle_loader import WeConnectVehicleLoader
    from weconnect_id.vehicle import WeConnectVehicle
from led.led_driver import create_led_driver
import logging
from weconnect.elements.generic_status import GenericStatus
from weconnect.domain import Domain
from weconnect.addressable import AddressableLeaf
from enum import Enum
from threading import Lock, Timer
from weconnect.elements.control_operation import ControlOperation, Operation
from weconnect.elements.climatization_status import ClimatizationStatus


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
    class AvailabilityState(Enum):
        AVAILABLE = "available"
        UNAVAILABLE = "unavailable"

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
    ONGOING_REQUESTS = [
        GenericStatus.Request.Status.QUEUED,
        GenericStatus.Request.Status.IN_PROGRESS,
        GenericStatus.Request.Status.DELAYED,
    ]
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
        GenericStatus.Request.Status.TIMEOUT,
    ]
    EXPECTED_OPERATION_VALUES = {
        ControlOperation.STOP: Operation.STOP,
        ControlOperation.START: Operation.START,
    }

    def __init__(
        self,
        weconnect_vehicle: WeConnectVehicle,
        weconnect_updater: WeConnectUpdater,
        lcd_controller: LCDController,
        weconnect_vehicle_loader: WeConnectVehicleLoader,
    ) -> None:
        """
        Used to remotely turn on/off the climate controller and set the climate controller temperature of given vehicle.

        Args:
            weconnect_vehicle (WeConnectVehicle): Specifies which vehicle the operations will take effect on.
            weconnect_updater (WeConnectUpdater): Used to fetch data from server.
            lcd_controller (LCDController): Used to display messages to the LCD screen informing about ongoing operations.
            weconnect_vehicle_loader (WeConnectVehicleLoader):
                Is used to temporarily disable ability to change which vehicle the app uses during climate controller operations.

        Raises:
            ClimateControllerCompatibilityError: Raised if vehicle is not compatible with remote climate controls.
        """

        self.__vehicle = weconnect_vehicle.api_vehicle
        self.__weconnect_updater = weconnect_updater
        self.__operation_led = create_led_driver(
            pin=6, id="CLIMATE OPERATION", default_frequency=1
        )
        self.__lcd_controller = lcd_controller
        self.__weconnect_vehicle_loader = weconnect_vehicle_loader

        self.__climate_controls = self.__vehicle.controls.climatizationControl
        self.__climate_temperature = weconnect_vehicle.get_data_property(
            "climate controller target temperature"
        )
        self.__climate_state = weconnect_vehicle.get_data_property(
            "climate controller state"
        )
        self.__climate_settings = self.__vehicle.domains["climatisation"][
            "climatisationSettings"
        ]
        self.__climate_requests = self.__vehicle.domains["climatisation"][
            "climatisationStatus"
        ].requests

        self.__availability_status = ClimateController.AvailabilityState.AVAILABLE

        self.__request = None
        self.__excepted_request_operation_value = None

        self.__request_tracking_lock = Lock()

        self.__timeout_timer = None

        if not (
            self.__climate_controls is not None and self.__climate_controls.enabled
        ):
            raise ClimateControllerCompatibilityError(
                "Car is not compatible with climate controller actions"
            )

    @property
    def availability_status(self) -> AvailabilityState:
        """
        Used to check climate controller's availability status.

        Returns:
            AvailabilityState: Availability status of the climate controller.
        """

        return self.__availability_status

    @property
    def state(self):
        return self.__climate_state

    def switch(self) -> None:
        """
        Switches the climate controller state.
        """

        LOG.info("Requested to switch climate controller state")
        self.__weconnect_updater.update(domains=[Domain.CLIMATISATION], silent=False)
        if self.__climate_state.value in self.CLIMATE_CONTROL_VALUES_OFF:
            self.start()
        else:
            self.stop()

    def start(self) -> None:
        """
        Starts the climate controller
        """

        LOG.info(
            f"Starting the climate controller (Vehicle: {self.__vehicle.nickname})"
        )
        self.__lcd_controller.display_message(
            message="Käynnistetään Ilmastointia", time_on_screen=3
        )
        self.__lcd_controller.display_message(
            message=f"Lämpötila: {self.__climate_temperature}°C", time_on_screen=3
        )
        self.__post_request(ControlOperation.START)

    def stop(self) -> None:
        """
        Stops the climate controller.
        """

        LOG.info(
            f"Requested to stop climate controller (Vehicle: {self.__vehicle.nickname})"
        )
        self.__lcd_controller.display_message(
            message="Pysäytetään Ilmastointia", time_on_screen=3
        )
        self.__post_request(ControlOperation.STOP)

    def set_temperature(self, temperature: float) -> None:
        """
        Sets the climate controller temperature.

        Args:
            temperature (float): New value for the climate controller temperature.
                Must be between 15.5 and 30°C.

        Raises:
            TemperatureOutOfRangeError: Raised if given temperature is out of range of 15.5 - 30°C.
            FailedToSetTemperatureError: Raised if unknown error occurs.
        """

        LOG.info(
            f"Requested to change climate controller target temperature to {temperature}°C"
        )

        if temperature < 15.5 or 30 < temperature:
            raise TemperatureOutOfRangeError(
                f"Requested temperature of {temperature} is out of accepted range. Target temperature must be between 15.5 and 30 degrees"
            )

        try:
            self.__lcd_controller.display_message(
                f"Päivitetään Lämpötila > {temperature}°C", time_on_screen=5
            )

            self.__climate_settings.targetTemperature_C.value = temperature

        except Exception as e:
            LOG.exception(e)
            self.__lcd_controller.display_message(
                "Virhe Lämpötilaa Päivittäessä", time_on_screen=5
            )
            raise FailedToSetTemperatureError(e)

    def __exception_handler(function: callable) -> callable:
        def decorator(self, *args, **kwargs):
            error = None
            operation = args[0]

            try:
                function(self, *args, **kwargs)

            except OperationAlreadyRunningError as e:
                LOG.exception(e)
                self.__lcd_controller.display_message(
                    message="Virhe: Ohjain On Varattu", time_on_screen=5
                )
                error = e

            except ClimateControllerAlreadyInRequestedStateError as e:
                LOG.exception(e)
                self.__lcd_controller.display_message(
                    message="Ilmastointi On Jo Pyydetyssä Tilassa",
                    time_on_screen=5,
                )
                error = e

            except FailedToIdentifyRequestError as e:
                LOG.exception(e)
                self.__lcd_controller.display_message(
                    message="Pyyntöä Ei Voida Seurata", time_on_screen=5
                )
                self.__lcd_controller.display_message(
                    message=f"Ilmastointi Saattaa Silti {'Käynnistyä' if operation == ControlOperation.START else 'Sammua'}",
                    time_on_screen=5,
                )
                error = e

            except WeConnectUpdaterError as e:
                LOG.exception(e)
                self.__lcd_controller.display_message(
                    message="Virhe WeConnectia Päivitettäessä", time_on_screen=5
                )
                self.__lcd_controller.display_message(
                    message=f"Ilmastointi Saattaa Silti {'Käynnistyä' if operation == ControlOperation.START else 'Sammua'}",
                    time_on_screen=5,
                )
                error = e

            except Exception as e:
                LOG.exception(e)
                self.__lcd_controller.display_message(
                    message="Ei-Tunnettu Virhe", time_on_screen=5
                )
                self.__lcd_controller.display_message(
                    message=f"Ilmastointi Saattaa Silti {'Käynnistyä' if operation == ControlOperation.START else 'Sammua'}",
                    time_on_screen=5,
                )
                error = e

            finally:
                if error is not None:
                    self.__availability_status = (
                        ClimateController.AvailabilityState.AVAILABLE
                    )
                    raise error

        return decorator

    @__exception_handler
    def __post_request(self, operation: ControlOperation):
        if (
            self.__availability_status
            == ClimateController.AvailabilityState.UNAVAILABLE
        ):
            raise OperationAlreadyRunningError("Climate controller is unavailable")

        self.__weconnect_updater.update(domains=[Domain.CLIMATISATION], silent=False)

        if not (
            self.__climate_state.value not in self.DISALLOWED_CLIMATE_STATES[operation]
        ):
            raise ClimateControllerAlreadyInRequestedStateError(
                f"Climate controller is already in requested state of {self.__climate_state}"
            )

        self.__availability_status = ClimateController.AvailabilityState.UNAVAILABLE
        self.__weconnect_vehicle_loader.disable_vehicle_change()

        self.__climate_requests.addObserver(
            observer=self.__on_requests_update,
            flag=AddressableLeaf.ObserverEvent.ALL,
            priority=AddressableLeaf.ObserverPriority.INTERNAL_FIRST,
        )

        self.__excepted_request_operation_value = self.EXPECTED_OPERATION_VALUES[
            operation
        ]
        self.__climate_controls.value = operation

        self.__weconnect_updater.add_scheduler(
            id="REQUEST FINDER",
            domains=[Domain.CLIMATISATION],
            interval=10,
            silent=False,
        )
        self.__timeout_timer = Timer(
            function=self.__finish_operation,
            args=[False],
            interval=5 * 60,
        )
        self.__timeout_timer.start()

    def __track_request(self, request: GenericStatus.Request) -> None:
        if not self.__request_tracking_lock.acquire(blocking=False):
            return

        LOG.debug(f"Initializing tracker on request (ID: {request.requestId})")
        self.__request = request

        self.__weconnect_updater.remove_scheduler(id="REQUEST FINDER")
        self.__climate_requests.removeObserver(
            observer=self.__on_requests_update,
            flag=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
        )

        if self.__request.operation.value == Operation.START:
            self.__operation_led.turn_on()
        else:
            self.__operation_led.blink(frequency=2)

        self.__request.status.addObserver(
            observer=self.__on_request_update,
            flag=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
            priority=AddressableLeaf.ObserverPriority.USER_HIGH,
        )
        self.__weconnect_updater.add_scheduler(
            id="CLIMATE", domains=[Domain.CLIMATISATION], interval=15, silent=False
        )
        LOG.debug(
            f"Successfully initialized tracker on request (ID: {self.__request.requestId})"
        )

    def __on_request_update(self, element, flags) -> None:
        LOG.debug(
            f"Request (ID: {self.__request.requestId}) state was updated to {self.__request.status.value}"
        )
        if self.__request.status.value == self.SUCCESSFULL_REQUEST:
            self.__finish_operation(successfull=True)

        elif self.__request.status.value in self.FAILED_REQUESTS:
            self.__finish_operation(successfull=False)

    def __finish_operation(self, successfull: bool) -> None:
        LOG.info(
            f"Finishing climate operation, operation was {'successfull' if successfull else 'not successfull'}"
        )
        self.__timeout_timer.cancel()

        if self.__request is not None:
            self.__request.status.removeObserver(
                observer=self.__on_request_update,
                flag=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
            )
        else:
            self.__weconnect_updater.remove_scheduler(id="REQUEST FINDER")

        self.__weconnect_updater.remove_scheduler(id="CLIMATE")

        if self.__request is None:
            self.__climate_requests.removeObserver(
                observer=self.__on_requests_update,
                flag=AddressableLeaf.ObserverEvent.ALL,
            )

        self.__request = None
        self.__excepted_request_operation_value = None

        self.__request_tracking_lock.release()

        if successfull:
            self.__operation_led.turn_off()
        else:
            self.__lcd_controller.display_message(
                "Ilmastointi-Pyyntö Epäonnistui", time_on_screen=5
            )
            self.__operation_led.blink(frequency=10)
            Timer(interval=3, function=self.__operation_led.turn_off).start()

        self.__availability_status = ClimateController.AvailabilityState.AVAILABLE
        self.__weconnect_vehicle_loader.enable_vehicle_change()
        LOG.info(
            f"Climate operation finished, operation was {'successfull' if successfull else 'not successfull'}"
        )

    def __on_requests_update(self, element, flags) -> None:
        for request in self.__climate_requests.values():
            if request.status.value not in self.ONGOING_REQUESTS:
                continue

            if request.operation.value == self.__excepted_request_operation_value:
                LOG.debug(
                    f"Found matching request for the operation (ID: {request.requestId})"
                )
                self.__track_request(request=request)
                break
