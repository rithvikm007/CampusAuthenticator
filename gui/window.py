from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from core.controller import AuthController, AuthState
from core.paths import resource_path
from gui.settings import SettingsPage


class CredentialsChangeWorker(QObject):

    finished = Signal(bool, bool)

    def __init__(self, controller: AuthController):

        super().__init__()

        self.controller = controller

    def run(self):

        success, cancelled = (
            self.controller.credentials_changed()
        )

        self.finished.emit(
            success,
            cancelled
        )


class MainWindow(QMainWindow):

    def __init__(
        self,
        controller: AuthController
    ):

        super().__init__()

        self.controller = controller

        self.credentials_thread = None
        self.credentials_worker = None
        self.credentials_restart_pending = False

        icon_path = resource_path(
            "assets",
            "icon.png"
        )

        self.setWindowIcon(
            QIcon(str(icon_path))
        )

        self.setWindowTitle(
            "CampusAuthenticator"
        )

        self.setFixedSize(
            520,
            500
        )

        self.setup_ui()
        self.apply_styles()

        self.refresh_timer = QTimer(self)

        self.refresh_timer.timeout.connect(
            self.update_status
        )

        self.refresh_timer.start(1000)

        self.update_status()

    def apply_styles(self):

        self.setStyleSheet(
            """
            QMainWindow {
                background: #171717;
            }

            QWidget {
                color: #f5f5f5;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            QLabel#title {
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#subtitle {
                color: #a1a1aa;
                font-size: 13px;
            }

            QLabel#section_title {
                color: #a1a1aa;
                font-size: 11px;
                font-weight: 700;
            }

            QFrame#status_card {
                background: #222222;
                border: 1px solid #303030;
                border-radius: 10px;
            }

            QFrame#info_card {
                background: #1e1e1e;
                border: 1px solid #2d2d2d;
                border-radius: 8px;
            }

            QLabel#status_label {
                font-size: 19px;
                font-weight: 700;
            }

            QLabel#status_description {
                color: #a1a1aa;
                font-size: 13px;
            }

            QLabel#status_indicator {
                font-size: 15px;
            }

            QLabel#row_label {
                color: #a1a1aa;
                font-size: 13px;
            }

            QLabel#row_value {
                color: #f5f5f5;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton {
                background: #292929;
                border: 1px solid #3a3a3a;
                border-radius: 7px;
                color: #f5f5f5;
                font-size: 13px;
                font-weight: 600;
                padding: 7px 14px;
            }

            QPushButton:hover {
                background: #333333;
            }

            QPushButton:pressed {
                background: #242424;
            }

            QPushButton:disabled {
                background: #202020;
                border-color: #292929;
                color: #5f5f5f;
            }

            QPushButton#settings_button {
                background: transparent;
                border: 1px solid transparent;
                color: #a1a1aa;
                font-size: 20px;
                font-weight: 400;
                padding: 2px;
            }

            QPushButton#settings_button:hover {
                background: #292929;
                border: 1px solid #303030;
                color: #f5f5f5;
            }

            QPushButton#refresh_button {
                background: transparent;
                border: 1px solid #303030;
                color: #a1a1aa;
            }

            QPushButton#refresh_button:hover {
                background: #222222;
                color: #f5f5f5;
            }

            QPushButton#exit_button {
                background: transparent;
                border: 1px solid #303030;
                color: #a1a1aa;
            }

            QPushButton#exit_button:hover {
                background: #2a2020;
                border-color: #4a3030;
                color: #f5f5f5;
            }

            QPushButton#login_button {
                background: #292929;
            }

            QPushButton#logout_button {
                background: #292929;
            }
            """
        )

    def setup_ui(self):

        central = QWidget()

        self.setCentralWidget(
            central
        )

        outer_layout = QVBoxLayout(
            central
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0
        )

        self.pages = QStackedWidget()

        outer_layout.addWidget(
            self.pages
        )

        self.main_page = QWidget()

        self.setup_main_page()

        self.pages.addWidget(
            self.main_page
        )

        self.settings_page = SettingsPage()

        self.settings_page.saved.connect(
            self.settings_saved
        )

        self.settings_page.cancelled.connect(
            self.show_main_page
        )

        self.pages.addWidget(
            self.settings_page
        )

    def setup_main_page(self):

        layout = QVBoxLayout(
            self.main_page
        )

        layout.setContentsMargins(
            28,
            22,
            28,
            22
        )

        layout.setSpacing(
            8
        )

        header_layout = QHBoxLayout()

        header_text_layout = QVBoxLayout()

        header_text_layout.setSpacing(
            2
        )

        title = QLabel(
            "CampusAuthenticator"
        )

        title.setObjectName(
            "title"
        )

        subtitle = QLabel(
            "Automatic campus network authentication"
        )

        subtitle.setObjectName(
            "subtitle"
        )

        header_text_layout.addWidget(
            title
        )

        header_text_layout.addWidget(
            subtitle
        )

        header_layout.addLayout(
            header_text_layout
        )

        header_layout.addStretch()

        self.settings_button = QPushButton(
            "⚙"
        )

        self.settings_button.setObjectName(
            "settings_button"
        )

        self.settings_button.setFixedSize(
            34,
            34
        )

        self.settings_button.setToolTip(
            "Settings"
        )

        self.settings_button.clicked.connect(
            self.show_settings_page
        )

        header_layout.addWidget(
            self.settings_button
        )

        layout.addLayout(
            header_layout
        )

        layout.addSpacing(
            4
        )

        status_card = QFrame()

        status_card.setObjectName(
            "status_card"
        )

        status_layout = QHBoxLayout(
            status_card
        )

        status_layout.setContentsMargins(
            16,
            12,
            16,
            12
        )

        status_layout.setSpacing(
            12
        )

        self.status_indicator = QLabel(
            "●"
        )

        self.status_indicator.setObjectName(
            "status_indicator"
        )

        self.status_indicator.setFixedWidth(
            18
        )

        status_text_layout = QVBoxLayout()

        status_text_layout.setSpacing(
            2
        )

        self.status_label = QLabel(
            "Disconnected"
        )

        self.status_label.setObjectName(
            "status_label"
        )

        self.status_description = QLabel(
            "Authentication inactive"
        )

        self.status_description.setObjectName(
            "status_description"
        )

        status_text_layout.addWidget(
            self.status_label
        )

        status_text_layout.addWidget(
            self.status_description
        )

        status_layout.addWidget(
            self.status_indicator
        )

        status_layout.addLayout(
            status_text_layout
        )

        status_layout.addStretch()

        layout.addWidget(
            status_card
        )

        network_title = QLabel(
            "NETWORK"
        )

        network_title.setObjectName(
            "section_title"
        )

        layout.addWidget(
            network_title
        )

        network_card = QFrame()

        network_card.setObjectName(
            "info_card"
        )

        network_layout = QVBoxLayout(
            network_card
        )

        network_layout.setContentsMargins(
            16,
            8,
            16,
            8
        )

        network_layout.setSpacing(
            5
        )

        self.network_label = self.add_info_row(
            network_layout,
            "Interface",
            "Not Connected"
        )

        layout.addWidget(
            network_card
        )

        session_title = QLabel(
            "SESSION"
        )

        session_title.setObjectName(
            "section_title"
        )

        layout.addWidget(
            session_title
        )

        session_card = QFrame()

        session_card.setObjectName(
            "info_card"
        )

        session_layout = QVBoxLayout(
            session_card
        )

        session_layout.setContentsMargins(
            16,
            8,
            16,
            8
        )

        session_layout.setSpacing(
            5
        )

        self.auth_label = self.add_info_row(
            session_layout,
            "Authentication",
            "Not authenticated"
        )

        self.keepalive_label = self.add_info_row(
            session_layout,
            "Keepalive",
            "Inactive"
        )

        self.cooldown_label = self.add_info_row(
            session_layout,
            "Auto Login",
            "Enabled"
        )

        layout.addWidget(
            session_card
        )

        layout.addStretch()

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(
            8
        )

        self.login_button = QPushButton(
            "Log In"
        )

        self.login_button.setObjectName(
            "login_button"
        )

        self.login_button.setFixedHeight(
            34
        )

        self.login_button.clicked.connect(
            self.login
        )

        buttons_layout.addWidget(
            self.login_button
        )

        self.disconnect_button = QPushButton(
            "Log Out"
        )

        self.disconnect_button.setObjectName(
            "logout_button"
        )

        self.disconnect_button.setFixedHeight(
            34
        )

        self.disconnect_button.clicked.connect(
            self.disconnect
        )

        buttons_layout.addWidget(
            self.disconnect_button
        )

        layout.addLayout(
            buttons_layout
        )

        bottom_layout = QHBoxLayout()

        bottom_layout.setSpacing(
            8
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.refresh_button.setObjectName(
            "refresh_button"
        )

        self.refresh_button.setFixedHeight(
            32
        )

        self.refresh_button.clicked.connect(
            self.update_status
        )

        bottom_layout.addWidget(
            self.refresh_button
        )

        self.exit_button = QPushButton(
            "Exit"
        )

        self.exit_button.setObjectName(
            "exit_button"
        )

        self.exit_button.setFixedHeight(
            32
        )

        self.exit_button.clicked.connect(
            self.exit_application
        )

        bottom_layout.addWidget(
            self.exit_button
        )

        layout.addLayout(
            bottom_layout
        )

    def show_settings_page(self):

        self.settings_page.load_saved_config()

        self.pages.setCurrentWidget(
            self.settings_page
        )

    def show_main_page(self):

        self.pages.setCurrentWidget(
            self.main_page
        )

    def settings_saved(
        self,
        credentials_changed
    ):

        if not credentials_changed:

            self.show_main_page()

            self.update_status()

            return

        # A credential-change authentication is already running.
        # Cancel it and remember that the latest saved credentials
        # need to be authenticated once the old operation exits.
        if (
            self.credentials_thread is not None
            and self.credentials_thread.isRunning()
        ):

            print(
                "Credential change already in progress — "
                "restarting with latest credentials."
            )

            self.credentials_restart_pending = True

            self.controller.cancel_credentials_change()

            self.show_main_page()

            return

        self.credentials_restart_pending = False

        self.show_main_page()

        self.start_credentials_change()

    def start_credentials_change(self):

        self.credentials_thread = QThread(
            self
        )

        self.credentials_worker = (
            CredentialsChangeWorker(
                self.controller
            )
        )

        self.credentials_worker.moveToThread(
            self.credentials_thread
        )

        self.credentials_thread.started.connect(
            self.credentials_worker.run
        )

        self.credentials_worker.finished.connect(
            self.credentials_change_finished
        )

        self.credentials_worker.finished.connect(
            self.credentials_thread.quit
        )

        self.credentials_worker.finished.connect(
            self.credentials_worker.deleteLater
        )

        self.credentials_thread.finished.connect(
            self.credentials_thread.deleteLater
        )

        self.credentials_thread.start()

        self.update_status()

    def credentials_change_finished(
        self,
        success,
        cancelled
    ):

        self.update_status()

        # If the user saved newer credentials while this
        # operation was running, immediately start a fresh
        # authentication using those latest credentials.
        if cancelled:

            if self.credentials_restart_pending:

                self.credentials_restart_pending = False

                self.credentials_worker = None
                self.credentials_thread = None

                self.start_credentials_change()

            return

        self.credentials_worker = None
        self.credentials_thread = None

        if not success:

            QMessageBox.warning(
                self,
                "Credentials",
                "Could not authenticate with the new credentials."
            )

    def add_info_row(
        self,
        layout,
        name,
        value
    ):

        row = QHBoxLayout()

        row.setContentsMargins(
            0,
            0,
            0,
            0
        )

        row.setSpacing(
            8
        )

        name_label = QLabel(
            name
        )

        name_label.setObjectName(
            "row_label"
        )

        value_label = QLabel(
            value
        )

        value_label.setObjectName(
            "row_value"
        )

        value_label.setAlignment(
            Qt.AlignmentFlag.AlignRight
        )

        row.addWidget(
            name_label
        )

        row.addStretch()

        row.addWidget(
            value_label
        )

        layout.addLayout(
            row
        )

        return value_label

    def login(self):

        self.login_button.setEnabled(
            False
        )

        success = self.controller.login()

        if not success:

            QMessageBox.warning(
                self,
                "Login",
                "Could not authenticate with the campus network."
            )

        self.update_status()

    def disconnect(self):

        self.disconnect_button.setEnabled(
            False
        )

        success = self.controller.disconnect()

        if not success:

            QMessageBox.warning(
                self,
                "Log Out",
                "Could not log out of the active session."
            )

        self.update_status()

    def exit_application(self):

        self.controller.stop()

        QApplication.quit()

    def closeEvent(
        self,
        event
    ):

        self.hide()

        event.ignore()

    def update_status(self):

        status = self.controller.get_status()

        state = status["state"]

        self.status_label.setText(
            state.value
        )

        if state == AuthState.AUTHENTICATED:

            self.status_description.setText(
                "Authentication active"
            )

            self.status_indicator.setStyleSheet(
                "color: #4ade80;"
            )

        elif state == AuthState.AUTHENTICATING:

            self.status_description.setText(
                "Authenticating..."
            )

            self.status_indicator.setStyleSheet(
                "color: #facc15;"
            )

        elif status["auto_login_blocked"]:

            self.status_description.setText(
                "Logged out — automatic login paused"
            )

            self.status_indicator.setStyleSheet(
                "color: #a1a1aa;"
            )

        elif state == AuthState.CONNECTED:

            self.status_description.setText(
                "Connected to network"
            )

            self.status_indicator.setStyleSheet(
                "color: #a1a1aa;"
            )

        else:

            self.status_description.setText(
                "Authentication inactive"
            )

            self.status_indicator.setStyleSheet(
                "color: #71717a;"
            )

        network_interface = status["network_interface"]

        if network_interface:

            self.network_label.setText(
                network_interface
            )

        else:

            self.network_label.setText(
                "Not Connected"
            )

        if state == AuthState.AUTHENTICATED:

            self.auth_label.setText(
                "Authenticated"
            )

        else:

            self.auth_label.setText(
                "Not authenticated"
            )

        if status["keepalive_active"]:

            self.keepalive_label.setText(
                "Active"
            )

        else:

            self.keepalive_label.setText(
                "Inactive"
            )

        if status["auto_login_blocked"]:

            minutes = (
                status["cooldown_remaining"]
                // 60
            )

            seconds = (
                status["cooldown_remaining"]
                % 60
            )

            self.cooldown_label.setText(
                f"Paused ({minutes}:{seconds:02d})"
            )

        else:

            self.cooldown_label.setText(
                "Enabled"
            )

        self.login_button.setEnabled(
            state != AuthState.AUTHENTICATED
            and state != AuthState.AUTHENTICATING
            and status["wifi_connected"]
        )

        self.disconnect_button.setEnabled(
            state == AuthState.AUTHENTICATED
        )