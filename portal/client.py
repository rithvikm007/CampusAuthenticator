import requests

from portal.parser import extract_login_data
from config import PORTAL_URL, USERNAME, PASSWORD


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


    def trigger_portal(self):

        print("Triggering captive portal...")

        response = self.session.get(
            "http://neverssl.com",
            timeout=5
        )

        print("\nInitial response URL:")
        print(response.url)

        print("\nResponse status:")
        print(response.status_code)

        print("\nResponse preview:")
        print(response.text[:300])


        return response



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


            print(
                "Headers:",
                response.headers
            )


            if response.status_code in (302, 303):

                print(
                    "Redirect:",
                    response.headers.get(
                        "Location"
                    )
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



if __name__ == "__main__":

    client = PortalClient()

    result = client.login()

    print(
        "\nCompleted:",
        result
    )