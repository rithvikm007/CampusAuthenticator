import requests
import threading

from portal.parser import extract_login_data
from config import PORTAL_URL, USERNAME, PASSWORD


# Refresh interval in seconds.
# Portal timeout is 6400s; we refresh at 6000s
# for a 400-second safety margin.
KEEPALIVE_INTERVAL = 6000


class PortalClient:

    def __init__(self):

        self.session = requests.Session()

        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/150.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,"
                "application/xml;q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-IN,en;q=0.9",
            "Connection": "keep-alive",
        })

        self.keepalive_url = None
        self._stop_event = threading.Event()
        self._keepalive_thread = None


    def check_auth(self):
        """
        Checks whether the network is already
        authenticated by trying to reach a plain
        HTTP site.

        Returns True if internet works (no portal
        redirect), False if captive portal intercepts.
        """

        try:
            response = self.session.get(
                "http://neverssl.com",
                timeout=5
            )

            if "fgtauth" in response.url:
                return False

            return True

        except Exception:
            return False


    def get_auth_page(self):

        print("Triggering captive portal...")


        response = self.session.get(
            "http://neverssl.com",
            timeout=5
        )


        print("\nCurrent URL:")
        print(response.url)


        print(
            "Status:",
            response.status_code
        )


        if "fgtauth" not in response.url:

            print(
                "Did not reach authentication page"
            )

            return None


        print(
            "\nAuthentication page reached"
        )


        return response



    def login(self):

        try:

            response = self.get_auth_page()


            if not response:
                return False


            login_data = extract_login_data(
                response.text
            )


            print("\nSubmitting credentials...")


            payload = {
                "4Tredir": login_data["redir"],
                "magic": login_data["magic"],
                "username": USERNAME,
                "password": PASSWORD
            }


            headers = {
                "Content-Type":
                    "application/x-www-form-urlencoded",

                "Origin":
                    response.url,

                "Referer":
                    response.url
            }


            response = self.session.post(
                response.url,
                data=payload,
                headers=headers,
                timeout=5,
                allow_redirects=False
            )


            print(
                "Login status:",
                response.status_code
            )


            if response.status_code in (302, 303):

                self.keepalive_url = (
                    response.headers.get("Location")
                )

                print(
                    "Keepalive URL:",
                    self.keepalive_url
                )

                # GET the keepalive URL to activate
                # the session on the firewall.
                # This is what the browser does after
                # following the 303 redirect.
                try:
                    self.session.get(
                        self.keepalive_url,
                        timeout=10
                    )
                    print(
                        "Keepalive page loaded"
                    )
                except Exception as e:
                    print(
                        "Keepalive load warning:",
                        repr(e)
                    )

                print(
                    "Authentication successful"
                )

                return True


            print(
                "Authentication failed"
            )

            print(
                response.text[:300]
            )

            return False


        except Exception as e:

            print(
                "Login error:",
                repr(e)
            )

            return False


    def start_keepalive(self):
        """
        Starts a background thread that periodically
        refreshes the keepalive URL to maintain the
        authentication session.
        """

        if not self.keepalive_url:
            print("No keepalive URL — skipping")
            return

        if self._keepalive_thread is not None:
            print("Keepalive already running")
            return

        self._stop_event.clear()

        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop,
            daemon=True
        )

        self._keepalive_thread.start()

        print("Keepalive started")


    def stop_keepalive(self):
        """
        Signals the keepalive thread to stop and
        waits for it to exit.
        """

        if self._keepalive_thread is None:
            return

        print("Stopping keepalive...")

        self._stop_event.set()

        self._keepalive_thread.join(timeout=60)

        self._keepalive_thread = None

        print("Keepalive stopped")


    def logout(self):
        """
        Sends a logout request to the firewall
        using the same token from the keepalive URL.
        """

        if not self.keepalive_url:
            print("No active session to logout")
            return

        logout_url = self.keepalive_url.replace(
            "/keepalive?", "/logout?"
        )

        print(f"Logging out: {logout_url}")

        try:
            response = self.session.get(
                logout_url,
                timeout=10
            )

            print(
                "Logout status:",
                response.status_code
            )

        except Exception as e:
            print(
                "Logout error:",
                repr(e)
            )

        self.keepalive_url = None


    def _keepalive_loop(self):
        """
        Internal loop that runs in the background thread.
        Sleeps in 30-second chunks so stop_keepalive()
        can interrupt within ~30 seconds.
        """

        while not self._stop_event.is_set():

            # Wait for the refresh interval,
            # checking the stop flag every 30 seconds.
            elapsed = 0

            while elapsed < KEEPALIVE_INTERVAL:

                if self._stop_event.wait(timeout=30):
                    return

                elapsed += 30

            # Time to refresh
            try:

                print(
                    "\nRefreshing keepalive..."
                )

                response = self.session.get(
                    self.keepalive_url,
                    timeout=10
                )

                print(
                    "Keepalive response:",
                    response.status_code
                )

            except Exception as e:

                print(
                    "Keepalive error:",
                    repr(e)
                )



if __name__ == "__main__":

    client = PortalClient()

    result = client.login()

    print(
        "\nCompleted:",
        result
    )

    if result:

        client.start_keepalive()

        print(
            "\nKeepalive thread is running."
        )
        print(
            "Press Ctrl+C to stop.\n"
        )

        try:
            # Block main thread until interrupted.
            # Use short timeouts so Ctrl+C works
            # on Windows.
            while not client._stop_event.is_set():
                client._stop_event.wait(timeout=1)

        except KeyboardInterrupt:
            client.stop_keepalive()
            client.logout()
            print("Done")