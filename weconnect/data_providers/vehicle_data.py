from enum import Enum
from weconnect.elements.vehicle import Vehicle
from weconnect.addressable import AddressableLeaf, AddressableAttribute


class Weconnect_vehicle_data:
    def __init__(self, vehicle: Vehicle, call_on_update: callable) -> None:
        self._vehicle = vehicle

        self._data = {}

        self.__call_on_update = call_on_update

        self.__add_observer()

    def get_data(self) -> dict:
        data = {}
        for key, item in self._data.items():
            data[item.name] = item
        return data

    def __add_observer(self) -> None:
        self._vehicle.weConnect.addObserver(
            self.__on_weconnect_event,
            AddressableLeaf.ObserverEvent.ENABLED
            | AddressableLeaf.ObserverEvent.DISABLED
            | AddressableLeaf.ObserverEvent.VALUE_CHANGED,
        )

    def __on_weconnect_event(self, element, flags) -> None:
        if (
            isinstance(element, AddressableAttribute)
            and flags
            and element.getGlobalAddress() in self._data.keys()
        ):
            self.__update_value(element)

    def __update_value(self, element: AddressableAttribute) -> None:
        value = element.value
        address = element.getGlobalAddress()
        self._data[address].value = value.value if isinstance(value, Enum) else value
        self.__call_on_update(self._data[address])
