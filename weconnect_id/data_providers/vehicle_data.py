from weconnect.elements.vehicle import Vehicle


class WeConnectVehicleData:
    def __init__(self, vehicle: Vehicle) -> None:
        self._vehicle = vehicle
        self._data = {}

    def get_data(self) -> dict:
        data = {}
        for item in self._data.values():
            if isinstance(item, list):
                for list_item in item:
                    data[list_item.id] = list_item
                continue
            data[item.id] = item
        return data
