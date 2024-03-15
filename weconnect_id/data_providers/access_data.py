from __future__ import annotations
from typing import TYPE_CHECKING

from weconnect.elements.vehicle import Vehicle

if TYPE_CHECKING:
    from weconnect.elements.access_status import AccessStatus
from weconnect_id.data_providers.vehicle_data import (
    WeConnectVehicleData,
)
from weconnect_id.data_providers.vehicle_data_property import (
    WeConnectVehicleDataProperty,
)
import logging


LOG = logging.getLogger("data_properties")


class WeConnectAccessData(WeConnectVehicleData):
    def __init__(self, vehicle: Vehicle) -> None:
        super().__init__(vehicle)
        self.__import_data()

    def __import_data(self) -> None:
        LOG.debug(f"Importing access data (Vehicle: {self._vehicle.nickname})")
        access_data = self._vehicle.domains["access"]
        self._data.update(
            self.__get_access_status_data(access_status=access_data["accessStatus"])
        )

    def __get_access_status_data(self, access_status: AccessStatus) -> dict:
        access_status_data = {}
        weconnect_element = access_status.overallStatus
        access_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="overallAccessStatus",
                weconnect_element=weconnect_element,
                category="access",
                desc="Overall safety status",
            )
        )
        weconnect_element = access_status.doorLockStatus
        access_status_data[weconnect_element.getGlobalAddress()] = (
            WeConnectVehicleDataProperty(
                id="doorLockStatus",
                weconnect_element=weconnect_element,
                category="access",
                desc="Overall lock status of the doors",
            )
        )
        return access_status_data
