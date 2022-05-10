import logging


def load_loggers(config: dict) -> None:
    logs = config["paths"]["logs"]

    formatter = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s.%(msecs)03d | %(message)s",
        datefmt="%d.%m.%Y | %H:%M:%S",
    )
    formatter_all = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s.%(msecs)03d | %(name)s | %(message)s",
        datefmt="%d.%m.%Y | %H:%M:%S",
    )

    file_handler_all = logging.FileHandler(logs + "all.log")
    file_handler_all.setFormatter(formatter_all)

    logger_names = [
        "main",
        "vehicle",
        "climate",
        "exception",
        "led",
        "weconnect updater",
        "display",
        "button",
        "datalogger",
        "data property"
    ]
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(logs + logger_name + ".log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.addHandler(file_handler_all)
