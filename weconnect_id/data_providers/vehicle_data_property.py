from datetime import datetime
import logging
from weconnect_id.tools.logger import (
    log as log_data,
    WeConnectLoggerError,
)
from enum import Enum
from weconnect.addressable import AddressableAttribute, AddressableLeaf


LOG = logging.getLogger("data_properties")


class WeConnectVehicleDataProperty:
    def __init__(
        self,
        id,
        weconnect_element: AddressableAttribute,
        category,
        desc=None,
        unit=None,
    ) -> None:
        LOG.debug(f"Initializing WeconnectVehicleDataProperty (ID: {id})")
        self._id = id
        self.__category = category
        self.__desc = desc
        self.__unit = unit
        self.__translations = None
        if weconnect_element is not None:
            self._value = weconnect_element.value
            self._value_string = str(
                self._value.value if isinstance(self._value, Enum) else self._value
            )
            self._time_updated = datetime.now().time().strftime("%H.%M:%S")
            self._date_updated = datetime.now().date().strftime("%d.%m.%Y")
            weconnect_element.addObserver(
                observer=self.__update_value,
                flag=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
            )
        self._callback_functions = []
        self.__logging_enabled = False
        self.__logger_path = None

    @property
    def id(self) -> str:
        return self._id

    @property
    def value(self):
        return self._value

    @property
    def category(self) -> str:
        return self.__category

    @property
    def desc(self) -> str:
        return self.__desc

    @property
    def string_value(self) -> str:
        return self._value_string

    @property
    def logging_enabled(self) -> bool:
        return self.__logging_enabled

    @property
    def last_update_time(self) -> str:
        return self._time_updated

    @property
    def last_update_date(self) -> str:
        return self._date_updated

    @property
    def logger_path(self) -> str:
        return self.__logger_path

    @property
    def logger_value_format(self) -> tuple:
        return (
            self.custom_value_format(translate=False, include_unit=True),
            self._time_updated,
            self._date_updated,
        )

    def custom_value_format(self, translate=False, include_unit=True) -> str:
        try:
            return (
                self.__translations[self._value_string]
                if translate and self.__translations is not None
                else self._value_string
            ) + (self.__unit if include_unit and self.__unit is not None else "")
        except Exception:
            return "Error"

    def __update_value(self, element, flags) -> None:
        LOG.debug(f"Updating WeconnectVehicleDataProperty (ID: {self._id}) value")
        self._value = element.value
        self._value_string = str(
            self._value.value if isinstance(self._value, Enum) else self._value
        )
        element.addObserver(
            observer=self.__update_value,
            flag=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
        )
        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")
        for function in self._callback_functions:
            function()
        self.log()

    def add_callback_function(self, function: callable) -> None:
        LOG.debug(
            f"Added callback function {function.__name__} to WeconnectVehicleDataProperty (ID: {self._id})"
        )
        self._callback_functions.append(function)

    def log(self) -> None:
        if not self.__logging_enabled:
            return
        try:
            LOG.debug(
                f"Logging data from WeconnectVehicleDataProperty (ID: {self._id})"
            )
            log_data(self)
        except WeConnectLoggerError as e:
            LOG.exception(e)

    def add_translations(self, translations: dict) -> None:
        if self.__translations is None:
            LOG.debug(
                f"Added translations ({translations}) to WeconnectVehicleDataProperty (ID: {self._id})"
            )
            self.__translations = translations

    def enable_logging(self, path: str) -> None:
        LOG.debug(
            f"Enabled logging on WeconnectVehicleDataProperty (ID: {self._id}), logs will be saved to '{path}'"
        )
        self.__logging_enabled = True
        self.__logger_path = path
        self.log()


class CalculatedWeConnectVehicleDataProperty(WeConnectVehicleDataProperty):
    def __init__(
        self, id, weconnect_element, category, formula: callable, desc=None, unit=None
    ) -> None:
        LOG.debug(f"Initializing CalculatedWeConnectVehicleDataProperty (ID: {id})")
        if not isinstance(weconnect_element.value, int) and not isinstance(
            weconnect_element.value, float
        ):
            raise AttributeError(
                "Value for CalculatedWeConnectVehicleDataProperty must be int or float"
            )
        super().__init__(
            id=id,
            weconnect_element=None,
            desc=desc,
            category=category,
            unit=unit,
        )
        self.__formula = formula
        calculation = self.__formula(weconnect_element.value)
        self._value = calculation
        self._value_string = str(calculation)
        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")

    def __update_value(self, value) -> None:
        LOG.debug(
            f"Updating CalculatedWeConnectVehicleDataProperty (ID: {self._id}) value"
        )
        calculation = self.__formula(value)
        self._value = calculation
        self._value_string = str(calculation)
        for function in self._callback_functions:
            function()
        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")
        self.log()
