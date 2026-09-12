import threading
import time
from enum import Enum

from network.events import watch_network_events
from network.wifi import (
    get_current_ssid,
    is_hostel_wifi
)
from notifications import notify
from portal.client import PortalClient


AUTO_LOGIN_COOLDOWN = 5 * 60


class AuthState(Enum):

    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"
    AUTHENTICATING = "Authenticating"
    AUTHENTICATED = "Authenticated"


class AuthController:

    def __init__(self):

        self.state = AuthState.DISCONNECTED
        self.wifi_connected = False
        self.ssid = None
        self.keepalive_active = False

        self.client = PortalClient()

        self.event_lock = threading.Lock()

        self.running = False
        self.worker_thread = None
        self.stop_event = threading.Event()

        self.auto_login_blocked_until = 0

    def get_status(self):

        cooldown_remaining = max(
            0,
            int(
                self.auto_login_blocked_until
                - time.monotonic()
            )
        )

        return {
            "state": self.state,
            "wifi_connected": self.wifi_connected,
            "ssid": self.ssid,
            "keepalive_active": (
                self.client._keepalive_thread
                is not None
            ),
            "auto_login_blocked": (
                cooldown_remaining > 0
            ),
            "cooldown_remaining": cooldown_remaining,
        }

    def handle_event(self, status):

        if self.stop_event.is_set():
            return

        with self.event_lock:

            print(
                f"\nEvent: {status}"
                f"  [state={self.state.value}]"
            )

            if status == "Connected":

                self._on_connected()

            elif status == "Disconnected":

                self._on_disconnected()

    def _on_connected(self):

        if self.stop_event.is_set():
            return

        self.ssid = get_current_ssid()

        if not is_hostel_wifi():

            self.wifi_connected = False
            self.ssid = None

            print(
                "Not hostel WiFi — ignoring"
            )

            return

        self.wifi_connected = True

        print(
            "Connected to:",
            self.ssid
        )

        if self.state == AuthState.AUTHENTICATED:

            print(
                "Already authenticated — "
                "verifying session..."
            )

            if self.client.check_auth():

                print(
                    "Session still valid — "
                    "ignoring event"
                )

                return

            print(
                "Session expired (likely during sleep). "
                "Re-authenticating..."
            )

            self.client.stop_keepalive()

            self.state = AuthState.DISCONNECTED
            self.keepalive_active = False

        if self.state == AuthState.AUTHENTICATING:

            print(
                "Authentication in progress — "
                "ignoring"
            )

            return

        if self.auto_login_blocked_until > time.monotonic():

            remaining = int(
                self.auto_login_blocked_until
                - time.monotonic()
            )

            print(
                "Automatic login temporarily blocked — "
                f"{remaining} seconds remaining"
            )

            self.state = AuthState.CONNECTED

            return

        print(
            "Waiting for network to stabilize..."
        )

        if self.stop_event.wait(5):
            return

        self.ssid = get_current_ssid()

        if not is_hostel_wifi():

            self._on_disconnected()
            return

        if self.auto_login_blocked_until > time.monotonic():

            print(
                "Automatic login was blocked "
                "while network stabilized"
            )

            self.state = AuthState.CONNECTED

            return

        if self.client.keepalive_url:

            if self.client.recover_session():

                self.state = AuthState.AUTHENTICATED

                self.client.start_keepalive()

                self.keepalive_active = True

                print(
                    "Previous session recovered — "
                    "keepalive running"
                )

                return

        print(
            "Checking network connectivity..."
        )

        if self.client.check_auth():

            print(
                "Internet is already working."
            )

            print(
                "Already authenticated, but no "
                "keepalive URL is available"
            )

            self.state = AuthState.CONNECTED

            return

        self.state = AuthState.AUTHENTICATING

        print(
            "Hostel WiFi detected — "
            "authenticating..."
        )

        self._authenticate_with_retry()

    def _authenticate_with_retry(self):

        max_attempts = 5

        for attempt in range(
            1,
            max_attempts + 1
        ):

            if self.stop_event.is_set():
                return False

            if self.auto_login_blocked_until > time.monotonic():

                print(
                    "Automatic login blocked"
                )

                self.state = AuthState.CONNECTED

                return False

            self.ssid = get_current_ssid()

            if not is_hostel_wifi():

                self.state = AuthState.DISCONNECTED
                self.wifi_connected = False
                self.ssid = None

                return False

            print(
                f"Authentication attempt "
                f"{attempt}/{max_attempts}"
            )

            success = self.client.login()

            if success:

                self.state = AuthState.AUTHENTICATED

                self.client.start_keepalive()

                self.keepalive_active = True

                print(
                    "Authentication successful — "
                    "keepalive running"
                )

                notify(
                    "Authentication successful",
                    "CampusAuthenticator is now connected."
                )

                return True

            if attempt < max_attempts:

                print(
                    "Authentication failed — "
                    "waiting before retry..."
                )

                if self.stop_event.wait(5):
                    return False

        self.state = AuthState.CONNECTED
        self.keepalive_active = False

        print(
            "Authentication failed after "
            f"{max_attempts} attempts"
        )

        notify(
            "Authentication failed",
            f"Could not authenticate after "
            f"{max_attempts} attempts."
        )

        return False

    def _on_disconnected(self):

        self.wifi_connected = False
        self.ssid = None

        if self.state == AuthState.AUTHENTICATED:

            print(
                "WiFi disconnected — "
                "stopping keepalive and logging out..."
            )

            self.client.stop_keepalive()

            self.keepalive_active = False

            logout_success = self.client.logout()

            if logout_success:

                notify(
                    "Logged out",
                    "Wi-Fi disconnected. "
                    "CampusAuthenticator logged out."
                )

            else:

                notify(
                    "Logout unavailable",
                    "Wi-Fi disconnected before "
                    "CampusAuthenticator could reach FortiGate."
                )

        elif self.state == AuthState.AUTHENTICATING:

            print(
                "WiFi disconnected during authentication"
            )

            self.client.stop_keepalive()
            self.keepalive_active = False

        self.state = AuthState.DISCONNECTED

        print(
            "WiFi disconnected — "
            "ready to reconnect"
        )

    def login(self):

        with self.event_lock:

            if self.stop_event.is_set():
                return False

            if self.state == AuthState.AUTHENTICATED:

                print(
                    "Already authenticated"
                )

                return True

            self.auto_login_blocked_until = 0

            self.ssid = get_current_ssid()

            if not is_hostel_wifi():

                self.wifi_connected = False
                self.ssid = None

                print(
                    "Not connected to hostel WiFi"
                )

                return False

            self.wifi_connected = True

            print(
                "Manual login requested"
            )

            self.state = AuthState.AUTHENTICATING

            return self._authenticate_with_retry()

    def disconnect(self):

        with self.event_lock:

            if self.state == AuthState.AUTHENTICATING:

                print(
                    "Cannot log out while "
                    "authentication is in progress"
                )

                return False

            if self.state != AuthState.AUTHENTICATED:

                print(
                    "No active authenticated session"
                )

                return False

            print(
                "Manual logout requested..."
            )

            self.client.stop_keepalive()

            self.keepalive_active = False

            success = self.client.logout()

            if not success:

                print(
                    "Manual logout failed"
                )

                return False

            self.auto_login_blocked_until = (
                time.monotonic()
                + AUTO_LOGIN_COOLDOWN
            )

            self.wifi_connected = is_hostel_wifi()

            self.ssid = (
                get_current_ssid()
                if self.wifi_connected
                else None
            )

            self.state = (
                AuthState.CONNECTED
                if self.wifi_connected
                else AuthState.DISCONNECTED
            )

            print(
                "Manual logout successful"
            )

            print(
                "Automatic login blocked for "
                f"{AUTO_LOGIN_COOLDOWN // 60} minutes"
            )

            notify(
                "Logged out",
                "CampusAuthenticator logged out. "
                "Automatic login is paused for 5 minutes."
            )

            return True

    def run(self):

        if self.running:
            return

        self.running = True
        self.stop_event.clear()

        print(
            "CampusAuthenticator started\n"
        )

        print(
            "Checking initial network state..."
        )

        self.ssid = get_current_ssid()

        if is_hostel_wifi():

            self.wifi_connected = True

            print(
                "Already connected to hostel WiFi"
            )

            print(
                "SSID:",
                self.ssid
            )

            if self.client.keepalive_url:

                print(
                    "Previous session found — "
                    "attempting session recovery..."
                )

                if self.client.recover_session():

                    self.state = AuthState.AUTHENTICATED

                    self.client.start_keepalive()

                    self.keepalive_active = True

                    print(
                        "Previous session recovered — "
                        "keepalive running"
                    )

                else:

                    print(
                        "Previous session could not "
                        "be recovered"
                    )

            if self.state != AuthState.AUTHENTICATED:

                print(
                    "Checking network connectivity..."
                )

                if self.client.check_auth():

                    print(
                        "Internet is already working."
                    )

                    self.state = AuthState.CONNECTED

                    print(
                        "Already authenticated, but no "
                        "known FortiGate session is available"
                    )

                else:

                    print(
                        "Not authenticated. "
                        "Authenticating now..."
                    )

                    self._authenticate_with_retry()

        else:

            self.wifi_connected = False
            self.ssid = None

            print(
                "Not connected to hostel WiFi"
            )

        try:

            watch_network_events(
                self.handle_event,
                self.stop_event
            )

        finally:

            self._shutdown()

    def start(self):

        if (
            self.worker_thread is not None
            and self.worker_thread.is_alive()
        ):
            return

        self.stop_event.clear()

        self.worker_thread = threading.Thread(
            target=self.run,
            daemon=True,
            name="AuthController"
        )

        self.worker_thread.start()

    def stop(self):

        if not self.running:
            return

        print(
            "Stopping CampusAuthenticator..."
        )

        self.stop_event.set()

        if self.worker_thread:

            self.worker_thread.join(
                timeout=15
            )

    def _shutdown(self):

        print(
            "\nShutting down..."
        )

        if self.state == AuthState.AUTHENTICATED:

            self.client.stop_keepalive()
            self.client.logout()

        elif self.state == AuthState.AUTHENTICATING:

            self.client.stop_keepalive()

        self.keepalive_active = False
        self.running = False

        print(
            "Goodbye"
        )