import subprocess

from config import HOSTEL_SSID


def get_current_ssid():

    try:

        result = subprocess.run(
            [
                "netsh",
                "wlan",
                "show",
                "interfaces"
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        for line in result.stdout.splitlines():

            line = line.strip()

            if line.startswith("SSID") and not line.startswith("BSSID"):

                return line.split(":", 1)[1].strip()

    except Exception as e:

        print(
            "Failed to get current SSID:",
            repr(e)
        )

    return None


def is_hostel_wifi():

    ssid = get_current_ssid()

    return ssid == HOSTEL_SSID


if __name__ == "__main__":

    print(
        "Current SSID:",
        get_current_ssid()
    )

    print(
        "Hostel WiFi:",
        is_hostel_wifi()
    )