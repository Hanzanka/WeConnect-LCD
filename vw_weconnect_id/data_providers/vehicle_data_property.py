from datetime import datetime
import logging
from vw_weconnect_id.tools.weconnect_logger import WeConnectCSVLogger, WeConnectLoggerError


class WeconnectVehicleDataProperty:
    def __init__(self, name, value, desc, category, unit=None) -> None:
        self.__name = name
        self.__value = str(value)
        self.__unit = unit
        self.__desc = desc
        self.__category = category
        self.__time_updated = datetime.now().time().strftime("%H.%M:%S")
        self.__date_updated = datetime.now().date().strftime("%d.%m.%Y")
        self.__log()

    @property
    def category(self) -> str:
        return self.__category

    @property
    def desc(self) -> str:
        return self.__desc

    @property
    def name(self) -> str:
        return self.__name

    @property
    def value(self) -> str:
        return self.__value

    @value.setter
    def value(self, value) -> None:
        self.__value = str(value)
        self.__time_updated = datetime.now().time().strftime("%H.%M:%S")
        self.__date_updated = datetime.now().date().strftime("%d.%m.%Y")
        self.__log()

    def __log(self) -> None:
        try:
            WeConnectCSVLogger.log(self)
        except WeConnectLoggerError as e:
            logging.error(e.message)

    def data_as_tuple(self) -> tuple:
        return (
            (
                f"{self.__value}{self.__unit}"
                if self.__unit is not None
                else self.__value
            ),
            self.__time_updated,
            self.__date_updated,
        )

    def __str__(self) -> str:
        return (
            f"{self.__desc:<50}{self.__value}"
            if self.__unit is None
            else f"{self.__desc:<50}{self.__value}{self.__unit}"
        )
