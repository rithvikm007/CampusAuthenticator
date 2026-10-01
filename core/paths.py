import os
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def is_frozen():
    return getattr(sys, "frozen", False)


def resource_path(*parts):
    """
    Return the path to a bundled application resource.

    Development:
        Project root is used.

    PyInstaller:
        PyInstaller's extracted bundle directory is used.
    """

    if is_frozen():
        base = Path(sys._MEIPASS)
    else:
        base = PROJECT_ROOT

    return base.joinpath(*parts)


def data_root():
    """
    Return the directory used for writable application data.

    Development:
        Project root.

    PyInstaller:
        %LOCALAPPDATA%\\CampusAuthenticator
    """

    if is_frozen():

        local_app_data = os.environ.get(
            "LOCALAPPDATA",
            str(Path.home() / "AppData" / "Local")
        )

        root = (
            Path(local_app_data)
            / "CampusAuthenticator"
        )

    else:

        root = PROJECT_ROOT

    root.mkdir(
        parents=True,
        exist_ok=True
    )

    return root


def data_path(*parts):
    """
    Return a writable application-data path.
    """

    path = data_root().joinpath(*parts)

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    return path