from datetime import datetime
import logging
from vw_weconnect_id.tools.weconnect_logger import (
    log as log_data,
    WeConnectLoggerError,
)
from enum import Enum


logger = logging.getLogger("data properties")


class WeconnectVehicleDataProperty:
    def __init__(
        self, data_id, value, desc, category, unit=None, log_data=False
    ) -> None:
        logger.debug(f"Initializing data property ID {data_id}")
        self.__data_id = data_id
        if issubclass(WeconnectVehicleDataProperty, self.__class__):
            self._string_value = str(value.value if isinstance(value, Enum) else value)
            self._absolute_value = value
        self.__unit = unit
        self.__desc = desc
        self.__category = category
        self.__translations = None
        self._call_on_update = []
        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")
        self.__log_data = log_data
        self.__logger_path = None

    @property
    def category(self) -> str:
        return self.__category

    @property
    def desc(self) -> str:
        return self.__desc

    @property
    def data_id(self) -> str:
        return self.__data_id

    @property
    def string_value(self) -> str:
        return self._string_value

    @property
    def absolute_value(self):
        return self._absolute_value

    @property
    def translated_value(self) -> str:
        return (
            self.__translations[self._string_value]
            if self._string_value in self.__translations
            else None
        )

    @property
    def logging_enabled(self) -> bool:
        return self.__log_data

    @property
    def last_update_time(self) -> str:
        return self._time_updated

    @property
    def last_update_date(self) -> str:
        return self._date_updated

    @property
    def logger_path(self) -> str:
        return self.__logger_path

    def update_value(self, value) -> None:
        logger.debug(f"Updating value of data property ID {self.__data_id}")
        self._string_value = str(value.value if isinstance(value, Enum) else value)
        self._absolute_value = value
        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")
        for function in self._call_on_update:
            function()
        self.log()

    def add_callback_function(self, function: callable) -> None:
        logger.debug(
            f"Added callback function {function.__name__} to data property ID {self.__data_id}"
        )
        self._call_on_update.append(function)

    def log(self) -> None:
        if not self.__log_data:
            return
        try:
            logger.debug(f"Logging data from data property ID {self.__data_id}")
            log_data(self)
        except WeConnectLoggerError as e:
            logger.exception(e)

    def get_value_with_unit(self, translate=False) -> str:
        if translate and self.__translations is not None:
            return self.__translations[self._string_value]
        return self._string_value + ("" if self.__unit is None else self.__unit)

    def get_logging_data(self) -> tuple:
        return (
            self.get_value_with_unit(),
            self._time_updated,
            self._date_updated,
        )

    def __str__(self) -> str:
        return (
            f"{self.__desc:<50}{self._string_value}"
            if self.__unit is None
            else f"{self.__desc:<50}{self._string_value}{self.__unit}"
        )

    def add_translations(self, translations: dict) -> None:
        if self.__translations is None:
            logger.debug(
                f"Added translations {translations} to data property ID {self.__data_id}"
            )
            self.__translations = translations

    def set_logger_path(self, path: str) -> None:
        if self.__logger_path is None:
            self.__logger_path = path
            self.log()


class CalculatedWeConnectVehicleDataProperty(WeconnectVehicleDataProperty):
    def __init__(
        self,
        data_id,
        value,
        formula: callable,
        desc,
        category,
        unit=None,
        log_data=False,
    ) -> None:
        if not isinstance(value, int) and not isinstance(value, float):
            raise ValueError(
                "Value for CalculatedWeConnectVehicleDataProperty must be int or float"
            )
        super().__init__(data_id, value, desc, category, unit, log_data)
        self.__formula = formula
        calculation = round(formula(value), 2)
        self._absolute_value = calculation
        self._string_value = str(calculation)

    def update_value(self, value) -> None:
        calculation = round(self.__formula(value), 2)
        self._string_value = str(calculation)
        self._absolute_value = calculation
        for function in self._call_on_update:
            function()
        self._time_updated = datetime.now().time().strftime("%H.%M:%S")
        self._date_updated = datetime.now().date().strftime("%d.%m.%Y")
        self.log()
