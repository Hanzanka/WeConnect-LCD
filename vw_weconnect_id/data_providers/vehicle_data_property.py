class Weconnect_vehicle_data_property():
    
    def __init__(self, name, value, desc, unit=None) -> None:
        self.__name = name
        self.__value = str(value)
        self.__unit = unit
        self.__desc = desc

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

    def __str__(self) -> str:
        return (
            f"{self.__desc:<50}{self.__value}"
            if self.__unit is None
            else f"{self.__desc:<50}{self.__value}{self.__unit}"
        )
