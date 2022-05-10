import logging


def load_loggers(config: dict) -> None:
    logs_path = config["paths"]["application_logs"]

    formatter = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s.%(msecs)03d | %(message)s",
        datefmt="%d.%m.%Y | %H:%M:%S",
    )
    formatter_all = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s.%(msecs)03d | %(name)s | %(message)s",
        datefmt="%d.%m.%Y | %H:%M:%S",
    )

    file_handler_all = logging.FileHandler(logs_path + "all.log")
    file_handler_all.setFormatter(formatter_all)

    file_handler_exceptions = logging.FileHandler(logs_path + "exceptions.log")
    file_handler_exceptions.setLevel(logging.ERROR)
    file_handler_exceptions.setFormatter(formatter_all)

    logger_names = [
        "main",
        "vehicle",
        "climate",
        "led",
        "weconnect_updater",
        "display",
        "button",
        "datalogger",
        "data_properties",
        "scene_controller"
    ]
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(logs_path + logger_name + ".log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(file_handler_all)
        logger.addHandler(file_handler_exceptions)
