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


def _is_virtual_adapter(adapter):
    """
    Returns True if the adapter appears to be a virtual/VPN adapter.
    """
    name = (adapter.Name or "").lower()
    connection_id = (adapter.NetConnectionID or "").lower()

    virtual_keywords = (
        "virtual",
        "vmware",
        "virtualbox",
        "hyper-v",
        "hyperv",
        "vpn",
        "tun",
        "tap",
        "anyconnect",
        "loopback",
        "wi-fi direct",
        "bluetooth",
    )

    return any(
        keyword in name or keyword in connection_id
        for keyword in virtual_keywords
    )


def get_active_interface():
    """
    Returns the active physical network interface type:

        "Wi-Fi"
        "Ethernet"
        None

    The active interface is determined from the IPv4 default route.
    Virtual/VPN adapters are ignored.

    NetConnectionID is preferred for determining Wi-Fi vs Ethernet
    because AdapterTypeID is not reliable across all Windows drivers.
    """
    try:
        c = wmi.WMI()

        # Find IPv4 default routes.
        routes = [
            route
            for route in c.Win32_IP4RouteTable()
            if route.Destination == "0.0.0.0"
            and route.Mask == "0.0.0.0"
        ]

        # Lower route metric = preferred route.
        routes.sort(
            key=lambda route: int(getattr(route, "Metric1", 999999))
        )

        for route in routes:
            interface_index = route.InterfaceIndex

            adapters = c.Win32_NetworkAdapter(
                InterfaceIndex=interface_index
            )

            if not adapters:
                continue

            adapter = adapters[0]

            # Ignore disconnected adapters.
            if adapter.NetConnectionStatus != 2:
                continue

            # Ignore VPN/virtual adapters.
            if _is_virtual_adapter(adapter):
                continue

            connection_id = (
                adapter.NetConnectionID or ""
            ).strip().lower()

            adapter_name = (
                adapter.Name or ""
            ).strip().lower()

            # NetConnectionID is the most reliable indicator here.
            if connection_id == "wi-fi":
                return "Wi-Fi"

            if connection_id == "ethernet":
                return "Ethernet"

            # Handle variants such as "Ethernet 2", "Ethernet 3", etc.
            if connection_id.startswith("ethernet"):
                return "Ethernet"

            # Fallback for Wi-Fi adapter names.
            if (
                "wi-fi" in connection_id
                or "wireless" in connection_id
                or "wi-fi" in adapter_name
                or "wireless" in adapter_name
                or "802.11" in adapter_name
            ):
                return "Wi-Fi"

            # Final fallback using AdapterTypeID.
            adapter_type = getattr(
                adapter,
                "AdapterTypeID",
                None
            )

            if adapter_type == 9:
                return "Wi-Fi"

            if adapter_type == 0:
                return "Ethernet"

        return None

    except Exception as e:
        print(
            "Failed to detect active network interface:",
            repr(e)
        )
        return None


def watch_network_events(callback, stop_event):
    print("Network event listener started")

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
            event = watcher(timeout_ms=1000)

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

                # ------------------------------------------------------
                # Reconcile the current network state.
                #
                # A WMI watcher can fail during hibernate/resume.
                # Network changes that occurred while the watcher was
                # unavailable may therefore never generate an event.
                #
                # Check the current physical interface once after
                # recreating the watcher and feed the result through
                # the existing controller event path.
                # ------------------------------------------------------

                active_interface = get_active_interface()

                if active_interface:

                    print(
                        "Network state after WMI recovery:",
                        active_interface
                    )

                    callback(
                        "Connected",
                        active_interface
                    )

                else:

                    print(
                        "No active physical network interface "
                        "after WMI recovery"
                    )

                    callback(
                        "Disconnected"
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

        # Ignore virtual adapters such as VPN, Hyper-V,
        # VirtualBox, etc.
        if hasattr(event, "PhysicalAdapter"):

            if not event.PhysicalAdapter:
                continue

        status = states.get(
            event.NetConnectionStatus,
            "Unknown"
        )

        if status not in (
            "Connected",
            "Disconnected"
        ):
            continue

        # Determine the current physical interface when a
        # connection event is received.
        interface = None

        if status == "Connected":
            interface = get_active_interface()

        callback(
            status,
            interface
        )

    print(
        "Network event listener stopped"
    )


if __name__ == "__main__":

    stop_event = __import__("threading").Event()

    def test_callback(status, interface=None):
        print(
            "Network status:",
            status,
            "| Interface:",
            interface
        )

    print(
        "Active interface:",
        get_active_interface()
    )

    watch_network_events(
        test_callback,
        stop_event
    )