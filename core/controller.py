import threading
import time
from enum import Enum

from network.events import watch_network_events
from notifications import notify
from portal.client import (
    NetworkStatus,
    PortalClient
)


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

        # Used to cancel an in-progress credential-change
        # authentication when newer credentials are saved.
        self.credentials_cancel_event = threading.Event()

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

        print(
            "Network connection detected."
        )

        network_status = self.client.detect_network()

        # --------------------------------------------------------------
        # Normal Internet
        # --------------------------------------------------------------

        if network_status == NetworkStatus.INTERNET_AVAILABLE:

            print(
                "Internet is available."
            )

            # A successful connectivity probe does not necessarily
            # mean this is a non-campus network. If we have a
            # previously saved FortiGate session, try recovering it.
            if self.client.keepalive_url:

                print(
                    "Previous session found — "
                    "attempting session recovery..."
                )

                if self.client.recover_session():

                    self.wifi_connected = True
                    self.state = AuthState.AUTHENTICATED

                    if not self.keepalive_active:

                        self.client.start_keepalive()

                        self.keepalive_active = True

                    print(
                        "Previous session recovered — "
                        "campus network detected."
                    )

                    return

                print(
                    "Previous session could not be recovered — "
                    "treating network as normal Internet."
                )

                # A Disconnected event may not always be delivered
                # before a new Connected event. Make sure an old
                # keepalive is not left running in that case.
                self.client.stop_keepalive()
                self.keepalive_active = False

            self.wifi_connected = False

            if self.state == AuthState.AUTHENTICATING:

                print(
                    "Network is already online. "
                    "Stopping authentication."
                )

                self.client.stop_keepalive()
                self.keepalive_active = False

            self.state = AuthState.CONNECTED

            return

        # --------------------------------------------------------------
        # No Internet
        # --------------------------------------------------------------

        if network_status == NetworkStatus.NO_INTERNET:

            print(
                "No usable Internet connection detected — "
                "ignoring network event."
            )

            self.wifi_connected = False

            return

        # --------------------------------------------------------------
        # Captive portal / campus network
        # --------------------------------------------------------------

        print(
            "NITC captive portal detected."
        )

        self.wifi_connected = True

        # --------------------------------------------------------------
        # Already authenticated
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Authentication already running
        # --------------------------------------------------------------

        if self.state == AuthState.AUTHENTICATING:

            print(
                "Authentication in progress — "
                "ignoring"
            )

            return

        # --------------------------------------------------------------
        # Manual logout cooldown
        # --------------------------------------------------------------

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

        # --------------------------------------------------------------
        # Let the network settle
        # --------------------------------------------------------------

        print(
            "Waiting for network to stabilize..."
        )

        if self.stop_event.wait(5):
            return

        # The network may have changed during the delay.
        network_status = self.client.detect_network()

        if network_status != NetworkStatus.CAPTIVE_PORTAL:

            if network_status == NetworkStatus.INTERNET_AVAILABLE:

                print(
                    "Internet became available while "
                    "network was stabilizing."
                )

            else:

                print(
                    "Captive portal is no longer reachable."
                )

            self.wifi_connected = False

            if network_status == NetworkStatus.NO_INTERNET:
                self.state = AuthState.DISCONNECTED
            else:
                self.state = AuthState.CONNECTED

            return

        # --------------------------------------------------------------
        # Cooldown may have started while network stabilized
        # --------------------------------------------------------------

        if self.auto_login_blocked_until > time.monotonic():

            print(
                "Automatic login was blocked "
                "while network stabilized"
            )

            self.state = AuthState.CONNECTED

            return

        # --------------------------------------------------------------
        # Try recovering an existing campus session
        # --------------------------------------------------------------

        if self.client.keepalive_url:

            if self.client.recover_session():

                self.state = AuthState.AUTHENTICATED

                if not self.keepalive_active:

                    self.client.start_keepalive()

                    self.keepalive_active = True

                print(
                    "Previous session recovered — "
                    "keepalive running"
                )

                return

        # --------------------------------------------------------------
        # Check whether authentication is already valid
        # --------------------------------------------------------------

        print(
            "Checking existing authentication..."
        )

        if self.client.check_auth():

            print(
                "Internet is already working."
            )

            self.state = AuthState.AUTHENTICATED

            if self.client.keepalive_url:

                self.client.start_keepalive()

                self.keepalive_active = True

            print(
                "Already authenticated."
            )

            return

        # --------------------------------------------------------------
        # Authenticate
        # --------------------------------------------------------------

        self.state = AuthState.AUTHENTICATING

        print(
            "Campus captive portal detected — "
            "authenticating..."
        )

        self._authenticate_with_retry()

    def _authenticate_with_retry(
        self,
        cancel_event=None
    ):

        max_attempts = 5

        for attempt in range(
            1,
            max_attempts + 1
        ):

            if self.stop_event.is_set():
                return False

            if (
                cancel_event is not None
                and cancel_event.is_set()
            ):

                print(
                    "Authentication cancelled."
                )

                return False

            if self.auto_login_blocked_until > time.monotonic():

                print(
                    "Automatic login blocked"
                )

                self.state = AuthState.CONNECTED

                return False

            # Re-check the network before every attempt.
            network_status = self.client.detect_network()

            if network_status != NetworkStatus.CAPTIVE_PORTAL:

                self.wifi_connected = False

                if network_status == NetworkStatus.INTERNET_AVAILABLE:

                    print(
                        "Internet is already available — "
                        "stopping authentication."
                    )

                    self.state = AuthState.CONNECTED

                else:

                    print(
                        "Captive portal unavailable — "
                        "stopping authentication."
                    )

                    self.state = AuthState.DISCONNECTED

                return False

            print(
                f"Authentication attempt "
                f"{attempt}/{max_attempts}"
            )

            success = self.client.login()

            # Credentials may have changed while the
            # HTTP request was in progress. Never accept
            # the result of that old request.
            if (
                cancel_event is not None
                and cancel_event.is_set()
            ):

                if success:

                    self.client.stop_keepalive()
                    self.keepalive_active = False

                    self.client.logout()

                print(
                    "Authentication result discarded "
                    "because newer credentials were saved."
                )

                return False

            if success:

                self.state = AuthState.AUTHENTICATED
                self.wifi_connected = True

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

            if (
                cancel_event is not None
                and cancel_event.is_set()
            ):

                print(
                    "Authentication cancelled."
                )

                return False

            if attempt < max_attempts:

                print(
                    "Authentication failed — "
                    "waiting before retry..."
                )

                if cancel_event is not None:

                    if cancel_event.wait(5):

                        print(
                            "Authentication cancelled."
                        )

                        return False

                elif self.stop_event.wait(5):

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

    def cancel_credentials_change(self):

        self.credentials_cancel_event.set()

    def credentials_changed(self):

        # Cancel any previous credential-change operation
        # before trying to acquire event_lock.
        self.credentials_cancel_event.set()

        with self.event_lock:

            if self.stop_event.is_set():
                return False, False

            self.credentials_cancel_event = (
                threading.Event()
            )

            cancel_event = (
                self.credentials_cancel_event
            )

            print(
                "Credentials changed."
            )

            # ----------------------------------------------------------
            # If currently authenticated, invalidate the old session.
            # ----------------------------------------------------------

            if self.state == AuthState.AUTHENTICATED:

                print(
                    "Currently authenticated — "
                    "logging out of previous session..."
                )

                self.client.stop_keepalive()

                self.keepalive_active = False

                logout_success = self.client.logout()

                if not logout_success:

                    if cancel_event.is_set():

                        print(
                            "Credential change cancelled."
                        )

                        return False, True

                    print(
                        "Could not log out of previous session. "
                        "Keeping current authentication state."
                    )

                    self.client.start_keepalive()

                    self.keepalive_active = (
                        self.client._keepalive_thread
                        is not None
                    )

                    notify(
                        "Credential change failed",
                        "Could not log out of the previous session."
                    )

                    return False, False

                print(
                    "Previous session logged out."
                )

                self.state = AuthState.CONNECTED

            # ----------------------------------------------------------
            # Determine what network we are currently on.
            # ----------------------------------------------------------

            network_status = self.client.detect_network()

            if network_status == NetworkStatus.NO_INTERNET:

                self.wifi_connected = False
                self.state = AuthState.DISCONNECTED

                print(
                    "No usable Internet connection detected — "
                    "credentials saved for next connection."
                )

                return True, False

            if network_status == NetworkStatus.INTERNET_AVAILABLE:

                self.wifi_connected = False
                self.state = AuthState.CONNECTED

                print(
                    "Normal Internet detected — "
                    "credentials saved for next campus connection."
                )

                return True, False

            # ----------------------------------------------------------
            # Campus captive portal detected.
            # ----------------------------------------------------------

            self.wifi_connected = True

            if cancel_event.is_set():

                print(
                    "Credential change cancelled."
                )

                return False, True

            print(
                "Authenticating with new credentials..."
            )

            self.state = AuthState.AUTHENTICATING

            success = self._authenticate_with_retry(
                cancel_event
            )

            if cancel_event.is_set():

                return False, True

            if success:

                notify(
                    "Credentials updated",
                    "Authenticated with the new credentials."
                )

                return True, False

            notify(
                "Authentication failed",
                "The new credentials could not authenticate."
            )

            return False, False

    def _on_disconnected(self):

        self.wifi_connected = False
        self.ssid = None

        if self.state == AuthState.AUTHENTICATED:

            print(
                "Network disconnected — "
                "stopping keepalive and logging out..."
            )

            self.client.stop_keepalive()

            self.keepalive_active = False

            logout_success = self.client.logout()

            if logout_success:

                notify(
                    "Logged out",
                    "Network disconnected. "
                    "CampusAuthenticator logged out."
                )

            else:

                notify(
                    "Logout unavailable",
                    "Network disconnected before "
                    "CampusAuthenticator could reach FortiGate."
                )

        elif self.state == AuthState.AUTHENTICATING:

            print(
                "Network disconnected during authentication"
            )

            self.client.stop_keepalive()
            self.keepalive_active = False

        self.state = AuthState.DISCONNECTED

        print(
            "Network disconnected — "
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

            network_status = self.client.detect_network()

            if network_status != NetworkStatus.CAPTIVE_PORTAL:

                self.wifi_connected = False

                if network_status == NetworkStatus.INTERNET_AVAILABLE:

                    print(
                        "Internet is already available — "
                        "no campus captive portal detected."
                    )

                else:

                    print(
                        "No campus captive portal detected."
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

            network_status = self.client.detect_network()

            if network_status == NetworkStatus.CAPTIVE_PORTAL:

                self.wifi_connected = True
                self.state = AuthState.CONNECTED

            elif network_status == NetworkStatus.INTERNET_AVAILABLE:

                self.wifi_connected = False
                self.state = AuthState.CONNECTED

            else:

                self.wifi_connected = False
                self.state = AuthState.DISCONNECTED

            self.ssid = None

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

        network_status = self.client.detect_network()

        # --------------------------------------------------------------
        # Campus captive portal
        # --------------------------------------------------------------

        if network_status == NetworkStatus.CAPTIVE_PORTAL:

            self.wifi_connected = True

            print(
                "Campus captive portal detected."
            )

            if self.client.keepalive_url:

                print(
                    "Previous session found — "
                    "attempting session recovery..."
                )

                if self.client.recover_session():

                    self.state = AuthState.AUTHENTICATED

                    if not self.keepalive_active:

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

                    self.state = AuthState.AUTHENTICATED

                    if self.client.keepalive_url:

                        self.client.start_keepalive()
                        self.keepalive_active = True

                    print(
                        "Already authenticated."
                    )

                else:

                    print(
                        "Not authenticated. "
                        "Authenticating now..."
                    )

                    self._authenticate_with_retry()

        # --------------------------------------------------------------
        # Normal Internet
        # --------------------------------------------------------------

        elif network_status == NetworkStatus.INTERNET_AVAILABLE:

            print(
                "Internet is available."
            )

            if self.client.keepalive_url:

                print(
                    "Previous session found — "
                    "attempting session recovery..."
                )

                if self.client.recover_session():

                    self.wifi_connected = True
                    self.state = AuthState.AUTHENTICATED

                    if not self.keepalive_active:

                        self.client.start_keepalive()

                        self.keepalive_active = True

                    print(
                        "Previous session recovered — "
                        "campus network detected."
                    )

                else:

                    print(
                        "Previous session could not be recovered — "
                        "treating network as normal Internet."
                    )

                    # Do not leave a stale keepalive running.
                    self.client.stop_keepalive()
                    self.keepalive_active = False

                    self.wifi_connected = False
                    self.state = AuthState.CONNECTED

            else:

                self.wifi_connected = False
                self.state = AuthState.CONNECTED

            if self.state == AuthState.CONNECTED:

                print(
                    "No campus captive portal detected."
                )

        # --------------------------------------------------------------
        # No Internet
        # --------------------------------------------------------------

        else:

            self.wifi_connected = False
            self.state = AuthState.DISCONNECTED

            print(
                "No usable Internet connection detected."
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

        self.credentials_cancel_event.set()

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