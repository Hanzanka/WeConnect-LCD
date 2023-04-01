from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from data_providers.vehicle_data_property import WeConnectVehicleDataProperty

import csv
from pathlib import Path
import os
import logging


class WeConnectLoggerError(Exception):
    pass


LOG = logging.getLogger("vehicle_data_logger")


def log(data_property: WeConnectVehicleDataProperty) -> None:
    '''
    Used to log data from WeConnectVehicleDataProperties

    Args:
        data_property (WeConnectVehicleDataProperty): WeConnectVehicleDataProperty where the data is logged from.
    '''
    
    path = data_property.logger_path
    LOG.debug(
        f"Logging data from WeconnectVehicleDataProperty (ID: {data_property.id})"
    )
    dir_path = Path(path + f"/{data_property.category}")
    if not dir_path.is_dir():
        try:
            LOG.info(f"Creating new folder (PATH: {dir_path})")
            os.mkdir(dir_path)
        except OSError as e:
            LOG.exception(e)

    file_path = Path(str(dir_path) + f"/{data_property.id.replace(' ', '_')}.csv")
    exists = file_path.is_file()

    try:
        with open(file_path, "a") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            if not exists:
                writer.writerow(("value", "time", "date"))
            LOG.debug(
                f"Writing data from WeconnectVehicleDataProperty (ID: {data_property.id}) to (PATH: {file_path})"
            )
            writer.writerow(data_property.logger_value_format)
    except Exception as e:
        LOG.exception(e)
