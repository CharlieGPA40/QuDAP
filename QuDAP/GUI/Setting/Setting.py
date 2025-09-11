"""
QuDAP - Notification Settings Page
A modern notification configuration page with multiple notification channels
"""

import sys
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import json
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QGridLayout,
    QGraphicsDropShadowEffect, QLineEdit, QComboBox,
    QCheckBox, QSpinBox, QListWidget, QListWidgetItem,
    QTextEdit, QTabWidget, QRadioButton, QButtonGroup,
    QMessageBox, QInputDialog, QTimeEdit
)
from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QSettings, QTime, QTimer
from PyQt6.QtGui import QFont, QPixmap, QColor, QDesktopServices, QIcon

class AnimatedCard(QFrame):
    """Animated card widget with hover effects"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: none;
            }
        """)

        # Add shadow effect
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 2)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(self.shadow)

    def enterEvent(self, event):
        """Enhance shadow on hover"""
        self.shadow.setBlurRadius(20)
        self.shadow.setOffset(0, 4)
        self.shadow.setColor(QColor(0, 0, 0, 40))
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Reset shadow on leave"""
        self.shadow.setBlurRadius(15)
        self.shadow.setOffset(0, 2)
        self.shadow.setColor(QColor(0, 0, 0, 30))
        super().leaveEvent(event)

class NotificationSettings(QWidget):
    """Notification settings page for QuDAP software"""

    # Signal emitted when settings are saved
    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.settings = QSettings('QuDAP', 'NotificationSettings')
        self.init_ui()
        # Load settings after UI is initialized
        QTimer.singleShot(0, self.load_settings)

    def init_ui(self):
        """Initialize the user interface"""
        self.setMinimumSize(1100, 800)
        self.setStyleSheet("background-color: #f5f5f5;")

        # Create main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        with open("GUI/QSS/QScrollbar.qss", "r") as file:
            scrollbar_stylesheet = file.read()
        scroll.setStyleSheet(scrollbar_stylesheet)

        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(30)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Add header section
        content_layout.addWidget(self.create_header_section())

        # Add notification channels tabs
        content_layout.addWidget(self.create_notification_tabs())

        # Add notification events section
        # content_layout.addWidget(self.create_notification_events_section())

        # Add test notification section
        content_layout.addWidget(self.create_test_section())

        # Add save buttons
        content_layout.addWidget(self.create_action_buttons())

        # Set scroll area widget
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def create_header_section(self):
        """Create the header section with logo and title"""
        header_card = AnimatedCard()
        header_layout = QVBoxLayout(header_card)
        header_layout.setSpacing(15)
        header_layout.setContentsMargins(40, 40, 40, 40)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title using logo
        title = QLabel(self)
        pixmap = QPixmap("GUI/Icon/logo.svg")
        if not pixmap.isNull():
            resized_pixmap = pixmap.scaled(600, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)
            title.setPixmap(resized_pixmap)
        else:
            title.setText("QuDAP")
            title.setFont(QFont("Arial", 42, QFont.Weight.Bold))
            title.setStyleSheet("color: #1e88e5;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle = QLabel("Notification Settings")
        subtitle.setFont(QFont("Arial", 24))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #2c3e50;")

        # Description
        description = QLabel(
            "Configure how QuDAP sends you notifications about experiment status, errors, and completions.\n"
            "Set up multiple notification channels to never miss important updates."
        )
        description.setFont(QFont("Arial", 12))
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d;")

        # Status indicator
        self.status_layout = QHBoxLayout()
        self.status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 16))
        self.status_label = QLabel("No channels configured")
        self.status_label.setFont(QFont("Arial", 11))

        self.update_status_indicator()

        self.status_layout.addWidget(self.status_indicator)
        self.status_layout.addWidget(self.status_label)

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addWidget(description)
        header_layout.addLayout(self.status_layout)

        return header_card

    def create_notification_tabs(self):
        """Create tabbed interface for different notification channels"""
        tabs_card = AnimatedCard()
        tabs_layout = QVBoxLayout(tabs_card)
        tabs_layout.setContentsMargins(30, 30, 30, 30)

        # Section title
        section_title = QLabel("📡 Notification Channels")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50;")
        tabs_layout.addWidget(section_title)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                background-color: white;
                border-radius: 5px;
            }
            QTabBar::tab {
                background-color: #f8f9fa;
                padding: 10px 20px;
                margin-right: 5px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #1e88e5;
            }
            QTabBar::tab:hover {
                background-color: #e8ecef;
            }
        """)

        # Add tabs for different channels
        self.tab_widget.addTab(self.create_email_tab(), "✉️ Email")
        self.tab_widget.addTab(self.create_telegram_tab(), "💬 Telegram")
        self.tab_widget.addTab(self.create_discord_tab(), "🎮 Discord")

        tabs_layout.addWidget(self.tab_widget)

        return tabs_card

    def create_email_tab(self):
        """Create email configuration tab"""
        email_widget = QWidget()
        email_layout = QVBoxLayout(email_widget)
        email_layout.setContentsMargins(20, 20, 20, 20)
        email_layout.setSpacing(15)

        # Enable email notifications
        self.email_enabled = QCheckBox("Enable Email Notifications")
        self.email_enabled.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.email_enabled.setStyleSheet("color: #2c3e50;")
        self.email_enabled.stateChanged.connect(self.toggle_email_settings)
        email_layout.addWidget(self.email_enabled)

        # Email settings container
        self.email_settings_widget = QWidget()
        email_settings_layout = QVBoxLayout(self.email_settings_widget)
        email_settings_layout.setSpacing(15)

        # SMTP Server settings
        server_group = QFrame()
        server_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        server_layout = QVBoxLayout(server_group)

        server_title = QLabel("📧 SMTP Server Configuration")
        server_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        server_title.setStyleSheet("color: #2c3e50;")
        server_layout.addWidget(server_title)

        # SMTP presets
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Quick Setup:")
        preset_label.setFont(QFont("Arial", 11))
        self.smtp_preset = QComboBox()
        self.smtp_preset.addItems([
            "Custom",
            "Gmail (smtp.gmail.com)",
            "Outlook (smtp-mail.outlook.com)",
            "Yahoo (smtp.mail.yahoo.com)",
            "Office 365 (smtp.office365.com)"
        ])
        self.smtp_preset.currentTextChanged.connect(self.apply_smtp_preset)
        self.smtp_preset.setStyleSheet(self.get_combo_style())
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.smtp_preset)
        preset_layout.addStretch()
        server_layout.addLayout(preset_layout)

        # SMTP server
        smtp_layout = QHBoxLayout()
        smtp_label = QLabel("SMTP Server:")
        smtp_label.setFont(QFont("Arial", 11))
        smtp_label.setFixedWidth(120)
        self.smtp_server = QLineEdit()
        self.smtp_server.setPlaceholderText("smtp.gmail.com")
        self.smtp_server.setStyleSheet(self.get_input_style())
        smtp_layout.addWidget(smtp_label)
        smtp_layout.addWidget(self.smtp_server)
        server_layout.addLayout(smtp_layout)

        # SMTP port
        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        port_label.setFont(QFont("Arial", 11))
        port_label.setFixedWidth(120)
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        self.smtp_port.setStyleSheet(self.get_input_style())

        self.smtp_ssl = QCheckBox("Use SSL/TLS")
        self.smtp_ssl.setChecked(True)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.smtp_port)
        port_layout.addWidget(self.smtp_ssl)
        port_layout.addStretch()
        server_layout.addLayout(port_layout)

        # Authentication
        auth_title = QLabel("🔐 Authentication")
        auth_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        auth_title.setStyleSheet("color: #2c3e50; margin-top: 10px;")
        server_layout.addWidget(auth_title)

        # Username
        user_layout = QHBoxLayout()
        user_label = QLabel("Username:")
        user_label.setFont(QFont("Arial", 11))
        user_label.setFixedWidth(120)
        self.smtp_username = QLineEdit()
        self.smtp_username.setPlaceholderText("your.email@gmail.com")
        self.smtp_username.setStyleSheet(self.get_input_style())
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.smtp_username)
        server_layout.addLayout(user_layout)

        # Password
        pass_layout = QHBoxLayout()
        pass_label = QLabel("Password/App Key:")
        pass_label.setFont(QFont("Arial", 11))
        pass_label.setFixedWidth(120)
        self.smtp_password = QLineEdit()
        self.smtp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.smtp_password.setPlaceholderText("App-specific password")
        self.smtp_password.setStyleSheet(self.get_input_style())

        self.show_password = QCheckBox("Show")
        self.show_password.stateChanged.connect(
            lambda: self.smtp_password.setEchoMode(
                QLineEdit.EchoMode.Normal if self.show_password.isChecked()
                else QLineEdit.EchoMode.Password
            )
        )
        pass_layout.addWidget(pass_label)
        pass_layout.addWidget(self.smtp_password)
        pass_layout.addWidget(self.show_password)
        server_layout.addLayout(pass_layout)

        # Help text for app passwords
        help_text = QLabel(
            "💡 For Gmail, use an App Password instead of your regular password.\n"
            "Go to Google Account Settings → Security → 2-Step Verification → App passwords"
        )
        help_text.setWordWrap(True)
        help_text.setFont(QFont("Arial", 10))
        help_text.setStyleSheet("color: #7f8c8d; background-color: #fff3cd; padding: 10px; border-radius: 5px;")
        server_layout.addWidget(help_text)

        email_settings_layout.addWidget(server_group)

        # Recipients settings
        recipients_group = QFrame()
        recipients_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        recipients_layout = QVBoxLayout(recipients_group)

        recipients_title = QLabel("📬 Recipients")
        recipients_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        recipients_title.setStyleSheet("color: #2c3e50;")
        recipients_layout.addWidget(recipients_title)

        # From email
        from_layout = QHBoxLayout()
        from_label = QLabel("From Email:")
        from_label.setFont(QFont("Arial", 11))
        from_label.setFixedWidth(120)
        self.from_email = QLineEdit()
        self.from_email.setPlaceholderText("qudap@auburn.edu")
        self.from_email.setStyleSheet(self.get_input_style())
        from_layout.addWidget(from_label)
        from_layout.addWidget(self.from_email)
        recipients_layout.addLayout(from_layout)

        # To emails
        to_label = QLabel("To Emails (one per line):")
        to_label.setFont(QFont("Arial", 11))
        recipients_layout.addWidget(to_label)

        self.to_emails = QTextEdit()
        self.to_emails.setMaximumHeight(100)
        self.to_emails.setPlaceholderText("recipient1@example.com\nrecipient2@example.com")
        self.to_emails.setStyleSheet(self.get_input_style())
        recipients_layout.addWidget(self.to_emails)

        email_settings_layout.addWidget(recipients_group)

        email_layout.addWidget(self.email_settings_widget)
        email_layout.addStretch()

        # Initially disable if not checked
        self.email_settings_widget.setEnabled(False)

        return email_widget

    def create_telegram_tab(self):
        """Create Telegram configuration tab"""
        telegram_widget = QWidget()
        telegram_layout = QVBoxLayout(telegram_widget)
        telegram_layout.setContentsMargins(20, 20, 20, 20)
        telegram_layout.setSpacing(5)

        # Enable Telegram notifications
        self.telegram_enabled = QCheckBox("Enable Telegram Notifications")
        self.telegram_enabled.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.telegram_enabled.setStyleSheet("color: #2c3e50;")
        self.telegram_enabled.stateChanged.connect(self.toggle_telegram_settings)
        telegram_layout.addWidget(self.telegram_enabled)

        # Telegram settings container
        self.telegram_settings_widget = QWidget()
        telegram_settings_layout = QVBoxLayout(self.telegram_settings_widget)

        # Bot configuration
        bot_group = QFrame()
        bot_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        bot_layout = QVBoxLayout(bot_group)

        bot_title = QLabel("🤖 Telegram Bot Configuration")
        bot_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        bot_title.setStyleSheet("color: #2c3e50;")
        bot_layout.addWidget(bot_title)

        # Bot token
        token_layout = QHBoxLayout()
        token_label = QLabel("Bot Token:")
        token_label.setFont(QFont("Arial", 11))
        token_label.setFixedWidth(100)
        self.telegram_token = QLineEdit()
        self.telegram_token.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
        self.telegram_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.telegram_token.setStyleSheet(self.get_input_style())

        self.show_token = QCheckBox("Show")
        self.show_token.stateChanged.connect(
            lambda: self.telegram_token.setEchoMode(
                QLineEdit.EchoMode.Normal if self.show_token.isChecked()
                else QLineEdit.EchoMode.Password
            )
        )
        token_layout.addWidget(token_label)
        token_layout.addWidget(self.telegram_token)
        token_layout.addWidget(self.show_token)
        bot_layout.addLayout(token_layout)

        # Chat ID
        chat_layout = QHBoxLayout()
        chat_label = QLabel("Chat ID:")
        chat_label.setFont(QFont("Arial", 11))
        chat_label.setFixedWidth(100)
        self.telegram_chat_id = QLineEdit()
        self.telegram_chat_id.setPlaceholderText("-1001234567890 or @channelname")
        self.telegram_chat_id.setStyleSheet(self.get_input_style())
        chat_layout.addWidget(chat_label)
        chat_layout.addWidget(self.telegram_chat_id)
        bot_layout.addLayout(chat_layout)

        # Setup instructions
        instructions = QLabel(
            "📖 How to set up Telegram notifications:\n"
            "1. Create a bot with @BotFather on Telegram\n"
            "2. Get your bot token from BotFather\n"
            "3. Add the bot to your channel/group or start a chat with it\n"
            "4. Get your Chat ID (use @userinfobot for personal chat ID)"
        )
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Arial", 10))
        instructions.setStyleSheet("color: #7f8c8d; background-color: #d1ecf1; padding: 10px; border-radius: 5px;")
        bot_layout.addWidget(instructions)

        # Open Telegram button
        telegram_btn = QPushButton("🔗 Open Telegram BotFather")
        telegram_btn.setFont(QFont("Arial", 11))
        telegram_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        telegram_btn.setStyleSheet("""
            QPushButton {
                background-color: #0088cc;
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0077b5;
            }
        """)
        telegram_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://t.me/botfather")))
        bot_layout.addWidget(telegram_btn)

        telegram_settings_layout.addWidget(bot_group)

        telegram_layout.addWidget(self.telegram_settings_widget)

        return telegram_widget

    def create_discord_tab(self):
        """Create Discord configuration tab"""
        discord_widget = QWidget()
        discord_layout = QVBoxLayout(discord_widget)
        discord_layout.setContentsMargins(20, 20, 20, 20)
        discord_layout.setSpacing(15)

        # Enable Discord notifications
        self.discord_enabled = QCheckBox("Enable Discord Notifications")
        self.discord_enabled.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.discord_enabled.setStyleSheet("color: #2c3e50;")
        self.discord_enabled.stateChanged.connect(self.toggle_discord_settings)
        discord_layout.addWidget(self.discord_enabled)

        # Discord settings container
        self.discord_settings_widget = QWidget()
        discord_settings_layout = QVBoxLayout(self.discord_settings_widget)
        discord_settings_layout.setSpacing(15)

        # Webhook configuration
        webhook_group = QFrame()
        webhook_group.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 5px;
                padding: 15px;
            }
        """)
        webhook_layout = QVBoxLayout(webhook_group)

        webhook_title = QLabel("🔗 Discord Webhook Configuration")
        webhook_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        webhook_title.setStyleSheet("color: #2c3e50;")
        webhook_layout.addWidget(webhook_title)

        # Webhook URL
        url_label = QLabel("Webhook URL:")
        url_label.setFont(QFont("Arial", 11))
        webhook_layout.addWidget(url_label)

        self.discord_webhook = QLineEdit()
        self.discord_webhook.setPlaceholderText("https://discord.com/api/webhooks/...")
        self.discord_webhook.setStyleSheet(self.get_input_style())
        webhook_layout.addWidget(self.discord_webhook)

        # Bot name
        name_layout = QHBoxLayout()
        name_label = QLabel("Bot Name:")
        name_label.setFont(QFont("Arial", 11))
        name_label.setFixedWidth(100)
        self.discord_name = QLineEdit()
        self.discord_name.setPlaceholderText("QuDAP Bot")
        self.discord_name.setStyleSheet(self.get_input_style())
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.discord_name)
        webhook_layout.addLayout(name_layout)

        # Setup instructions
        instructions = QLabel(
            "📖 How to create a Discord webhook:\n"
            "1. Open your Discord server\n"
            "2. Go to Server Settings → Integrations → Webhooks\n"
            "3. Click 'New Webhook' and configure it\n"
            "4. Copy the webhook URL and paste it above"
        )
        instructions.setWordWrap(True)
        instructions.setFont(QFont("Arial", 10))
        instructions.setStyleSheet("color: #7f8c8d; background-color: #e3d5ff; padding: 10px; border-radius: 5px;")
        webhook_layout.addWidget(instructions)

        discord_settings_layout.addWidget(webhook_group)

        discord_layout.addWidget(self.discord_settings_widget)
        discord_layout.addStretch()

        # Initially disable if not checked
        self.discord_settings_widget.setEnabled(False)

        return discord_widget

    def create_test_section(self):
        """Create test notification section"""
        test_card = AnimatedCard()
        test_layout = QVBoxLayout(test_card)
        test_layout.setContentsMargins(30, 30, 30, 30)
        test_layout.setSpacing(15)

        # Section title
        section_title = QLabel("🧪 Test Notifications")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50;")
        test_layout.addWidget(section_title)

        # Description
        description = QLabel("Send a test notification to verify your configuration:")
        description.setFont(QFont("Arial", 12))
        description.setStyleSheet("color: #7f8c8d;")
        test_layout.addWidget(description)

        # Test buttons layout
        buttons_layout = QHBoxLayout()

        # Test email button
        test_email_btn = QPushButton("✉️ Test Email")
        test_email_btn.setFont(QFont("Arial", 11))
        test_email_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_email_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        test_email_btn.clicked.connect(lambda: self.send_test_notification("email"))
        buttons_layout.addWidget(test_email_btn)

        # Test Telegram button
        test_telegram_btn = QPushButton("💬 Test Telegram")
        test_telegram_btn.setFont(QFont("Arial", 11))
        test_telegram_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_telegram_btn.setStyleSheet("""
            QPushButton {
                background-color: #0088cc;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0077b5;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        test_telegram_btn.clicked.connect(lambda: self.send_test_notification("telegram"))
        buttons_layout.addWidget(test_telegram_btn)

        # Test all button
        test_discord_btn = QPushButton("📡 Test Discord")
        test_discord_btn.setFont(QFont("Arial", 11))
        test_discord_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_discord_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        test_discord_btn.clicked.connect(lambda: self.send_test_notification("discord"))
        buttons_layout.addWidget(test_discord_btn)

        buttons_layout.addStretch()
        test_layout.addLayout(buttons_layout)

        # Test result display
        self.test_result = QLabel("")
        self.test_result.setWordWrap(True)
        self.test_result.setFont(QFont("Arial", 11))
        test_layout.addWidget(self.test_result)

        return test_card

    def create_action_buttons(self):
        """Create save and cancel buttons"""
        buttons_card = AnimatedCard()
        buttons_layout = QHBoxLayout(buttons_card)
        buttons_layout.setContentsMargins(30, 20, 30, 20)

        # Save button
        save_btn = QPushButton("💾 Save Settings")
        save_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e88e5;
                color: white;
                padding: 12px 30px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
        """)
        save_btn.clicked.connect(self.save_settings)

        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setFont(QFont("Arial", 12))
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #dc3545;
                padding: 12px 30px;
                border: 2px solid #dc3545;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #dc3545;
                color: white;
            }
        """)
        cancel_btn.clicked.connect(self.close)

        # Reset button
        resetl_btn = QPushButton("🔄 Reset Settings")
        resetl_btn.setFont(QFont("Arial", 12))
        resetl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        resetl_btn.setStyleSheet("""
                            QPushButton {
                                background-color: #ea711a;
                                color: white;
                                padding: 12px 30px;
                                border-radius: 5px;
                            }
                            QPushButton:hover {
                                background-color: #e86100;
                            }
                        """)
        resetl_btn.clicked.connect(self.delete_settings)

        buttons_layout.addStretch()
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(resetl_btn)
        buttons_layout.addWidget(cancel_btn)

        return buttons_card

    def get_input_style(self):
        """Get consistent input field style"""
        return """
            QLineEdit, QTextEdit, QSpinBox {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 10px;
                font-size: 11px;
                background-color: white;
            }
            QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
                border-color: #1e88e5;
                outline: none;
            }
        """

    def get_combo_style(self):
        """Get consistent combo box style"""
        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            combo_stylesheet = file.read()
        return combo_stylesheet

    def toggle_email_settings(self, state):
        """Toggle email settings availability"""
        self.email_settings_widget.setEnabled(state == 2)
        self.update_status_indicator()

    def toggle_telegram_settings(self, state):
        """Toggle Telegram settings availability"""
        self.telegram_settings_widget.setEnabled(state == 2)
        self.update_status_indicator()

    def toggle_discord_settings(self, state):
        """Toggle Discord settings availability"""
        self.discord_settings_widget.setEnabled(state == 2)
        self.update_status_indicator()

    def apply_smtp_preset(self, preset):
        """Apply SMTP server preset"""
        presets = {
            "Gmail (smtp.gmail.com)": ("smtp.gmail.com", 587, True),
            "Outlook (smtp-mail.outlook.com)": ("smtp-mail.outlook.com", 587, True),
            "Yahoo (smtp.mail.yahoo.com)": ("smtp.mail.yahoo.com", 587, True),
            "Office 365 (smtp.office365.com)": ("smtp.office365.com", 587, True)
        }

        if preset in presets:
            server, port, ssl = presets[preset]
            self.smtp_server.setText(server)
            self.smtp_port.setValue(port)
            self.smtp_ssl.setChecked(ssl)

    def update_status_indicator(self):
        """Update the status indicator based on enabled channels"""
        # Check if UI elements exist before accessing them
        if not all([
            hasattr(self, 'email_enabled') and self.email_enabled,
            hasattr(self, 'telegram_enabled') and self.telegram_enabled,
            hasattr(self, 'discord_enabled') and self.discord_enabled
        ]):
            return

        enabled_count = sum([
            self.email_enabled.isChecked(),
            self.telegram_enabled.isChecked(),
            self.discord_enabled.isChecked(),
        ])

        if enabled_count == 0:
            self.status_indicator.setText("●")
            self.status_indicator.setStyleSheet("color: #dc3545;")
            self.status_label.setText("No channels configured")
        elif enabled_count == 1:
            self.status_indicator.setText("●")
            self.status_indicator.setStyleSheet("color: #28a745;")
            self.status_label.setText(f"{enabled_count} channel configured")
        else:
            self.status_indicator.setText("●")
            self.status_indicator.setStyleSheet("color: #28a745;")
            self.status_label.setText(f"{enabled_count} channels configured")

    def send_test_notification(self, channel):
        """Send test notification to specified channel"""
        if channel == "email" and self.email_enabled.isChecked():
            self.test_result.setText("📧 Sending test email...")
            self.test_result.setStyleSheet("color: #17a2b8;")
            # Implement actual email sending here
            sender_email = self.from_email.text()
            password = self.smtp_password.text()  # Consider using an app password or environment variable
            receiver_email = self.to_emails.toPlainText()
            receiver_email = [email.strip() for email in receiver_email.splitlines() if email.strip()]
            receiver_email = ", ".join(receiver_email)
            # Create the email
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = "This is a test email"

            body = "This is a test email."
            message.attach(MIMEText(body, "plain"))

            # Send the email using AU's SMTP server
            try:
                with smtplib.SMTP( self.smtp_server.text(), self.smtp_port.value()) as server:
                    server.starttls()
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_email, message.as_string())
                self.show_test_result('Successfully sent test email!', True)
            except Exception as e:
                self.show_test_result('Fail sent test email!', False)
                QMessageBox.warning(self, 'Warning', f'{e}')
            # QTimer.singleShot(2000, lambda: self.show_test_result("Email sent successfully!", True))
        elif channel == "telegram" and self.telegram_enabled.isChecked():
            self.test_result.setText("💬 Sending test Telegram message...")
            self.test_result.setStyleSheet("color: #17a2b8;")
            # Implement actual Telegram sending here
            bot_token = self.telegram_token.text()
            chat_id = self.telegram_chat_id.text()
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {"chat_id": chat_id, "text": "This is a test message..."}
            response = requests.post(url, data=data)
            QTimer.singleShot(2000, lambda: self.show_test_result("Telegram message sent!", True))
        elif channel == "discord":
            self.test_result.setText("📡 Sending test to all enabled channels...")
            self.test_result.setStyleSheet("color: #17a2b8;")
            webhook_url = self.discord_webhook.text()

            # Message content
            data = {
                "content": "This is a test message...",
                "username": f"{self.discord_name.text()}"  # Optional: sets the sender name
            }

            response = requests.post(webhook_url, json=data)

            if response.status_code == 204:
                QTimer.singleShot(2000, lambda: self.show_test_result("Discord message sent!", True))
            else:
                QMessageBox.warning(self, 'Warning', f"Failed to send message: {response.status_code} - {response.text}")
                QTimer.singleShot(2000, lambda: self.show_test_result("Failed to send message!", False))
        else:
            self.test_result.setText("⚠️ Please enable and configure the channel first")
            self.test_result.setStyleSheet("color: #dc3545;")

    def show_test_result(self, message, success):
        """Show test result message"""
        if success:
            self.test_result.setText(f"✅ {message}")
            self.test_result.setStyleSheet("color: #28a745;")
        else:
            self.test_result.setText(f"❌ {message}")
            self.test_result.setStyleSheet("color: #dc3545;")

    def save_settings(self):
        """Save all notification settings"""
        # Save email settings
        self.settings.setValue('email/enabled', self.email_enabled.isChecked())
        self.settings.setValue('email/smtp_server', self.smtp_server.text())
        self.settings.setValue('email/smtp_port', self.smtp_port.value())
        self.settings.setValue('email/smtp_ssl', self.smtp_ssl.isChecked())
        self.settings.setValue('email/username', self.smtp_username.text())
        self.settings.setValue('email/password', self.smtp_password.text())
        self.settings.setValue('email/from_email', self.from_email.text())
        self.settings.setValue('email/to_emails', self.to_emails.toPlainText())

        # Save Telegram settings
        self.settings.setValue('telegram/enabled', self.telegram_enabled.isChecked())
        self.settings.setValue('telegram/token', self.telegram_token.text())
        self.settings.setValue('telegram/chat_id', self.telegram_chat_id.text())

        # Save Discord settings
        self.settings.setValue('discord/enabled', self.discord_enabled.isChecked())
        self.settings.setValue('discord/webhook', self.discord_webhook.text())
        self.settings.setValue('discord/name', self.discord_name.text())

        # Show success message
        QMessageBox.information(self, "Success", "Notification settings saved successfully!")
        self.settings_saved.emit()

    def load_settings(self):
        """Load saved notification settings"""
        # Load email settings
        self.email_enabled.setChecked(self.settings.value('email/enabled', False, bool))
        self.smtp_server.setText(self.settings.value('email/smtp_server', ''))
        self.smtp_port.setValue(self.settings.value('email/smtp_port', 587, int))
        self.smtp_ssl.setChecked(self.settings.value('email/smtp_ssl', True, bool))
        self.smtp_username.setText(self.settings.value('email/username', ''))
        self.smtp_password.setText(self.settings.value('email/password', ''))
        self.from_email.setText(self.settings.value('email/from_email', ''))
        self.to_emails.setPlainText(self.settings.value('email/to_emails', ''))

        # Load Telegram settings
        self.telegram_enabled.setChecked(self.settings.value('telegram/enabled', False, bool))
        self.telegram_token.setText(self.settings.value('telegram/token', ''))
        self.telegram_chat_id.setText(self.settings.value('telegram/chat_id', ''))

        # Load Discord settings
        self.discord_enabled.setChecked(self.settings.value('discord/enabled', False, bool))
        self.discord_webhook.setText(self.settings.value('discord/webhook', ''))
        self.discord_name.setText(self.settings.value('discord/name', ''))


        self.update_status_indicator()

    def delete_settings(self):
        """Delete all saved notification settings"""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Delete All Settings",
            "Are you sure you want to delete all notification settings?\n\n"
            "This will remove:\n"
            "• All email configurations\n"
            "• All notification channel settings\n"
            "• All saved credentials\n\n"
            "This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Clear all settings
            self.settings.clear()

            # Reset UI to defaults
            self.reset_ui_to_defaults()

            # Show success message
            QMessageBox.information(
                self,
                "Settings Deleted",
                "All notification settings have been deleted successfully.\n"
                "The form has been reset to defaults."
            )

            # Update status indicator
            self.update_status_indicator()

    def reset_ui_to_defaults(self):
        """Reset all UI elements to default values"""
        # Reset email settings
        self.email_enabled.setChecked(False)
        self.smtp_server.clear()
        self.smtp_port.setValue(587)
        self.smtp_ssl.setChecked(True)
        self.smtp_username.clear()
        self.smtp_password.clear()
        self.from_email.clear()
        self.to_emails.clear()
        self.smtp_preset.setCurrentIndex(0)

        # Reset Telegram settings
        self.telegram_enabled.setChecked(False)
        self.telegram_token.clear()
        self.telegram_chat_id.clear()

        # Reset Discord settings
        self.discord_enabled.setChecked(False)
        self.discord_webhook.clear()
        self.discord_name.clear()

        # Clear test result
        self.test_result.clear()

        # Disable all settings widgets
        self.email_settings_widget.setEnabled(False)
        self.telegram_settings_widget.setEnabled(False)
        self.discord_settings_widget.setEnabled(False)


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = NotificationSettings()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()