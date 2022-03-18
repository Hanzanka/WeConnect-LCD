from datetime import datetime
import logging
from vw_weconnect_id.tools.weconnect_logger import WeConnectCSVLogger, WeConnectLoggerError
from enum import Enum


class WeconnectVehicleDataProperty:
    def __init__(self, data_id, value, desc, category, unit=None, log_data=False) -> None:
        self.__data_id = data_id
        self.__string_value = str(value.value if isinstance(value, Enum) else value)
        self.__absolute_value = value
        self.__unit = unit
        self.__desc = desc
        self.__category = category
        self.__call_on_update = []
        self.__time_updated = datetime.now().time().strftime("%H.%M:%S")
        self.__date_updated = datetime.now().date().strftime("%d.%m.%Y")
        self.__log_data = log_data
        self.__log()

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
        return self.__string_value

    @property
    def absolute_value(self):
        return self.__absolute_value

    def update_value(self, value) -> None:
        self.__string_value = str(value.value if isinstance(value, Enum) else value)
        self.__absolute_value = value
        for function in self.__call_on_update:
            function()
        self.__time_updated = datetime.now().time().strftime("%H.%M:%S")
        self.__date_updated = datetime.now().date().strftime("%d.%m.%Y")
        self.__log()

    def add_callback_function(self, function: callable) -> None:
        self.__call_on_update.append(function)

    def __log(self) -> None:
        if not self.__log_data:
            return
        try:
            WeConnectCSVLogger.log(self)
        except WeConnectLoggerError as e:
            logging.error(e.message)

    def data_as_tuple(self) -> tuple:
        return (
            (
                f"{self.__string_value}{self.__unit}"
                if self.__unit is not None
                else self.__string_value
            ),
            self.__time_updated,
            self.__date_updated,
        )

    def __str__(self) -> str:
        return (
            f"{self.__desc:<50}{self.__string_value}"
            if self.__unit is None
            else f"{self.__desc:<50}{self.__string_value}{self.__unit}"
        )
