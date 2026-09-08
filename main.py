import sys
import datetime
import os
import threading
from network.events import watch_network_events
from network.wifi import is_hostel_wifi
from portal.client import PortalClient
from notifications import notify

class TimestampLogger:
    def __init__(self, stream):
        self.stream = stream
        self.at_line_start = True

        self.log_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "logs"
        )

        os.makedirs(self.log_dir, exist_ok=True)

        self.current_date = None
        self.log_file = None

        self._update_log_file()

    def _update_log_file(self):
        today = datetime.date.today()

        if today == self.current_date:
            return

        if self.log_file:
            self.log_file.close()

        self.current_date = today

        filename = (
            f"authenticator-{today.strftime('%Y-%m-%d')}.log"
        )

        filepath = os.path.join(self.log_dir, filename)

        self.log_file = open(
            filepath,
            "a",
            encoding="utf-8"
        )

        self._cleanup_old_logs()

    def _cleanup_old_logs(self):
        cutoff = self.current_date - datetime.timedelta(days=3)

        for filename in os.listdir(self.log_dir):

            if not filename.startswith("authenticator-"):
                continue

            if not filename.endswith(".log"):
                continue

            try:
                date_string = filename[
                    len("authenticator-"):-len(".log")
                ]

                file_date = datetime.datetime.strptime(
                    date_string,
                    "%Y-%m-%d"
                ).date()

                if file_date < cutoff:
                    os.remove(
                        os.path.join(self.log_dir, filename)
                    )

            except ValueError:
                continue

    def write(self, message):
        if not message:
            return

        self._update_log_file()

        if self.at_line_start and message.strip():
            timestamp = datetime.datetime.now().strftime(
                "[%Y-%m-%d %H:%M:%S] "
            )
            self.log_file.write(timestamp)

        self.log_file.write(message)
        self.log_file.flush()

        self.at_line_start = message.endswith("\n")

    def flush(self):
        self.log_file.flush()

sys.stdout = TimestampLogger(sys.stdout)
sys.stderr = TimestampLogger(sys.stderr)


