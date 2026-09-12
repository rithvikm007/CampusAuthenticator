from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.controller import AuthController, AuthState


class MainWindow(QMainWindow):

    def __init__(
        self,
        controller: AuthController
    ):

        super().__init__()

        self.controller = controller

        icon_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "icon.png"
        )

        self.setWindowIcon(
            QIcon(str(icon_path))
        )

        self.setWindowTitle(
            "CampusAuthenticator"
        )

        self.resize(
            520,
            480
        )

        self.setup_ui()
        self.apply_styles()

        self.refresh_timer = QTimer(
            self
        )

        self.refresh_timer.timeout.connect(
            self.update_status
        )

        self.refresh_timer.start(
            1000
        )

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

        layout = QVBoxLayout(
            central
        )

        layout.setContentsMargins(
            28,
            22,
            28,
            22
        )

        layout.setSpacing(
            12
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

        layout.addWidget(
            title
        )

        layout.addWidget(
            subtitle
        )

        layout.addSpacing(
            8
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
            14,
            16,
            14
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
            11,
            16,
            11
        )

        network_layout.setSpacing(
            8
        )

        self.wifi_label = self.add_info_row(
            network_layout,
            "Wi-Fi",
            "Not Connected"
        )

        self.ssid_label = self.add_info_row(
            network_layout,
            "SSID",
            "—"
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
            11,
            16,
            11
        )

        session_layout.setSpacing(
            8
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

    def add_info_row(
        self,
        layout,
        name,
        value
    ):

        row = QHBoxLayout()

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

    def closeEvent(self, event):

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

        if status["wifi_connected"]:

            self.wifi_label.setText(
                "Connected"
            )

        else:

            self.wifi_label.setText(
                "Not Connected"
            )

        self.ssid_label.setText(
            status["ssid"] or "—"
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