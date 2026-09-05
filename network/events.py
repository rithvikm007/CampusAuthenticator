import wmi


def watch_network_events(callback):

    print("Network event listener started")

    c = wmi.WMI()

    watcher = c.watch_for(
        notification_type="Modification",
        wmi_class="Win32_NetworkAdapter",
        delay_secs=1
    )

    states = {
        0: "Disconnected",
        1: "Connecting",
        2: "Connected",
        3: "Disconnecting",
        7: "Disconnected",
    }

    import os

    while True:
        try:
            if os.path.exists("stop.flag"):
                print("Stop flag detected. Stopping event listener...")
                os.remove("stop.flag")
                break

            event = watcher(timeout_ms=1000)

            if not event.Name:
                continue

            if "Wi-Fi" not in event.Name:
                continue

            status = states.get(
                event.NetConnectionStatus,
                "Unknown"
            )

            callback(status)


        except wmi.x_wmi_timed_out:
            continue

if __name__ == "__main__":

    def test_callback(status):
        print(
            "Network state changed:",
            status
        )

    try:
        watch_network_events(test_callback)

    except KeyboardInterrupt:
        print("\nListener stopped")