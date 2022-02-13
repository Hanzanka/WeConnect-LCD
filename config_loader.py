import json
import logging


class ConfigLoaderError(Exception):
    def __init__(self, message) -> None:
        super().__init__(message)
        self.message = message


class ConfigLoader:
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
            raise e

    def save_config(config_dict=None) -> None:
        """
        Saves items from given config_dict to config.json

        Args:
            config_dict (dict, optional): [Dict containing changed config items]. Defaults to None.
        """
        if config_dict is None:
            config_dict = ConfigLoader.load_config()
        with open("config.json", "w") as config_file:
            json.dump(
                config_dict,
                config_file,
                sort_keys=True,
                indent=4,
                separators=(",", ": "),
            )

    def edit_config(keys: list, property: str, value) -> None:
        """
        Makes changes to config.json file

        Args:
            keys (list): [keys of the config property being edited]
            property (str): [Property being edited]
            value (str/int): [New value]
        """
        config = ConfigLoader.load_config()
        replacing_dict = config
        for key in keys:
            try:
                replacing_dict = replacing_dict[key]
            except KeyError as e:
                logging.error(f"Key {key} is invalid")
                raise ConfigLoaderError(f"Couldn't edit config file {e}")
        if property not in replacing_dict.keys():
            logging.error(f"{property} -property is not in config.json")
            raise ConfigLoaderError(f"{property} -property is not in config.json")
        replacing_dict[property] = value
        ConfigLoader.save_config(config_dict=config)


if __name__ == "__main__":
    print(ConfigLoader.load_config()["paths"]["data"])
