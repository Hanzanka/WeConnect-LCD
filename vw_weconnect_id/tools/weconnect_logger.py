import csv
from pathlib import Path
import os
import logging


class WeConnectLoggerError(Exception):
    pass


logger = logging.getLogger("datalogger")


def log(data_property) -> None:
    """
    Logs data from WeConnectVehicleDataProperty-object to csv file in given path

    Args:
        data (WeConnectVehicleDataProperty): [WeConnectVehicleDataProperty-object where data is logged from]

    Raises:
        WeConnectLoggerError: [Raised if creating dir to given path fails or if writing to file fails]
    """
    path = data_property.logger_path
    logger.info(f"Logging data from property '{data_property.data_id}'")
    dir_path = Path(path + f"/{data_property.category}")
    if not dir_path.is_dir():
        try:
            logger.info(f"Creating new folder to path {dir_path}")
            os.mkdir(dir_path)
        except OSError as e:
            logger.exception(e)
            raise WeConnectLoggerError(f"Error occurred while trying to create directory in path {dir_path}")

    file_path = Path(str(dir_path) + f"/{data_property.data_id.replace(' ', '_')}.csv")
    exists = file_path.is_file()

    try:
        with open(file_path, "a") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            if not exists:
                writer.writerow(("value", "time", "date"))
            logger.info(f"Writing data to {file_path}")
            writer.writerow(data_property.get_logging_data())
    except Exception as e:
        logger.exception(e)
        raise WeConnectLoggerError(f"Error occurred while trying to log data into file in path {file_path}")
