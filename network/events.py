import time

import wmi


def create_watcher():

    c = wmi.WMI()

    watcher = c.watch_for(
        notification_type="Modification",
        wmi_class="Win32_NetworkAdapter",
        delay_secs=1
    )

    return watcher


def watch_network_events(
    callback,
    stop_event
):

    print(
        "Network event listener started"
    )

    states = {
        0: "Disconnected",
        1: "Connecting",
        2: "Connected",
        3: "Disconnecting",
        7: "Disconnected",
    }

    watcher = create_watcher()

    while not stop_event.is_set():

        try:

            event = watcher(
                timeout_ms=1000
            )

        except wmi.x_wmi_timed_out:

            continue

        except wmi.x_wmi as e:

            if stop_event.is_set():
                break

            print(
                "WMI event watcher error:",
                repr(e)
            )

            print(
                "Recreating network event watcher..."
            )

            if stop_event.wait(2):
                break

            try:

                watcher = create_watcher()

                print(
                    "Network event watcher restarted"
                )

            except Exception as recreate_error:

                print(
                    "Failed to recreate WMI watcher:",
                    repr(recreate_error)
                )

                print(
                    "Will retry watcher creation..."
                )

                if stop_event.wait(5):
                    break

            continue

        if not event.Name:
            continue

        if "Wi-Fi" not in event.Name:
            continue

        status = states.get(
            event.NetConnectionStatus,
            "Unknown"
        )

        callback(status)

    print(
        "Network event listener stopped"
    )


if __name__ == "__main__":

    import threading

    stop_event = threading.Event()

    def test_callback(status):

        print(
            "Network state changed:",
            status
        )

    try:

        watch_network_events(
            test_callback,
            stop_event
        )

    except KeyboardInterrupt:

        stop_event.set()

        print(
            "\nListener stopped"
        )