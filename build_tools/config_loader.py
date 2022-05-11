import json


class ConfigLoaderError(Exception):
    pass


def load_config() -> dict:
    """
    Loads config from config.json-file

    Raises:
        e: [Raised if reading config fails]

    Returns:
        dict: [Dict containing config]
    """
    try:
        with open("config.json", "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError as e:
        raise ConfigLoaderError(e)
