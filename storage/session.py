import json

from core.paths import data_path


SESSION_FILE = data_path(
    "storage",
    "session.json"
)


def save_session(keepalive_url):

    """
    Save the current FortiGate session information.
    """

    data = {
        "keepalive_url": keepalive_url
    }

    with open(
        SESSION_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


def load_session():

    """
    Load the previously saved FortiGate session.

    Returns:
        keepalive_url if one exists,
        otherwise None.
    """

    if not SESSION_FILE.exists():
        return None

    try:

        with open(
            SESSION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data.get(
            "keepalive_url"
        )

    except (
        json.JSONDecodeError,
        OSError
    ):

        return None


def clear_session():

    """
    Delete the persisted FortiGate session.
    """

    if SESSION_FILE.exists():
        SESSION_FILE.unlink()


if __name__ == "__main__":

    test_url = (
        "http://192.168.116.1:1000/"
        "keepalive?TEST_SESSION_123"
    )

    print("Saving session...")

    save_session(
        test_url
    )

    print("Loading session...")

    print(
        load_session()
    )

    print("Clearing session...")

    clear_session()

    print("Loading after clear...")

    print(
        load_session()
    )