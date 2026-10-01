import json

from core.paths import data_path


CONFIG_FILE = data_path(
    "storage",
    "config.json"
)


def config_exists():

    return CONFIG_FILE.exists()


def save_config(username, password):

    data = {
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

    if not CONFIG_FILE.exists():
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
            for key in ("username", "password")
        ):
            return None

        return {
            "username": data["username"],
            "password": data["password"]
        }

    except (
        json.JSONDecodeError,
        OSError
    ):

        return None


def clear_config():

    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


if __name__ == "__main__":

    print(
        "Config file:",
        CONFIG_FILE
    )

    print(
        "Config exists:",
        config_exists()
    )