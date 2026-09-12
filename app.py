from core.controller import AuthController
from core.logger import setup_logging
from gui.tray import TrayApplication


def main():

    setup_logging()

    controller = AuthController()

    application = TrayApplication(
        controller
    )

    application.run()


if __name__ == "__main__":

    main()