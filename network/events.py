import os
import time

import wmi


def create_watcher():
    """
    Create a fresh WMI connection and network event watcher.

    A WMI event subscription can become invalid after events
    such as Sleep/Hibernate or other WMI/COM interruptions.

    When that happens, the old watcher is discarded and a new
    WMI connection and watcher are created.
    """

    c = wmi.WMI()

    watcher = c.watch_for(
        notification_type="Modification",
        wmi_class="Win32_NetworkAdapter",
        delay_secs=1
    )

    return watcher


def watch_network_events(callback):

    print("Network event listener started")

    states = {
        0: "Disconnected",
        1: "Connecting",
        2: "Connected",
        3: "Disconnecting",
        7: "Disconnected",
    }

    watcher = create_watcher()

    while True:

        # Check for a requested shutdown before entering
        # the WMI wait call.
        if os.path.exists("stop.flag"):

            print(
                "Stop flag detected. "
                "Stopping event listener..."
            )

            os.remove("stop.flag")

            break

        try:

            event = watcher(timeout_ms=1000)

        except wmi.x_wmi_timed_out:

            # Normal timeout.
            #
            # The 1-second timeout allows us to periodically
            # check for stop.flag.
            continue

        except wmi.x_wmi as e:

            # The WMI event subscription has failed.
            #
            # This can happen when the underlying WMI/COM
            # subscription gets cancelled, for example after
            # certain Sleep/Hibernate or network subsystem
            # transitions.
            print(
                "WMI event watcher error:",
                repr(e)
            )

            print(
                "Recreating network event watcher..."
            )

            time.sleep(2)

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

                time.sleep(5)

            continue

        # Ignore adapters without a usable name.
        if not event.Name:
            continue

        # Only handle Wi-Fi adapter events.
        if "Wi-Fi" not in event.Name:
            continue

        status = states.get(
            event.NetConnectionStatus,
            "Unknown"
        )

        callback(status)


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