from network.events import watch_network_events
from network.wifi import is_hostel_wifi
from portal.client import PortalClient


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

        # Already authenticated — ignore
        # (handles duplicate Connected events)
        if self.state == "AUTHENTICATED":
            print("Already authenticated — ignoring")
            return

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