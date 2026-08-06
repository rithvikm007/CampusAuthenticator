import subprocess
import re


def get_wifi_info():
    """
    Returns current WiFi information.

    Output:
    {
        "connected": True/False,
        "ssid": "GalaxyS21FE"
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

        # Check connection state
        if "State" not in output:
            return {
                "connected": False,
                "ssid": None
            }

        if "connected" not in output:
            return {
                "connected": False,
                "ssid": None
            }

        # Extract SSID
        match = re.search(
            r"^\s*SSID\s*:\s*(.+)$",
            output,
            re.MULTILINE
        )

        if match:
            ssid = match.group(1).strip()

            return {
                "connected": True,
                "ssid": ssid
            }

        return {
            "connected": True,
            "ssid": None
        }

    except Exception as e:
        print("WiFi detection error:", e)

        return {
            "connected": False,
            "ssid": None
        }


if __name__ == "__main__":

    from config import HOSTEL_SSID

    info = get_wifi_info()

    print(info)

    if info["ssid"] == HOSTEL_SSID:
        print("Hostel WiFi detected")
    else:
        print("Different network")