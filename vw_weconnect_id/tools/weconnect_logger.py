import csv
from pathlib import Path
from config_loader import ConfigLoader
import os
import logging


class WeConnectLoggerError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class WeConnectCSVLogger:
    def log(data) -> None:
        '''
        Logs data from WeConnectVehicleDataProperty-object to csv file in path given in config.json

        Args:
            data (WeConnectVehicleDataProperty): [WeConnectVehicleDataProperty-object where data is logged from]

        Raises:
            WeConnectLoggerError: [Raised if creating dir to given path fails]
            WeConnectLoggerError: [Raised if something fails when writing to .csv-file]
        '''
        logging.info(f"Logging data from property '{data.data_id}'")
        dir_path = Path(
            ConfigLoader.load_config()["paths"]["data"] + f"/{data.category}"
        )
        if not dir_path.is_dir():
            try:
                logging.info(f"Creating new folder to {dir_path}")
                os.mkdir(dir_path)
            except OSError as e:
                logging.error(
                    f"Error occurred while trying to create directory in path {dir_path}\n{e}"
                )
                raise WeConnectLoggerError(
                    f"Error occurred while trying to create directory in path {dir_path}\n{e}"
                )
        
        file_path = Path(str(dir_path) + f"/{data.data_id.replace(' ', '_')}.csv")
        exists = file_path.is_file()
        
        try:
            with open(file_path, "a") as csv_file:
                writer = csv.writer(csv_file, delimiter=";")
                if not exists:
                    writer.writerow(("value", "time", "date"))
                logging.info(f"Writing data to {file_path}")
                writer.writerow(data.data_as_tuple())
        except Exception as e:
            logging.error(
                f"Error occurred while trying to log data into file in path {file_path}\n{e}"
            )
            raise WeConnectLoggerError(
                f"Error occurred while trying to log data into file in path {file_path}\n{e}"
            )
