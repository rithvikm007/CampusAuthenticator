import json
import os


CONFIG_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "config.json"
)


def config_exists():
    return os.path.exists(CONFIG_FILE)


def save_config(username, password):

    data = {
        "username": username,
        "password": password
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def load_config():

    if not os.path.exists(CONFIG_FILE):
        return None

    try:

        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not all(key in data for key in ("username", "password")):
            return None

        return {
            "username": data["username"],
            "password": data["password"]
        }

    except (json.JSONDecodeError, OSError):
        return None


def clear_config():

    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)


if __name__ == "__main__":

    print("Config file:", CONFIG_FILE)
    print("Config exists:", config_exists())