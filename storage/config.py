import json
import os


CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "config.json"
)


def config_exists():
    """
    Check whether a saved application configuration exists.
    """

    return os.path.exists(CONFIG_FILE)


def save_config(
    ssid,
    username,
    password
):
    """
    Save application configuration.
    """

    data = {
        "ssid": ssid,
        "username": username,
        "password": password
    }

    with open(
        CONFIG_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


def load_config():
    """
    Load the saved application configuration.

    Returns:
        Configuration dictionary if valid,
        otherwise None.
    """

    if not os.path.exists(CONFIG_FILE):
        return None

    try:

        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not all(
            key in data
            for key in (
                "ssid",
                "username",
                "password"
            )
        ):

            return None

        return data

    except (
        json.JSONDecodeError,
        OSError
    ):

        return None


def clear_config():
    """
    Delete the saved application configuration.
    """

    if os.path.exists(CONFIG_FILE):

        os.remove(CONFIG_FILE)


if __name__ == "__main__":

    print(
        "Config file:",
        CONFIG_FILE
    )

    print(
        "Config exists:",
        config_exists()
    )