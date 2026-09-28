import requests
import threading
from enum import Enum

from portal.parser import extract_login_data
from storage.config import load_config
from storage.session import (
    save_session,
    load_session,
    clear_session
)


# Refresh interval in seconds.
# Portal timeout is 6400s; we refresh at 6000s
# for a 400-second safety margin.
KEEPALIVE_INTERVAL = 6000


class NetworkStatus(Enum):

    CAPTIVE_PORTAL = "CaptivePortal"
    INTERNET_AVAILABLE = "InternetAvailable"
    NO_INTERNET = "NoInternet"


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

        self.keepalive_url = load_session()
        self._stop_event = threading.Event()
        self._keepalive_thread = None

    def detect_network(self):

        print(
            "Checking network type..."
        )

        try:

            response = self.session.get(
                "http://connectivitycheck.gstatic.com/generate_204",
                timeout=5,
                allow_redirects=False
            )

            print(
                "Network probe status:",
                response.status_code
            )

            print(
                "Network probe location:",
                response.headers.get("Location")
            )

            location = response.headers.get(
                "Location",
                ""
            )

            if (
                300 <= response.status_code < 400
                and "fgtauth" in location
            ):

                print(
                    "FortiGate captive portal detected"
                )

                return NetworkStatus.CAPTIVE_PORTAL

            if response.status_code in (
                200,
                204
            ):

                print(
                    "Normal Internet access detected"
                )

                return NetworkStatus.INTERNET_AVAILABLE

            print(
                "Network probe returned an unexpected "
                "response"
            )

            return NetworkStatus.NO_INTERNET

        except requests.RequestException as e:

            print(
                "Network probe failed:",
                repr(e)
            )

            return NetworkStatus.NO_INTERNET

    def check_auth(self):

        """
        Checks whether normal Internet access is available.

        Returns True if at least one connectivity check
        succeeds without being redirected to the captive portal.
        """

        urls = [
            "http://connectivitycheck.gstatic.com/generate_204",
        ]

        for url in urls:

            try:

                response = self.session.get(
                    url,
                    timeout=5,
                    allow_redirects=True
                )

                if "fgtauth" in response.url:
                    continue

                if response.status_code in (
                    200,
                    204
                ):

                    return True

            except requests.RequestException:

                continue

        return False

    def recover_session(self):

        """
        Attempts to recover the previously known FortiGate
        authentication session using the existing keepalive URL.

        Returns True if the session appears to still be valid.
        Returns False if there is no previous session or if
        the session can no longer be used.
        """

        if not self.keepalive_url:

            print(
                "No previous keepalive URL — "
                "session recovery unavailable"
            )

            return False

        print(
            "Attempting to recover previous FortiGate session..."
        )

        try:

            response = self.session.get(
                self.keepalive_url,
                timeout=10,
                allow_redirects=False
            )

            print(
                "Session recovery status:",
                response.status_code
            )

            if response.status_code == 200:

                print(
                    "Previous FortiGate session is still valid"
                )

                return True

            print(
                "Previous FortiGate session is no longer valid"
            )

            clear_session()
            self.keepalive_url = None

            return False

        except requests.RequestException as e:

            print(
                "Session recovery failed:",
                repr(e)
            )

            return False

    def get_auth_page(self):

        print(
            "Triggering captive portal..."
        )

        response = self.session.get(
            "http://connectivitycheck.gstatic.com/generate_204",
            timeout=5,
            allow_redirects=True
        )

        print(
            "\nCurrent URL:"
        )

        print(
            response.url
        )

        print(
            "Status:",
            response.status_code
        )

        if "fgtauth" not in response.url:

            print(
                "Captive portal did not intercept the request"
            )

            return None

        print(
            "\nAuthentication page reached"
        )

        return response

    def login(self):

        try:

            config = load_config()

            if not config:

                print(
                    "No saved application configuration"
                )

                return False

            username = config.get(
                "username"
            )

            password = config.get(
                "password"
            )

            if username is None or password is None:

                print(
                    "Username or password is missing"
                )

                return False

            response = self.get_auth_page()

            if not response:
                return False

            login_data = extract_login_data(
                response.text
            )

            print(
                "\nSubmitting credentials..."
            )

            payload = {
                "4Tredir": login_data["redir"],
                "magic": login_data["magic"],
                "username": username,
                "password": password
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

            if response.status_code in (
                302,
                303
            ):

                self.keepalive_url = response.headers.get(
                    "Location"
                )

                if not self.keepalive_url:

                    print(
                        "Login succeeded but no keepalive URL "
                        "was provided"
                    )

                    return False

                save_session(
                    self.keepalive_url
                )

                print(
                    "Keepalive URL:",
                    self.keepalive_url
                )

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

            print(
                "No keepalive URL — skipping"
            )

            return

        if self._keepalive_thread is not None:

            print(
                "Keepalive already running"
            )

            return

        self._stop_event.clear()

        self._keepalive_thread = threading.Thread(
            target=self._keepalive_loop,
            daemon=True
        )

        self._keepalive_thread.start()

        print(
            "Keepalive started"
        )

    def stop_keepalive(self):

        """
        Signals the keepalive thread to stop and
        waits for it to exit.
        """

        if self._keepalive_thread is None:
            return

        print(
            "Stopping keepalive..."
        )

        self._stop_event.set()

        self._keepalive_thread.join(
            timeout=60
        )

        self._keepalive_thread = None

        print(
            "Keepalive stopped"
        )

    def logout(self):

        """
        Attempts to send a logout request to the firewall
        using the same token from the keepalive URL.

        Returns True if the logout request succeeds.
        Returns False if the FortiGate cannot be reached
        or the logout request fails.
        """

        if not self.keepalive_url:

            print(
                "No active session to logout"
            )

            return False

        logout_url = self.keepalive_url.replace(
            "/keepalive?",
            "/logout?"
        )

        print(
            f"Logging out: {logout_url}"
        )

        try:

            response = self.session.get(
                logout_url,
                timeout=10
            )

            print(
                "Logout status:",
                response.status_code
            )

            if response.status_code == 200:

                clear_session()
                self.keepalive_url = None

                return True

            print(
                "Logout request did not return "
                "a successful status"
            )

            return False

        except requests.RequestException as e:

            print(
                "Logout error:",
                repr(e)
            )

            return False

    def _keepalive_loop(self):

        """
        Internal loop that runs in the background thread.
        Sleeps in 30-second chunks so stop_keepalive()
        can interrupt within ~30 seconds.
        """

        while not self._stop_event.is_set():

            elapsed = 0

            while elapsed < KEEPALIVE_INTERVAL:

                if self._stop_event.wait(
                    timeout=30
                ):
                    return

                elapsed += 30

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

            while not client._stop_event.is_set():

                client._stop_event.wait(
                    timeout=1
                )

        except KeyboardInterrupt:

            client.stop_keepalive()
            client.logout()

            print(
                "Done"
            )