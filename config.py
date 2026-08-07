import os
from dotenv import load_dotenv


load_dotenv()


# WiFi configuration

HOSTEL_SSID = "Galaxy S21 FE 5G"


# Campus portal

PORTAL_IP = "192.168.116.1"
PORTAL_PORT = 1000


PORTAL_URL = (
    f"http://{PORTAL_IP}:{PORTAL_PORT}/"
)


# Credentials

USERNAME = os.getenv(
    "CAMPUS_USERNAME"
)

PASSWORD = os.getenv(
    "CAMPUS_PASSWORD"
)


if USERNAME is None or PASSWORD is None:
    raise RuntimeError(
        "Campus credentials not found. Create a .env file."
    )