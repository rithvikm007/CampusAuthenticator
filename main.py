import sys
import datetime
import os
from network.events import watch_network_events
from network.wifi import is_hostel_wifi
from portal.client import PortalClient

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
        AUTHENTICATING — login in progress
        AUTHENTICATED  — keepalive running
    """

    def __init__(self):

        self.state = "DISCONNECTED"
        self.client = PortalClient()


    def handle_event(self, status):

        print(
            f"\nEvent: {status}"
            f"  [state={self.state}]"
        )


        if status == "Connected":
            self._on_connected()

        elif status == "Disconnected":
            self._on_disconnected()


    def _on_connected(self):

        # If we think we're authenticated, verify it.
        # This handles waking from Sleep/Hibernate where
        # the session might have expired on the firewall.
        if self.state == "AUTHENTICATED":
            print("Already authenticated — verifying session...")
            if self.client.check_auth():
                print("Session still valid — ignoring event")
                return
            else:
                print("Session expired (likely during sleep). Re-authenticating...")
                self.client.stop_keepalive()
                self.state = "DISCONNECTED"
                # Fall through to the authentication logic below

        # Currently authenticating — ignore
        if self.state == "AUTHENTICATING":
            print("Authentication in progress — ignoring")
            return

        # Check if this is the target network
        if not is_hostel_wifi():
            print("Not hostel WiFi — ignoring")
            return

        # Attempt authentication
        self.state = "AUTHENTICATING"
        print("Hostel WiFi detected — authenticating...")

        success = self.client.login()

        if success:
            self.state = "AUTHENTICATED"
            self.client.start_keepalive()
        else:
            self.state = "DISCONNECTED"
            print("Login failed — will retry on next event")


    def _on_disconnected(self):

        if self.state == "AUTHENTICATED":
            self.client.stop_keepalive()

        self.state = "DISCONNECTED"
        print("WiFi disconnected — ready to reconnect")


    def run(self):

        print("CampusAuthenticator started\n")

        # Initial startup check
        print("Checking initial network state...")
        if is_hostel_wifi():
            print("Already connected to hostel WiFi")
            if self.client.check_auth():
                self.state = "AUTHENTICATED"
                print("Already authenticated (internet is working)")
                # We can't easily resume the keepalive loop because we don't have the token.
                # The session will eventually expire and a reconnect/disconnect will fix it,
                # or we could force a logout/login.
                # For now, we just mark it authenticated.
            else:
                print("Not authenticated. Authenticating now...")
                self.state = "AUTHENTICATING"
                if self.client.login():
                    self.state = "AUTHENTICATED"
                    self.client.start_keepalive()
                else:
                    self.state = "DISCONNECTED"
                    print("Initial login failed")
        else:
            print("Not connected to hostel WiFi")

        try:
            watch_network_events(self.handle_event)
        except KeyboardInterrupt:
            pass
        finally:
            self._shutdown()


    def _shutdown(self):

        print("\nShutting down...")

        if self.state == "AUTHENTICATED":
            self.client.stop_keepalive()
            self.client.logout()

        print("Goodbye")



if __name__ == "__main__":

    controller = AuthController()
    controller.run()