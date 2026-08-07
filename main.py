from network.events import watch_network_events
from network.wifi import is_hostel_wifi


def network_changed(status):

    print(f"\nEvent: {status}")

    if status == "Connected":

        if is_hostel_wifi():
            print("Connected to hostel WiFi")
        else:
            print("Ignoring (not hostel WiFi)")

    elif status == "Disconnected":

        print("WiFi disconnected")


if __name__ == "__main__":

    watch_network_events(network_changed)