class AuthController:
    """
    Manages the authentication lifecycle.

    States:
        DISCONNECTED   — waiting for a connection
        CONNECTED      — Internet works, but no keepalive URL is known
        AUTHENTICATING — login in progress
        AUTHENTICATED  — authenticated with keepalive running
    """

    def __init__(self):

        self.state = "DISCONNECTED"
        self.client = PortalClient()

        # Prevent multiple WMI events from running
        # authentication logic at the same time.
        self.event_lock = threading.Lock()


    def handle_event(self, status):

        # WMI can generate duplicate events very close
        # together. Only allow one event to be processed
        # at a time.
        with self.event_lock:

            print(
                f"\nEvent: {status}"
                f"  [state={self.state}]"
            )

            if status == "Connected":
                self._on_connected()

            elif status == "Disconnected":
                self._on_disconnected()


    def _on_connected(self):

        # Check that we are actually connected to the
        # hostel WiFi before doing anything.
        if not is_hostel_wifi():
            print("Not hostel WiFi — ignoring")
            return


        # If we think we're authenticated, verify the
        # session. This handles waking from Sleep/Hibernate.
        if self.state == "AUTHENTICATED":

            print(
                "Already authenticated — verifying session..."
            )

            if self.client.check_auth():

                print(
                    "Session still valid — ignoring event"
                )

                return

            else:

                print(
                    "Session expired (likely during sleep). "
                    "Re-authenticating..."
                )

                self.client.stop_keepalive()

                self.state = "DISCONNECTED"


        # Another event may arrive while authentication
        # is already running.
        if self.state == "AUTHENTICATING":

            print(
                "Authentication in progress — ignoring"
            )

            return


        # Network may have just recovered from sleep.
        # Give Windows/router/DNS a few seconds to settle.
        print(
            "Waiting for network to stabilize..."
        )

        import time
        time.sleep(5)


        # If we have a previous keepalive URL,
        # first try to recover that FortiGate session.
        if self.client.keepalive_url:

            if self.client.recover_session():

                self.state = "AUTHENTICATED"

                self.client.start_keepalive()

                print(
                    "Previous session recovered — "
                    "keepalive running"
                )

                return


        # Check whether Internet is already working.
        #
        # If it is, the machine is already authenticated,
        # but we do not know the FortiGate session URL.
        print(
            "Checking network connectivity..."
        )

        if self.client.check_auth():

            print(
                "Internet is already working."
            )

            print(
                "Already authenticated, but no keepalive "
                "URL is available"
            )

            self.state = "CONNECTED"

            return


        # Attempt authentication.
        self.state = "AUTHENTICATING"

        print(
            "Hostel WiFi detected — authenticating..."
        )


        # Retry a few times because immediately after
        # waking from sleep DNS/network connectivity
        # may not be ready yet.
        max_attempts = 5

        for attempt in range(1, max_attempts + 1):

            print(
                f"Authentication attempt "
                f"{attempt}/{max_attempts}"
            )

            success = self.client.login()

            if success:

                self.state = "AUTHENTICATED"

                self.client.start_keepalive()

                print(
                    "Authentication successful — "
                    "keepalive running"
                )

                notify(
                    "Authentication successful",
                    "CampusAuthenticator is now connected."
                )

                return


            if attempt < max_attempts:

                print(
                    "Authentication attempt failed — "
                    "waiting before retry..."
                )

                time.sleep(5)


        # All attempts failed.
        self.state = "DISCONNECTED"

        print(
            "Authentication failed after "
            f"{max_attempts} attempts"
        )

        notify(
            "Authentication failed",
            f"Could not authenticate after {max_attempts} attempts."
        )


    def _on_disconnected(self):

        if self.state == "AUTHENTICATED":

            print(
                "WiFi disconnected — "
                "stopping keepalive and logging out..."
            )

            self.client.stop_keepalive()

            logout_success = self.client.logout()

            if logout_success:

                notify(
                    "Logged out",
                    "Wi-Fi disconnected. CampusAuthenticator logged out."
                )

            else:

                notify(
                    "Logout unavailable",
                    "Wi-Fi disconnected before CampusAuthenticator "
                    "could reach FortiGate."
                )

        elif self.state == "AUTHENTICATING":

            print(
                "WiFi disconnected during authentication"
            )

            self.client.stop_keepalive()

        self.state = "DISCONNECTED"

        print(
            "WiFi disconnected — ready to reconnect"
        )


    def run(self):

        print(
            "CampusAuthenticator started\n"
        )


        # Initial startup check.
        print(
            "Checking initial network state..."
        )


        if is_hostel_wifi():

            print(
                "Already connected to hostel WiFi"
            )


            # If a previous FortiGate session was persisted,
            # first try to recover it.
            if self.client.keepalive_url:

                print(
                    "Previous session found — "
                    "attempting session recovery..."
                )

                if self.client.recover_session():

                    self.state = "AUTHENTICATED"

                    self.client.start_keepalive()

                    print(
                        "Previous session recovered — "
                        "keepalive running"
                    )

                else:

                    print(
                        "Previous session could not be recovered"
                    )


            # If session recovery did not succeed,
            # check whether Internet is already working.
            if self.state != "AUTHENTICATED":

                print(
                    "Checking network connectivity..."
                )

                if self.client.check_auth():

                    print(
                        "Internet is already working."
                    )

                    self.state = "CONNECTED"

                    print(
                        "Already authenticated, but no known "
                        "FortiGate session is available"
                    )

                    print(
                        "Waiting for a fresh authentication session "
                        "to obtain the keepalive URL"
                    )


                else:

                    print(
                        "Not authenticated. "
                        "Authenticating now..."
                    )

                    self._authenticate_with_retry()


        else:

            print(
                "Not connected to hostel WiFi"
            )


        try:

            watch_network_events(
                self.handle_event
            )

        except KeyboardInterrupt:

            pass

        finally:

            self._shutdown()


    def _authenticate_with_retry(self):

        import time

        self.state = "AUTHENTICATING"

        max_attempts = 5

        for attempt in range(1, max_attempts + 1):

            print(
                f"Authentication attempt "
                f"{attempt}/{max_attempts}"
            )

            success = self.client.login()

            if success:

                self.state = "AUTHENTICATED"

                self.client.start_keepalive()

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

                time.sleep(5)


        self.state = "DISCONNECTED"

        print(
            "Authentication failed after "
            f"{max_attempts} attempts"
        )

        notify(
            "Authentication failed",
            f"Could not authenticate after {max_attempts} attempts."
        )

        return False


    def _shutdown(self):

        print(
            "\nShutting down..."
        )


        if self.state == "AUTHENTICATED":

            self.client.stop_keepalive()

            self.client.logout()


        elif self.state == "AUTHENTICATING":

            self.client.stop_keepalive()


        print(
            "Goodbye"
        )

if __name__ == "__main__":

    controller = AuthController()
    controller.run()