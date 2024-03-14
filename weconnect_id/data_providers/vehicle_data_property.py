from weconnect_id.tools.logger import (
    log as log_data,
    WeConnectLoggerError,
)
from datetime import datetime
import logging
from enum import Enum
from weconnect.addressable import AddressableAttribute, AddressableLeaf
import json


LOG = logging.getLogger("data_properties")


class WeConnectVehicleDataProperty:
    def __init__(
        self,
        id: str,
        weconnect_element: AddressableAttribute,
        category: str,
        desc: str = None,
        unit: str = None,
    ) -> None:
        """
        Used to store vehicle based data.

        Args:
            id (str): ID of the data property
            weconnect_element (AddressableAttribute): WeConnect-API element that provides data to the data property.
            category (str): Category where the data property belongs to.
            desc (str, optional): Description for the data property. Defaults to None.
            unit (str, optional): Unit for the data property. Defaults to None.
        """

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
                flag=AddressableLeaf.ObserverEvent.ENABLED
                | AddressableLeaf.ObserverEvent.DISABLED
                | AddressableLeaf.ObserverEvent.VALUE_CHANGED,
                priority=AddressableLeaf.ObserverPriority.INTERNAL_HIGH,
            )
        self._callback_functions = {}
        self.__logging_enabled = False
        self.__logger_path = None

    def __str__(self) -> str:
        return self._value_string

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
        """
        Used to get the value of the data property with unit.

        Args:
            translate (bool, optional): If the returned data should be translated. Defaults to False.
            include_unit (bool, optional): If the unit should be included in the returned string. Defaults to True.

        Returns:
            str: String generated with given arguments.
        """

        try:
            return (
                self.__translations[self._value_string]
                if translate and self.__translations is not None
                else self._value_string
            ) + (self.__unit if include_unit and self.__unit is not None else "")
        except Exception:
            return "Error"

    def __update_value(self, element, flags) -> None:
        self._value = element.value
        self._value_string = str(
            self._value.value if isinstance(self._value, Enum) else self._value
        )

        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")

        for callback in self._callback_functions.values():
            if callback["specific values"] is None:
                callback["function"](*callback["args"])
            elif self._value in callback["specific values"]:
                callback["function"](*callback["args"])

        self.log()

    def add_callback_function(
        self, id, function: callable, args: list = None, specific_values: list = None
    ) -> None:
        """
        Adds callback function to the data property which are called when the data provider receives an update.

        Args:
            id: ID for the function so it can be removed later.
            function (callable): Function to be called when an update. occurs
            args (list, optional): Arguments for the given function. Defaults to None.
            specific_values (list, optional): If the function should be called only when data provider gets specific values. Defaults to None.
        """

        self._callback_functions[id] = {
            "id": id,
            "function": function,
            "specific values": specific_values,
            "args": [] if args is None else args,
        }
        LOG.debug(
            f"Added callback function (ID: {id}) to WeConnectVehicleDataProperty (ID: {self._id})"
        )

    def remove_callback_function(self, id) -> None:
        self._callback_functions.pop(id)
        LOG.debug(
            f"Removed callback function (ID: {id}) from WeConnectVehicleDataProperty (ID: {self._id})"
        )

    def log(self) -> None:
        if not self.__logging_enabled:
            return
        try:
            log_data(self)
        except WeConnectLoggerError as e:
            LOG.exception(e)

    def add_translations(self, translations: dict) -> None:
        """
        Adds translations for data provider values.

        Args:
            translations (dict): Dict containing the translations.
        """

        if self.__translations is None:
            LOG.debug(
                f"Added translations ({translations}) to WeconnectVehicleDataProperty (ID: {self._id})"
            )
            self.__translations = translations

    def set_logging(self, logging_enabled: bool, path: str) -> None:
        """
        Used to enable logging for the data property values.

        Args:
            path (str): Path of the .csv file where logs will get saved.
        """

        LOG.debug(
            (
                f"Setting logging status to {logging_enabled} on WeconnectVehicleDataProperty (ID: {self._id})"
                f"{', logs will be saved to {path}' if logging_enabled else ''}"
            )
        )
        self.__logging_enabled = logging_enabled
        self.__logger_path = path
        self.log()

    def as_json(self) -> str:
        return json.dumps(
            {
                "category": self.__category,
                "description": self.__desc,
                "unit": self.__unit,
                "value": self._value,
                "time": self._time_updated,
                "date": self._date_updated,
            }
        )


class CalculatedWeConnectVehicleDataProperty(WeConnectVehicleDataProperty):
    def __init__(
        self,
        id: str,
        weconnect_element: AddressableAttribute,
        category: str,
        formula: callable,
        desc: str = None,
        unit: str = None,
    ) -> None:
        """
        Used to generate data property of an value the API doesn't provide, but it can be calculated using other property.

        Args:
            id (str): ID of the data property
            weconnect_element (AddressableAttribute): WeConnect-API element that is used to calculate the value for the data property.
            category (str): Category where the data property belongs to.
            formula (callable): Function used to calculate the value for the data property.
            desc (_type_, optional): Description for the data property. Defaults to None.
            unit (_type_, optional): Unit for the data property. Defaults to None.

        Raises:
            AttributeError: Raised if the type of the value provided by the WeConnect-API element is not int nor float.
        """

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
        weconnect_element.addObserver(
            observer=self.__update_value,
            flag=AddressableLeaf.ObserverEvent.VALUE_CHANGED,
            priority=AddressableLeaf.ObserverPriority.INTERNAL_HIGH,
        )
        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")

    def __update_value(self, element, flags) -> None:
        calculation = self.__formula(element.value)
        self._value = calculation
        self._value_string = str(calculation)

        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")

        for callback in self._callback_functions.values():
            if callback["specific values"] is None:
                callback["function"](*callback["args"])
            elif self._value in callback["specific values"]:
                callback["function"](*callback["args"])

        self.log()
