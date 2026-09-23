from core.controller import AuthController
from core.logger import setup_logging
from gui.tray import TrayApplication
from storage.config import config_exists


def main():

    setup_logging()

    controller = AuthController()

    application = TrayApplication(
        controller
    )

    if not config_exists():

        application.show_window()

        application.window.show_settings_page()

    application.run()


if __name__ == "__main__":

    main()