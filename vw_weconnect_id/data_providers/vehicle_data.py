from enum import Enum
from weconnect.elements.vehicle import Vehicle
from weconnect.addressable import AddressableLeaf, AddressableAttribute


class WeconnectVehicleData:
    def __init__(self, vehicle: Vehicle, add_observer_to: AddressableLeaf) -> None:
        self._vehicle = vehicle
        
        self._data = {}
        
        self.__call_on_update = []
        self.__add_observer(add_observer_to)

    def get_data(self) -> dict:
        """
        Get data from vehicle

        Returns:
            dict: ["Dict that contains weconnect_vehicle_data_property objects, each on contains data about one property"]
        """
        data = {}
        for key, item in self._data.items():
            data[item.name] = item
        return data

    def add_update_function(self, function: callable) -> None:
        """
        Add function which will be called when event is detected

        Args:
            function (callable): ["Function to call"]
        """
        self.__call_on_update.append(function)

    def __add_observer(self, add_observer_to: AddressableLeaf) -> None:
        add_observer_to.addObserver(
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

    def __call_update_functions(self, address) -> None:
        for function in self.__call_on_update:
            function(self._data[address])

    def __update_value(self, element: AddressableAttribute) -> None:
        value = element.value
        address = element.getGlobalAddress()
        self._data[address].value = value.value if isinstance(value, Enum) else value
        self.__call_update_functions(address)
