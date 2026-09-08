import json
import os


SESSION_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
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

    if not os.path.exists(SESSION_FILE):
        return None

    try:

        with open(
            SESSION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data.get("keepalive_url")

    except (json.JSONDecodeError, OSError):

        return None


def clear_session():
    """
    Delete the persisted FortiGate session.
    """

    if os.path.exists(SESSION_FILE):

        os.remove(SESSION_FILE)


if __name__ == "__main__":

    test_url = (
        "http://192.168.116.1:1000/"
        "keepalive?TEST_SESSION_123"
    )

    print("Saving session...")
    save_session(test_url)

    print("Loading session...")
    print(load_session())

    print("Clearing session...")
    clear_session()

    print("Loading after clear...")
    print(load_session())