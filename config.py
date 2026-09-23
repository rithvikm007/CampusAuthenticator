import os

from dotenv import load_dotenv

from storage.config import load_config


load_dotenv()


# Application configuration

saved_config = load_config()


if saved_config:

    HOSTEL_SSID = saved_config.get(
        "ssid"
    )

    USERNAME = saved_config.get(
        "username"
    )

    PASSWORD = saved_config.get(
        "password"
    )

else:

    HOSTEL_SSID = None
    USERNAME = None
    PASSWORD = None


# Campus portal

PORTAL_IP = os.getenv("PORTAL_IP")
PORTAL_PORT = os.getenv("PORTAL_PORT")


# Validate portal configuration

required_portal_config = {
    "PORTAL_IP": PORTAL_IP,
    "PORTAL_PORT": PORTAL_PORT,
}


missing = [
    key
    for key, value in required_portal_config.items()
    if value is None
]


if missing:

    raise RuntimeError(
        "Missing configuration in .env: "
        + ", ".join(missing)
    )


# Convert port from string to integer

PORTAL_PORT = int(PORTAL_PORT)


# Construct portal URL

PORTAL_URL = (
    f"http://{PORTAL_IP}:{PORTAL_PORT}/"
)