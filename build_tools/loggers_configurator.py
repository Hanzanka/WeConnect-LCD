import logging


def load_loggers(config: dict) -> None:
    '''
    Configures the loggers used to log app's events.

    Args:
        config (dict): Configurations for the loggers.
    '''
    
    logs_path = config["paths"]["application_logs"]

    base_formatter = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s.%(msecs)03d | %(message)s",
        datefmt="%d.%m.%Y | %H:%M:%S",
    )
    all_logs_formatter = logging.Formatter(
        fmt="%(levelname)s | %(asctime)s.%(msecs)03d | %(name)s | %(message)s",
        datefmt="%d.%m.%Y | %H:%M:%S",
    )

    all_logs_file_handler = logging.FileHandler(logs_path + "all.log")
    all_logs_file_handler.setFormatter(all_logs_formatter)

    exceptions_file_handler = logging.FileHandler(logs_path + "exceptions.log")
    exceptions_file_handler.setLevel(logging.ERROR)
    exceptions_file_handler.setFormatter(all_logs_formatter)

    logger_names = [
        "main",
        "vehicle",
        "climate",
        "led",
        "weconnect_updater",
        "lcd_controller",
        "button",
        "vehicle_data_logger",
        "data_properties",
        "lcd_scene_controller",
        "lcd_scene",
        "lcd_item",
        "scene_builder",
        "lcd_message",
        "lcd_status_bar",
        "spot_price_provider"
    ]
    
    for logger_name in logger_names:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG)
        file_handler = logging.FileHandler(logs_path + logger_name + ".log")
        file_handler.setFormatter(base_formatter)
        logger.addHandler(file_handler)
        logger.addHandler(all_logs_file_handler)
        logger.addHandler(exceptions_file_handler)
        logger.addHandler(logging.StreamHandler())
