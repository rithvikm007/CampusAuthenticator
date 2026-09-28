import os

from dotenv import load_dotenv

from storage.config import load_config


load_dotenv()


saved_config = load_config()


if saved_config:

    USERNAME = saved_config.get("username")
    PASSWORD = saved_config.get("password")

else:

    USERNAME = None
    PASSWORD = None


PORTAL_IP = os.getenv("PORTAL_IP")
PORTAL_PORT = os.getenv("PORTAL_PORT")


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
        "Missing configuration in .env: " + ", ".join(missing)
    )


PORTAL_PORT = int(PORTAL_PORT)

PORTAL_URL = f"http://{PORTAL_IP}:{PORTAL_PORT}/"