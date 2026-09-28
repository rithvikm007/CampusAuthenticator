from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from storage.config import load_config, save_config


class SettingsPage(QWidget):

    saved = Signal(bool)
    cancelled = Signal()

    def __init__(self, parent=None):

        super().__init__(parent)

        self.setup_ui()
        self.apply_styles()
        self.load_saved_config()

    def setup_ui(self):

        main_layout = QVBoxLayout(
            self
        )

        main_layout.setContentsMargins(
            28,
            22,
            28,
            22
        )

        main_layout.setSpacing(
            12
        )

        header_layout = QHBoxLayout()

        header_text_layout = QVBoxLayout()

        header_text_layout.setSpacing(
            2
        )

        title = QLabel(
            "Settings"
        )

        title.setObjectName(
            "title"
        )

        subtitle = QLabel(
            "Configure your campus network credentials"
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

        main_layout.addLayout(
            header_layout
        )

        main_layout.addSpacing(
            20
        )

        form_layout = QFormLayout()

        form_layout.setVerticalSpacing(
            18
        )

        form_layout.setHorizontalSpacing(
            15
        )

        self.username_input = QLineEdit()

        self.username_input.setPlaceholderText(
            "Campus username"
        )

        self.password_input = QLineEdit()

        self.password_input.setPlaceholderText(
            "Campus password"
        )

        self.password_input.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        form_layout.addRow(
            "Username",
            self.username_input
        )

        form_layout.addRow(
            "Password",
            self.password_input
        )

        main_layout.addLayout(
            form_layout
        )

        main_layout.addStretch()

        buttons_layout = QHBoxLayout()

        buttons_layout.setSpacing(
            8
        )

        buttons_layout.addStretch()

        cancel_button = QPushButton(
            "Cancel"
        )

        cancel_button.setFixedSize(
            100,
            38
        )

        cancel_button.clicked.connect(
            self.cancelled.emit
        )

        buttons_layout.addWidget(
            cancel_button
        )

        save_button = QPushButton(
            "Save"
        )

        save_button.setObjectName(
            "save_button"
        )

        save_button.setFixedSize(
            100,
            38
        )

        save_button.clicked.connect(
            self.save_settings
        )

        buttons_layout.addWidget(
            save_button
        )

        main_layout.addLayout(
            buttons_layout
        )

    def load_saved_config(self):

        config = load_config()

        if not config:
            return

        self.username_input.setText(
            config.get(
                "username",
                ""
            )
        )

        self.password_input.setText(
            config.get(
                "password",
                ""
            )
        )

    def save_settings(self):

        old_config = load_config()

        old_username = (
            old_config.get(
                "username",
                ""
            )
            if old_config
            else ""
        )

        old_password = (
            old_config.get(
                "password",
                ""
            )
            if old_config
            else ""
        )

        new_username = (
            self.username_input.text().strip()
        )

        new_password = (
            self.password_input.text()
        )

        credentials_changed = (
            old_username != new_username
            or old_password != new_password
        )

        save_config(
            new_username,
            new_password
        )

        self.saved.emit(
            credentials_changed
        )

    def apply_styles(self):

        self.setStyleSheet(
            """
            QWidget {
                background: #171717;
                color: #f5f5f5;
                font-family: "Segoe UI";
                font-size: 14px;
            }

            QLabel#title {
                color: #f5f5f5;
                font-size: 26px;
                font-weight: 700;
            }

            QLabel#subtitle {
                color: #a1a1aa;
                font-size: 13px;
            }

            QLabel {
                color: #a1a1aa;
                font-size: 13px;
            }

            QLineEdit {
                background: #222222;
                border: 1px solid #303030;
                border-radius: 7px;
                color: #f5f5f5;
                padding: 8px 10px;
                min-height: 20px;
            }

            QLineEdit:focus {
                border-color: #4a4a4a;
            }

            QPushButton {
                background: #292929;
                border: 1px solid #3a3a3a;
                border-radius: 7px;
                color: #f5f5f5;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #333333;
            }

            QPushButton:pressed {
                background: #242424;
            }

            QPushButton#save_button {
                background: #292929;
            }

            QPushButton#save_button:hover {
                background: #333333;
            }
            """
        )