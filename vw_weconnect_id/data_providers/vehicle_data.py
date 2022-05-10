from weconnect.elements.vehicle import Vehicle
from weconnect.addressable import AddressableLeaf, AddressableAttribute


class WeconnectVehicleData:
    def __init__(self, vehicle: Vehicle, add_observer_to: AddressableLeaf) -> None:
        self._vehicle = vehicle
        self._data = {}
        self.__add_observer(add_observer_to)

    def get_data(self) -> dict:
        """
        Get data from vehicle

        Returns:
            dict: ["Dict that contains weconnect_vehicle_data_property objects"]
        """
        data = {}
        for item in self._data.values():
            if isinstance(item, list):
                for list_item in item:
                    data[list_item.data_id] = list_item
            else:
                data[item.data_id] = item
        return data

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

    def __update_value(self, element: AddressableAttribute) -> None:
        if isinstance(self._data[element.getGlobalAddress()], list):
            for item in self._data[element.getGlobalAddress()]:
                item.update_value(element.value)
        else:
            self._data[element.getGlobalAddress()].update_value(element.value)
