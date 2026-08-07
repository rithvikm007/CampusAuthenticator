from bs4 import BeautifulSoup
import re


def extract_login_data(html):
    """
    Extracts the hidden fields required for login.

    Returns:
    {
        "magic": "...",
        "redir": "..."
    }

    Raises:
        ValueError if required fields are missing.
    """

    soup = BeautifulSoup(html, "html.parser")

    magic = soup.find("input", {"name": "magic"})
    redir = soup.find("input", {"name": "4Tredir"})

    if magic is None or redir is None:
        raise ValueError("Login page does not contain required hidden fields.")

    return {
        "magic": magic["value"],
        "redir": redir["value"]
    }


import re


def extract_auth_url(html):

    match = re.search(
        r'href="([^"]*fgtauth[^"]*)"',
        html
    )

    if match:
        return match.group(1)

    return None


if __name__ == "__main__":

    with open("login.html", encoding="utf-8") as f:
        html = f.read()

    print(extract_login_data(html))