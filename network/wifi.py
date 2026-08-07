import subprocess
import re

from config import HOSTEL_SSID


def get_current_wifi():
    """
    Returns current WiFi information.

    Returns:
    {
        "connected": bool,
        "ssid": str | None
    }
    """

    try:
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )

        output = result.stdout

        # Extract connection state
        state_match = re.search(
            r"^\s*State\s*:\s*(.+)$",
            output,
            re.MULTILINE
        )

        if not state_match:
            return {
                "connected": False,
                "ssid": None
            }

        state = state_match.group(1).strip().lower()

        if state != "connected":
            return {
                "connected": False,
                "ssid": None
            }

        # Extract SSID
        ssid_match = re.search(
            r"^\s*SSID\s*:\s*(.+)$",
            output,
            re.MULTILINE
        )

        if not ssid_match:
            return {
                "connected": True,
                "ssid": None
            }

        return {
            "connected": True,
            "ssid": ssid_match.group(1).strip()
        }

    except Exception as e:
        print(f"WiFi detection error: {e}")

        return {
            "connected": False,
            "ssid": None
        }


def is_hostel_wifi():
    """
    Returns True if connected to the configured hostel WiFi.
    """

    wifi = get_current_wifi()

    return (
        wifi["connected"]
        and wifi["ssid"] == HOSTEL_SSID
    )


if __name__ == "__main__":

    info = get_current_wifi()

    print(info)

    if is_hostel_wifi():
        print("Hostel WiFi detected")
    else:
        print("Not connected to hostel WiFi")