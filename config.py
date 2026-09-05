import os
from dotenv import load_dotenv


load_dotenv()


# WiFi configuration

HOSTEL_SSID = os.getenv("HOSTEL_SSID")


# Campus portal

PORTAL_IP = os.getenv("PORTAL_IP")
PORTAL_PORT = os.getenv("PORTAL_PORT")


# Credentials

USERNAME = os.getenv("CAMPUS_USERNAME")
PASSWORD = os.getenv("CAMPUS_PASSWORD")


# Validate configuration

required_config = {
    "HOSTEL_SSID": HOSTEL_SSID,
    "PORTAL_IP": PORTAL_IP,
    "PORTAL_PORT": PORTAL_PORT,
    "CAMPUS_USERNAME": USERNAME,
    "CAMPUS_PASSWORD": PASSWORD,
}


missing = [
    key
    for key, value in required_config.items()
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