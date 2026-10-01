from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import (
    QColor,
    QIcon,
    QPainter,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QMenu,
    QSystemTrayIcon,
)

from core.controller import AuthController, AuthState
from core.paths import resource_path
from gui.window import MainWindow
from notifications import get_pending_notifications


class TrayApplication:

    def __init__(
        self,
        controller: AuthController
    ):

        self.controller = controller

        self.application = QApplication([])

        icon_path = resource_path(
            "assets",
            "icon.ico"
        )

        self.application.setWindowIcon(
            QIcon(str(icon_path))
        )

        self.application.setQuitOnLastWindowClosed(
            False
        )

        self.window = MainWindow(
            controller
        )

        self.tray = QSystemTrayIcon(
            self.application
        )

        self.tray.setToolTip(
            "CampusAuthenticator"
        )

        self.status_action = None

        self.setup_tray()

        self.status_timer = QTimer()

        self.status_timer.timeout.connect(
            self.update_tray
        )

        self.status_timer.start(
            1000
        )

        self.notification_timer = QTimer()

        self.notification_timer.timeout.connect(
            self.process_notifications
        )

        self.notification_timer.start(
            250
        )

        self.controller.start()

    def setup_tray(self):

        self.tray.setIcon(
            self.create_tray_icon(
                AuthState.DISCONNECTED
            )
        )

        menu = QMenu()

        self.status_action = menu.addAction(
            "Status: Disconnected"
        )

        self.status_action.setEnabled(
            True
        )

        menu.addSeparator()

        open_action = menu.addAction(
            "Open"
        )

        open_action.triggered.connect(
            self.show_window
        )

        self.login_action = menu.addAction(
            "Log In"
        )

        self.login_action.triggered.connect(
            self.login
        )

        self.logout_action = menu.addAction(
            "Log Out"
        )

        self.logout_action.triggered.connect(
            self.logout
        )

        menu.addSeparator()

        exit_action = menu.addAction(
            "Exit"
        )

        exit_action.triggered.connect(
            self.exit_application
        )

        self.tray.setContextMenu(
            menu
        )

        self.tray.activated.connect(
            self.tray_activated
        )

        self.tray.show()

    def create_tray_icon(
        self,
        state
    ):

        icon_path = resource_path(
            "assets",
            "icon.png"
        )

        source = QPixmap(
            str(icon_path)
        )

        size = 32

        pixmap = source.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )

        painter = QPainter(
            pixmap
        )

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        if state == AuthState.AUTHENTICATED:

            indicator_color = "#4ade80"

        elif state == AuthState.AUTHENTICATING:

            indicator_color = "#facc15"

        elif state == AuthState.CONNECTED:

            indicator_color = "#a1a1aa"

        else:

            indicator_color = "#ef4444"

        painter.setPen(
            QColor("#171717")
        )

        painter.setBrush(
            QColor(indicator_color)
        )

        painter.drawEllipse(
            21,
            1,
            10,
            10
        )

        painter.end()

        return QIcon(
            pixmap
        )

    def update_tray(self):

        status = self.controller.get_status()

        state = status["state"]

        self.tray.setIcon(
            self.create_tray_icon(
                state
            )
        )

        if state == AuthState.AUTHENTICATED:

            status_text = "Authenticated"

        elif state == AuthState.AUTHENTICATING:

            status_text = "Authenticating"

        elif state == AuthState.CONNECTED:

            status_text = "Connected"

        else:

            status_text = "Disconnected"

        if status["auto_login_blocked"]:

            remaining = status[
                "cooldown_remaining"
            ]

            minutes = remaining // 60
            seconds = remaining % 60

            status_text = (
                f"Logged out — "
                f"auto login paused "
                f"({minutes}:{seconds:02d})"
            )

        self.status_action.setText(
            f"Status: {status_text}"
        )

        self.login_action.setEnabled(
            state != AuthState.AUTHENTICATED
            and state != AuthState.AUTHENTICATING
            and status["wifi_connected"]
        )

        self.logout_action.setEnabled(
            state == AuthState.AUTHENTICATED
        )

        self.tray.setToolTip(
            f"CampusAuthenticator — "
            f"{status_text}"
        )

    def process_notifications(self):

        notifications = (
            get_pending_notifications()
        )

        for title, message in notifications:

            self.tray.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                5000
            )

    def show_window(self):

        self.window.show()

        self.window.raise_()

        self.window.activateWindow()

    def login(self):

        self.controller.login()

        self.update_tray()

        self.window.update_status()

    def logout(self):

        self.controller.disconnect()

        self.update_tray()

        self.window.update_status()

    def tray_activated(
        self,
        reason
    ):

        if reason == (
            QSystemTrayIcon.ActivationReason.DoubleClick
        ):

            self.show_window()

    def exit_application(self):

        self.status_timer.stop()

        self.notification_timer.stop()

        self.controller.stop()

        self.application.quit()

    def run(self):

        self.application.exec()