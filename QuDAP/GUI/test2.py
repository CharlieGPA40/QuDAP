# # # """
# # # QuDAP - Notification Settings Page
# # # A modern notification configuration page with multiple notification channels
# # # """
# # #
# # # import sys
# # # import json
# # # import os
# # # from pathlib import Path
# # # from PyQt6.QtWidgets import (
# # #     QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
# # #     QPushButton, QScrollArea, QFrame, QGridLayout,
# # #     QGraphicsDropShadowEffect, QLineEdit, QComboBox,
# # #     QCheckBox, QSpinBox, QListWidget, QListWidgetItem,
# # #     QTextEdit, QTabWidget, QRadioButton, QButtonGroup,
# # #     QMessageBox, QInputDialog, QTimeEdit
# # # )
# # # from PyQt6.QtCore import Qt, QUrl, pyqtSignal, QSettings, QTime, QTimer
# # # from PyQt6.QtGui import QFont, QPixmap, QColor, QDesktopServices, QIcon
# # #
# # # class AnimatedCard(QFrame):
# # #     """Animated card widget with hover effects"""
# # #
# # #     def __init__(self, parent=None):
# # #         super().__init__(parent)
# # #         self.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: white;
# # #                 border-radius: 10px;
# # #                 border: none;
# # #             }
# # #         """)
# # #
# # #         # Add shadow effect
# # #         self.shadow = QGraphicsDropShadowEffect()
# # #         self.shadow.setBlurRadius(15)
# # #         self.shadow.setOffset(0, 2)
# # #         self.shadow.setColor(QColor(0, 0, 0, 30))
# # #         self.setGraphicsEffect(self.shadow)
# # #
# # #     def enterEvent(self, event):
# # #         """Enhance shadow on hover"""
# # #         self.shadow.setBlurRadius(20)
# # #         self.shadow.setOffset(0, 4)
# # #         self.shadow.setColor(QColor(0, 0, 0, 40))
# # #         super().enterEvent(event)
# # #
# # #     def leaveEvent(self, event):
# # #         """Reset shadow on leave"""
# # #         self.shadow.setBlurRadius(15)
# # #         self.shadow.setOffset(0, 2)
# # #         self.shadow.setColor(QColor(0, 0, 0, 30))
# # #         super().leaveEvent(event)
# # #
# # # class NotificationSettings(QWidget):
# # #     """Notification settings page for QuDAP software"""
# # #
# # #     # Signal emitted when settings are saved
# # #     settings_saved = pyqtSignal()
# # #
# # #     def __init__(self):
# # #         super().__init__()
# # #         self.settings = QSettings('QuDAP', 'NotificationSettings')
# # #         self.init_ui()
# # #         # Load settings after UI is initialized
# # #         QTimer.singleShot(0, self.load_settings)
# # #
# # #     def init_ui(self):
# # #         """Initialize the user interface"""
# # #         self.setWindowTitle("Notification Settings - QuDAP")
# # #         self.setMinimumSize(1100, 800)
# # #         self.setStyleSheet("background-color: #f5f5f5;")
# # #
# # #         # Create main layout
# # #         main_layout = QVBoxLayout(self)
# # #         main_layout.setSpacing(20)
# # #         main_layout.setContentsMargins(20, 20, 20, 20)
# # #
# # #         # Create scroll area
# # #         scroll = QScrollArea()
# # #         scroll.setWidgetResizable(True)
# # #         scroll.setStyleSheet("""
# # #             QScrollArea {
# # #                 border: none;
# # #                 background-color: transparent;
# # #             }
# # #             QScrollBar:vertical {
# # #                 width: 12px;
# # #                 background-color: #f0f0f0;
# # #                 border-radius: 6px;
# # #             }
# # #             QScrollBar::handle:vertical {
# # #                 background-color: #c0c0c0;
# # #                 border-radius: 6px;
# # #                 min-height: 20px;
# # #             }
# # #             QScrollBar::handle:vertical:hover {
# # #                 background-color: #a0a0a0;
# # #             }
# # #         """)
# # #
# # #         # Create content widget
# # #         content_widget = QWidget()
# # #         content_layout = QVBoxLayout(content_widget)
# # #         content_layout.setSpacing(30)
# # #         content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
# # #
# # #         # Add header section
# # #         content_layout.addWidget(self.create_header_section())
# # #
# # #         # Add notification channels tabs
# # #         content_layout.addWidget(self.create_notification_tabs())
# # #
# # #         # Add notification events section
# # #         content_layout.addWidget(self.create_notification_events_section())
# # #
# # #         # Add test notification section
# # #         content_layout.addWidget(self.create_test_section())
# # #
# # #         # Add save buttons
# # #         content_layout.addWidget(self.create_action_buttons())
# # #
# # #         # Set scroll area widget
# # #         scroll.setWidget(content_widget)
# # #         main_layout.addWidget(scroll)
# # #
# # #     def create_header_section(self):
# # #         """Create the header section with logo and title"""
# # #         header_card = AnimatedCard()
# # #         header_layout = QVBoxLayout(header_card)
# # #         header_layout.setSpacing(15)
# # #         header_layout.setContentsMargins(40, 40, 40, 40)
# # #         header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
# # #
# # #         # Title using logo
# # #         title = QLabel(self)
# # #         pixmap = QPixmap("GUI/Icon/logo.svg")
# # #         if not pixmap.isNull():
# # #             resized_pixmap = pixmap.scaled(200, 88, Qt.AspectRatioMode.KeepAspectRatio,
# # #                                           Qt.TransformationMode.SmoothTransformation)
# # #             title.setPixmap(resized_pixmap)
# # #         else:
# # #             title.setText("QuDAP")
# # #             title.setFont(QFont("Arial", 42, QFont.Weight.Bold))
# # #             title.setStyleSheet("color: #1e88e5;")
# # #         title.setAlignment(Qt.AlignmentFlag.AlignCenter)
# # #
# # #         # Subtitle
# # #         subtitle = QLabel("Notification Settings")
# # #         subtitle.setFont(QFont("Arial", 24))
# # #         subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
# # #         subtitle.setStyleSheet("color: #2c3e50;")
# # #
# # #         # Description
# # #         description = QLabel(
# # #             "Configure how QuDAP sends you notifications about experiment status, errors, and completions.\n"
# # #             "Set up multiple notification channels to never miss important updates."
# # #         )
# # #         description.setFont(QFont("Arial", 12))
# # #         description.setAlignment(Qt.AlignmentFlag.AlignCenter)
# # #         description.setWordWrap(True)
# # #         description.setStyleSheet("color: #7f8c8d;")
# # #
# # #         # Status indicator
# # #         self.status_layout = QHBoxLayout()
# # #         self.status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
# # #
# # #         self.status_indicator = QLabel("●")
# # #         self.status_indicator.setFont(QFont("Arial", 16))
# # #         self.status_label = QLabel("No channels configured")
# # #         self.status_label.setFont(QFont("Arial", 11))
# # #
# # #         self.update_status_indicator()
# # #
# # #         self.status_layout.addWidget(self.status_indicator)
# # #         self.status_layout.addWidget(self.status_label)
# # #
# # #         header_layout.addWidget(title)
# # #         header_layout.addWidget(subtitle)
# # #         header_layout.addWidget(description)
# # #         header_layout.addLayout(self.status_layout)
# # #
# # #         return header_card
# # #
# # #     def create_notification_tabs(self):
# # #         """Create tabbed interface for different notification channels"""
# # #         tabs_card = AnimatedCard()
# # #         tabs_layout = QVBoxLayout(tabs_card)
# # #         tabs_layout.setContentsMargins(30, 30, 30, 30)
# # #
# # #         # Section title
# # #         section_title = QLabel("📡 Notification Channels")
# # #         section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
# # #         section_title.setStyleSheet("color: #2c3e50;")
# # #         tabs_layout.addWidget(section_title)
# # #
# # #         # Create tab widget
# # #         self.tab_widget = QTabWidget()
# # #         self.tab_widget.setStyleSheet("""
# # #             QTabWidget::pane {
# # #                 border: 1px solid #e0e0e0;
# # #                 background-color: white;
# # #                 border-radius: 5px;
# # #             }
# # #             QTabBar::tab {
# # #                 background-color: #f8f9fa;
# # #                 padding: 10px 20px;
# # #                 margin-right: 5px;
# # #                 border-top-left-radius: 5px;
# # #                 border-top-right-radius: 5px;
# # #             }
# # #             QTabBar::tab:selected {
# # #                 background-color: white;
# # #                 border-bottom: 2px solid #1e88e5;
# # #             }
# # #             QTabBar::tab:hover {
# # #                 background-color: #e8ecef;
# # #             }
# # #         """)
# # #
# # #         # Add tabs for different channels
# # #         self.tab_widget.addTab(self.create_email_tab(), "✉️ Email")
# # #         self.tab_widget.addTab(self.create_telegram_tab(), "💬 Telegram")
# # #         self.tab_widget.addTab(self.create_discord_tab(), "🎮 Discord")
# # #         self.tab_widget.addTab(self.create_slack_tab(), "💼 Slack")
# # #         self.tab_widget.addTab(self.create_webhook_tab(), "🔗 Webhook")
# # #
# # #         tabs_layout.addWidget(self.tab_widget)
# # #
# # #         return tabs_card
# # #
# # #     def create_email_tab(self):
# # #         """Create email configuration tab"""
# # #         email_widget = QWidget()
# # #         email_layout = QVBoxLayout(email_widget)
# # #         email_layout.setContentsMargins(20, 20, 20, 20)
# # #         email_layout.setSpacing(15)
# # #
# # #         # Enable email notifications
# # #         self.email_enabled = QCheckBox("Enable Email Notifications")
# # #         self.email_enabled.setFont(QFont("Arial", 12, QFont.Weight.Bold))
# # #         self.email_enabled.setStyleSheet("color: #2c3e50;")
# # #         self.email_enabled.stateChanged.connect(self.toggle_email_settings)
# # #         email_layout.addWidget(self.email_enabled)
# # #
# # #         # Email settings container
# # #         self.email_settings_widget = QWidget()
# # #         email_settings_layout = QVBoxLayout(self.email_settings_widget)
# # #         email_settings_layout.setSpacing(15)
# # #
# # #         # SMTP Server settings
# # #         server_group = QFrame()
# # #         server_group.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 15px;
# # #             }
# # #         """)
# # #         server_layout = QVBoxLayout(server_group)
# # #
# # #         server_title = QLabel("📧 SMTP Server Configuration")
# # #         server_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         server_title.setStyleSheet("color: #2c3e50;")
# # #         server_layout.addWidget(server_title)
# # #
# # #         # SMTP presets
# # #         preset_layout = QHBoxLayout()
# # #         preset_label = QLabel("Quick Setup:")
# # #         preset_label.setFont(QFont("Arial", 11))
# # #         self.smtp_preset = QComboBox()
# # #         self.smtp_preset.addItems([
# # #             "Custom",
# # #             "Gmail (smtp.gmail.com)",
# # #             "Outlook (smtp-mail.outlook.com)",
# # #             "Yahoo (smtp.mail.yahoo.com)",
# # #             "Office 365 (smtp.office365.com)"
# # #         ])
# # #         self.smtp_preset.currentTextChanged.connect(self.apply_smtp_preset)
# # #         self.smtp_preset.setStyleSheet(self.get_combo_style())
# # #         preset_layout.addWidget(preset_label)
# # #         preset_layout.addWidget(self.smtp_preset)
# # #         preset_layout.addStretch()
# # #         server_layout.addLayout(preset_layout)
# # #
# # #         # SMTP server
# # #         smtp_layout = QHBoxLayout()
# # #         smtp_label = QLabel("SMTP Server:")
# # #         smtp_label.setFont(QFont("Arial", 11))
# # #         smtp_label.setFixedWidth(120)
# # #         self.smtp_server = QLineEdit()
# # #         self.smtp_server.setPlaceholderText("smtp.gmail.com")
# # #         self.smtp_server.setStyleSheet(self.get_input_style())
# # #         smtp_layout.addWidget(smtp_label)
# # #         smtp_layout.addWidget(self.smtp_server)
# # #         server_layout.addLayout(smtp_layout)
# # #
# # #         # SMTP port
# # #         port_layout = QHBoxLayout()
# # #         port_label = QLabel("Port:")
# # #         port_label.setFont(QFont("Arial", 11))
# # #         port_label.setFixedWidth(120)
# # #         self.smtp_port = QSpinBox()
# # #         self.smtp_port.setRange(1, 65535)
# # #         self.smtp_port.setValue(587)
# # #         self.smtp_port.setStyleSheet(self.get_input_style())
# # #
# # #         self.smtp_ssl = QCheckBox("Use SSL/TLS")
# # #         self.smtp_ssl.setChecked(True)
# # #         port_layout.addWidget(port_label)
# # #         port_layout.addWidget(self.smtp_port)
# # #         port_layout.addWidget(self.smtp_ssl)
# # #         port_layout.addStretch()
# # #         server_layout.addLayout(port_layout)
# # #
# # #         # Authentication
# # #         auth_title = QLabel("🔐 Authentication")
# # #         auth_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         auth_title.setStyleSheet("color: #2c3e50; margin-top: 10px;")
# # #         server_layout.addWidget(auth_title)
# # #
# # #         # Username
# # #         user_layout = QHBoxLayout()
# # #         user_label = QLabel("Username:")
# # #         user_label.setFont(QFont("Arial", 11))
# # #         user_label.setFixedWidth(120)
# # #         self.smtp_username = QLineEdit()
# # #         self.smtp_username.setPlaceholderText("your.email@gmail.com")
# # #         self.smtp_username.setStyleSheet(self.get_input_style())
# # #         user_layout.addWidget(user_label)
# # #         user_layout.addWidget(self.smtp_username)
# # #         server_layout.addLayout(user_layout)
# # #
# # #         # Password
# # #         pass_layout = QHBoxLayout()
# # #         pass_label = QLabel("Password/App Key:")
# # #         pass_label.setFont(QFont("Arial", 11))
# # #         pass_label.setFixedWidth(120)
# # #         self.smtp_password = QLineEdit()
# # #         self.smtp_password.setEchoMode(QLineEdit.EchoMode.Password)
# # #         self.smtp_password.setPlaceholderText("App-specific password")
# # #         self.smtp_password.setStyleSheet(self.get_input_style())
# # #
# # #         self.show_password = QCheckBox("Show")
# # #         self.show_password.stateChanged.connect(
# # #             lambda: self.smtp_password.setEchoMode(
# # #                 QLineEdit.EchoMode.Normal if self.show_password.isChecked()
# # #                 else QLineEdit.EchoMode.Password
# # #             )
# # #         )
# # #         pass_layout.addWidget(pass_label)
# # #         pass_layout.addWidget(self.smtp_password)
# # #         pass_layout.addWidget(self.show_password)
# # #         server_layout.addLayout(pass_layout)
# # #
# # #         # Help text for app passwords
# # #         help_text = QLabel(
# # #             "💡 For Gmail, use an App Password instead of your regular password.\n"
# # #             "Go to Google Account Settings → Security → 2-Step Verification → App passwords"
# # #         )
# # #         help_text.setWordWrap(True)
# # #         help_text.setFont(QFont("Arial", 10))
# # #         help_text.setStyleSheet("color: #7f8c8d; background-color: #fff3cd; padding: 10px; border-radius: 5px;")
# # #         server_layout.addWidget(help_text)
# # #
# # #         email_settings_layout.addWidget(server_group)
# # #
# # #         # Recipients settings
# # #         recipients_group = QFrame()
# # #         recipients_group.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 15px;
# # #             }
# # #         """)
# # #         recipients_layout = QVBoxLayout(recipients_group)
# # #
# # #         recipients_title = QLabel("📬 Recipients")
# # #         recipients_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         recipients_title.setStyleSheet("color: #2c3e50;")
# # #         recipients_layout.addWidget(recipients_title)
# # #
# # #         # From email
# # #         from_layout = QHBoxLayout()
# # #         from_label = QLabel("From Email:")
# # #         from_label.setFont(QFont("Arial", 11))
# # #         from_label.setFixedWidth(120)
# # #         self.from_email = QLineEdit()
# # #         self.from_email.setPlaceholderText("qudap@auburn.edu")
# # #         self.from_email.setStyleSheet(self.get_input_style())
# # #         from_layout.addWidget(from_label)
# # #         from_layout.addWidget(self.from_email)
# # #         recipients_layout.addLayout(from_layout)
# # #
# # #         # To emails
# # #         to_label = QLabel("To Emails (one per line):")
# # #         to_label.setFont(QFont("Arial", 11))
# # #         recipients_layout.addWidget(to_label)
# # #
# # #         self.to_emails = QTextEdit()
# # #         self.to_emails.setMaximumHeight(100)
# # #         self.to_emails.setPlaceholderText("recipient1@example.com\nrecipient2@example.com")
# # #         self.to_emails.setStyleSheet(self.get_input_style())
# # #         recipients_layout.addWidget(self.to_emails)
# # #
# # #         email_settings_layout.addWidget(recipients_group)
# # #
# # #         email_layout.addWidget(self.email_settings_widget)
# # #         email_layout.addStretch()
# # #
# # #         # Initially disable if not checked
# # #         self.email_settings_widget.setEnabled(False)
# # #
# # #         return email_widget
# # #
# # #     def create_telegram_tab(self):
# # #         """Create Telegram configuration tab"""
# # #         telegram_widget = QWidget()
# # #         telegram_layout = QVBoxLayout(telegram_widget)
# # #         telegram_layout.setContentsMargins(20, 20, 20, 20)
# # #         telegram_layout.setSpacing(15)
# # #
# # #         # Enable Telegram notifications
# # #         self.telegram_enabled = QCheckBox("Enable Telegram Notifications")
# # #         self.telegram_enabled.setFont(QFont("Arial", 12, QFont.Weight.Bold))
# # #         self.telegram_enabled.setStyleSheet("color: #2c3e50;")
# # #         self.telegram_enabled.stateChanged.connect(self.toggle_telegram_settings)
# # #         telegram_layout.addWidget(self.telegram_enabled)
# # #
# # #         # Telegram settings container
# # #         self.telegram_settings_widget = QWidget()
# # #         telegram_settings_layout = QVBoxLayout(self.telegram_settings_widget)
# # #         telegram_settings_layout.setSpacing(15)
# # #
# # #         # Bot configuration
# # #         bot_group = QFrame()
# # #         bot_group.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 15px;
# # #             }
# # #         """)
# # #         bot_layout = QVBoxLayout(bot_group)
# # #
# # #         bot_title = QLabel("🤖 Telegram Bot Configuration")
# # #         bot_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         bot_title.setStyleSheet("color: #2c3e50;")
# # #         bot_layout.addWidget(bot_title)
# # #
# # #         # Bot token
# # #         token_layout = QHBoxLayout()
# # #         token_label = QLabel("Bot Token:")
# # #         token_label.setFont(QFont("Arial", 11))
# # #         token_label.setFixedWidth(100)
# # #         self.telegram_token = QLineEdit()
# # #         self.telegram_token.setPlaceholderText("123456789:ABCdefGHIjklMNOpqrsTUVwxyz")
# # #         self.telegram_token.setEchoMode(QLineEdit.EchoMode.Password)
# # #         self.telegram_token.setStyleSheet(self.get_input_style())
# # #
# # #         self.show_token = QCheckBox("Show")
# # #         self.show_token.stateChanged.connect(
# # #             lambda: self.telegram_token.setEchoMode(
# # #                 QLineEdit.EchoMode.Normal if self.show_token.isChecked()
# # #                 else QLineEdit.EchoMode.Password
# # #             )
# # #         )
# # #         token_layout.addWidget(token_label)
# # #         token_layout.addWidget(self.telegram_token)
# # #         token_layout.addWidget(self.show_token)
# # #         bot_layout.addLayout(token_layout)
# # #
# # #         # Chat ID
# # #         chat_layout = QHBoxLayout()
# # #         chat_label = QLabel("Chat ID:")
# # #         chat_label.setFont(QFont("Arial", 11))
# # #         chat_label.setFixedWidth(100)
# # #         self.telegram_chat_id = QLineEdit()
# # #         self.telegram_chat_id.setPlaceholderText("-1001234567890 or @channelname")
# # #         self.telegram_chat_id.setStyleSheet(self.get_input_style())
# # #         chat_layout.addWidget(chat_label)
# # #         chat_layout.addWidget(self.telegram_chat_id)
# # #         bot_layout.addLayout(chat_layout)
# # #
# # #         # Setup instructions
# # #         instructions = QLabel(
# # #             "📖 How to set up Telegram notifications:\n"
# # #             "1. Create a bot with @BotFather on Telegram\n"
# # #             "2. Get your bot token from BotFather\n"
# # #             "3. Add the bot to your channel/group or start a chat with it\n"
# # #             "4. Get your Chat ID (use @userinfobot for personal chat ID)"
# # #         )
# # #         instructions.setWordWrap(True)
# # #         instructions.setFont(QFont("Arial", 10))
# # #         instructions.setStyleSheet("color: #7f8c8d; background-color: #d1ecf1; padding: 10px; border-radius: 5px;")
# # #         bot_layout.addWidget(instructions)
# # #
# # #         # Open Telegram button
# # #         telegram_btn = QPushButton("🔗 Open Telegram BotFather")
# # #         telegram_btn.setFont(QFont("Arial", 11))
# # #         telegram_btn.setCursor(Qt.CursorShape.PointingHandCursor)
# # #         telegram_btn.setStyleSheet("""
# # #             QPushButton {
# # #                 background-color: #0088cc;
# # #                 color: white;
# # #                 padding: 10px;
# # #                 border-radius: 5px;
# # #                 font-weight: bold;
# # #             }
# # #             QPushButton:hover {
# # #                 background-color: #0077b5;
# # #             }
# # #         """)
# # #         telegram_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://t.me/botfather")))
# # #         bot_layout.addWidget(telegram_btn)
# # #
# # #         telegram_settings_layout.addWidget(bot_group)
# # #
# # #         # Message format
# # #         format_group = QFrame()
# # #         format_group.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 15px;
# # #             }
# # #         """)
# # #         format_layout = QVBoxLayout(format_group)
# # #
# # #         format_title = QLabel("📝 Message Format")
# # #         format_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         format_title.setStyleSheet("color: #2c3e50;")
# # #         format_layout.addWidget(format_title)
# # #
# # #         self.telegram_format = QComboBox()
# # #         self.telegram_format.addItems(["Plain Text", "Markdown", "HTML"])
# # #         self.telegram_format.setStyleSheet(self.get_combo_style())
# # #         format_layout.addWidget(self.telegram_format)
# # #
# # #         telegram_settings_layout.addWidget(format_group)
# # #
# # #         telegram_layout.addWidget(self.telegram_settings_widget)
# # #         telegram_layout.addStretch()
# # #
# # #         # Initially disable if not checked
# # #         self.telegram_settings_widget.setEnabled(False)
# # #
# # #         return telegram_widget
# # #
# # #     def create_discord_tab(self):
# # #         """Create Discord configuration tab"""
# # #         discord_widget = QWidget()
# # #         discord_layout = QVBoxLayout(discord_widget)
# # #         discord_layout.setContentsMargins(20, 20, 20, 20)
# # #         discord_layout.setSpacing(15)
# # #
# # #         # Enable Discord notifications
# # #         self.discord_enabled = QCheckBox("Enable Discord Notifications")
# # #         self.discord_enabled.setFont(QFont("Arial", 12, QFont.Weight.Bold))
# # #         self.discord_enabled.setStyleSheet("color: #2c3e50;")
# # #         self.discord_enabled.stateChanged.connect(self.toggle_discord_settings)
# # #         discord_layout.addWidget(self.discord_enabled)
# # #
# # #         # Discord settings container
# # #         self.discord_settings_widget = QWidget()
# # #         discord_settings_layout = QVBoxLayout(self.discord_settings_widget)
# # #         discord_settings_layout.setSpacing(15)
# # #
# # #         # Webhook configuration
# # #         webhook_group = QFrame()
# # #         webhook_group.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 15px;
# # #             }
# # #         """)
# # #         webhook_layout = QVBoxLayout(webhook_group)
# # #
# # #         webhook_title = QLabel("🔗 Discord Webhook Configuration")
# # #         webhook_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         webhook_title.setStyleSheet("color: #2c3e50;")
# # #         webhook_layout.addWidget(webhook_title)
# # #
# # #         # Webhook URL
# # #         url_label = QLabel("Webhook URL:")
# # #         url_label.setFont(QFont("Arial", 11))
# # #         webhook_layout.addWidget(url_label)
# # #
# # #         self.discord_webhook = QLineEdit()
# # #         self.discord_webhook.setPlaceholderText("https://discord.com/api/webhooks/...")
# # #         self.discord_webhook.setStyleSheet(self.get_input_style())
# # #         webhook_layout.addWidget(self.discord_webhook)
# # #
# # #         # Bot name
# # #         name_layout = QHBoxLayout()
# # #         name_label = QLabel("Bot Name:")
# # #         name_label.setFont(QFont("Arial", 11))
# # #         name_label.setFixedWidth(100)
# # #         self.discord_name = QLineEdit()
# # #         self.discord_name.setPlaceholderText("QuDAP Bot")
# # #         self.discord_name.setStyleSheet(self.get_input_style())
# # #         name_layout.addWidget(name_label)
# # #         name_layout.addWidget(self.discord_name)
# # #         webhook_layout.addLayout(name_layout)
# # #
# # #         # Setup instructions
# # #         instructions = QLabel(
# # #             "📖 How to create a Discord webhook:\n"
# # #             "1. Open your Discord server\n"
# # #             "2. Go to Server Settings → Integrations → Webhooks\n"
# # #             "3. Click 'New Webhook' and configure it\n"
# # #             "4. Copy the webhook URL and paste it above"
# # #         )
# # #         instructions.setWordWrap(True)
# # #         instructions.setFont(QFont("Arial", 10))
# # #         instructions.setStyleSheet("color: #7f8c8d; background-color: #e3d5ff; padding: 10px; border-radius: 5px;")
# # #         webhook_layout.addWidget(instructions)
# # #
# # #         discord_settings_layout.addWidget(webhook_group)
# # #
# # #         discord_layout.addWidget(self.discord_settings_widget)
# # #         discord_layout.addStretch()
# # #
# # #         # Initially disable if not checked
# # #         self.discord_settings_widget.setEnabled(False)
# # #
# # #         return discord_widget
# # #
# # #     def create_slack_tab(self):
# # #         """Create Slack configuration tab"""
# # #         slack_widget = QWidget()
# # #         slack_layout = QVBoxLayout(slack_widget)
# # #         slack_layout.setContentsMargins(20, 20, 20, 20)
# # #         slack_layout.setSpacing(15)
# # #
# # #         # Enable Slack notifications
# # #         self.slack_enabled = QCheckBox("Enable Slack Notifications")
# # #         self.slack_enabled.setFont(QFont("Arial", 12, QFont.Weight.Bold))
# # #         self.slack_enabled.setStyleSheet("color: #2c3e50;")
# # #         self.slack_enabled.stateChanged.connect(self.toggle_slack_settings)
# # #         slack_layout.addWidget(self.slack_enabled)
# # #
# # #         # Slack settings container
# # #         self.slack_settings_widget = QWidget()
# # #         slack_settings_layout = QVBoxLayout(self.slack_settings_widget)
# # #         slack_settings_layout.setSpacing(15)
# # #
# # #         # Webhook configuration
# # #         webhook_group = QFrame()
# # #         webhook_group.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 15px;
# # #             }
# # #         """)
# # #         webhook_layout = QVBoxLayout(webhook_group)
# # #
# # #         webhook_title = QLabel("💼 Slack Webhook Configuration")
# # #         webhook_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         webhook_title.setStyleSheet("color: #2c3e50;")
# # #         webhook_layout.addWidget(webhook_title)
# # #
# # #         # Webhook URL
# # #         url_label = QLabel("Incoming Webhook URL:")
# # #         url_label.setFont(QFont("Arial", 11))
# # #         webhook_layout.addWidget(url_label)
# # #
# # #         self.slack_webhook = QLineEdit()
# # #         self.slack_webhook.setPlaceholderText("https://hooks.slack.com/services/...")
# # #         self.slack_webhook.setStyleSheet(self.get_input_style())
# # #         webhook_layout.addWidget(self.slack_webhook)
# # #
# # #         # Channel
# # #         channel_layout = QHBoxLayout()
# # #         channel_label = QLabel("Channel:")
# # #         channel_label.setFont(QFont("Arial", 11))
# # #         channel_label.setFixedWidth(100)
# # #         self.slack_channel = QLineEdit()
# # #         self.slack_channel.setPlaceholderText("#general or @username")
# # #         self.slack_channel.setStyleSheet(self.get_input_style())
# # #         channel_layout.addWidget(channel_label)
# # #         channel_layout.addWidget(self.slack_channel)
# # #         webhook_layout.addLayout(channel_layout)
# # #
# # #         # Username
# # #         username_layout = QHBoxLayout()
# # #         username_label = QLabel("Bot Username:")
# # #         username_label.setFont(QFont("Arial", 11))
# # #         username_label.setFixedWidth(100)
# # #         self.slack_username = QLineEdit()
# # #         self.slack_username.setPlaceholderText("QuDAP Bot")
# # #         self.slack_username.setStyleSheet(self.get_input_style())
# # #         username_layout.addWidget(username_label)
# # #         username_layout.addWidget(self.slack_username)
# # #         webhook_layout.addLayout(username_layout)
# # #
# # #         # Setup instructions
# # #         instructions = QLabel(
# # #             "📖 How to create a Slack webhook:\n"
# # #             "1. Go to your Slack workspace\n"
# # #             "2. Visit api.slack.com/apps and create a new app\n"
# # #             "3. Add 'Incoming Webhooks' feature\n"
# # #             "4. Create a new webhook and copy the URL"
# # #         )
# # #         instructions.setWordWrap(True)
# # #         instructions.setFont(QFont("Arial", 10))
# # #         instructions.setStyleSheet("color: #7f8c8d; background-color: #ffe4e1; padding: 10px; border-radius: 5px;")
# # #         webhook_layout.addWidget(instructions)
# # #
# # #         slack_settings_layout.addWidget(webhook_group)
# # #
# # #         slack_layout.addWidget(self.slack_settings_widget)
# # #         slack_layout.addStretch()
# # #
# # #         # Initially disable if not checked
# # #         self.slack_settings_widget.setEnabled(False)
# # #
# # #         return slack_widget
# # #
# # #     def create_webhook_tab(self):
# # #         """Create custom webhook configuration tab"""
# # #         webhook_widget = QWidget()
# # #         webhook_layout = QVBoxLayout(webhook_widget)
# # #         webhook_layout.setContentsMargins(20, 20, 20, 20)
# # #         webhook_layout.setSpacing(15)
# # #
# # #         # Enable webhook notifications
# # #         self.webhook_enabled = QCheckBox("Enable Custom Webhook")
# # #         self.webhook_enabled.setFont(QFont("Arial", 12, QFont.Weight.Bold))
# # #         self.webhook_enabled.setStyleSheet("color: #2c3e50;")
# # #         self.webhook_enabled.stateChanged.connect(self.toggle_webhook_settings)
# # #         webhook_layout.addWidget(self.webhook_enabled)
# # #
# # #         # Webhook settings container
# # #         self.webhook_settings_widget = QWidget()
# # #         webhook_settings_layout = QVBoxLayout(self.webhook_settings_widget)
# # #         webhook_settings_layout.setSpacing(15)
# # #
# # #         # Webhook configuration
# # #         config_group = QFrame()
# # #         config_group.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 15px;
# # #             }
# # #         """)
# # #         config_layout = QVBoxLayout(config_group)
# # #
# # #         config_title = QLabel("🔗 Custom Webhook Configuration")
# # #         config_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         config_title.setStyleSheet("color: #2c3e50;")
# # #         config_layout.addWidget(config_title)
# # #
# # #         # Webhook URL
# # #         url_label = QLabel("Webhook URL:")
# # #         url_label.setFont(QFont("Arial", 11))
# # #         config_layout.addWidget(url_label)
# # #
# # #         self.custom_webhook_url = QLineEdit()
# # #         self.custom_webhook_url.setPlaceholderText("https://your-service.com/webhook")
# # #         self.custom_webhook_url.setStyleSheet(self.get_input_style())
# # #         config_layout.addWidget(self.custom_webhook_url)
# # #
# # #         # Method
# # #         method_layout = QHBoxLayout()
# # #         method_label = QLabel("HTTP Method:")
# # #         method_label.setFont(QFont("Arial", 11))
# # #         method_label.setFixedWidth(100)
# # #         self.webhook_method = QComboBox()
# # #         self.webhook_method.addItems(["POST", "GET", "PUT"])
# # #         self.webhook_method.setStyleSheet(self.get_combo_style())
# # #         method_layout.addWidget(method_label)
# # #         method_layout.addWidget(self.webhook_method)
# # #         method_layout.addStretch()
# # #         config_layout.addLayout(method_layout)
# # #
# # #         # Headers
# # #         headers_label = QLabel("Headers (JSON format):")
# # #         headers_label.setFont(QFont("Arial", 11))
# # #         config_layout.addWidget(headers_label)
# # #
# # #         self.webhook_headers = QTextEdit()
# # #         self.webhook_headers.setMaximumHeight(80)
# # #         self.webhook_headers.setPlaceholderText('{"Content-Type": "application/json", "Authorization": "Bearer YOUR_TOKEN"}')
# # #         self.webhook_headers.setStyleSheet(self.get_input_style())
# # #         config_layout.addWidget(self.webhook_headers)
# # #
# # #         webhook_settings_layout.addWidget(config_group)
# # #
# # #         webhook_layout.addWidget(self.webhook_settings_widget)
# # #         webhook_layout.addStretch()
# # #
# # #         # Initially disable if not checked
# # #         self.webhook_settings_widget.setEnabled(False)
# # #
# # #         return webhook_widget
# # #
# # #     def create_notification_events_section(self):
# # #         """Create notification events configuration section"""
# # #         events_card = AnimatedCard()
# # #         events_layout = QVBoxLayout(events_card)
# # #         events_layout.setContentsMargins(30, 30, 30, 30)
# # #         events_layout.setSpacing(20)
# # #
# # #         # Section title
# # #         section_title = QLabel("🔔 Notification Events")
# # #         section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
# # #         section_title.setStyleSheet("color: #2c3e50;")
# # #         events_layout.addWidget(section_title)
# # #
# # #         # Description
# # #         description = QLabel("Choose which events trigger notifications:")
# # #         description.setFont(QFont("Arial", 12))
# # #         description.setStyleSheet("color: #7f8c8d;")
# # #         events_layout.addWidget(description)
# # #
# # #         # Events grid
# # #         events_grid = QGridLayout()
# # #         events_grid.setSpacing(15)
# # #
# # #         self.event_checkboxes = {}
# # #         events = [
# # #             ("experiment_start", "🚀 Experiment Started", "When a new experiment begins"),
# # #             ("experiment_complete", "✅ Experiment Completed", "When an experiment finishes successfully"),
# # #             ("experiment_error", "❌ Experiment Error", "When an error occurs during experiment"),
# # #             ("temperature_reached", "🌡️ Temperature Reached", "When target temperature is reached"),
# # #             ("field_reached", "🧲 Field Reached", "When target field is reached"),
# # #             ("data_saved", "💾 Data Saved", "When measurement data is saved"),
# # #             ("connection_lost", "🔌 Connection Lost", "When instrument connection is lost"),
# # #             ("connection_restored", "🔗 Connection Restored", "When instrument connection is restored"),
# # #             ("low_helium", "⚠️ Low Helium", "When helium level is low"),
# # #             ("system_warning", "⚠️ System Warning", "General system warnings"),
# # #             ("daily_summary", "📊 Daily Summary", "Daily summary of experiments"),
# # #             ("weekly_report", "📈 Weekly Report", "Weekly activity report")
# # #         ]
# # #
# # #         for i, (key, title, description) in enumerate(events):
# # #             event_widget = self.create_event_item(key, title, description)
# # #             row = i // 2
# # #             col = i % 2
# # #             events_grid.addWidget(event_widget, row, col)
# # #
# # #         events_layout.addLayout(events_grid)
# # #
# # #         # Notification priority
# # #         priority_layout = QHBoxLayout()
# # #         priority_label = QLabel("Default Priority Level:")
# # #         priority_label.setFont(QFont("Arial", 12))
# # #         self.priority_combo = QComboBox()
# # #         self.priority_combo.addItems(["🔵 Low", "🟡 Normal", "🟠 High", "🔴 Critical"])
# # #         self.priority_combo.setCurrentIndex(1)
# # #         self.priority_combo.setStyleSheet(self.get_combo_style())
# # #         priority_layout.addWidget(priority_label)
# # #         priority_layout.addWidget(self.priority_combo)
# # #         priority_layout.addStretch()
# # #         events_layout.addLayout(priority_layout)
# # #
# # #         # Quiet hours
# # #         quiet_group = QFrame()
# # #         quiet_group.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 15px;
# # #             }
# # #         """)
# # #         quiet_layout = QVBoxLayout(quiet_group)
# # #
# # #         quiet_title = QLabel("🌙 Quiet Hours")
# # #         quiet_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
# # #         quiet_title.setStyleSheet("color: #2c3e50;")
# # #         quiet_layout.addWidget(quiet_title)
# # #
# # #         self.quiet_hours_enabled = QCheckBox("Enable quiet hours (no notifications during specified time)")
# # #         self.quiet_hours_enabled.stateChanged.connect(self.toggle_quiet_hours)
# # #         quiet_layout.addWidget(self.quiet_hours_enabled)
# # #
# # #         quiet_time_layout = QHBoxLayout()
# # #         quiet_time_layout.addWidget(QLabel("From:"))
# # #         self.quiet_start = QTimeEdit()
# # #         self.quiet_start.setTime(QTime(22, 0))
# # #         self.quiet_start.setDisplayFormat("hh:mm AP")
# # #         self.quiet_start.setEnabled(False)
# # #         quiet_time_layout.addWidget(self.quiet_start)
# # #
# # #         quiet_time_layout.addWidget(QLabel("To:"))
# # #         self.quiet_end = QTimeEdit()
# # #         self.quiet_end.setTime(QTime(7, 0))
# # #         self.quiet_end.setDisplayFormat("hh:mm AP")
# # #         self.quiet_end.setEnabled(False)
# # #         quiet_time_layout.addWidget(self.quiet_end)
# # #         quiet_time_layout.addStretch()
# # #         quiet_layout.addLayout(quiet_time_layout)
# # #
# # #         events_layout.addWidget(quiet_group)
# # #
# # #         return events_card
# # #
# # #     def create_event_item(self, key, title, description):
# # #         """Create individual event checkbox item"""
# # #         event_frame = QFrame()
# # #         event_frame.setStyleSheet("""
# # #             QFrame {
# # #                 background-color: #f8f9fa;
# # #                 border-radius: 5px;
# # #                 padding: 10px;
# # #             }
# # #             QFrame:hover {
# # #                 background-color: #e8ecef;
# # #             }
# # #         """)
# # #
# # #         layout = QVBoxLayout(event_frame)
# # #
# # #         checkbox = QCheckBox(title)
# # #         checkbox.setFont(QFont("Arial", 11, QFont.Weight.Bold))
# # #         checkbox.setStyleSheet("color: #2c3e50;")
# # #
# # #         desc_label = QLabel(description)
# # #         desc_label.setFont(QFont("Arial", 9))
# # #         desc_label.setStyleSheet("color: #7f8c8d; margin-left: 25px;")
# # #
# # #         layout.addWidget(checkbox)
# # #         layout.addWidget(desc_label)
# # #
# # #         self.event_checkboxes[key] = checkbox
# # #
# # #         return event_frame
# # #
# # #     def create_test_section(self):
# # #         """Create test notification section"""
# # #         test_card = AnimatedCard()
# # #         test_layout = QVBoxLayout(test_card)
# # #         test_layout.setContentsMargins(30, 30, 30, 30)
# # #         test_layout.setSpacing(15)
# # #
# # #         # Section title
# # #         section_title = QLabel("🧪 Test Notifications")
# # #         section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
# # #         section_title.setStyleSheet("color: #2c3e50;")
# # #         test_layout.addWidget(section_title)
# # #
# # #         # Description
# # #         description = QLabel("Send a test notification to verify your configuration:")
# # #         description.setFont(QFont("Arial", 12))
# # #         description.setStyleSheet("color: #7f8c8d;")
# # #         test_layout.addWidget(description)
# # #
# # #         # Test buttons layout
# # #         buttons_layout = QHBoxLayout()
# # #
# # #         # Test email button
# # #         test_email_btn = QPushButton("✉️ Test Email")
# # #         test_email_btn.setFont(QFont("Arial", 11))
# # #         test_email_btn.setCursor(Qt.CursorShape.PointingHandCursor)
# # #         test_email_btn.setStyleSheet("""
# # #             QPushButton {
# # #                 background-color: #28a745;
# # #                 color: white;
# # #                 padding: 10px 20px;
# # #                 border-radius: 5px;
# # #                 font-weight: bold;
# # #             }
# # #             QPushButton:hover {
# # #                 background-color: #218838;
# # #             }
# # #             QPushButton:disabled {
# # #                 background-color: #6c757d;
# # #             }
# # #         """)
# # #         test_email_btn.clicked.connect(lambda: self.send_test_notification("email"))
# # #         buttons_layout.addWidget(test_email_btn)
# # #
# # #         # Test Telegram button
# # #         test_telegram_btn = QPushButton("💬 Test Telegram")
# # #         test_telegram_btn.setFont(QFont("Arial", 11))
# # #         test_telegram_btn.setCursor(Qt.CursorShape.PointingHandCursor)
# # #         test_telegram_btn.setStyleSheet("""
# # #             QPushButton {
# # #                 background-color: #0088cc;
# # #                 color: white;
# # #                 padding: 10px 20px;
# # #                 border-radius: 5px;
# # #                 font-weight: bold;
# # #             }
# # #             QPushButton:hover {
# # #                 background-color: #0077b5;
# # #             }
# # #             QPushButton:disabled {
# # #                 background-color: #6c757d;
# # #             }
# # #         """)
# # #         test_telegram_btn.clicked.connect(lambda: self.send_test_notification("telegram"))
# # #         buttons_layout.addWidget(test_telegram_btn)
# # #
# # #         # Test all button
# # #         test_all_btn = QPushButton("📡 Test All Enabled")
# # #         test_all_btn.setFont(QFont("Arial", 11))
# # #         test_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
# # #         test_all_btn.setStyleSheet("""
# # #             QPushButton {
# # #                 background-color: #ffc107;
# # #                 color: #212529;
# # #                 padding: 10px 20px;
# # #                 border-radius: 5px;
# # #                 font-weight: bold;
# # #             }
# # #             QPushButton:hover {
# # #                 background-color: #e0a800;
# # #             }
# # #         """)
# # #         test_all_btn.clicked.connect(lambda: self.send_test_notification("all"))
# # #         buttons_layout.addWidget(test_all_btn)
# # #
# # #         buttons_layout.addStretch()
# # #         test_layout.addLayout(buttons_layout)
# # #
# # #         # Test result display
# # #         self.test_result = QLabel("")
# # #         self.test_result.setWordWrap(True)
# # #         self.test_result.setFont(QFont("Arial", 11))
# # #         test_layout.addWidget(self.test_result)
# # #
# # #         return test_card
# # #
# # #     def create_action_buttons(self):
# # #         """Create save and cancel buttons"""
# # #         buttons_card = AnimatedCard()
# # #         buttons_layout = QHBoxLayout(buttons_card)
# # #         buttons_layout.setContentsMargins(30, 20, 30, 20)
# # #
# # #         # Save button
# # #         save_btn = QPushButton("💾 Save Settings")
# # #         save_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
# # #         save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
# # #         save_btn.setStyleSheet("""
# # #             QPushButton {
# # #                 background-color: #1e88e5;
# # #                 color: white;
# # #                 padding: 12px 30px;
# # #                 border-radius: 5px;
# # #             }
# # #             QPushButton:hover {
# # #                 background-color: #1976d2;
# # #             }
# # #         """)
# # #         save_btn.clicked.connect(self.save_settings)
# # #
# # #         # Cancel button
# # #         cancel_btn = QPushButton("❌ Cancel")
# # #         cancel_btn.setFont(QFont("Arial", 12))
# # #         cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
# # #         cancel_btn.setStyleSheet("""
# # #             QPushButton {
# # #                 background-color: white;
# # #                 color: #dc3545;
# # #                 padding: 12px 30px;
# # #                 border: 2px solid #dc3545;
# # #                 border-radius: 5px;
# # #             }
# # #             QPushButton:hover {
# # #                 background-color: #dc3545;
# # #                 color: white;
# # #             }
# # #         """)
# # #         cancel_btn.clicked.connect(self.close)
# # #
# # #         # Reset button
# # #         resetl_btn = QPushButton("🔄 Reset Settings")
# # #         resetl_btn.setFont(QFont("Arial", 12))
# # #         resetl_btn.setCursor(Qt.CursorShape.PointingHandCursor)
# # #         resetl_btn.setStyleSheet("""
# # #                     QPushButton {
# # #                         background-color: #1e88e5;
# # #                         color: white;
# # #                         padding: 12px 30px;
# # #                         border-radius: 5px;
# # #                     }
# # #                     QPushButton:hover {
# # #                         background-color: #1976d2;
# # #                     }
# # #                 """)
# # #         resetl_btn.clicked.connect(self.close)
# # #
# # #         buttons_layout.addStretch()
# # #         buttons_layout.addWidget(save_btn)
# # #         buttons_layout.addWidget(resetl_btn)
# # #         buttons_layout.addWidget(cancel_btn)
# # #
# # #         return buttons_card
# # #
# # #     def get_input_style(self):
# # #         """Get consistent input field style"""
# # #         return """
# # #             QLineEdit, QTextEdit, QSpinBox {
# # #                 padding: 8px;
# # #                 border: 1px solid #ddd;
# # #                 border-radius: 5px;
# # #                 font-size: 11px;
# # #                 background-color: white;
# # #             }
# # #             QLineEdit:focus, QTextEdit:focus, QSpinBox:focus {
# # #                 border-color: #1e88e5;
# # #                 outline: none;
# # #             }
# # #         """
# # #
# # #     def get_combo_style(self):
# # #         """Get consistent combo box style"""
# # #         return """
# # #             QComboBox {
# # #                 padding: 8px;
# # #                 border: 1px solid #ddd;
# # #                 border-radius: 5px;
# # #                 font-size: 11px;
# # #                 background-color: white;
# # #             }
# # #             QComboBox:focus {
# # #                 border-color: #1e88e5;
# # #             }
# # #             QComboBox::drop-down {
# # #                 border: none;
# # #             }
# # #             QComboBox::down-arrow {
# # #                 image: none;
# # #                 border-left: 5px solid transparent;
# # #                 border-right: 5px solid transparent;
# # #                 border-top: 5px solid #5d6d7e;
# # #                 margin-right: 5px;
# # #             }
# # #         """
# # #
# # #     def toggle_email_settings(self, state):
# # #         """Toggle email settings availability"""
# # #         self.email_settings_widget.setEnabled(state == 2)
# # #         self.update_status_indicator()
# # #
# # #     def toggle_telegram_settings(self, state):
# # #         """Toggle Telegram settings availability"""
# # #         self.telegram_settings_widget.setEnabled(state == 2)
# # #         self.update_status_indicator()
# # #
# # #     def toggle_discord_settings(self, state):
# # #         """Toggle Discord settings availability"""
# # #         self.discord_settings_widget.setEnabled(state == 2)
# # #         self.update_status_indicator()
# # #
# # #     def toggle_slack_settings(self, state):
# # #         """Toggle Slack settings availability"""
# # #         self.slack_settings_widget.setEnabled(state == 2)
# # #         self.update_status_indicator()
# # #
# # #     def toggle_webhook_settings(self, state):
# # #         """Toggle webhook settings availability"""
# # #         self.webhook_settings_widget.setEnabled(state == 2)
# # #         self.update_status_indicator()
# # #
# # #     def toggle_quiet_hours(self, state):
# # #         """Toggle quiet hours settings"""
# # #         self.quiet_start.setEnabled(state == 2)
# # #         self.quiet_end.setEnabled(state == 2)
# # #
# # #     def apply_smtp_preset(self, preset):
# # #         """Apply SMTP server preset"""
# # #         presets = {
# # #             "Gmail (smtp.gmail.com)": ("smtp.gmail.com", 587, True),
# # #             "Outlook (smtp-mail.outlook.com)": ("smtp-mail.outlook.com", 587, True),
# # #             "Yahoo (smtp.mail.yahoo.com)": ("smtp.mail.yahoo.com", 587, True),
# # #             "Office 365 (smtp.office365.com)": ("smtp.office365.com", 587, True)
# # #         }
# # #
# # #         if preset in presets:
# # #             server, port, ssl = presets[preset]
# # #             self.smtp_server.setText(server)
# # #             self.smtp_port.setValue(port)
# # #             self.smtp_ssl.setChecked(ssl)
# # #
# # #     def update_status_indicator(self):
# # #         """Update the status indicator based on enabled channels"""
# # #         # Check if UI elements exist before accessing them
# # #         if not all([
# # #             hasattr(self, 'email_enabled') and self.email_enabled,
# # #             hasattr(self, 'telegram_enabled') and self.telegram_enabled,
# # #             hasattr(self, 'discord_enabled') and self.discord_enabled,
# # #             hasattr(self, 'slack_enabled') and self.slack_enabled,
# # #             hasattr(self, 'webhook_enabled') and self.webhook_enabled
# # #         ]):
# # #             return
# # #
# # #         enabled_count = sum([
# # #             self.email_enabled.isChecked(),
# # #             self.telegram_enabled.isChecked(),
# # #             self.discord_enabled.isChecked(),
# # #             self.slack_enabled.isChecked(),
# # #             self.webhook_enabled.isChecked()
# # #         ])
# # #
# # #         if enabled_count == 0:
# # #             self.status_indicator.setText("●")
# # #             self.status_indicator.setStyleSheet("color: #dc3545;")
# # #             self.status_label.setText("No channels configured")
# # #         elif enabled_count == 1:
# # #             self.status_indicator.setText("●")
# # #             self.status_indicator.setStyleSheet("color: #ffc107;")
# # #             self.status_label.setText(f"{enabled_count} channel configured")
# # #         else:
# # #             self.status_indicator.setText("●")
# # #             self.status_indicator.setStyleSheet("color: #28a745;")
# # #             self.status_label.setText(f"{enabled_count} channels configured")
# # #
# # #     def delete_settings(self):
# # #         """Delete all saved notification settings"""
# # #         # Show confirmation dialog
# # #         reply = QMessageBox.question(
# # #             self,
# # #             "Delete All Settings",
# # #             "Are you sure you want to delete all notification settings?\n\n"
# # #             "This will remove:\n"
# # #             "• All email configurations\n"
# # #             "• All notification channel settings\n"
# # #             "• All event preferences\n"
# # #             "• All saved credentials\n\n"
# # #             "This action cannot be undone.",
# # #             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
# # #             QMessageBox.StandardButton.No
# # #         )
# # #
# # #         if reply == QMessageBox.StandardButton.Yes:
# # #             # Clear all settings
# # #             self.settings.clear()
# # #
# # #             # Reset UI to defaults
# # #             self.reset_ui_to_defaults()
# # #
# # #             # Show success message
# # #             QMessageBox.information(
# # #                 self,
# # #                 "Settings Deleted",
# # #                 "All notification settings have been deleted successfully.\n"
# # #                 "The form has been reset to defaults."
# # #             )
# # #
# # #             # Update status indicator
# # #             self.update_status_indicator()
# # #
# # #     def reset_ui_to_defaults(self):
# # #         """Reset all UI elements to default values"""
# # #         # Reset email settings
# # #         self.email_enabled.setChecked(False)
# # #         self.smtp_server.clear()
# # #         self.smtp_port.setValue(587)
# # #         self.smtp_ssl.setChecked(True)
# # #         self.smtp_username.clear()
# # #         self.smtp_password.clear()
# # #         self.from_email.clear()
# # #         self.to_emails.clear()
# # #         self.smtp_preset.setCurrentIndex(0)
# # #
# # #         # Reset Telegram settings
# # #         self.telegram_enabled.setChecked(False)
# # #         self.telegram_token.clear()
# # #         self.telegram_chat_id.clear()
# # #         self.telegram_format.setCurrentIndex(0)
# # #
# # #         # Reset Discord settings
# # #         self.discord_enabled.setChecked(False)
# # #         self.discord_webhook.clear()
# # #         self.discord_name.clear()
# # #
# # #         # Reset Slack settings
# # #         self.slack_enabled.setChecked(False)
# # #         self.slack_webhook.clear()
# # #         self.slack_channel.clear()
# # #         self.slack_username.clear()
# # #
# # #         # Reset webhook settings
# # #         self.webhook_enabled.setChecked(False)
# # #         self.custom_webhook_url.clear()
# # #         self.webhook_method.setCurrentIndex(0)
# # #         self.webhook_headers.clear()
# # #
# # #         # Reset all event checkboxes to checked (default)
# # #         for checkbox in self.event_checkboxes.values():
# # #             checkbox.setChecked(True)
# # #
# # #         # Reset priority and quiet hours
# # #         self.priority_combo.setCurrentIndex(1)  # Normal priority
# # #         self.quiet_hours_enabled.setChecked(False)
# # #         self.quiet_start.setTime(QTime(22, 0))
# # #         self.quiet_end.setTime(QTime(7, 0))
# # #
# # #         # Clear test result
# # #         self.test_result.clear()
# # #
# # #         # Disable all settings widgets
# # #         self.email_settings_widget.setEnabled(False)
# # #         self.telegram_settings_widget.setEnabled(False)
# # #         self.discord_settings_widget.setEnabled(False)
# # #         self.slack_settings_widget.setEnabled(False)
# # #         self.webhook_settings_widget.setEnabled(False)
# # #         self.quiet_start.setEnabled(False)
# # #         self.quiet_end.setEnabled(False)
# # #         """Send test notification to specified channel"""
# # #         if channel == "email" and self.email_enabled.isChecked():
# # #             self.test_result.setText("📧 Sending test email...")
# # #             self.test_result.setStyleSheet("color: #17a2b8;")
# # #             # Implement actual email sending here
# # #             QTimer.singleShot(2000, lambda: self.show_test_result("Email sent successfully!", True))
# # #         elif channel == "telegram" and self.telegram_enabled.isChecked():
# # #             self.test_result.setText("💬 Sending test Telegram message...")
# # #             self.test_result.setStyleSheet("color: #17a2b8;")
# # #             # Implement actual Telegram sending here
# # #             QTimer.singleShot(2000, lambda: self.show_test_result("Telegram message sent!", True))
# # #         elif channel == "all":
# # #             self.test_result.setText("📡 Sending test to all enabled channels...")
# # #             self.test_result.setStyleSheet("color: #17a2b8;")
# # #             QTimer.singleShot(2000, lambda: self.show_test_result("Test notifications sent to all channels!", True))
# # #         else:
# # #             self.test_result.setText("⚠️ Please enable and configure the channel first")
# # #             self.test_result.setStyleSheet("color: #dc3545;")
# # #
# # #     def show_test_result(self, message, success):
# # #         """Show test result message"""
# # #         if success:
# # #             self.test_result.setText(f"✅ {message}")
# # #             self.test_result.setStyleSheet("color: #28a745;")
# # #         else:
# # #             self.test_result.setText(f"❌ {message}")
# # #             self.test_result.setStyleSheet("color: #dc3545;")
# # #
# # #     def save_settings(self):
# # #         """Save all notification settings"""
# # #         # Save email settings
# # #         self.settings.setValue('email/enabled', self.email_enabled.isChecked())
# # #         self.settings.setValue('email/smtp_server', self.smtp_server.text())
# # #         self.settings.setValue('email/smtp_port', self.smtp_port.value())
# # #         self.settings.setValue('email/smtp_ssl', self.smtp_ssl.isChecked())
# # #         self.settings.setValue('email/username', self.smtp_username.text())
# # #         self.settings.setValue('email/password', self.smtp_password.text())
# # #         self.settings.setValue('email/from_email', self.from_email.text())
# # #         self.settings.setValue('email/to_emails', self.to_emails.toPlainText())
# # #
# # #         # Save Telegram settings
# # #         self.settings.setValue('telegram/enabled', self.telegram_enabled.isChecked())
# # #         self.settings.setValue('telegram/token', self.telegram_token.text())
# # #         self.settings.setValue('telegram/chat_id', self.telegram_chat_id.text())
# # #         self.settings.setValue('telegram/format', self.telegram_format.currentText())
# # #
# # #         # Save Discord settings
# # #         self.settings.setValue('discord/enabled', self.discord_enabled.isChecked())
# # #         self.settings.setValue('discord/webhook', self.discord_webhook.text())
# # #         self.settings.setValue('discord/name', self.discord_name.text())
# # #
# # #         # Save Slack settings
# # #         self.settings.setValue('slack/enabled', self.slack_enabled.isChecked())
# # #         self.settings.setValue('slack/webhook', self.slack_webhook.text())
# # #         self.settings.setValue('slack/channel', self.slack_channel.text())
# # #         self.settings.setValue('slack/username', self.slack_username.text())
# # #
# # #         # Save webhook settings
# # #         self.settings.setValue('webhook/enabled', self.webhook_enabled.isChecked())
# # #         self.settings.setValue('webhook/url', self.custom_webhook_url.text())
# # #         self.settings.setValue('webhook/method', self.webhook_method.currentText())
# # #         self.settings.setValue('webhook/headers', self.webhook_headers.toPlainText())
# # #
# # #         # Save event settings
# # #         for key, checkbox in self.event_checkboxes.items():
# # #             self.settings.setValue(f'events/{key}', checkbox.isChecked())
# # #
# # #         # Save priority and quiet hours
# # #         self.settings.setValue('priority', self.priority_combo.currentIndex())
# # #         self.settings.setValue('quiet_hours/enabled', self.quiet_hours_enabled.isChecked())
# # #         self.settings.setValue('quiet_hours/start', self.quiet_start.time().toString())
# # #         self.settings.setValue('quiet_hours/end', self.quiet_end.time().toString())
# # #
# # #         # Show success message
# # #         QMessageBox.information(self, "Success", "Notification settings saved successfully!")
# # #         self.settings_saved.emit()
# # #
# # #     def load_settings(self):
# # #         """Load saved notification settings"""
# # #         # Load email settings
# # #         self.email_enabled.setChecked(self.settings.value('email/enabled', False, bool))
# # #         self.smtp_server.setText(self.settings.value('email/smtp_server', ''))
# # #         self.smtp_port.setValue(self.settings.value('email/smtp_port', 587, int))
# # #         self.smtp_ssl.setChecked(self.settings.value('email/smtp_ssl', True, bool))
# # #         self.smtp_username.setText(self.settings.value('email/username', ''))
# # #         self.smtp_password.setText(self.settings.value('email/password', ''))
# # #         self.from_email.setText(self.settings.value('email/from_email', ''))
# # #         self.to_emails.setPlainText(self.settings.value('email/to_emails', ''))
# # #
# # #         # Load Telegram settings
# # #         self.telegram_enabled.setChecked(self.settings.value('telegram/enabled', False, bool))
# # #         self.telegram_token.setText(self.settings.value('telegram/token', ''))
# # #         self.telegram_chat_id.setText(self.settings.value('telegram/chat_id', ''))
# # #         format_text = self.settings.value('telegram/format', 'Plain Text')
# # #         index = self.telegram_format.findText(format_text)
# # #         if index >= 0:
# # #             self.telegram_format.setCurrentIndex(index)
# # #
# # #         # Load Discord settings
# # #         self.discord_enabled.setChecked(self.settings.value('discord/enabled', False, bool))
# # #         self.discord_webhook.setText(self.settings.value('discord/webhook', ''))
# # #         self.discord_name.setText(self.settings.value('discord/name', ''))
# # #
# # #         # Load Slack settings
# # #         self.slack_enabled.setChecked(self.settings.value('slack/enabled', False, bool))
# # #         self.slack_webhook.setText(self.settings.value('slack/webhook', ''))
# # #         self.slack_channel.setText(self.settings.value('slack/channel', ''))
# # #         self.slack_username.setText(self.settings.value('slack/username', ''))
# # #
# # #         # Load webhook settings
# # #         self.webhook_enabled.setChecked(self.settings.value('webhook/enabled', False, bool))
# # #         self.custom_webhook_url.setText(self.settings.value('webhook/url', ''))
# # #         method = self.settings.value('webhook/method', 'POST')
# # #         index = self.webhook_method.findText(method)
# # #         if index >= 0:
# # #             self.webhook_method.setCurrentIndex(index)
# # #         self.webhook_headers.setPlainText(self.settings.value('webhook/headers', ''))
# # #
# # #         # Load event settings
# # #         for key, checkbox in self.event_checkboxes.items():
# # #             checkbox.setChecked(self.settings.value(f'events/{key}', True, bool))
# # #
# # #         # Load priority and quiet hours
# # #         self.priority_combo.setCurrentIndex(self.settings.value('priority', 1, int))
# # #         self.quiet_hours_enabled.setChecked(self.settings.value('quiet_hours/enabled', False, bool))
# # #
# # #         start_time = self.settings.value('quiet_hours/start', '22:00')
# # #         end_time = self.settings.value('quiet_hours/end', '07:00')
# # #         self.quiet_start.setTime(QTime.fromString(start_time))
# # #         self.quiet_end.setTime(QTime.fromString(end_time))
# # #
# # #         self.update_status_indicator()
# # #
# # #
# # # def main():
# # #     """Main function to run the application"""
# # #     app = QApplication(sys.argv)
# # #     app.setStyle("Fusion")
# # #
# # #     window = NotificationSettings()
# # #     window.show()
# # #
# # #     sys.exit(app.exec())
# # #
# # #
# # # if __name__ == "__main__":
# # #     main()
# #
# #
# # # import smtplib
# # # from email.mime.text import MIMEText
# # # from email.mime.multipart import MIMEMultipart
# # #
# # # # AU email credentials
# # # sender_email = "czt0036@auburn.edu"
# # # password = "Atcll741368934"  # Consider using an app password or environment variable
# # #
# # # # Recipient
# # # receiver_email = "czt0036@auburn.edu"
# # #
# # # # Create the email
# # # message = MIMEMultipart()
# # # message["From"] = sender_email
# # # message["To"] = receiver_email
# # # message["Subject"] = "Test Email from Python"
# # #
# # # body = "This is a test email sent from Python using Auburn University email."
# # # message.attach(MIMEText(body, "plain"))
# # #
# # # # Send the email using AU's SMTP server
# # # try:
# # #     with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
# # #         server.starttls()
# # #         server.login(sender_email, password)
# # #         server.sendmail(sender_email, receiver_email, message.as_string())
# # #     print("Email sent successfully!")
# # # except Exception as e:
# # #     print("Error sending email:", e)
# #
# #
# # """
# # Improved Measurement Module for QuDAP
# # Enhanced with better OOP design and notification system integration
# # """
# #
# # import time
# # import traceback
# # from datetime import datetime
# # from pathlib import Path
# # from typing import Optional, Dict, Any, List, Tuple
# # from dataclasses import dataclass
# # from enum import Enum, auto
# # from abc import ABC, abstractmethod
# #
# # from PyQt6.QtWidgets import (
# #     QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
# #     QComboBox, QLineEdit, QCheckBox, QGroupBox, QMessageBox,
# #     QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar,
# #     QTextEdit, QSplitter, QFrame, QGridLayout
# # )
# # from PyQt6.QtCore import (
# #     QThread, pyqtSignal, QTimer, Qt, QSettings, QObject
# # )
# # from PyQt6.QtGui import QFont, QColor
# #
# # import numpy as np
# # import pandas as pd
# # import matplotlib.pyplot as plt
# # from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# # from matplotlib.figure import Figure
# #
# # # Import notification manager
# # # from QuDAP.utils.notification_manager import NotificationManager
# #
# #
# # # # ============================================================================
# # # # Data Classes and Enums
# # # # ============================================================================
# # #
# # # class MeasurementState(Enum):
# # #     """Enumeration for measurement states"""
# # #     IDLE = auto()
# # #     INITIALIZING = auto()
# # #     RUNNING = auto()
# # #     PAUSED = auto()
# # #     COMPLETED = auto()
# # #     ERROR = auto()
# # #     ABORTED = auto()
# # #
# # #
# # # class MeasurementType(Enum):
# # #     """Enumeration for measurement types"""
# # #     VSM = "VSM"
# # #     RESISTANCE = "Resistance"
# # #     HEAT_CAPACITY = "Heat Capacity"
# # #     AC_SUSCEPTIBILITY = "AC Susceptibility"
# # #     TORQUE = "Torque"
# # #     CUSTOM = "Custom"
# # #
# # #
# # # @dataclass
# # # class MeasurementConfig:
# # #     """Configuration data class for measurements"""
# # #     measurement_type: MeasurementType
# # #     sample_name: str
# # #
# # #     # Temperature settings
# # #     temp_start: float
# # #     temp_end: float
# # #     temp_rate: float
# # #     temp_settle_time: float = 60.0
# # #
# # #     # Field settings
# # #     field_start: float
# # #     field_end: float
# # #     field_rate: float
# # #     field_settle_time: float = 30.0
# # #
# # #     # Measurement settings
# # #     num_points: int = 100
# # #     averaging_time: float = 1.0
# # #     num_averages: int = 1
# # #
# # #     # Data saving
# # #     save_path: Path = Path("./data")
# # #     auto_save: bool = True
# # #     file_format: str = "csv"
# # #
# # #     # Notification settings
# # #     notify_on_complete: bool = True
# # #     notify_on_error: bool = True
# # #     notify_on_milestone: bool = False
# # #
# # #     def validate(self) -> Tuple[bool, str]:
# # #         """Validate configuration parameters"""
# # #         errors = []
# # #
# # #         # Temperature validation
# # #         if not (1.8 <= self.temp_start <= 400):
# # #             errors.append(f"Start temperature {self.temp_start}K out of range (1.8-400K)")
# # #         if not (1.8 <= self.temp_end <= 400):
# # #             errors.append(f"End temperature {self.temp_end}K out of range (1.8-400K)")
# # #         if not (0 < self.temp_rate <= 50):
# # #             errors.append(f"Temperature rate {self.temp_rate}K/min out of range (0-50K/min)")
# # #
# # #         # Field validation
# # #         if not (-90000 <= self.field_start <= 90000):
# # #             errors.append(f"Start field {self.field_start}Oe out of range (-90kOe to 90kOe)")
# # #         if not (-90000 <= self.field_end <= 90000):
# # #             errors.append(f"End field {self.field_end}Oe out of range (-90kOe to 90kOe)")
# # #         if not (0 < self.field_rate <= 1000):
# # #             errors.append(f"Field rate {self.field_rate}Oe/s out of range (0-1000Oe/s)")
# # #
# # #         # General validation
# # #         if self.num_points < 1:
# # #             errors.append("Number of points must be at least 1")
# # #         if self.averaging_time <= 0:
# # #             errors.append("Averaging time must be positive")
# # #
# # #         if errors:
# # #             return False, "\n".join(errors)
# # #         return True, "Configuration valid"
# #
# # #
# # # @dataclass
# # # class MeasurementData:
# # #     """Data class for storing measurement results"""
# # #     timestamp: datetime
# # #     # config: MeasurementConfig
# # #
# # #     # Data arrays
# # #     temperature: np.ndarray = None
# # #     field: np.ndarray = None
# # #     moment: np.ndarray = None
# # #     resistance: np.ndarray = None
# # #
# # #     # Metadata
# # #     metadata: Dict[str, Any] = None
# # #     errors: List[str] = None
# # #
# # #     def __post_init__(self):
# # #         if self.metadata is None:
# # #             self.metadata = {}
# # #         if self.errors is None:
# # #             self.errors = []
# # #
# # #     def to_dataframe(self) -> pd.DataFrame:
# # #         """Convert to pandas DataFrame"""
# # #         data = {}
# # #         if self.temperature is not None:
# # #             data['Temperature (K)'] = self.temperature
# # #         if self.field is not None:
# # #             data['Field (Oe)'] = self.field
# # #         if self.moment is not None:
# # #             data['Moment (emu)'] = self.moment
# # #         if self.resistance is not None:
# # #             data['Resistance (Ohm)'] = self.resistance
# # #
# # #         return pd.DataFrame(data)
# # #
# # #     def save(self, filepath: Path = None):
# # #         """Save measurement data"""
# # #         if filepath is None:
# # #             timestamp_str = self.timestamp.strftime("%Y%m%d_%H%M%S")
# # #             filename = f"{self.config.sample_name}_{timestamp_str}.{self.config.file_format}"
# # #             filepath = self.config.save_path / filename
# # #
# # #         filepath.parent.mkdir(parents=True, exist_ok=True)
# # #
# # #         if self.config.file_format == 'csv':
# # #             df = self.to_dataframe()
# # #             df.to_csv(filepath, index=False)
# # #         elif self.config.file_format == 'hdf5':
# # #             import h5py
# # #             with h5py.File(filepath, 'w') as f:
# # #                 # Save data arrays
# # #                 if self.temperature is not None:
# # #                     f.create_dataset('temperature', data=self.temperature)
# # #                 if self.field is not None:
# # #                     f.create_dataset('field', data=self.field)
# # #                 if self.moment is not None:
# # #                     f.create_dataset('moment', data=self.moment)
# # #
# # #                 # Save metadata
# # #                 for key, value in self.metadata.items():
# # #                     f.attrs[key] = value
# # #
# # #         return filepath
# #
# #
# # # # ============================================================================
# # # # Measurement Engine Base Class
# # # # ============================================================================
# # #
# # # class MeasurementEngine(ABC):
# # #     """Abstract base class for measurement engines"""
# # #
# # #     def __init__(self):
# # #         self.state = MeasurementState.IDLE
# # #         self.progress = 0
# # #         self.current_point = 0
# # #         self.total_points = 0
# # #
# # #     # @abstractmethod
# # #     # def initialize(self, config: MeasurementConfig) -> bool:
# # #     #     """Initialize measurement hardware"""
# # #     #     pass
# # #
# # #     @abstractmethod
# # #     def measure_point(self, point_index: int) -> Dict[str, float]:
# # #         """Measure a single data point"""
# # #         pass
# # #
# # #     @abstractmethod
# # #     def finalize(self):
# # #         """Cleanup after measurement"""
# # #         pass
# # #
# # #     @abstractmethod
# # #     def abort(self):
# # #         """Abort measurement"""
# # #         pass
# # #
# # #
# # # class PPMSMeasurementEngine(MeasurementEngine):
# # #     """PPMS-specific measurement engine"""
# # #
# # #     def __init__(self, ppms_client):
# # #         super().__init__()
# # #         self.ppms = ppms_client
# # #         self.config = None
# # #
# # #     # def initialize(self, config: MeasurementConfig) -> bool:
# # #     #     """Initialize PPMS for measurement"""
# # #     #     try:
# # #     #         self.config = config
# # #     #         self.state = MeasurementState.INITIALIZING
# # #     #
# # #     #         # Set initial temperature
# # #     #         self.ppms.set_temperature(
# # #     #             config.temp_start,
# # #     #             config.temp_rate,
# # #     #             self.ppms.temperature.approach_mode.fast_settle
# # #     #         )
# # #     #
# # #     #         # Set initial field
# # #     #         self.ppms.set_field(
# # #     #             config.field_start,
# # #     #             config.field_rate,
# # #     #             self.ppms.field.approach_mode.linear
# # #     #         )
# # #     #
# # #     #         self.total_points = config.num_points
# # #     #         self.state = MeasurementState.RUNNING
# # #     #         return True
# # #     #
# # #     #     except Exception as e:
# # #     #         self.state = MeasurementState.ERROR
# # #     #         raise e
# # #
# # #     def measure_point(self, point_index: int) -> Dict[str, float]:
# # #         """Measure a single data point"""
# # #         if self.state != MeasurementState.RUNNING:
# # #             return None
# # #
# # #         self.current_point = point_index
# # #         self.progress = (point_index / self.total_points) * 100
# # #
# # #         # Get current readings
# # #         temp, temp_status = self.ppms.get_temperature()
# # #         field, field_status = self.ppms.get_field()
# # #
# # #         # Perform measurement based on type
# # #         data = {
# # #             'temperature': temp,
# # #             'field': field,
# # #             'timestamp': time.time()
# # #         }
# # #
# # #         if self.config.measurement_type == MeasurementType.VSM:
# # #             # VSM measurement
# # #             moment = self.ppms.get_vsm_measurement()
# # #             data['moment'] = moment
# # #         elif self.config.measurement_type == MeasurementType.RESISTANCE:
# # #             # Resistance measurement
# # #             resistance = self.ppms.get_resistance()
# # #             data['resistance'] = resistance
# # #
# # #         return data
# # #
# # #     def finalize(self):
# # #         """Cleanup after measurement"""
# # #         self.state = MeasurementState.COMPLETED
# # #
# # #     def abort(self):
# # #         """Abort measurement"""
# # #         self.state = MeasurementState.ABORTED
# # #         # Stop temperature and field sweeps
# # #         if self.ppms:
# # #             self.ppms.set_temperature_rate(0)
# # #             self.ppms.set_field_rate(0)
# #
# #
# # # # ============================================================================
# # # # Measurement Thread
# # # # ============================================================================
# # #
# # # class MeasurementThread(QThread):
# # #     """Thread for running measurements"""
# # #
# # #     # Signals
# # #     progress_update = pyqtSignal(int, str)
# # #     data_update = pyqtSignal(dict)
# # #     measurement_complete = pyqtSignal(MeasurementData)
# # #     error_occurred = pyqtSignal(str)
# # #     status_update = pyqtSignal(str)
# # #
# # #     def __init__(self, engine: MeasurementEngine):
# # #         super().__init__()
# # #         self.engine = engine
# # #         # self.config = config
# # #         self.measurement_data = MeasurementData(
# # #             timestamp=datetime.now(),
# # #             # config=config
# # #         )
# # #         self._is_running = True
# # #
# # #     def run(self):
# # #         """Run the measurement sequence"""
# # #         try:
# # #             # Initialize
# # #             self.status_update.emit("Initializing measurement...")
# # #             if not self.engine.initialize(self.config):
# # #                 raise RuntimeError("Failed to initialize measurement")
# # #
# # #             # Prepare data arrays
# # #             data_points = []
# # #
# # #             # Main measurement loop
# # #             for i in range(self.config.num_points):
# # #                 if not self._is_running:
# # #                     self.status_update.emit("Measurement aborted")
# # #                     break
# # #
# # #                 # Update status
# # #                 self.status_update.emit(f"Measuring point {i + 1}/{self.config.num_points}")
# # #
# # #                 # Measure point
# # #                 point_data = self.engine.measure_point(i)
# # #                 if point_data:
# # #                     data_points.append(point_data)
# # #                     self.data_update.emit(point_data)
# # #
# # #                 # Update progress
# # #                 progress = int((i + 1) / self.config.num_points * 100)
# # #                 self.progress_update.emit(progress, f"Point {i + 1}/{self.config.num_points}")
# # #
# # #                 # Wait for averaging time
# # #                 time.sleep(self.config.averaging_time)
# # #
# # #             # Process collected data
# # #             if data_points:
# # #                 self._process_data(data_points)
# # #
# # #             # Finalize
# # #             self.engine.finalize()
# # #             self.status_update.emit("Measurement completed")
# # #             self.measurement_complete.emit(self.measurement_data)
# # #
# # #         except Exception as e:
# # #             error_msg = f"Measurement error: {str(e)}\n{traceback.format_exc()}"
# # #             self.error_occurred.emit(error_msg)
# # #             self.measurement_data.errors.append(error_msg)
# # #
# # #     def _process_data(self, data_points: List[Dict]):
# # #         """Process collected data points"""
# # #         # Convert to numpy arrays
# # #         if data_points:
# # #             self.measurement_data.temperature = np.array([p.get('temperature', np.nan) for p in data_points])
# # #             self.measurement_data.field = np.array([p.get('field', np.nan) for p in data_points])
# # #
# # #             if 'moment' in data_points[0]:
# # #                 self.measurement_data.moment = np.array([p.get('moment', np.nan) for p in data_points])
# # #             if 'resistance' in data_points[0]:
# # #                 self.measurement_data.resistance = np.array([p.get('resistance', np.nan) for p in data_points])
# # #
# # #     def stop(self):
# # #         """Stop the measurement"""
# # #         self._is_running = False
# # #         if self.engine:
# # #             self.engine.abort()
# #
# #
# # # ============================================================================
# # # Measurement Controller
# # # ============================================================================
# #
# # # class MeasurementController(QObject):
# # #     """Controller for managing measurements with notifications"""
# # #
# # #     # Signals
# # #     measurement_started = pyqtSignal(str)
# # #     measurement_completed = pyqtSignal(MeasurementData)
# # #     measurement_error = pyqtSignal(str)
# # #
# # #     def __init__(self, ppms_client=None):
# # #         super().__init__()
# # #         self.ppms_client = ppms_client
# # #         self.notification_manager = NotificationManager()
# # #         self.current_thread = None
# # #         self.current_engine = None
# # #         self.measurement_history = []
# # #
# # #     def start_measurement(self, config: MeasurementConfig):
# # #         """Start a new measurement"""
# # #         # Validate configuration
# # #         valid, message = config.validate()
# # #         if not valid:
# # #             self.measurement_error.emit(f"Invalid configuration:\n{message}")
# # #             return False
# # #
# # #         # Stop any running measurement
# # #         if self.current_thread and self.current_thread.isRunning():
# # #             self.stop_measurement()
# # #
# # #         # Create engine
# # #         self.current_engine = PPMSMeasurementEngine(self.ppms_client)
# # #
# # #         # Create and configure thread
# # #         self.current_thread = MeasurementThread(self.current_engine, config)
# # #         self.current_thread.measurement_complete.connect(self._on_measurement_complete)
# # #         self.current_thread.error_occurred.connect(self._on_measurement_error)
# # #
# # #         # Start measurement
# # #         self.current_thread.start()
# # #         self.measurement_started.emit(config.sample_name)
# # #
# # #         # Send notification
# # #         if config.notify_on_complete:
# # #             self.notification_manager.send_notification(
# # #                 'experiment_start',
# # #                 'Measurement Started',
# # #                 f'Starting {config.measurement_type.value} measurement for {config.sample_name}\n'
# # #                 f'Temperature: {config.temp_start}K → {config.temp_end}K\n'
# # #                 f'Field: {config.field_start}Oe → {config.field_end}Oe'
# # #             )
# # #
# # #         return True
# # #
# # #     def stop_measurement(self):
# # #         """Stop current measurement"""
# # #         if self.current_thread and self.current_thread.isRunning():
# # #             self.current_thread.stop()
# # #             self.current_thread.wait()
# # #
# # #     def _on_measurement_complete(self, data: MeasurementData):
# # #         """Handle measurement completion"""
# # #         # Save data if auto-save enabled
# # #         if data.config.auto_save:
# # #             filepath = data.save()
# # #
# # #             # Send notification
# # #             if data.config.notify_on_complete:
# # #                 self.notification_manager.send_notification(
# # #                     'experiment_complete',
# # #                     'Measurement Completed',
# # #                     f'Measurement "{data.config.sample_name}" completed successfully!\n'
# # #                     f'Data saved to: {filepath}\n'
# # #                     f'Points collected: {len(data.temperature) if data.temperature is not None else 0}'
# # #                 )
# # #
# # #         # Add to history
# # #         self.measurement_history.append(data)
# # #         self.measurement_completed.emit(data)
# # #
# # #     def _on_measurement_error(self, error_msg: str):
# # #         """Handle measurement error"""
# # #         # Send error notification
# # #         if self.current_engine and hasattr(self.current_engine, 'config'):
# # #             config = self.current_engine.config
# # #             if config.notify_on_error:
# # #                 self.notification_manager.send_notification(
# # #                     'experiment_error',
# # #                     'Measurement Error',
# # #                     f'Error in measurement "{config.sample_name}":\n{error_msg}'
# # #                 )
# # #
# # #         self.measurement_error.emit(error_msg)
# #
# #
# # # # ============================================================================
# # # # Measurement Widget (UI)
# # # # ============================================================================
# # #
# # # class MeasurementWidget(QWidget):
# # #     """Main measurement control widget"""
# # #
# # #     def __init__(self, ppms_client=None):
# # #         super().__init__()
# # #         # self.controller = MeasurementController(ppms_client)
# # #         self.init_ui()
# # #         # self.connect_signals()
# # #
# # #     def init_ui(self):
# # #         """Initialize the user interface"""
# # #         layout = QVBoxLayout(self)
# # #
# # #         # Title
# # #         title = QLabel("Measurement Control")
# # #         title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
# # #         title.setAlignment(Qt.AlignmentFlag.AlignCenter)
# # #         layout.addWidget(title)
# # #
# # #         # Create main sections
# # #         layout.addWidget(self.create_config_section())
# # #         layout.addWidget(self.create_control_section())
# # #         layout.addWidget(self.create_status_section())
# # #         layout.addWidget(self.create_plot_section())
# # #
# # #     def create_config_section(self) -> QGroupBox:
# # #         """Create configuration section"""
# # #         group = QGroupBox("Measurement Configuration")
# # #         layout = QVBoxLayout()
# # #
# # #         # Measurement type
# # #         type_layout = QHBoxLayout()
# # #         type_layout.addWidget(QLabel("Type:"))
# # #         self.type_combo = QComboBox()
# # #         self.type_combo.addItems([t.value for t in MeasurementType])
# # #         type_layout.addWidget(self.type_combo)
# # #         type_layout.addStretch()
# # #         layout.addLayout(type_layout)
# # #
# # #         # Sample name
# # #         name_layout = QHBoxLayout()
# # #         name_layout.addWidget(QLabel("Sample:"))
# # #         self.sample_name = QLineEdit()
# # #         self.sample_name.setPlaceholderText("Enter sample name")
# # #         name_layout.addWidget(self.sample_name)
# # #         layout.addLayout(name_layout)
# # #
# # #         # Temperature settings
# # #         temp_group = QGroupBox("Temperature Settings")
# # #         temp_layout = QGridLayout()
# # #
# # #         temp_layout.addWidget(QLabel("Start (K):"), 0, 0)
# # #         self.temp_start = QLineEdit("300")
# # #         temp_layout.addWidget(self.temp_start, 0, 1)
# # #
# # #         temp_layout.addWidget(QLabel("End (K):"), 0, 2)
# # #         self.temp_end = QLineEdit("2")
# # #         temp_layout.addWidget(self.temp_end, 0, 3)
# # #
# # #         temp_layout.addWidget(QLabel("Rate (K/min):"), 1, 0)
# # #         self.temp_rate = QLineEdit("5")
# # #         temp_layout.addWidget(self.temp_rate, 1, 1)
# # #
# # #         temp_layout.addWidget(QLabel("Settle (s):"), 1, 2)
# # #         self.temp_settle = QLineEdit("60")
# # #         temp_layout.addWidget(self.temp_settle, 1, 3)
# # #
# # #         temp_group.setLayout(temp_layout)
# # #         layout.addWidget(temp_group)
# # #
# # #         # Field settings
# # #         field_group = QGroupBox("Field Settings")
# # #         field_layout = QGridLayout()
# # #
# # #         field_layout.addWidget(QLabel("Start (Oe):"), 0, 0)
# # #         self.field_start = QLineEdit("0")
# # #         field_layout.addWidget(self.field_start, 0, 1)
# # #
# # #         field_layout.addWidget(QLabel("End (Oe):"), 0, 2)
# # #         self.field_end = QLineEdit("10000")
# # #         field_layout.addWidget(self.field_end, 0, 3)
# # #
# # #         field_layout.addWidget(QLabel("Rate (Oe/s):"), 1, 0)
# # #         self.field_rate = QLineEdit("100")
# # #         field_layout.addWidget(self.field_rate, 1, 1)
# # #
# # #         field_layout.addWidget(QLabel("Settle (s):"), 1, 2)
# # #         self.field_settle = QLineEdit("30")
# # #         field_layout.addWidget(self.field_settle, 1, 3)
# # #
# # #         field_group.setLayout(field_layout)
# # #         layout.addWidget(field_group)
# # #
# # #         # Measurement settings
# # #         meas_layout = QHBoxLayout()
# # #         meas_layout.addWidget(QLabel("Points:"))
# # #         self.num_points = QLineEdit("100")
# # #         meas_layout.addWidget(self.num_points)
# # #
# # #         meas_layout.addWidget(QLabel("Averaging (s):"))
# # #         self.averaging_time = QLineEdit("1.0")
# # #         meas_layout.addWidget(self.averaging_time)
# # #
# # #         meas_layout.addWidget(QLabel("Averages:"))
# # #         self.num_averages = QLineEdit("1")
# # #         meas_layout.addWidget(self.num_averages)
# # #         meas_layout.addStretch()
# # #         layout.addLayout(meas_layout)
# # #
# # #         # Notification settings
# # #         notify_layout = QHBoxLayout()
# # #         self.notify_complete = QCheckBox("Notify on complete")
# # #         self.notify_complete.setChecked(True)
# # #         self.notify_error = QCheckBox("Notify on error")
# # #         self.notify_error.setChecked(True)
# # #         self.notify_milestone = QCheckBox("Notify milestones")
# # #         notify_layout.addWidget(self.notify_complete)
# # #         notify_layout.addWidget(self.notify_error)
# # #         notify_layout.addWidget(self.notify_milestone)
# # #         notify_layout.addStretch()
# # #         layout.addLayout(notify_layout)
# # #
# # #         group.setLayout(layout)
# # #         return group
# # #
# # #     def create_control_section(self) -> QGroupBox:
# # #         """Create control section"""
# # #         group = QGroupBox("Measurement Control")
# # #         layout = QHBoxLayout()
# # #
# # #         # Control buttons
# # #         self.start_btn = QPushButton("▶ Start")
# # #         self.start_btn.setStyleSheet("""
# # #             QPushButton {
# # #                 background-color: #28a745;
# # #                 color: white;
# # #                 padding: 10px 20px;
# # #                 font-size: 14px;
# # #                 font-weight: bold;
# # #                 border-radius: 5px;
# # #             }
# # #             QPushButton:hover {
# # #                 background-color: #218838;
# # #             }
# # #         """)
# # #         # self.start_btn.clicked.connect(self.start_measurement)
# # #
# # #         self.stop_btn = QPushButton("⏹ Stop")
# # #         self.stop_btn.setEnabled(False)
# # #         self.stop_btn.setStyleSheet("""
# # #             QPushButton {
# # #                 background-color: #dc3545;
# # #                 color: white;
# # #                 padding: 10px 20px;
# # #                 font-size: 14px;
# # #                 font-weight: bold;
# # #                 border-radius: 5px;
# # #             }
# # #             QPushButton:hover {
# # #                 background-color: #c82333;
# # #             }
# # #             QPushButton:disabled {
# # #                 background-color: #6c757d;
# # #             }
# # #         """)
# # #         # self.stop_btn.clicked.connect(self.stop_measurement)
# # #
# # #         self.pause_btn = QPushButton("⏸ Pause")
# # #         self.pause_btn.setEnabled(False)
# # #
# # #         # Progress bar
# # #         self.progress_bar = QProgressBar()
# # #         self.progress_bar.setStyleSheet("""
# # #             QProgressBar {
# # #                 border: 2px solid #ddd;
# # #                 border-radius: 5px;
# # #                 text-align: center;
# # #                 height: 25px;
# # #             }
# # #             QProgressBar::chunk {
# # #                 background-color: #1e88e5;
# # #                 border-radius: 3px;
# # #             }
# # #         """)
# # #
# # #         layout.addWidget(self.start_btn)
# # #         layout.addWidget(self.stop_btn)
# # #         layout.addWidget(self.pause_btn)
# # #         layout.addWidget(self.progress_bar, 1)
# # #
# # #         group.setLayout(layout)
# # #         return group
# # #
# # #     def create_status_section(self) -> QGroupBox:
# # #         """Create status section"""
# # #         group = QGroupBox("Status")
# # #         layout = QVBoxLayout()
# # #
# # #         # Status display
# # #         self.status_text = QTextEdit()
# # #         self.status_text.setReadOnly(True)
# # #         self.status_text.setMaximumHeight(100)
# # #         self.status_text.setStyleSheet("""
# # #             QTextEdit {
# # #                 background-color: #f8f9fa;
# # #                 border: 1px solid #dee2e6;
# # #                 border-radius: 5px;
# # #                 padding: 5px;
# # #                 font-family: monospace;
# # #             }
# # #         """)
# # #
# # #         layout.addWidget(self.status_text)
# # #         group.setLayout(layout)
# # #         return group
# # #
# # #     def create_plot_section(self) -> QGroupBox:
# # #         """Create plot section"""
# # #         group = QGroupBox("Live Data")
# # #         layout = QVBoxLayout()
# # #
# # #         # Create matplotlib figure
# # #         self.figure = Figure(figsize=(10, 6))
# # #         self.canvas = FigureCanvas(self.figure)
# # #
# # #         # Create subplots
# # #         self.ax1 = self.figure.add_subplot(121)
# # #         self.ax2 = self.figure.add_subplot(122)
# # #
# # #         self.ax1.set_xlabel('Temperature (K)')
# # #         self.ax1.set_ylabel('Moment (emu)')
# # #         self.ax1.grid(True, alpha=0.3)
# # #
# # #         self.ax2.set_xlabel('Field (Oe)')
# # #         self.ax2.set_ylabel('Moment (emu)')
# # #         self.ax2.grid(True, alpha=0.3)
# # #
# # #         self.figure.tight_layout()
# # #
# # #         layout.addWidget(self.canvas)
# # #         group.setLayout(layout)
# # #         return group
# #
# #     # def connect_signals(self):
# #     #     """Connect controller signals"""
# #     #     self.controller.measurement_started.connect(self.on_measurement_started)
# #     #     self.controller.measurement_completed.connect(self.on_measurement_completed)
# #     #     self.controller.measurement_error.connect(self.on_measurement_error)
# #     #
# #     #     if self.controller.current_thread:
# #     #         self.controller.current_thread.progress_update.connect(self.update_progress)
# #     #         self.controller.current_thread.status_update.connect(self.update_status)
# #     #         self.controller.current_thread.data_update.connect(self.update_plot)
# #
# #     # def start_measurement(self):
# #     #     """Start measurement"""
# #     #     try:
# #     #         # Create configuration from UI
# #     #         # config = MeasurementConfig(
# #     #         #     measurement_type=MeasurementType(self.type_combo.currentText()),
# #     #         #     sample_name=self.sample_name.text() or "Unknown",
# #     #         #     temp_start=float(self.temp_start.text()),
# #     #         #     temp_end=float(self.temp_end.text()),
# #     #         #     temp_rate=float(self.temp_rate.text()),
# #     #         #     temp_settle_time=float(self.temp_settle.text()),
# #     #         #     field_start=float(self.field_start.text()),
# #     #         #     field_end=float(self.field_end.text()),
# #     #         #     field_rate=float(self.field_rate.text()),
# #     #         #     field_settle_time=float(self.field_settle.text()),
# #     #         #     num_points=int(self.num_points.text()),
# #     #         #     averaging_time=float(self.averaging_time.text()),
# #     #         #     num_averages=int(self.num_averages.text()),
# #     #         #     notify_on_complete=self.notify_complete.isChecked(),
# #     #         #     notify_on_error=self.notify_error.isChecked(),
# #     #         #     notify_on_milestone=self.notify_milestone.isChecked()
# #     #         # )
# #     #
# #     #         # Start measurement
# #     #         if self.controller.start_measurement(config):
# #     #             self.start_btn.setEnabled(False)
# #     #             self.stop_btn.setEnabled(True)
# #     #             self.pause_btn.setEnabled(True)
# #     #
# #     #     except ValueError as e:
# #     #         QMessageBox.warning(self, "Invalid Input", f"Please check your input values:\n{str(e)}")
# #     #     except Exception as e:
# #     #         QMessageBox.critical(self, "Error", f"Failed to start measurement:\n{str(e)}")
# #
# #     # def stop_measurement(self):
# #     #     """Stop measurement"""
# #     #     reply = QMessageBox.question(
# #     #         self, "Stop Measurement",
# #     #         "Are you sure you want to stop the measurement?",
# #     #         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
# #     #     )
# #     #
# #     #     if reply == QMessageBox.StandardButton.Yes:
# #     #         self.controller.stop_measurement()
# #     #         self.start_btn.setEnabled(True)
# #     #         self.stop_btn.setEnabled(False)
# #     #         self.pause_btn.setEnabled(False)
# #     #         self.progress_bar.setValue(0)
# #     #
# #     # def on_measurement_started(self, sample_name: str):
# #     #     """Handle measurement started"""
# #     #     self.update_status(f"Measurement started: {sample_name}")
# #     #
# #     # def on_measurement_completed(self, data: MeasurementData):
# #     #     """Handle measurement completed"""
# #     #     self.start_btn.setEnabled(True)
# #     #     self.stop_btn.setEnabled(False)
# #     #     self.pause_btn.setEnabled(False)
# #     #     self.update_status(f"Measurement completed: {data.config.sample_name}")
# #     #
# #     #     # Show summary
# #     #     QMessageBox.information(
# #     #         self, "Measurement Complete",
# #     #         f"Measurement '{data.config.sample_name}' completed successfully!\n"
# #     #         f"Data points: {len(data.temperature) if data.temperature is not None else 0}\n"
# #     #         f"Saved to: {data.config.save_path}"
# #     #     )
# #     #
# #     # def on_measurement_error(self, error_msg: str):
# #     #     """Handle measurement error"""
# #     #     self.start_btn.setEnabled(True)
# #     #     self.stop_btn.setEnabled(False)
# #     #     self.pause_btn.setEnabled(False)
# #     #     self.update_status(f"Error: {error_msg}")
# #     #
# #     #     QMessageBox.critical(
# #     #         self, "Measurement Error",
# #     #         f"An error occurred during measurement:\n{error_msg}"
# #     #     )
# #     #
# #     # def update_progress(self, value: int, text: str):
# #     #     """Update progress bar"""
# #     #     self.progress_bar.setValue(value)
# #     #     self.progress_bar.setFormat(f"{text} - {value}%")
# #     #
# #     # def update_status(self, message: str):
# #     #     """Update status text"""
# #     #     timestamp = datetime.now().strftime("%H:%M:%S")
# #     #     self.status_text.append(f"[{timestamp}] {message}")
# #     #     # Auto-scroll to bottom
# #     #     scrollbar = self.status_text.verticalScrollBar()
# #     #     scrollbar.setValue(scrollbar.maximum())
# #     #
# #     # def update_plot(self, data: dict):
# #     #     """Update live plot with new data"""
# #     #     # This method would be connected to real-time data updates
# #     #     # For now, it's a placeholder for live plotting
# #     #     pass
# #
# #
# # # # ============================================================================
# # # # Notification Manager (Extended)
# # # # ============================================================================
# # # from QuDAP.utils.notification_manager import NotificationManager
# # #
# # # class NotificationManager:
# # #     """Enhanced notification manager for QuDAP measurements"""
# # #
# # #     def __init__(self):
# # #         self.settings = QSettings('QuDAP', 'NotificationSettings')
# # #         self.enabled_channels = self._load_enabled_channels()
# # #
# # #     def _load_enabled_channels(self) -> Dict[str, bool]:
# # #         """Load enabled notification channels"""
# # #         return {
# # #             'email': self.settings.value('email/enabled', False, bool),
# # #             'telegram': self.settings.value('telegram/enabled', False, bool),
# # #             'discord': self.settings.value('discord/enabled', False, bool),
# # #             'slack': self.settings.value('slack/enabled', False, bool),
# # #             'webhook': self.settings.value('webhook/enabled', False, bool)
# # #         }
# # #
# # #     def should_notify(self, event_type: str) -> bool:
# # #         """Check if notification should be sent for event type"""
# # #         return self.settings.value(f'events/{event_type}', True, bool)
# # #
# # #     def send_notification(self, event_type: str, title: str, message: str, priority: str = "normal"):
# # #         """Send notification to all enabled channels"""
# # #         if not self.should_notify(event_type):
# # #             return
# # #
# # #         # Check quiet hours
# # #         if self.in_quiet_hours() and priority != "critical":
# # #             return
# # #
# # #         # Format message with timestamp
# # #         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# # #         formatted_message = f"{message}\n\nTime: {timestamp}"
# # #
# # #         # Send to each enabled channel
# # #         if self.enabled_channels.get('email'):
# # #             self._send_email(title, formatted_message, priority)
# # #         if self.enabled_channels.get('telegram'):
# # #             self._send_telegram(title, formatted_message, priority)
# # #         if self.enabled_channels.get('discord'):
# # #             self._send_discord(title, formatted_message, priority)
# # #         if self.enabled_channels.get('slack'):
# # #             self._send_slack(title, formatted_message, priority)
# # #         if self.enabled_channels.get('webhook'):
# # #             self._send_webhook(title, formatted_message, priority)
# # #
# # #     def _send_email(self, subject: str, body: str, priority: str):
# # #         """Send email notification"""
# # #         import smtplib
# # #         from email.mime.text import MIMEText
# # #         from email.mime.multipart import MIMEMultipart
# # #
# # #         try:
# # #             # Get settings
# # #             smtp_server = self.settings.value('email/smtp_server', '')
# # #             smtp_port = self.settings.value('email/smtp_port', 587, int)
# # #             use_ssl = self.settings.value('email/smtp_ssl', True, bool)
# # #             username = self.settings.value('email/username', '')
# # #             password = self.settings.value('email/password', '')
# # #             from_email = self.settings.value('email/from_email', username)
# # #             to_emails = self.settings.value('email/to_emails', '').split('\n')
# # #
# # #             if not all([smtp_server, username, password, to_emails]):
# # #                 return
# # #
# # #             # Create message
# # #             msg = MIMEMultipart('alternative')
# # #             msg['From'] = from_email
# # #             msg['To'] = ', '.join(filter(None, to_emails))
# # #             msg['Subject'] = f"[QuDAP {priority.upper()}] {subject}"
# # #
# # #             # Add priority headers
# # #             if priority == "critical":
# # #                 msg['X-Priority'] = '1'
# # #                 msg['Importance'] = 'high'
# # #             elif priority == "high":
# # #                 msg['X-Priority'] = '2'
# # #                 msg['Importance'] = 'high'
# # #
# # #             # Create HTML version
# # #             html_body = f"""
# # #             <html>
# # #                 <body style="font-family: Arial, sans-serif;">
# # #                     <div style="background-color: #1e88e5; color: white; padding: 20px; border-radius: 5px 5px 0 0;">
# # #                         <h2 style="margin: 0;">🔬 QuDAP Notification</h2>
# # #                     </div>
# # #                     <div style="padding: 20px; background-color: #f5f5f5;">
# # #                         <h3 style="color: #2c3e50;">{subject}</h3>
# # #                         <pre style="background-color: white; padding: 15px; border-radius: 5px; white-space: pre-wrap;">{body}</pre>
# # #                     </div>
# # #                     <div style="padding: 10px; background-color: #e0e0e0; text-align: center; font-size: 12px;">
# # #                         QuDAP - Quantum Materials Data Acquisition and Processing
# # #                     </div>
# # #                 </body>
# # #             </html>
# # #             """
# # #
# # #             # Attach parts
# # #             msg.attach(MIMEText(body, 'plain'))
# # #             msg.attach(MIMEText(html_body, 'html'))
# # #
# # #             # Send email
# # #             with smtplib.SMTP(smtp_server, smtp_port) as server:
# # #                 if use_ssl:
# # #                     server.starttls()
# # #                 server.login(username, password)
# # #                 server.send_message(msg)
# # #
# # #         except Exception as e:
# # #             print(f"Email notification error: {e}")
# # #
# # #     def _send_telegram(self, title: str, message: str, priority: str):
# # #         """Send Telegram notification"""
# # #         import requests
# # #
# # #         try:
# # #             token = self.settings.value('telegram/token', '')
# # #             chat_id = self.settings.value('telegram/chat_id', '')
# # #             format_type = self.settings.value('telegram/format', 'Markdown')
# # #
# # #             if not all([token, chat_id]):
# # #                 return
# # #
# # #             # Priority emoji
# # #             priority_emoji = {
# # #                 'low': '🔵',
# # #                 'normal': '🟡',
# # #                 'high': '🟠',
# # #                 'critical': '🔴'
# # #             }.get(priority, '⚪')
# # #
# # #             # Format message
# # #             if format_type == 'Markdown':
# # #                 text = f"{priority_emoji} *{title}*\n\n```\n{message}\n```"
# # #                 parse_mode = 'Markdown'
# # #             elif format_type == 'HTML':
# # #                 text = f"{priority_emoji} <b>{title}</b>\n\n<pre>{message}</pre>"
# # #                 parse_mode = 'HTML'
# # #             else:
# # #                 text = f"{priority_emoji} {title}\n\n{message}"
# # #                 parse_mode = None
# # #
# # #             # Send message
# # #             url = f"https://api.telegram.org/bot{token}/sendMessage"
# # #             data = {
# # #                 'chat_id': chat_id,
# # #                 'text': text,
# # #             }
# # #             if parse_mode:
# # #                 data['parse_mode'] = parse_mode
# # #
# # #             response = requests.post(url, data=data, timeout=10)
# # #             response.raise_for_status()
# # #
# # #         except Exception as e:
# # #             print(f"Telegram notification error: {e}")
# # #
# # #     def _send_discord(self, title: str, message: str, priority: str):
# # #         """Send Discord notification"""
# # #         import requests
# # #
# # #         try:
# # #             webhook_url = self.settings.value('discord/webhook', '')
# # #             bot_name = self.settings.value('discord/name', 'QuDAP Bot')
# # #
# # #             if not webhook_url:
# # #                 return
# # #
# # #             # Priority color
# # #             color_map = {
# # #                 'low': 0x3498db,  # Blue
# # #                 'normal': 0xf1c40f,  # Yellow
# # #                 'high': 0xe67e22,  # Orange
# # #                 'critical': 0xe74c3c  # Red
# # #             }
# # #
# # #             # Create embed
# # #             data = {
# # #                 'username': bot_name,
# # #                 'embeds': [{
# # #                     'title': f'🔬 {title}',
# # #                     'description': f"```\n{message}\n```",
# # #                     'color': color_map.get(priority, 0x95a5a6),
# # #                     'footer': {
# # #                         'text': 'QuDAP Notification System'
# # #                     },
# # #                     'timestamp': datetime.now().isoformat()
# # #                 }]
# # #             }
# # #
# # #             response = requests.post(webhook_url, json=data, timeout=10)
# # #             response.raise_for_status()
# # #
# # #         except Exception as e:
# # #             print(f"Discord notification error: {e}")
# # #
# # #     def _send_slack(self, title: str, message: str, priority: str):
# # #         """Send Slack notification"""
# # #         import requests
# # #
# # #         try:
# # #             webhook_url = self.settings.value('slack/webhook', '')
# # #             channel = self.settings.value('slack/channel', '')
# # #             username = self.settings.value('slack/username', 'QuDAP Bot')
# # #
# # #             if not webhook_url:
# # #                 return
# # #
# # #             # Priority emoji and color
# # #             priority_config = {
# # #                 'low': ('🔵', '#3498db'),
# # #                 'normal': ('🟡', '#f1c40f'),
# # #                 'high': ('🟠', '#e67e22'),
# # #                 'critical': ('🔴', '#e74c3c')
# # #             }
# # #             emoji, color = priority_config.get(priority, ('⚪', '#95a5a6'))
# # #
# # #             # Create message
# # #             data = {
# # #                 'username': username,
# # #                 'icon_emoji': ':microscope:',
# # #                 'attachments': [{
# # #                     'fallback': f"{title}: {message}",
# # #                     'color': color,
# # #                     'title': f"{emoji} {title}",
# # #                     'text': message,
# # #                     'footer': 'QuDAP',
# # #                     'footer_icon': 'https://platform.slack-edge.com/img/default_application_icon.png',
# # #                     'ts': int(datetime.now().timestamp())
# # #                 }]
# # #             }
# # #
# # #             if channel:
# # #                 data['channel'] = channel
# # #
# # #             response = requests.post(webhook_url, json=data, timeout=10)
# # #             response.raise_for_status()
# # #
# # #         except Exception as e:
# # #             print(f"Slack notification error: {e}")
# # #
# # #     def _send_webhook(self, title: str, message: str, priority: str):
# # #         """Send custom webhook notification"""
# # #         import requests
# # #         import json
# # #
# # #         try:
# # #             url = self.settings.value('webhook/url', '')
# # #             method = self.settings.value('webhook/method', 'POST')
# # #             headers_str = self.settings.value('webhook/headers', '{}')
# # #
# # #             if not url:
# # #                 return
# # #
# # #             # Parse headers
# # #             try:
# # #                 headers = json.loads(headers_str) if headers_str else {}
# # #             except:
# # #                 headers = {'Content-Type': 'application/json'}
# # #
# # #             # Create payload
# # #             payload = {
# # #                 'title': title,
# # #                 'message': message,
# # #                 'priority': priority,
# # #                 'timestamp': datetime.now().isoformat(),
# # #                 'source': 'QuDAP',
# # #                 'event_type': 'measurement_notification'
# # #             }
# # #
# # #             # Send request
# # #             if method.upper() == 'GET':
# # #                 response = requests.get(url, params=payload, headers=headers, timeout=10)
# # #             elif method.upper() == 'PUT':
# # #                 response = requests.put(url, json=payload, headers=headers, timeout=10)
# # #             else:  # POST
# # #                 response = requests.post(url, json=payload, headers=headers, timeout=10)
# # #
# # #             response.raise_for_status()
# # #
# # #         except Exception as e:
# # #             print(f"Webhook notification error: {e}")
# # #
# # #     def in_quiet_hours(self) -> bool:
# # #         """Check if current time is within quiet hours"""
# # #         if not self.settings.value('quiet_hours/enabled', False, bool):
# # #             return False
# # #
# # #         from PyQt6.QtCore import QTime
# # #
# # #         current = QTime.currentTime()
# # #         start = QTime.fromString(self.settings.value('quiet_hours/start', '22:00'))
# # #         end = QTime.fromString(self.settings.value('quiet_hours/end', '07:00'))
# # #
# # #         if start <= end:
# # #             # Quiet hours don't cross midnight
# # #             return start <= current <= end
# # #         else:
# # #             # Quiet hours cross midnight
# # #             return current >= start or current <= end
# # #
# # #     def send_milestone_notification(self, sample_name: str, percentage: int, details: str):
# # #         """Send milestone notification"""
# # #         if percentage in [25, 50, 75]:
# # #             self.send_notification(
# # #                 'experiment_milestone',
# # #                 f'Measurement Progress: {percentage}%',
# # #                 f'Sample: {sample_name}\n'
# # #                 f'Progress: {percentage}% complete\n'
# # #                 f'Details: {details}',
# # #                 priority='low'
# # #             )
# # #
# # #
# # # # ============================================================================
# # # # Main Application Example
# # # # ============================================================================
# # #
# # # if __name__ == "__main__":
# # #     import sys
# # #     from PyQt6.QtWidgets import QApplication, QMainWindow
# # #
# # #
# # #     class MeasurementMainWindow(QMainWindow):
# # #         """Main window for testing measurement widget"""
# # #
# # #         def __init__(self):
# # #             super().__init__()
# # #             self.setWindowTitle("QuDAP - Measurement Control")
# # #             self.setGeometry(100, 100, 1200, 800)
# # #
# # #             # Create measurement widget (pass None for demo)
# # #             self.measurement_widget = MeasurementWidget(ppms_client=None)
# # #             self.setCentralWidget(self.measurement_widget)
# # #
# # #             # Add menu bar
# # #             self.create_menu()
# # #
# # #         def create_menu(self):
# # #             """Create menu bar"""
# # #             menubar = self.menuBar()
# # #
# # #             # File menu
# # #             file_menu = menubar.addMenu('File')
# # #             file_menu.addAction('Load Configuration')
# # #             file_menu.addAction('Save Configuration')
# # #             file_menu.addSeparator()
# # #             file_menu.addAction('Exit', self.close)
# # #
# # #             # Settings menu
# # #             settings_menu = menubar.addMenu('Settings')
# # #             notification_action = settings_menu.addAction('Notification Settings')
# # #         #     notification_action.triggered.connect(self.open_notification_settings)
# # #         #
# # #         # def open_notification_settings(self):
# # #         #     """Open notification settings window"""
# # #         #     from notification_settings import NotificationSettings
# # #         #     self.notification_window = NotificationSettings()
# # #         #     self.notification_window.show()
# # #
# # #
# # #     app = QApplication(sys.argv)
# # #     app.setStyle("Fusion")
# # #
# # #     window = MeasurementMainWindow()
# # #     window.show()
# # #
# # #     sys.exit(app.exec())
# #
# # """
# # QuDAP Interactive Plotting GUI
# # A modern, feature-rich plotting interface using PyQt6 and Plotly
# # """
# #
# # import sys
# # import os
# # from pathlib import Path
# # from typing import List, Dict, Any, Optional, Tuple
# # import pandas as pd
# # import numpy as np
# # import plotly.graph_objects as go
# # from plotly.subplots import make_subplots
# # import plotly.express as px
# # import json
# #
# # from PyQt6.QtWidgets import (
# #     QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
# #     QLabel, QPushButton, QComboBox, QLineEdit, QCheckBox, QGroupBox,
# #     QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
# #     QListWidget, QListWidgetItem, QSplitter, QSpinBox, QDoubleSpinBox,
# #     QColorDialog, QMessageBox, QTabWidget, QSlider, QButtonGroup,
# #     QRadioButton, QTextEdit, QToolBar, QStatusBar, QDockWidget,
# #     QAbstractItemView, QMenu, QGraphicsDropShadowEffect
# # )
# # from PyQt6.QtCore import (
# #     Qt, QThread, pyqtSignal, QMimeData, QUrl, QTimer,
# #     QPropertyAnimation, QEasingCurve, QRect, QSize
# # )
# # from PyQt6.QtGui import (
# #     QFont, QColor, QPalette, QDragEnterEvent, QDropEvent,
# #     QAction, QIcon, QPixmap, QPainter, QBrush
# # )
# # from PyQt6.QtWebEngineWidgets import QWebEngineView
# #
# #
# # # ============================================================================
# # # Custom Widgets
# # # ============================================================================
# #
# # class AnimatedCard(QWidget):
# #     """Animated card widget with shadow effects"""
# #
# #     def __init__(self, parent=None):
# #         super().__init__(parent)
# #         self.setStyleSheet("""
# #             QWidget {
# #                 background-color: white;
# #                 border-radius: 10px;
# #                 border: none;
# #             }
# #         """)
# #
# #         # Add shadow effect
# #         self.shadow = QGraphicsDropShadowEffect()
# #         self.shadow.setBlurRadius(15)
# #         self.shadow.setOffset(0, 2)
# #         self.shadow.setColor(QColor(0, 0, 0, 30))
# #         self.setGraphicsEffect(self.shadow)
# #
# #     def enterEvent(self, event):
# #         """Enhance shadow on hover"""
# #         self.shadow.setBlurRadius(20)
# #         self.shadow.setOffset(0, 4)
# #         self.shadow.setColor(QColor(0, 0, 0, 40))
# #         super().enterEvent(event)
# #
# #     def leaveEvent(self, event):
# #         """Reset shadow on leave"""
# #         self.shadow.setBlurRadius(15)
# #         self.shadow.setOffset(0, 2)
# #         self.shadow.setColor(QColor(0, 0, 0, 30))
# #         super().leaveEvent(event)
# #
# #
# # class DragDropArea(AnimatedCard):
# #     """Drag and drop area for files"""
# #
# #     files_dropped = pyqtSignal(list)
# #
# #     def __init__(self):
# #         super().__init__()
# #         self.setAcceptDrops(True)
# #         self.init_ui()
# #
# #     def init_ui(self):
# #         layout = QVBoxLayout(self)
# #         layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
# #
# #         # Icon
# #         icon_label = QLabel("📁")
# #         icon_label.setFont(QFont("Arial", 48))
# #         icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
# #
# #         # Text
# #         text_label = QLabel("Drag & Drop Files Here\nor Click to Browse")
# #         text_label.setFont(QFont("Arial", 14))
# #         text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
# #         text_label.setStyleSheet("color: #7f8c8d;")
# #
# #         # Browse button
# #         browse_btn = QPushButton("Browse Files")
# #         browse_btn.setFont(QFont("Arial", 12))
# #         browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
# #         browse_btn.setStyleSheet("""
# #             QPushButton {
# #                 background-color: #1e88e5;
# #                 color: white;
# #                 padding: 10px 20px;
# #                 border-radius: 5px;
# #                 font-weight: bold;
# #             }
# #             QPushButton:hover {
# #                 background-color: #1976d2;
# #             }
# #         """)
# #         browse_btn.clicked.connect(self.browse_files)
# #
# #         layout.addWidget(icon_label)
# #         layout.addWidget(text_label)
# #         layout.addWidget(browse_btn)
# #
# #         self.setMinimumHeight(200)
# #
# #     def dragEnterEvent(self, event: QDragEnterEvent):
# #         if event.mimeData().hasUrls():
# #             event.acceptProposedAction()
# #             self.setStyleSheet("""
# #                 QWidget {
# #                     background-color: #e3f2fd;
# #                     border: 2px dashed #1e88e5;
# #                     border-radius: 10px;
# #                 }
# #             """)
# #
# #     def dragLeaveEvent(self, event):
# #         self.setStyleSheet("""
# #             QWidget {
# #                 background-color: white;
# #                 border-radius: 10px;
# #                 border: none;
# #             }
# #         """)
# #
# #     def dropEvent(self, event: QDropEvent):
# #         files = []
# #         for url in event.mimeData().urls():
# #             file_path = url.toLocalFile()
# #             if os.path.isfile(file_path):
# #                 files.append(file_path)
# #             elif os.path.isdir(file_path):
# #                 # Get all CSV/TXT files from directory
# #                 for ext in ['*.csv', '*.txt', '*.dat', '*.xlsx']:
# #                     files.extend(Path(file_path).glob(ext))
# #
# #         if files:
# #             self.files_dropped.emit([str(f) for f in files])
# #
# #         self.setStyleSheet("""
# #             QWidget {
# #                 background-color: white;
# #                 border-radius: 10px;
# #                 border: none;
# #             }
# #         """)
# #
# #     def browse_files(self):
# #         files, _ = QFileDialog.getOpenFileNames(
# #             self,
# #             "Select Data Files",
# #             "",
# #             "Data Files (*.csv *.txt *.dat *.xlsx);;All Files (*.*)"
# #         )
# #         if files:
# #             self.files_dropped.emit(files)
# #
# #
# # # ============================================================================
# # # Data Manager
# # # ============================================================================
# #
# # class DataManager:
# #     """Manages loaded data files"""
# #
# #     def __init__(self):
# #         self.datasets = {}
# #         self.current_dataset = None
# #
# #     def load_file(self, filepath: str) -> Tuple[bool, str, Optional[pd.DataFrame]]:
# #         """Load a data file"""
# #         try:
# #             file_path = Path(filepath)
# #
# #             if file_path.suffix.lower() == '.csv':
# #                 df = pd.read_csv(filepath)
# #             elif file_path.suffix.lower() in ['.txt', '.dat']:
# #                 # Try different delimiters
# #                 df = pd.read_csv(filepath, sep=None, engine='python')
# #             elif file_path.suffix.lower() == '.xlsx':
# #                 df = pd.read_excel(filepath)
# #             else:
# #                 return False, f"Unsupported file type: {file_path.suffix}", None
# #
# #             # Store dataset
# #             dataset_name = file_path.stem
# #             self.datasets[dataset_name] = {
# #                 'path': filepath,
# #                 'data': df,
# #                 'columns': df.columns.tolist()
# #             }
# #             self.current_dataset = dataset_name
# #
# #             return True, f"Loaded {len(df)} rows from {file_path.name}", df
# #
# #         except Exception as e:
# #             return False, f"Error loading file: {str(e)}", None
# #
# #     def get_current_data(self) -> Optional[pd.DataFrame]:
# #         """Get current dataset"""
# #         if self.current_dataset and self.current_dataset in self.datasets:
# #             return self.datasets[self.current_dataset]['data']
# #         return None
# #
# #     def get_columns(self) -> List[str]:
# #         """Get columns of current dataset"""
# #         df = self.get_current_data()
# #         if df is not None:
# #             return df.columns.tolist()
# #         return []
# #
# #
# # # ============================================================================
# # # Plot Configuration Panel
# # # ============================================================================
# #
# # class PlotConfigPanel(AnimatedCard):
# #     """Panel for configuring plot settings"""
# #
# #     plot_updated = pyqtSignal()
# #
# #     def __init__(self):
# #         super().__init__()
# #         self.init_ui()
# #         self.trace_configs = {}  # Store configuration for each trace
# #
# #     def init_ui(self):
# #         layout = QVBoxLayout(self)
# #         layout.setContentsMargins(20, 20, 20, 20)
# #
# #         # Title
# #         title = QLabel("Plot Configuration")
# #         title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
# #         title.setStyleSheet("color: #2c3e50;")
# #         layout.addWidget(title)
# #
# #         # === Axis Selection ===
# #         axis_group = QGroupBox("Axis Selection")
# #         axis_layout = QVBoxLayout()
# #
# #         # X-axis
# #         x_layout = QHBoxLayout()
# #         x_layout.addWidget(QLabel("X-Axis:"))
# #         self.x_combo = QComboBox()
# #         self.x_combo.currentTextChanged.connect(lambda: self.plot_updated.emit())
# #         x_layout.addWidget(self.x_combo)
# #         axis_layout.addLayout(x_layout)
# #
# #         # Y-axis (multiple selection)
# #         y_label = QLabel("Y-Axis (multiple):")
# #         axis_layout.addWidget(y_label)
# #
# #         self.y_list = QListWidget()
# #         self.y_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
# #         self.y_list.setMaximumHeight(150)
# #         self.y_list.itemSelectionChanged.connect(lambda: self.plot_updated.emit())
# #         axis_layout.addWidget(self.y_list)
# #
# #         axis_group.setLayout(axis_layout)
# #         layout.addWidget(axis_group)
# #
# #         # === Plot Type ===
# #         type_group = QGroupBox("Plot Type")
# #         type_layout = QVBoxLayout()
# #
# #         self.plot_type_group = QButtonGroup()
# #
# #         self.line_radio = QRadioButton("Line")
# #         self.line_radio.setChecked(True)
# #         self.plot_type_group.addButton(self.line_radio, 0)
# #
# #         self.scatter_radio = QRadioButton("Scatter")
# #         self.plot_type_group.addButton(self.scatter_radio, 1)
# #
# #         self.line_scatter_radio = QRadioButton("Line + Scatter")
# #         self.plot_type_group.addButton(self.line_scatter_radio, 2)
# #
# #         type_layout.addWidget(self.line_radio)
# #         type_layout.addWidget(self.scatter_radio)
# #         type_layout.addWidget(self.line_scatter_radio)
# #
# #         self.plot_type_group.buttonClicked.connect(lambda: self.plot_updated.emit())
# #
# #         type_group.setLayout(type_layout)
# #         layout.addWidget(type_group)
# #
# #         # === Trace Configuration ===
# #         trace_group = QGroupBox("Trace Settings")
# #         trace_layout = QVBoxLayout()
# #
# #         # Trace selector
# #         trace_select_layout = QHBoxLayout()
# #         trace_select_layout.addWidget(QLabel("Select Trace:"))
# #         self.trace_combo = QComboBox()
# #         self.trace_combo.currentTextChanged.connect(self.load_trace_config)
# #         trace_select_layout.addWidget(self.trace_combo)
# #         trace_layout.addLayout(trace_select_layout)
# #
# #         # Color picker
# #         color_layout = QHBoxLayout()
# #         color_layout.addWidget(QLabel("Color:"))
# #         self.color_button = QPushButton()
# #         self.color_button.setFixedSize(50, 30)
# #         self.color_button.setStyleSheet("background-color: #1e88e5;")
# #         self.color_button.clicked.connect(self.pick_color)
# #         color_layout.addWidget(self.color_button)
# #         color_layout.addStretch()
# #         trace_layout.addLayout(color_layout)
# #
# #         # Line width
# #         line_width_layout = QHBoxLayout()
# #         line_width_layout.addWidget(QLabel("Line Width:"))
# #         self.line_width_spin = QSpinBox()
# #         self.line_width_spin.setRange(1, 10)
# #         self.line_width_spin.setValue(2)
# #         self.line_width_spin.valueChanged.connect(self.update_trace_config)
# #         line_width_layout.addWidget(self.line_width_spin)
# #         line_width_layout.addStretch()
# #         trace_layout.addLayout(line_width_layout)
# #
# #         # Marker size
# #         marker_size_layout = QHBoxLayout()
# #         marker_size_layout.addWidget(QLabel("Marker Size:"))
# #         self.marker_size_spin = QSpinBox()
# #         self.marker_size_spin.setRange(1, 20)
# #         self.marker_size_spin.setValue(6)
# #         self.marker_size_spin.valueChanged.connect(self.update_trace_config)
# #         marker_size_layout.addWidget(self.marker_size_spin)
# #         marker_size_layout.addStretch()
# #         trace_layout.addLayout(marker_size_layout)
# #
# #         trace_group.setLayout(trace_layout)
# #         layout.addWidget(trace_group)
# #
# #         # === Axis Labels ===
# #         labels_group = QGroupBox("Axis Labels")
# #         labels_layout = QVBoxLayout()
# #
# #         # X-axis label
# #         x_label_layout = QHBoxLayout()
# #         x_label_layout.addWidget(QLabel("X Label:"))
# #         self.x_label_input = QLineEdit()
# #         self.x_label_input.setPlaceholderText("X Axis")
# #         self.x_label_input.textChanged.connect(lambda: self.plot_updated.emit())
# #         x_label_layout.addWidget(self.x_label_input)
# #         labels_layout.addLayout(x_label_layout)
# #
# #         # Y-axis label
# #         y_label_layout = QHBoxLayout()
# #         y_label_layout.addWidget(QLabel("Y Label:"))
# #         self.y_label_input = QLineEdit()
# #         self.y_label_input.setPlaceholderText("Y Axis")
# #         self.y_label_input.textChanged.connect(lambda: self.plot_updated.emit())
# #         y_label_layout.addWidget(self.y_label_input)
# #         labels_layout.addLayout(y_label_layout)
# #
# #         # Title
# #         title_layout = QHBoxLayout()
# #         title_layout.addWidget(QLabel("Title:"))
# #         self.title_input = QLineEdit()
# #         self.title_input.setPlaceholderText("Plot Title")
# #         self.title_input.textChanged.connect(lambda: self.plot_updated.emit())
# #         title_layout.addWidget(self.title_input)
# #         labels_layout.addLayout(title_layout)
# #
# #         labels_group.setLayout(labels_layout)
# #         layout.addWidget(labels_group)
# #
# #         # === Display Options ===
# #         display_group = QGroupBox("Display Options")
# #         display_layout = QVBoxLayout()
# #
# #         # Legend
# #         self.legend_checkbox = QCheckBox("Show Legend")
# #         self.legend_checkbox.setChecked(True)
# #         self.legend_checkbox.stateChanged.connect(lambda: self.plot_updated.emit())
# #         display_layout.addWidget(self.legend_checkbox)
# #
# #         # Grid
# #         self.grid_checkbox = QCheckBox("Show Grid")
# #         self.grid_checkbox.setChecked(True)
# #         self.grid_checkbox.stateChanged.connect(lambda: self.plot_updated.emit())
# #         display_layout.addWidget(self.grid_checkbox)
# #
# #         # Font size
# #         font_size_layout = QHBoxLayout()
# #         font_size_layout.addWidget(QLabel("Font Size:"))
# #         self.font_size_spin = QSpinBox()
# #         self.font_size_spin.setRange(8, 24)
# #         self.font_size_spin.setValue(12)
# #         self.font_size_spin.valueChanged.connect(lambda: self.plot_updated.emit())
# #         font_size_layout.addWidget(self.font_size_spin)
# #         font_size_layout.addStretch()
# #         display_layout.addLayout(font_size_layout)
# #
# #         display_group.setLayout(display_layout)
# #         layout.addWidget(display_group)
# #
# #         # === Axis Scale ===
# #         scale_group = QGroupBox("Axis Scale")
# #         scale_layout = QVBoxLayout()
# #
# #         # X-axis scale
# #         x_scale_layout = QHBoxLayout()
# #         x_scale_layout.addWidget(QLabel("X Scale:"))
# #         self.x_scale_combo = QComboBox()
# #         self.x_scale_combo.addItems(["Linear", "Log"])
# #         self.x_scale_combo.currentTextChanged.connect(lambda: self.plot_updated.emit())
# #         x_scale_layout.addWidget(self.x_scale_combo)
# #         scale_layout.addLayout(x_scale_layout)
# #
# #         # Y-axis scale
# #         y_scale_layout = QHBoxLayout()
# #         y_scale_layout.addWidget(QLabel("Y Scale:"))
# #         self.y_scale_combo = QComboBox()
# #         self.y_scale_combo.addItems(["Linear", "Log"])
# #         self.y_scale_combo.currentTextChanged.connect(lambda: self.plot_updated.emit())
# #         y_scale_layout.addWidget(self.y_scale_combo)
# #         scale_layout.addLayout(y_scale_layout)
# #
# #         scale_group.setLayout(scale_layout)
# #         layout.addWidget(scale_group)
# #
# #         layout.addStretch()
# #
# #     def update_columns(self, columns: List[str]):
# #         """Update available columns"""
# #         self.x_combo.clear()
# #         self.x_combo.addItems(columns)
# #
# #         self.y_list.clear()
# #         self.y_list.addItems(columns)
# #
# #     def get_selected_y_columns(self) -> List[str]:
# #         """Get selected Y columns"""
# #         return [item.text() for item in self.y_list.selectedItems()]
# #
# #     def update_trace_list(self, traces: List[str]):
# #         """Update trace combo box"""
# #         current = self.trace_combo.currentText()
# #         self.trace_combo.clear()
# #         self.trace_combo.addItems(traces)
# #
# #         # Initialize trace configs if needed
# #         for trace in traces:
# #             if trace not in self.trace_configs:
# #                 self.trace_configs[trace] = {
# #                     'color': self.get_default_color(len(self.trace_configs)),
# #                     'line_width': 2,
# #                     'marker_size': 6
# #                 }
# #
# #         # Restore selection if possible
# #         if current in traces:
# #             self.trace_combo.setCurrentText(current)
# #
# #     def get_default_color(self, index: int) -> str:
# #         """Get default color for trace"""
# #         colors = [
# #             '#1e88e5', '#43a047', '#e53935', '#fb8c00',
# #             '#8e24aa', '#00acc1', '#ffb300', '#546e7a'
# #         ]
# #         return colors[index % len(colors)]
# #
# #     def load_trace_config(self, trace_name: str):
# #         """Load configuration for selected trace"""
# #         if trace_name in self.trace_configs:
# #             config = self.trace_configs[trace_name]
# #             self.color_button.setStyleSheet(f"background-color: {config['color']};")
# #             self.line_width_spin.setValue(config['line_width'])
# #             self.marker_size_spin.setValue(config['marker_size'])
# #
# #     def update_trace_config(self):
# #         """Update configuration for current trace"""
# #         trace_name = self.trace_combo.currentText()
# #         if trace_name:
# #             self.trace_configs[trace_name] = {
# #                 'color': self.color_button.styleSheet().split(':')[1].strip(';'),
# #                 'line_width': self.line_width_spin.value(),
# #                 'marker_size': self.marker_size_spin.value()
# #             }
# #             self.plot_updated.emit()
# #
# #     def pick_color(self):
# #         """Open color picker dialog"""
# #         color = QColorDialog.getColor()
# #         if color.isValid():
# #             self.color_button.setStyleSheet(f"background-color: {color.name()};")
# #             self.update_trace_config()
# #
# #     def get_plot_config(self) -> Dict[str, Any]:
# #         """Get complete plot configuration"""
# #         plot_type = ["line", "scatter", "line+scatter"][self.plot_type_group.checkedId()]
# #
# #         return {
# #             'x_column': self.x_combo.currentText(),
# #             'y_columns': self.get_selected_y_columns(),
# #             'plot_type': plot_type,
# #             'trace_configs': self.trace_configs,
# #             'x_label': self.x_label_input.text() or self.x_combo.currentText(),
# #             'y_label': self.y_label_input.text() or "Value",
# #             'title': self.title_input.text() or "Data Plot",
# #             'show_legend': self.legend_checkbox.isChecked(),
# #             'show_grid': self.grid_checkbox.isChecked(),
# #             'font_size': self.font_size_spin.value(),
# #             'x_scale': self.x_scale_combo.currentText().lower(),
# #             'y_scale': self.y_scale_combo.currentText().lower()
# #         }
# #
# #
# # # ============================================================================
# # # Plotly Viewer Widget
# # # ============================================================================
# #
# # class PlotlyViewer(QWebEngineView):
# #     """Widget for displaying Plotly plots"""
# #
# #     def __init__(self):
# #         super().__init__()
# #         self.setMinimumSize(600, 400)
# #
# #     def plot_data(self, df: pd.DataFrame, config: Dict[str, Any]):
# #         """Create and display Plotly plot"""
# #         if not config['x_column'] or not config['y_columns']:
# #             self.setHtml("<h3>Please select X and Y columns</h3>")
# #             return
# #
# #         # Create figure
# #         fig = go.Figure()
# #
# #         # Add traces for each Y column
# #         for y_col in config['y_columns']:
# #             trace_config = config['trace_configs'].get(y_col, {})
# #
# #             if config['plot_type'] == 'line':
# #                 fig.add_trace(go.Scatter(
# #                     x=df[config['x_column']],
# #                     y=df[y_col],
# #                     mode='lines',
# #                     name=y_col,
# #                     line=dict(
# #                         color=trace_config.get('color', '#1e88e5'),
# #                         width=trace_config.get('line_width', 2)
# #                     ),
# #                     hovertemplate=f"<b>{y_col}</b><br>" +
# #                                   f"{config['x_column']}: %{{x}}<br>" +
# #                                   f"{y_col}: %{{y}}<br>" +
# #                                   "<extra></extra>"
# #                 ))
# #             elif config['plot_type'] == 'scatter':
# #                 fig.add_trace(go.Scatter(
# #                     x=df[config['x_column']],
# #                     y=df[y_col],
# #                     mode='markers',
# #                     name=y_col,
# #                     marker=dict(
# #                         color=trace_config.get('color', '#1e88e5'),
# #                         size=trace_config.get('marker_size', 6)
# #                     ),
# #                     hovertemplate=f"<b>{y_col}</b><br>" +
# #                                   f"{config['x_column']}: %{{x}}<br>" +
# #                                   f"{y_col}: %{{y}}<br>" +
# #                                   "<extra></extra>"
# #                 ))
# #             else:  # line+scatter
# #                 fig.add_trace(go.Scatter(
# #                     x=df[config['x_column']],
# #                     y=df[y_col],
# #                     mode='lines+markers',
# #                     name=y_col,
# #                     line=dict(
# #                         color=trace_config.get('color', '#1e88e5'),
# #                         width=trace_config.get('line_width', 2)
# #                     ),
# #                     marker=dict(
# #                         color=trace_config.get('color', '#1e88e5'),
# #                         size=trace_config.get('marker_size', 6)
# #                     ),
# #                     hovertemplate=f"<b>{y_col}</b><br>" +
# #                                   f"{config['x_column']}: %{{x}}<br>" +
# #                                   f"{y_col}: %{{y}}<br>" +
# #                                   "<extra></extra>"
# #                 ))
# #
# #         # Update layout
# #         fig.update_layout(
# #             title=dict(
# #                 text=config['title'],
# #                 font=dict(size=config['font_size'] + 4)
# #             ),
# #             xaxis=dict(
# #                 title=config['x_label'],
# #                 type=config['x_scale'],
# #                 showgrid=config['show_grid'],
# #                 gridcolor='lightgray',
# #                 titlefont=dict(size=config['font_size']),
# #                 tickfont=dict(size=config['font_size'] - 2)
# #             ),
# #             yaxis=dict(
# #                 title=config['y_label'],
# #                 type=config['y_scale'],
# #                 showgrid=config['show_grid'],
# #                 gridcolor='lightgray',
# #                 titlefont=dict(size=config['font_size']),
# #                 tickfont=dict(size=config['font_size'] - 2)
# #             ),
# #             showlegend=config['show_legend'],
# #             legend=dict(
# #                 font=dict(size=config['font_size'] - 2)
# #             ),
# #             hovermode='closest',
# #             template='plotly_white',
# #             margin=dict(l=60, r=30, t=60, b=60)
# #         )
# #
# #         # Convert to HTML
# #         html = fig.to_html(include_plotlyjs='cdn')
# #         self.setHtml(html)
# #
# #
# # # ============================================================================
# # # Main Plotting Window
# # # ============================================================================
# #
# # class QuDAPPlottingWindow(QMainWindow):
# #     """Main window for QuDAP plotting interface"""
# #
# #     def __init__(self):
# #         super().__init__()
# #         self.data_manager = DataManager()
# #         self.init_ui()
# #         self.setup_style()
# #
# #     def init_ui(self):
# #         """Initialize the user interface"""
# #         self.setWindowTitle("QuDAP - Interactive Data Plotter")
# #         self.setGeometry(100, 100, 1400, 900)
# #
# #         # Central widget
# #         central_widget = QWidget()
# #         self.setCentralWidget(central_widget)
# #
# #         # Main layout
# #         main_layout = QVBoxLayout(central_widget)
# #         main_layout.setSpacing(20)
# #         main_layout.setContentsMargins(20, 20, 20, 20)
# #
# #         # Header
# #         header = self.create_header()
# #         main_layout.addWidget(header)
# #
# #         # Content area with splitter
# #         splitter = QSplitter(Qt.Orientation.Horizontal)
# #
# #         # Left panel - File management and data table
# #         left_panel = self.create_left_panel()
# #         splitter.addWidget(left_panel)
# #
# #         # Center panel - Plot viewer
# #         center_panel = self.create_center_panel()
# #         splitter.addWidget(center_panel)
# #
# #         # Right panel - Configuration
# #         right_panel = self.create_right_panel()
# #         splitter.addWidget(right_panel)
# #
# #         # Set splitter sizes
# #         splitter.setSizes([400, 600, 400])
# #
# #         main_layout.addWidget(splitter)
# #
# #         # Status bar
# #         self.status_bar = QStatusBar()
# #         self.setStatusBar(self.status_bar)
# #         self.status_bar.showMessage("Ready")
# #
# #         # Create toolbar
# #         self.create_toolbar()
# #
# #     def create_header(self) -> QWidget:
# #         """Create header section"""
# #         header_card = AnimatedCard()
# #         header_layout = QVBoxLayout(header_card)
# #         header_layout.setContentsMargins(30, 20, 30, 20)
# #
# #         # Title with logo
# #         title_layout = QHBoxLayout()
# #         title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
# #
# #         # Logo
# #         logo_label = QLabel()
# #         pixmap = QPixmap("GUI/Icon/logo.svg")
# #         if not pixmap.isNull():
# #             resized_pixmap = pixmap.scaled(150, 66, Qt.AspectRatioMode.KeepAspectRatio,
# #                                            Qt.TransformationMode.SmoothTransformation)
# #             logo_label.setPixmap(resized_pixmap)
# #         else:
# #             logo_label.setText("QuDAP")
# #             logo_label.setFont(QFont("Arial", 32, QFont.Weight.Bold))
# #             logo_label.setStyleSheet("color: #1e88e5;")
# #
# #         title_layout.addWidget(logo_label)
# #
# #         # Subtitle
# #         subtitle = QLabel("Interactive Data Visualization")
# #         subtitle.setFont(QFont("Arial", 16))
# #         subtitle.setStyleSheet("color: #7f8c8d;")
# #         subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
# #
# #         header_layout.addLayout(title_layout)
# #         header_layout.addWidget(subtitle)
# #
# #         return header_card
# #
# #     def create_left_panel(self) -> QWidget:
# #         """Create left panel with file management"""
# #         panel = AnimatedCard()
# #         layout = QVBoxLayout(panel)
# #         layout.setContentsMargins(20, 20, 20, 20)
# #
# #         # Title
# #         title = QLabel("Data Management")
# #         title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
# #         title.setStyleSheet("color: #2c3e50;")
# #         layout.addWidget(title)
# #
# #         # Drag & drop area
# #         self.drop_area = DragDropArea()
# #         self.drop_area.files_dropped.connect(self.load_files)
# #         layout.addWidget(self.drop_area)
# #
# #         # Loaded files list
# #         files_label = QLabel("Loaded Files:")
# #         files_label.setFont(QFont("Arial", 12))
# #         layout.addWidget(files_label)
# #
# #         self.files_list = QListWidget()
# #         self.files_list.setMaximumHeight(150)
# #         self.files_list.currentItemChanged.connect(self.on_file_selected)
# #         layout.addWidget(self.files_list)
# #
# #         # Data table
# #         table_label = QLabel("Data Preview:")
# #         table_label.setFont(QFont("Arial", 12))
# #         layout.addWidget(table_label)
# #
# #         self.data_table = QTableWidget()
# #         self.data_table.setAlternatingRowColors(True)
# #         self.data_table.setStyleSheet("""
# #             QTableWidget {
# #                 border: 1px solid #ddd;
# #                 border-radius: 5px;
# #             }
# #             QTableWidget::item {
# #                 padding: 5px;
# #             }
# #             QTableWidget::item:selected {
# #                 background-color: #1e88e5;
# #                 color: white;
# #             }
# #         """)
# #         layout.addWidget(self.data_table)
# #
# #         return panel
# #
# #     def create_center_panel(self) -> QWidget:
# #         """Create center panel with plot viewer"""
# #         panel = AnimatedCard()
# #         layout = QVBoxLayout(panel)
# #         layout.setContentsMargins(20, 20, 20, 20)
# #
# #         # Title bar
# #         title_bar = QHBoxLayout()
# #
# #         title = QLabel("Plot Viewer")
# #         title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
# #         title.setStyleSheet("color: #2c3e50;")
# #         title_bar.addWidget(title)
# #
# #         title_bar.addStretch()
# #
# #         # Export button
# #         export_btn = QPushButton("📥 Export")
# #         export_btn.setFont(QFont("Arial", 11))
# #         export_btn.setStyleSheet("""
# #             QPushButton {
# #                 background-color: #28a745;
# #                 color: white;
# #                 padding: 8px 16px;
# #                 border-radius: 5px;
# #                 font-weight: bold;
# #             }
# #             QPushButton:hover {
# #                 background-color: #218838;
# #             }
# #         """)
# #         export_btn.clicked.connect(self.export_plot)
# #         title_bar.addWidget(export_btn)
# #
# #         layout.addLayout(title_bar)
# #
# #         # Plotly viewer
# #         self.plot_viewer = PlotlyViewer()
# #         layout.addWidget(self.plot_viewer)
# #
# #         return panel
# #
# #     def create_right_panel(self) -> QWidget:
# #         """Create right panel with configuration"""
# #         # Use the PlotConfigPanel
# #         self.config_panel = PlotConfigPanel()
# #         self.config_panel.plot_updated.connect(self.update_plot)
# #         return self.config_panel
# #
# #     def create_toolbar(self):
# #         """Create toolbar with quick actions"""
# #         toolbar = QToolBar()
# #         toolbar.setMovable(False)
# #         toolbar.setStyleSheet("""
# #             QToolBar {
# #                 background-color: white;
# #                 border-bottom: 1px solid #e0e0e0;
# #                 padding: 5px;
# #             }
# #         """)
# #         self.addToolBar(toolbar)
# #
# #         # New plot action
# #         new_action = QAction("📊 New Plot", self)
# #         new_action.triggered.connect(self.new_plot)
# #         toolbar.addAction(new_action)
# #
# #         toolbar.addSeparator()
# #
# #         # Clear data action
# #         clear_action = QAction("🗑️ Clear All", self)
# #         clear_action.triggered.connect(self.clear_all)
# #         toolbar.addAction(clear_action)
# #
# #         toolbar.addSeparator()
# #
# #         # Refresh action
# #         refresh_action = QAction("🔄 Refresh", self)
# #         refresh_action.triggered.connect(self.update_plot)
# #         toolbar.addAction(refresh_action)
# #
# #         toolbar.addSeparator()
# #
# #         # Save configuration
# #         save_config_action = QAction("💾 Save Config", self)
# #         save_config_action.triggered.connect(self.save_configuration)
# #         toolbar.addAction(save_config_action)
# #
# #         # Load configuration
# #         load_config_action = QAction("📁 Load Config", self)
# #         load_config_action.triggered.connect(self.load_configuration)
# #         toolbar.addAction(load_config_action)
# #
# #     def setup_style(self):
# #         """Set up application style"""
# #         self.setStyleSheet("""
# #             QMainWindow {
# #                 background-color: #f5f5f5;
# #             }
# #             QGroupBox {
# #                 font-weight: bold;
# #                 border: 2px solid #e0e0e0;
# #                 border-radius: 5px;
# #                 margin-top: 10px;
# #                 padding-top: 10px;
# #             }
# #             QGroupBox::title {
# #                 subcontrol-origin: margin;
# #                 left: 10px;
# #                 padding: 0 5px 0 5px;
# #             }
# #             QComboBox {
# #                 padding: 5px;
# #                 border: 1px solid #ddd;
# #                 border-radius: 5px;
# #             }
# #             QLineEdit {
# #                 padding: 5px;
# #                 border: 1px solid #ddd;
# #                 border-radius: 5px;
# #             }
# #             QSpinBox {
# #                 padding: 5px;
# #                 border: 1px solid #ddd;
# #                 border-radius: 5px;
# #             }
# #         """)
# #
# #     def load_files(self, file_paths: List[str]):
# #         """Load multiple files"""
# #         for file_path in file_paths:
# #             success, message, df = self.data_manager.load_file(file_path)
# #
# #             if success:
# #                 # Add to files list
# #                 item = QListWidgetItem(Path(file_path).name)
# #                 item.setData(Qt.ItemDataRole.UserRole, Path(file_path).stem)
# #                 self.files_list.addItem(item)
# #
# #                 # Show first file
# #                 if self.files_list.count() == 1:
# #                     self.files_list.setCurrentRow(0)
# #
# #                 self.status_bar.showMessage(message, 3000)
# #             else:
# #                 QMessageBox.warning(self, "Load Error", message)
# #
# #     def on_file_selected(self, current, previous):
# #         """Handle file selection"""
# #         if current:
# #             dataset_name = current.data(Qt.ItemDataRole.UserRole)
# #             self.data_manager.current_dataset = dataset_name
# #
# #             # Update data table
# #             df = self.data_manager.get_current_data()
# #             if df is not None:
# #                 self.update_data_table(df)
# #
# #                 # Update column lists
# #                 columns = df.columns.tolist()
# #                 self.config_panel.update_columns(columns)
# #
# #                 # Update plot
# #                 self.update_plot()
# #
# #     def update_data_table(self, df: pd.DataFrame):
# #         """Update data table with dataframe"""
# #         # Limit to first 100 rows for performance
# #         display_df = df.head(100)
# #
# #         self.data_table.setRowCount(len(display_df))
# #         self.data_table.setColumnCount(len(display_df.columns))
# #         self.data_table.setHorizontalHeaderLabels(display_df.columns.tolist())
# #
# #         for row in range(len(display_df)):
# #             for col in range(len(display_df.columns)):
# #                 value = display_df.iloc[row, col]
# #                 item = QTableWidgetItem(str(value))
# #                 self.data_table.setItem(row, col, item)
# #
# #         self.data_table.resizeColumnsToContents()
# #
# #     def update_plot(self):
# #         """Update the plot based on current configuration"""
# #         df = self.data_manager.get_current_data()
# #         if df is None:
# #             return
# #
# #         config = self.config_panel.get_plot_config()
# #
# #         # Update trace list
# #         y_columns = config['y_columns']
# #         if y_columns:
# #             self.config_panel.update_trace_list(y_columns)
# #
# #         # Create plot
# #         self.plot_viewer.plot_data(df, config)
# #
# #         self.status_bar.showMessage("Plot updated", 2000)
# #
# #     def export_plot(self):
# #         """Export current plot"""
# #         file_path, _ = QFileDialog.getSaveFileName(
# #             self,
# #             "Export Plot",
# #             "",
# #             "HTML Files (*.html);;PNG Files (*.png);;SVG Files (*.svg)"
# #         )
# #
# #         if file_path:
# #             df = self.data_manager.get_current_data()
# #             if df is None:
# #                 return
# #
# #             config = self.config_panel.get_plot_config()
# #
# #             # Create figure again for export
# #             fig = self.create_plotly_figure(df, config)
# #
# #             if file_path.endswith('.html'):
# #                 fig.write_html(file_path)
# #             elif file_path.endswith('.png'):
# #                 fig.write_image(file_path)
# #             elif file_path.endswith('.svg'):
# #                 fig.write_image(file_path, format='svg')
# #
# #             self.status_bar.showMessage(f"Plot exported to {file_path}", 3000)
# #
# #     def create_plotly_figure(self, df: pd.DataFrame, config: Dict[str, Any]) -> go.Figure:
# #         """Create Plotly figure for export"""
# #         fig = go.Figure()
# #
# #         for y_col in config['y_columns']:
# #             trace_config = config['trace_configs'].get(y_col, {})
# #
# #             if config['plot_type'] == 'line':
# #                 mode = 'lines'
# #             elif config['plot_type'] == 'scatter':
# #                 mode = 'markers'
# #             else:
# #                 mode = 'lines+markers'
# #
# #             fig.add_trace(go.Scatter(
# #                 x=df[config['x_column']],
# #                 y=df[y_col],
# #                 mode=mode,
# #                 name=y_col,
# #                 line=dict(
# #                     color=trace_config.get('color', '#1e88e5'),
# #                     width=trace_config.get('line_width', 2)
# #                 ) if 'lines' in mode else None,
# #                 marker=dict(
# #                     color=trace_config.get('color', '#1e88e5'),
# #                     size=trace_config.get('marker_size', 6)
# #                 ) if 'markers' in mode else None
# #             ))
# #
# #         fig.update_layout(
# #             title=config['title'],
# #             xaxis_title=config['x_label'],
# #             yaxis_title=config['y_label'],
# #             xaxis_type=config['x_scale'],
# #             yaxis_type=config['y_scale'],
# #             showlegend=config['show_legend'],
# #             template='plotly_white'
# #         )
# #
# #         return fig
# #
# #     def clear_all(self):
# #         """Clear all data and plots"""
# #         reply = QMessageBox.question(
# #             self,
# #             "Clear All",
# #             "Are you sure you want to clear all data and plots?",
# #             QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
# #         )
# #
# #         if reply == QMessageBox.StandardButton.Yes:
# #             self.data_manager.datasets.clear()
# #             self.data_manager.current_dataset = None
# #             self.files_list.clear()
# #             self.data_table.clear()
# #             self.plot_viewer.setHtml("<h3>No data loaded</h3>")
# #             self.status_bar.showMessage("All data cleared", 2000)
# #
# #     def new_plot(self):
# #         """Create new plot window"""
# #         new_window = QuDAPPlottingWindow()
# #         new_window.show()
# #
# #     def save_configuration(self):
# #         """Save current plot configuration"""
# #         file_path, _ = QFileDialog.getSaveFileName(
# #             self,
# #             "Save Configuration",
# #             "",
# #             "JSON Files (*.json)"
# #         )
# #
# #         if file_path:
# #             config = self.config_panel.get_plot_config()
# #             with open(file_path, 'w') as f:
# #                 json.dump(config, f, indent=2)
# #             self.status_bar.showMessage(f"Configuration saved to {file_path}", 3000)
# #
# #     def load_configuration(self):
# #         """Load plot configuration"""
# #         file_path, _ = QFileDialog.getOpenFileName(
# #             self,
# #             "Load Configuration",
# #             "",
# #             "JSON Files (*.json)"
# #         )
# #
# #         if file_path:
# #             try:
# #                 with open(file_path, 'r') as f:
# #                     config = json.load(f)
# #
# #                 # Apply configuration
# #                 self.apply_configuration(config)
# #                 self.status_bar.showMessage(f"Configuration loaded from {file_path}", 3000)
# #
# #             except Exception as e:
# #                 QMessageBox.warning(self, "Load Error", f"Failed to load configuration: {str(e)}")
# #
# #     def apply_configuration(self, config: Dict[str, Any]):
# #         """Apply loaded configuration to UI"""
# #         # Set X column
# #         index = self.config_panel.x_combo.findText(config.get('x_column', ''))
# #         if index >= 0:
# #             self.config_panel.x_combo.setCurrentIndex(index)
# #
# #         # Set Y columns
# #         self.config_panel.y_list.clearSelection()
# #         for y_col in config.get('y_columns', []):
# #             items = self.config_panel.y_list.findItems(y_col, Qt.MatchFlag.MatchExactly)
# #             for item in items:
# #                 item.setSelected(True)
# #
# #         # Set plot type
# #         plot_type = config.get('plot_type', 'line')
# #         if plot_type == 'line':
# #             self.config_panel.line_radio.setChecked(True)
# #         elif plot_type == 'scatter':
# #             self.config_panel.scatter_radio.setChecked(True)
# #         else:
# #             self.config_panel.line_scatter_radio.setChecked(True)
# #
# #         # Set labels
# #         self.config_panel.x_label_input.setText(config.get('x_label', ''))
# #         self.config_panel.y_label_input.setText(config.get('y_label', ''))
# #         self.config_panel.title_input.setText(config.get('title', ''))
# #
# #         # Set display options
# #         self.config_panel.legend_checkbox.setChecked(config.get('show_legend', True))
# #         self.config_panel.grid_checkbox.setChecked(config.get('show_grid', True))
# #         self.config_panel.font_size_spin.setValue(config.get('font_size', 12))
# #
# #         # Set scales
# #         self.config_panel.x_scale_combo.setCurrentText(config.get('x_scale', 'linear').title())
# #         self.config_panel.y_scale_combo.setCurrentText(config.get('y_scale', 'linear').title())
# #
# #         # Set trace configurations
# #         if 'trace_configs' in config:
# #             self.config_panel.trace_configs = config['trace_configs']
# #
# #         # Update plot
# #         self.update_plot()
# #
# #
# # # ============================================================================
# # # Main Application
# # # ============================================================================
# #
# # def main():
# #     """Main function to run the application"""
# #     app = QApplication(sys.argv)
# #     app.setStyle("Fusion")
# #
# #     # Set application icon and metadata
# #     app.setApplicationName("QuDAP Plotter")
# #     app.setOrganizationName("Auburn University")
# #
# #     # Create and show main window
# #     window = QuDAPPlottingWindow()
# #     window.show()
# #
# #     sys.exit(app.exec())
# #
# #
# # if __name__ == "__main__":
# #     main()
#
# from PyQt6.QtWidgets import (
#     QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QPushButton,
#     QGroupBox, QTreeWidget, QTreeWidgetItem, QDialog, QDialogButtonBox,
#     QHeaderView, QFileDialog, QMessageBox, QScrollArea, QSizePolicy,
#     QMenu, QWidgetAction, QApplication, QTableView, QRadioButton, QButtonGroup,
#     QLineEdit, QFormLayout
# )
# from PyQt6.QtCore import Qt, QPoint
# from PyQt6.QtGui import QFont, QBrush, QColor, QStandardItemModel, QStandardItem
# import os
# import numpy as np
# import traceback
# import csv
# import pandas as pd
# from pathlib import Path
#
# try:
#     from GUI.VSM.qd import Loadfile
#     import misc.dragdropwidget as ddw
# except ImportError:
#     from QuDAP.GUI.VSM.qd import Loadfile
#     import QuDAP.misc.dragdropwidget as ddw
#
#
# class ExportOptionsDialog(QDialog):
#     """Dialog for selecting export format"""
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Export Options")
#         self.setModal(True)
#         self.selected_format = None
#         self.init_ui()
#
#     def init_ui(self):
#         layout = QVBoxLayout(self)
#
#         # Title
#         title = QLabel("Select Export Format")
#         title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
#         title.setStyleSheet("color: #2c3e50; padding: 10px;")
#         layout.addWidget(title)
#
#         # Format selection group
#         format_group = QGroupBox("Export Format")
#         format_layout = QVBoxLayout()
#
#         self.format_button_group = QButtonGroup()
#
#         self.csv_radio = QRadioButton("CSV (.csv)")
#         self.csv_radio.setChecked(True)
#         self.format_button_group.addButton(self.csv_radio, 0)
#
#         self.xlsx_radio = QRadioButton("Excel (.xlsx)")
#         self.format_button_group.addButton(self.xlsx_radio, 1)
#
#         format_layout.addWidget(self.csv_radio)
#         format_layout.addWidget(self.xlsx_radio)
#         format_group.setLayout(format_layout)
#         layout.addWidget(format_group)
#
#         # Buttons
#         button_box = QDialogButtonBox(
#             QDialogButtonBox.StandardButton.Ok |
#             QDialogButtonBox.StandardButton.Cancel
#         )
#         button_box.accepted.connect(self.accept)
#         button_box.rejected.connect(self.reject)
#         layout.addWidget(button_box)
#
#         self.setStyleSheet("""
#             QDialog {
#                 background-color: white;
#             }
#             QGroupBox {
#                 font-weight: bold;
#                 border: 2px solid #e0e0e0;
#                 border-radius: 5px;
#                 margin-top: 10px;
#                 padding: 15px;
#             }
#             QGroupBox::title {
#                 subcontrol-origin: margin;
#                 left: 10px;
#                 padding: 0 5px;
#             }
#             QRadioButton {
#                 padding: 5px;
#                 font-size: 12px;
#             }
#         """)
#
#     def get_selected_format(self):
#         """Return selected format"""
#         if self.csv_radio.isChecked():
#             return 'csv'
#         elif self.xlsx_radio.isChecked():
#             return 'xlsx'
#         return 'csv'
#
#
# class BatchExportOptionsDialog(QDialog):
#     """Dialog for batch export options"""
#
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setWindowTitle("Batch Export Options")
#         self.setModal(True)
#         self.init_ui()
#
#     def init_ui(self):
#         layout = QVBoxLayout(self)
#
#         # Title
#         title = QLabel("Batch Export Configuration")
#         title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
#         title.setStyleSheet("color: #2c3e50; padding: 10px;")
#         layout.addWidget(title)
#
#         # Export mode selection
#         mode_group = QGroupBox("Export Mode")
#         mode_layout = QVBoxLayout()
#
#         self.mode_button_group = QButtonGroup()
#
#         self.separate_radio = QRadioButton("Separate Files (one file per input)")
#         self.separate_radio.setChecked(True)
#         self.mode_button_group.addButton(self.separate_radio, 0)
#
#         self.combined_radio = QRadioButton("Single Combined File")
#         self.mode_button_group.addButton(self.combined_radio, 1)
#
#         mode_layout.addWidget(self.separate_radio)
#         mode_layout.addWidget(self.combined_radio)
#         mode_group.setLayout(mode_layout)
#         layout.addWidget(mode_group)
#
#         # Format selection
#         format_group = QGroupBox("Export Format")
#         format_layout = QVBoxLayout()
#
#         self.format_button_group = QButtonGroup()
#
#         self.csv_radio = QRadioButton("CSV (.csv)")
#         self.csv_radio.setChecked(True)
#         self.format_button_group.addButton(self.csv_radio, 0)
#
#         self.xlsx_radio = QRadioButton("Excel (.xlsx)")
#         self.format_button_group.addButton(self.xlsx_radio, 1)
#
#         format_layout.addWidget(self.csv_radio)
#         format_layout.addWidget(self.xlsx_radio)
#         format_group.setLayout(format_layout)
#         layout.addWidget(format_group)
#
#         # File name input (only for combined mode)
#         self.filename_group = QGroupBox("Combined File Name")
#         filename_layout = QFormLayout()
#
#         self.filename_input = QLineEdit()
#         self.filename_input.setPlaceholderText("combined_data")
#         self.filename_input.setText("combined_data")
#         filename_layout.addRow("File Name:", self.filename_input)
#
#         self.filename_group.setLayout(filename_layout)
#         self.filename_group.setEnabled(False)
#         layout.addWidget(self.filename_group)
#
#         # Connect signals
#         self.combined_radio.toggled.connect(self.on_mode_changed)
#
#         # Buttons
#         button_box = QDialogButtonBox(
#             QDialogButtonBox.StandardButton.Ok |
#             QDialogButtonBox.StandardButton.Cancel
#         )
#         button_box.accepted.connect(self.accept)
#         button_box.rejected.connect(self.reject)
#         layout.addWidget(button_box)
#
#         self.setStyleSheet("""
#             QDialog {
#                 background-color: white;
#             }
#             QGroupBox {
#                 font-weight: bold;
#                 border: 2px solid #e0e0e0;
#                 border-radius: 5px;
#                 margin-top: 10px;
#                 padding: 15px;
#             }
#             QGroupBox::title {
#                 subcontrol-origin: margin;
#                 left: 10px;
#                 padding: 0 5px;
#             }
#             QRadioButton {
#                 padding: 5px;
#                 font-size: 12px;
#             }
#             QLineEdit {
#                 padding: 5px;
#                 border: 1px solid #ddd;
#                 border-radius: 3px;
#             }
#         """)
#
#     def on_mode_changed(self, checked):
#         """Enable/disable filename input based on mode"""
#         self.filename_group.setEnabled(checked)
#
#     def get_export_mode(self):
#         """Return 'separate' or 'combined'"""
#         return 'combined' if self.combined_radio.isChecked() else 'separate'
#
#     def get_export_format(self):
#         """Return 'csv' or 'xlsx'"""
#         return 'xlsx' if self.xlsx_radio.isChecked() else 'csv'
#
#     def get_filename(self):
#         """Return the custom filename"""
#         return self.filename_input.text().strip() or "combined_data"
#
#
# class FileExport(QMainWindow):
#     def __init__(self, label):
#         super().__init__()
#         self.process_type_label = label
#         # Selection tracking variables for ordered selection
#         self.x_column = None  # Store X column index
#         self.y_columns = []  # Store Y column indices in order
#         self._in_context_menu = False  # Add flag here
#
#         try:
#             self.isInit = False
#             self.file_in_list = []
#             self.init_ui()
#         except Exception as e:
#             QMessageBox.warning(self, "Error", str(e))
#             return
#
#     def init_ui(self):
#         try:
#             if self.isInit == False:
#                 self.isInit = True
#                 self.rstpage()
#
#                 # Load stylesheets (adjust paths as needed)
#                 try:
#                     with open("GUI/VSM/QButtonWidget.qss", "r") as file:
#                         self.Browse_Button_stylesheet = file.read()
#                 except:
#                     self.Browse_Button_stylesheet = ""
#
#                 titlefont = QFont("Arial", 20)
#                 self.font = QFont("Arial", 12)
#                 self.setStyleSheet("background-color: white;")
#
#                 try:
#                     with open("GUI/QSS/QScrollbar.qss", "r") as file:
#                         self.scrollbar_stylesheet = file.read()
#                 except:
#                     self.scrollbar_stylesheet = ""
#
#                 # Create a QScrollArea
#                 self.scroll_area = QScrollArea()
#                 self.scroll_area.setWidgetResizable(True)
#                 self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
#                 self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
#                 self.scroll_area.setStyleSheet(self.scrollbar_stylesheet)
#
#                 # Create a widget to hold the main layout
#                 self.content_widget = QWidget()
#                 self.scroll_area.setWidget(self.content_widget)
#
#                 # Set the content widget to expand
#                 self.main_layout = QVBoxLayout(self.content_widget)
#                 self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
#                 self.main_layout.setContentsMargins(20, 20, 20, 20)
#                 self.content_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
#
#                 # Button stylesheet
#                 try:
#                     with open("GUI/QSS/QButtonWidget.qss", "r") as file:
#                         self.Button_stylesheet = file.read()
#                 except:
#                     self.Button_stylesheet = """
#                         QPushButton {
#                             background-color: #1e88e5;
#                             color: white;
#                             padding: 10px 20px;
#                             border-radius: 5px;
#                             font-weight: bold;
#                         }
#                         QPushButton:hover {
#                             background-color: #1976d2;
#                         }
#                     """
#
#                 self.label = QLabel(f"{self.process_type_label} Data Extraction")
#                 self.label.setFont(titlefont)
#                 self.label.setStyleSheet("QLabel{background-color: white;}")
#
#                 # File Upload Section
#                 self.fileUpload_layout = QHBoxLayout()
#                 self.drag_drop_layout = QVBoxLayout()
#                 self.file_selection_group_box = QGroupBox("Upload Directory")
#                 self.file_view_group_box = QGroupBox("View Files")
#                 self.file_selection_group_box.setStyleSheet("""
#                     QGroupBox {
#                         max-width: 600px;
#                         max-height: 230px;
#                     }
#                 """)
#                 self.file_view_group_box.setStyleSheet("""
#                     QGroupBox {
#                         max-width: 650px;
#                         max-height: 230px;
#                     }
#                 """)
#
#                 self.file_selection_display_label = QLabel('Please Upload Files or Directory')
#                 self.file_selection_display_label.setStyleSheet("""
#                     color: white;
#                     font-size: 12px;
#                     background-color: #f38d76;
#                     border-radius: 5px;
#                     padding: 5px;
#                 """)
#
#                 # Create drag-drop widget
#                 try:
#                     self.drag_drop_widget = ddw.DragDropWidget(self)
#                     self.selected_file_type = self.drag_drop_widget.get_selected_file_type()
#                 except:
#                     # Fallback if drag-drop widget not available
#                     self.drag_drop_widget = QWidget()
#                     browse_btn = QPushButton("Browse Files")
#                     browse_btn.clicked.connect(self.browse_files_fallback)
#                     fallback_layout = QVBoxLayout(self.drag_drop_widget)
#                     fallback_layout.addWidget(browse_btn)
#
#                 self.drag_drop_layout.addWidget(self.drag_drop_widget, 4)
#                 self.drag_drop_layout.addWidget(self.file_selection_display_label, 1,
#                                                 alignment=Qt.AlignmentFlag.AlignCenter)
#                 self.file_selection_group_box.setLayout(self.drag_drop_layout)
#
#                 # Create the file browser area
#                 self.file_tree = QTreeWidget()
#                 self.file_tree_layout = QHBoxLayout()
#                 self.file_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
#                 self.file_tree.customContextMenuRequested.connect(self.open_context_menu)
#                 self.file_tree.setHeaderLabels(["Name", "Type", "Size"])
#                 self.file_tree.setSelectionMode(QTreeWidget.SelectionMode.ExtendedSelection)
#                 self.file_tree_layout.addWidget(self.file_tree)
#
#                 try:
#                     with open("GUI/SHG/QTreeWidget.qss", "r") as file:
#                         self.QTree_stylesheet = file.read()
#                     self.file_tree.setStyleSheet(self.QTree_stylesheet)
#                 except:
#                     pass
#
#                 self.file_view_group_box.setLayout(self.file_tree_layout)
#                 self.fileUpload_layout.addWidget(self.file_selection_group_box, 1)
#                 self.fileUpload_layout.addWidget(self.file_view_group_box, 1)
#                 self.fileupload_container = QWidget(self)
#                 self.fileupload_container.setLayout(self.fileUpload_layout)
#                 self.fileupload_container.setFixedSize(1150, 260)
#
#                 # Selection Instruction
#                 self.instruction_label = QLabel(
#                     "Column Selection: Click = Set as X (blue) | Ctrl+Click = Add as Y (red) | Shift+Click = Remove")
#                 self.instruction_label.setStyleSheet("""
#                     QLabel {
#                         color: #666;
#                         padding: 8px;
#                         background-color: #f0f0f0;
#                         border-radius: 5px;
#                         font-weight: bold;
#                     }
#                 """)
#
#                 # Selection display
#                 self.selection_display = QLabel("X: None | Y: None")
#                 self.selection_display.setStyleSheet("""
#                     QLabel {
#                         padding: 8px;
#                         background-color: #e8f4ff;
#                         border: 1px solid #ccc;
#                         border-radius: 5px;
#                         font-weight: bold;
#                     }
#                 """)
#
#                 # Clear button
#                 self.clear_selection_btn = QPushButton("Clear All Selections")
#                 self.clear_selection_btn.clicked.connect(self.clear_column_selection)
#                 self.clear_selection_btn.setStyleSheet("""
#                     QPushButton {
#                         background-color: #95a5a6;
#                         color: white;
#                         padding: 5px 15px;
#                         border-radius: 3px;
#                         font-weight: bold;
#                     }
#                     QPushButton:hover {
#                         background-color: #7f8c8d;
#                     }
#                 """)
#
#                 selection_info_layout = QHBoxLayout()
#                 selection_info_layout.addWidget(self.instruction_label)
#                 selection_info_layout.addWidget(self.selection_display)
#                 selection_info_layout.addWidget(self.clear_selection_btn)
#                 selection_info_layout.addStretch()
#
#                 # Table Widget with QTableView
#                 self.table_layout = QVBoxLayout()
#                 self.table_view = QTableView()
#                 self.table_model = QStandardItemModel()
#                 self.table_view.setModel(self.table_model)
#                 self.table_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectColumns)
#                 self.table_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
#                 self.table_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
#
#                 header = self.table_view.horizontalHeader()
#                 header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
#                 self.table_view.horizontalHeader().sectionClicked.connect(self.on_header_clicked)
#                 self.table_view.setFixedSize(1150, 320)
#                 self.table_layout.addWidget(self.table_view)
#
#                 # Buttons
#                 self.btn_layout = QHBoxLayout()
#                 self.rst_btn = QPushButton("Reset")
#                 self.rst_btn.clicked.connect(self.rstpage)
#                 self.export_btn = QPushButton("Export")
#                 self.export_btn.clicked.connect(self.export_selected_column_data)
#                 self.export_btn.setToolTip("Export single file with selected columns")
#                 self.export_all_btn = QPushButton("Export All")
#                 self.export_all_btn.clicked.connect(self.export_selected_column_alldata)
#                 self.export_all_btn.setToolTip("Batch exporting files")
#
#                 self.rst_btn.setStyleSheet(self.Button_stylesheet)
#                 self.export_btn.setStyleSheet(self.Button_stylesheet)
#                 self.export_all_btn.setStyleSheet(self.Button_stylesheet)
#
#                 self.btn_layout.addStretch(2)
#                 self.btn_layout.addWidget(self.rst_btn)
#                 self.btn_layout.addWidget(self.export_btn)
#                 self.btn_layout.addWidget(self.export_all_btn)
#
#                 # Main Layout Assembly
#                 self.main_layout.addWidget(self.label, alignment=Qt.AlignmentFlag.AlignTop)
#                 self.main_layout.addWidget(self.fileupload_container)
#                 self.main_layout.addLayout(selection_info_layout)
#                 self.main_layout.addLayout(self.table_layout)
#                 self.main_layout.addLayout(self.btn_layout)
#                 self.main_layout.addStretch(1)
#
#                 self.setCentralWidget(self.scroll_area)
#                 self.content_widget.adjustSize()
#
#         except Exception as e:
#             QMessageBox.warning(self, "Error", f"Initialization error: {str(e)}")
#             return
#
#     def browse_files_fallback(self):
#         """Fallback file browser if drag-drop widget not available"""
#         files, _ = QFileDialog.getOpenFileNames(
#             self,
#             "Select Data Files",
#             "",
#             "Data Files (*.csv *.txt *.dat *.xlsx *.xls);;All Files (*.*)"
#         )
#         if files:
#             self.display_multiple_files(files)
#
#     def display_dataframe(self, df):
#         """Display a pandas DataFrame in the table view"""
#         try:
#             self.table_model.clear()
#
#             # Set headers
#             headers = list(df.columns)
#             self.table_model.setHorizontalHeaderLabels(headers)
#
#
#             # Store original headers
#             self.original_headers = {}
#             for col, header in enumerate(headers):
#                 self.original_headers[col] = str(header)
#
#             # Set row and column count
#             self.table_model.setRowCount(len(df))
#             self.table_model.setColumnCount(len(df.columns))
#
#             # Fill model with data
#             for row in range(len(df)):
#                 for col in range(len(df.columns)):
#                     value = df.iloc[row, col]
#
#                     # Handle different data types
#                     if pd.isna(value):
#                         item_text = ""
#                     elif isinstance(value, (int, float)):
#                         if isinstance(value, float):
#                             item_text = f"{value:.6g}"
#                         else:
#                             item_text = str(value)
#                     else:
#                         item_text = str(value)
#
#                     item = QStandardItem(item_text)
#                     self.table_model.setItem(row, col, item)
#
#             # Adjust column widths
#             self.table_view.resizeColumnsToContents()
#
#             # Limit column width for better display
#             for col in range(self.table_model.columnCount()):
#                 if self.table_view.columnWidth(col) > 200:
#                     self.table_view.setColumnWidth(col, 200)
#
#         except Exception as e:
#             raise Exception(f"Error displaying data: {str(e)}")
#
#     def on_header_clicked(self, logical_index):
#         """Handle header clicks with modifiers for column selection"""
#         modifiers = QApplication.keyboardModifiers()
#
#         if modifiers == Qt.KeyboardModifier.ControlModifier:
#             # Ctrl+Click: Add as Y column
#             if logical_index not in self.y_columns:
#                 if logical_index == self.x_column:
#                     self.x_column = None
#                 self.y_columns.append(logical_index)
#
#         elif modifiers == Qt.KeyboardModifier.ShiftModifier:
#             # Shift+Click: Remove from selection
#             if logical_index == self.x_column:
#                 self.x_column = None
#             elif logical_index in self.y_columns:
#                 self.y_columns.remove(logical_index)
#
#         else:
#             # Normal click: Set as X column
#             if logical_index in self.y_columns:
#                 self.y_columns.remove(logical_index)
#             self.x_column = logical_index
#
#         self.update_column_colors()
#         self.update_selection_display()
#
#     def clear_column_selection(self):
#         """Clear all column selections"""
#         self.x_column = None
#         self.y_columns = []
#         self.update_column_colors()
#         self.update_selection_display()
#
#     def update_column_colors(self):
#         """Update table view colors based on selection"""
#         if not hasattr(self, 'original_headers'):
#             self.original_headers = {}
#             for col in range(self.table_model.columnCount()):
#                 header_item = self.table_model.horizontalHeaderItem(col)
#                 if header_item:
#                     self.original_headers[col] = header_item.text()
#
#         # Reset all columns to default
#         for col in range(self.table_model.columnCount()):
#             # Reset cells
#             for row in range(self.table_model.rowCount()):
#                 item = self.table_model.item(row, col)
#                 if item:
#                     item.setBackground(QBrush(Qt.GlobalColor.white))
#
#             # Reset header
#             header_text = self.original_headers.get(col, f"Column {col}")
#             self.table_model.setHorizontalHeaderItem(col, QStandardItem(header_text))
#
#         # Color X column (blue)
#         if self.x_column is not None:
#             for row in range(self.table_model.rowCount()):
#                 item = self.table_model.item(row, self.x_column)
#                 if item:
#                     item.setBackground(QBrush(QColor(52, 152, 219, 80)))
#
#             # Update header
#             if self.x_column in self.original_headers:
#                 header_item = QStandardItem(f"[X] {self.original_headers[self.x_column]}")
#                 header_item.setBackground(QBrush(QColor(52, 152, 219)))
#                 header_item.setForeground(QBrush(Qt.GlobalColor.white))
#                 self.table_model.setHorizontalHeaderItem(self.x_column, header_item)
#
#         # Color Y columns (red with varying intensity)
#         for idx, col in enumerate(self.y_columns):
#             alpha = 60 + (idx * 30) if idx < 5 else 200
#
#             for row in range(self.table_model.rowCount()):
#                 item = self.table_model.item(row, col)
#                 if item:
#                     item.setBackground(QBrush(QColor(231, 76, 60, alpha)))
#
#             # Update header
#             if col in self.original_headers:
#                 header_item = QStandardItem(f"[Y{idx + 1}] {self.original_headers[col]}")
#                 header_item.setBackground(QBrush(QColor(231, 76, 60)))
#                 header_item.setForeground(QBrush(Qt.GlobalColor.white))
#                 self.table_model.setHorizontalHeaderItem(col, header_item)
#
#     def update_selection_display(self):
#         """Update the selection display label"""
#         x_text = "X: None"
#         if self.x_column is not None and self.x_column in self.original_headers:
#             x_text = f"X: {self.original_headers[self.x_column]}"
#
#         y_text = "Y: None"
#         if self.y_columns:
#             y_headers = []
#             for col in self.y_columns:
#                 if col in self.original_headers:
#                     y_headers.append(self.original_headers[col])
#             if y_headers:
#                 y_text = f"Y: {', '.join(y_headers)}"
#
#         self.selection_display.setText(f"{x_text} | {y_text}")
#
#     def display_files(self, folder_path, selected_file_type):
#         """Display files from a folder using QTreeView"""
#         self.file_tree_model.removeRows(0, self.file_tree_model.rowCount())
#         self.folder = folder_path
#         self.file_selection_display_label.setText("Directory Successfully Uploaded")
#         self.file_selection_display_label.setStyleSheet("""
#                color: #4b6172;
#                font-size: 12px;
#                background-color: #DfE7Ef;
#                border-radius: 5px;
#                padding: 5px;
#            """)
#
#         supported_extensions = [selected_file_type]
#
#         for root, dirs, files in os.walk(folder_path):
#             for file_name in files:
#                 file_ext = os.path.splitext(file_name)[1].lower()
#                 if file_ext in supported_extensions:
#                     file_path = os.path.join(root, file_name)
#                     self.file_in_list.append(file_path)
#
#                     file_info = os.stat(file_path)
#                     file_size_kb = file_info.st_size / 1024
#                     if file_size_kb < 1024:
#                         file_size_str = f"{file_size_kb:.2f} KB"
#                     elif file_size_kb < 1024 ** 2:
#                         file_size_mb = file_size_kb / 1024
#                         file_size_str = f"{file_size_mb:.2f} MB"
#                     else:
#                         file_size_gb = file_size_kb / (1024 ** 2)
#                         file_size_str = f"{file_size_gb:.2f} GB"
#
#                     file_type_map = {
#                         '.dat': 'application/dat',
#                         '.csv': 'CSV',
#                         '.xlsx': 'Excel',
#                         '.xls': 'Excel',
#                         '.txt': 'Text'
#                     }
#                     file_type = file_type_map.get(file_ext, 'other')
#
#                     # Create row items
#                     name_item = QStandardItem(file_name)
#                     name_item.setData(file_path, Qt.ItemDataRole.UserRole)  # Store full path
#                     name_item.setEditable(False)
#
#                     type_item = QStandardItem(file_type)
#                     type_item.setEditable(False)
#
#                     size_item = QStandardItem(file_size_str)
#                     size_item.setEditable(False)
#
#                     self.file_tree_model.appendRow([name_item, type_item, size_item])
#
#     def display_multiple_files(self, file_paths, selected_file_type):
#         """Display multiple files using QTreeView"""
#         # Get existing files
#         existing_files = set()
#         for row in range(self.file_tree_model.rowCount()):
#             name_item = self.file_tree_model.item(row, 0)
#             if name_item:
#                 existing_files.add(name_item.text())
#
#         supported_extensions = [selected_file_type]
#
#         for file_path in file_paths:
#             file_name = os.path.basename(file_path)
#             file_ext = os.path.splitext(file_name)[1].lower()
#
#             if file_ext not in supported_extensions:
#                 continue
#
#             if file_name not in existing_files:
#                 self.file_in_list.append(file_path)
#
#                 file_info = os.stat(file_path)
#                 file_size_kb = file_info.st_size / 1024
#                 if file_size_kb < 1024:
#                     file_size_str = f"{file_size_kb:.2f} KB"
#                 elif file_size_kb < 1024 ** 2:
#                     file_size_mb = file_size_kb / 1024
#                     file_size_str = f"{file_size_mb:.2f} MB"
#                 else:
#                     file_size_gb = file_size_kb / (1024 ** 2)
#                     file_size_str = f"{file_size_gb:.2f} GB"
#
#                 file_type_map = {
#                     '.dat': 'application/dat',
#                     '.csv': 'CSV',
#                     '.xlsx': 'Excel',
#                     '.xls': 'Excel',
#                     '.txt': 'Text'
#                 }
#                 file_type = file_type_map.get(file_ext, 'other')
#
#                 # Create row items
#                 name_item = QStandardItem(file_name)
#                 name_item.setData(file_path, Qt.ItemDataRole.UserRole)
#                 name_item.setEditable(False)
#
#                 type_item = QStandardItem(file_type)
#                 type_item.setEditable(False)
#
#                 size_item = QStandardItem(file_size_str)
#                 size_item.setEditable(False)
#
#                 self.file_tree_model.appendRow([name_item, type_item, size_item])
#
#         self.file_selection_display_label.setText(
#             f"{self.file_tree_model.rowCount()} Files Successfully Uploaded")
#         self.file_selection_display_label.setStyleSheet("""
#             color: #4b6172;
#             font-size: 12px;
#             background-color: #DfE7Ef;
#             border-radius: 5px;
#             padding: 5px;
#         """)
#
#     # def on_item_selection_changed(self):
#     #     """Handle file selection in tree"""
#     #     self.clear_column_selection()
#     #     selected_items = self.file_tree.selectedItems()
#     #     if selected_items:
#     #         selected_item = selected_items[0]
#     #         self.file_path = selected_item.toolTip(0)
#     #         self.open_file_in_table(self.file_path)
#     def on_left_click(self, item):
#         """Handle left click on tree item"""
#         # Check if this is a single selection (not Ctrl+Click or Shift+Click)
#         modifiers = QApplication.keyboardModifiers()
#
#         # If no modifiers, load the file
#         if modifiers == Qt.KeyboardModifier.NoModifier:
#             self.clear_column_selection()
#             file_path = item.data(Qt.ItemDataRole.UserRole)
#             if file_path:
#                 self.file_path = file_path
#                 self.open_file_in_table(self.file_path)
#         else:
#             # Multi-select mode - clear table
#             selected_indexes = self.file_tree.selectedIndexes()
#             # Count unique rows (each row has 3 columns)
#             selected_rows = set(index.row() for index in selected_indexes)
#
#             if len(selected_rows) != 1:
#                 if hasattr(self, 'file_path'):
#                     delattr(self, 'file_path')
#                 self.table_model.clear()
#                 self.table_model.setRowCount(0)
#                 self.table_model.setColumnCount(0)
#                 self.clear_column_selection()
#
#     def detect_headers(self, df, file_path):
#         """
#         Detect if DataFrame has headers or if first row is data
#         Returns: (has_headers: bool, df: DataFrame)
#         """
#         try:
#             # Check if first row looks like numeric data
#             first_row = df.iloc[0]
#             numeric_count = sum(pd.to_numeric(first_row, errors='coerce').notna())
#
#             # If most of first row is numeric and column names are also numeric-like,
#             # likely no headers
#             col_numeric = sum(pd.to_numeric(df.columns, errors='coerce').notna())
#
#             if numeric_count > len(first_row) * 0.7 and col_numeric > len(df.columns) * 0.5:
#                 # Likely no headers - first row is data
#                 return False, df
#
#             return True, df
#
#         except Exception as e:
#             # Default to assuming headers exist
#             return True, df
#
#     def open_file_in_table(self, file_path):
#         """Load and display file data in table view"""
#         try:
#             df = None
#             has_headers = True
#             file_ext = Path(file_path).suffix.lower()
#
#             # Load file based on extension
#             if file_ext == '.dat':
#                 try:
#                     loaded_file = Loadfile(file_path)
#                     headers = loaded_file.column_headers
#                     data = loaded_file.data
#                     df = pd.DataFrame(data, columns=headers)
#                     has_headers = True
#                 except Exception as e:
#                     raise Exception(f"Error loading .dat file: {str(e)}")
#
#             elif file_ext == '.csv':
#                 # Try with header first
#                 df = pd.read_csv(file_path)
#                 has_headers, df = self.detect_headers(df, file_path)
#
#                 if not has_headers:
#                     # Reload without header
#                     df = pd.read_csv(file_path, header=None)
#                     df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]
#
#             elif file_ext == '.xlsx':
#                 df = pd.read_excel(file_path, engine='openpyxl')
#                 has_headers, df = self.detect_headers(df, file_path)
#
#                 if not has_headers:
#                     df = pd.read_excel(file_path, engine='openpyxl', header=None)
#                     df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]
#
#             elif file_ext == '.xls':
#                 df = pd.read_excel(file_path)
#                 has_headers, df = self.detect_headers(df, file_path)
#
#                 if not has_headers:
#                     df = pd.read_excel(file_path, header=None)
#                     df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]
#
#             elif file_ext == '.txt':
#                 # Try different separators
#                 df = None
#                 for sep in ['\t', ',', None]:
#                     try:
#                         if sep is None:
#                             df = pd.read_csv(file_path, delim_whitespace=True)
#                         else:
#                             df = pd.read_csv(file_path, sep=sep)
#                         break
#                     except:
#                         continue
#
#                 if df is None:
#                     raise Exception("Unable to parse .txt file format")
#
#                 has_headers, df = self.detect_headers(df, file_path)
#
#                 if not has_headers:
#                     # Reload without header
#                     if sep is None:
#                         df = pd.read_csv(file_path, delim_whitespace=True, header=None)
#                     else:
#                         df = pd.read_csv(file_path, sep=sep, header=None)
#                     df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]
#
#             else:
#                 raise Exception(f"Unsupported file type: {file_ext}")
#
#             # Display the dataframe
#             if df is not None:
#                 self.display_dataframe(df)
#
#                 # Show info message if no headers detected
#                 if not has_headers:
#                     self.file_selection_display_label.setText(
#                         f"File loaded (no headers detected - using Column_1, Column_2, etc.)")
#                     self.file_selection_display_label.setStyleSheet("""
#                         color: #856404;
#                         font-size: 12px;
#                         background-color: #fff3cd;
#                         border-radius: 5px;
#                         padding: 5px;
#                     """)
#
#         except Exception as e:
#             tb_str = traceback.format_exc()
#             QMessageBox.warning(self, "Error Loading File", f"{str(e)}\n\n{tb_str}")
#
#     def export_selected_column_data(self):
#         """Export data with X column first, then Y columns in order"""
#         try:
#             if self.x_column is None:
#                 QMessageBox.warning(self, "No X Column", "Please select an X column first (normal click on header)")
#                 return
#
#             if not self.y_columns:
#                 QMessageBox.warning(self, "No Y Columns",
#                                     "Please select at least one Y column (Ctrl+Click on headers)")
#                 return
#
#             # Show export options dialog
#             options_dialog = ExportOptionsDialog(self)
#             if options_dialog.exec() != QDialog.DialogCode.Accepted:
#                 return
#
#             export_format = options_dialog.get_selected_format()
#
#             # Prepare data with X first, then Y columns in order
#             column_data = {}
#
#             # Add X column
#             x_header = self.original_headers.get(self.x_column, f"Column {self.x_column}")
#             x_values = []
#             for row in range(self.table_model.rowCount()):
#                 item = self.table_model.item(row, self.x_column)
#                 x_values.append(item.text() if item else "")
#             column_data[x_header] = x_values
#
#             # Add Y columns in the order they were selected
#             for col in self.y_columns:
#                 column_header = self.original_headers.get(col, f"Column {col}")
#                 column_values = []
#                 for row in range(self.table_model.rowCount()):
#                     item = self.table_model.item(row, col)
#                     column_values.append(item.text() if item else "")
#                 column_data[column_header] = column_values
#
#             # Get file name
#             if hasattr(self, 'file_path'):
#                 file_name = Path(self.file_path).stem
#                 folder_name = str(Path(self.file_path).parent)
#             else:
#                 file_name = "exported_data"
#                 folder_name = os.getcwd()
#
#             # File dialog with appropriate filter
#             if export_format == 'csv':
#                 file_filter = "CSV Files (*.csv)"
#                 default_ext = ".csv"
#             else:
#                 file_filter = "Excel Files (*.xlsx)"
#                 default_ext = ".xlsx"
#
#             save_path, _ = QFileDialog.getSaveFileName(
#                 self,
#                 "Save Export File",
#                 os.path.join(folder_name, f"{file_name}{default_ext}"),
#                 file_filter
#             )
#
#             if save_path:
#                 # Ensure correct extension
#                 if not save_path.endswith(default_ext):
#                     save_path += default_ext
#
#                 # Export based on format
#                 if export_format == 'csv':
#                     self.export_to_csv(column_data, save_path)
#                 else:
#                     self.export_to_xlsx(column_data, save_path)
#
#                 QMessageBox.information(self, "Success", f"Data exported to {save_path}")
#
#         except Exception as e:
#             QMessageBox.warning(self, "Error", f"Export failed: {str(e)}\n\n{traceback.format_exc()}")
#
#     def export_selected_column_alldata(self):
#         """Export all files with selected columns"""
#         try:
#             if self.x_column is None:
#                 QMessageBox.warning(self, "No X Column", "Please select an X column first")
#                 return
#
#             if not self.y_columns:
#                 QMessageBox.warning(self, "No Y Columns", "Please select at least one Y column")
#                 return
#
#             # Show batch export options dialog
#             options_dialog = BatchExportOptionsDialog(self)
#             if options_dialog.exec() != QDialog.DialogCode.Accepted:
#                 return
#
#             export_mode = options_dialog.get_export_mode()
#             export_format = options_dialog.get_export_format()
#             combined_filename = options_dialog.get_filename()
#
#             # Select folder or file based on mode
#             if export_mode == 'separate':
#                 dialog = QFileDialog(self)
#                 dialog.setFileMode(QFileDialog.FileMode.Directory)
#                 if hasattr(self, 'file_path'):
#                     dialog.setDirectory(os.path.dirname(self.file_path))
#
#                 if not dialog.exec():
#                     return
#
#                 folder_name = dialog.selectedFiles()[0]
#             else:
#                 # Combined mode - select file location
#                 if export_format == 'csv':
#                     file_filter = "CSV Files (*.csv)"
#                     default_ext = ".csv"
#                 else:
#                     file_filter = "Excel Files (*.xlsx)"
#                     default_ext = ".xlsx"
#
#                 default_path = os.path.join(
#                     os.path.dirname(self.file_path) if hasattr(self, 'file_path') else os.getcwd(),
#                     f"{combined_filename}{default_ext}"
#                 )
#
#                 save_path, _ = QFileDialog.getSaveFileName(
#                     self,
#                     "Save Combined Export File",
#                     default_path,
#                     file_filter
#                 )
#
#                 if not save_path:
#                     return
#
#                 # Ensure correct extension
#                 if not save_path.endswith(default_ext):
#                     save_path += default_ext
#
#             exported_count = 0
#             failed_files = []
#
#             # For combined mode - collect all dataframes with file identifiers
#             combined_data = {}  # Will store {column_name: data_list}
#             file_names = []  # Track file names for column naming
#
#             for file in self.file_in_list:
#                 try:
#                     df = None
#                     file_ext = Path(file).suffix.lower()
#
#                     # Load with header detection
#                     if file_ext == '.dat':
#                         try:
#                             loaded_file = Loadfile(file)
#                             headers = loaded_file.column_headers
#                             data = loaded_file.data
#                             df = pd.DataFrame(data, columns=headers)
#                         except Exception as e:
#                             failed_files.append(f"{Path(file).name} (Loadfile error)")
#                             continue
#
#                     elif file_ext == '.csv':
#                         df = pd.read_csv(file)
#                         has_headers, df = self.detect_headers(df, file)
#                         if not has_headers:
#                             df = pd.read_csv(file, header=None)
#                             df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]
#
#                     elif file_ext == '.xlsx':
#                         df = pd.read_excel(file, engine='openpyxl')
#                         has_headers, df = self.detect_headers(df, file)
#                         if not has_headers:
#                             df = pd.read_excel(file, engine='openpyxl', header=None)
#                             df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]
#
#                     elif file_ext == '.xls':
#                         df = pd.read_excel(file)
#                         has_headers, df = self.detect_headers(df, file)
#                         if not has_headers:
#                             df = pd.read_excel(file, header=None)
#                             df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]
#
#                     elif file_ext == '.txt':
#                         for sep in ['\t', ',', None]:
#                             try:
#                                 df = pd.read_csv(file, sep=sep, delim_whitespace=(sep is None))
#                                 break
#                             except:
#                                 continue
#
#                         if df is not None:
#                             has_headers, df = self.detect_headers(df, file)
#                             if not has_headers:
#                                 if sep is None:
#                                     df = pd.read_csv(file, delim_whitespace=True, header=None)
#                                 else:
#                                     df = pd.read_csv(file, sep=sep, header=None)
#                                 df.columns = [f"Column_{i + 1}" for i in range(len(df.columns))]
#
#                     if df is None:
#                         failed_files.append(f"{Path(file).name} (could not load)")
#                         continue
#
#                     # Get file name without extension
#                     file_basename = Path(file).stem
#
#                     # Validate column indices
#                     if self.x_column >= len(df.columns):
#                         failed_files.append(f"{Path(file).name} (X column index out of range)")
#                         continue
#
#                     # Check if any Y column is out of range
#                     valid_y_columns = [col for col in self.y_columns if col < len(df.columns)]
#                     if not valid_y_columns:
#                         failed_files.append(f"{Path(file).name} (No valid Y columns)")
#                         continue
#
#                     if export_mode == 'separate':
#                         # Create export dataframe with selected columns
#                         column_data = {}
#
#                         # Add X column
#                         x_header = df.columns[self.x_column]
#                         column_data[x_header] = df.iloc[:, self.x_column]
#
#                         # Add Y columns
#                         for col in valid_y_columns:
#                             y_header = df.columns[col]
#                             column_data[y_header] = df.iloc[:, col]
#
#                         export_df = pd.DataFrame(column_data)
#
#                         # Export each file separately
#                         export_file_name = os.path.join(folder_name, f"{file_basename}.{export_format}")
#
#                         if export_format == 'csv':
#                             export_df.to_csv(export_file_name, index=False)
#                         else:
#                             export_df.to_excel(export_file_name, index=False, engine='openpyxl')
#
#                         exported_count += 1
#
#                     else:
#                         # Combined mode - store data in columns with file name prefix
#                         file_names.append(file_basename)
#
#                         # Get X column header name
#                         x_header = df.columns[self.x_column]
#
#                         # Add X column with file name prefix
#                         x_column_name = f"{file_basename}_{x_header}"
#                         combined_data[x_column_name] = df.iloc[:, self.x_column].tolist()
#
#                         # Add Y columns with file name prefix
#                         for col in valid_y_columns:
#                             y_header = df.columns[col]
#                             # Create unique column name: FileName_ColumnName
#                             combined_column_name = f"{file_basename}_{y_header}"
#                             combined_data[combined_column_name] = df.iloc[:, col].tolist()
#
#                         exported_count += 1
#
#                 except Exception as e:
#                     failed_files.append(f"{Path(file).name} ({str(e)})")
#
#             # Handle combined export
#             if export_mode == 'combined' and combined_data:
#                 try:
#                     # Find the maximum length among all columns
#                     max_length = max(len(v) for v in combined_data.values())
#
#                     # Pad shorter columns with empty strings or NaN
#                     for key in combined_data:
#                         current_length = len(combined_data[key])
#                         if current_length < max_length:
#                             combined_data[key].extend([np.nan] * (max_length - current_length))
#
#                     # Create DataFrame with proper column ordering
#                     combined_df = pd.DataFrame()
#
#                     # Add columns in order: File1_X, File1_Y1, File1_Y2, File2_X, File2_Y1, File2_Y2, etc.
#                     for file_name in file_names:
#                         for col_name in combined_data.keys():
#                             if col_name.startswith(f"{file_name}_"):
#                                 combined_df[col_name] = combined_data[col_name]
#
#                     # Export combined file
#                     if export_format == 'csv':
#                         combined_df.to_csv(save_path, index=False)
#                     else:
#                         combined_df.to_excel(save_path, index=False, engine='openpyxl')
#
#                     message = f"Successfully combined {exported_count} files into {save_path}\n"
#                     message += f"Total columns: {len(combined_df.columns)} "
#                     message += f"({exported_count} X columns + {len(combined_df.columns) - exported_count} Y columns)"
#
#                 except Exception as e:
#                     message = f"Error creating combined file: {str(e)}"
#                     QMessageBox.critical(self, "Export Error", message)
#                     return
#             else:
#                 message = f"Successfully exported {exported_count} files"
#                 if export_mode == 'separate':
#                     message += f" to {folder_name}"
#
#             if failed_files:
#                 message += f"\n\nFailed: {len(failed_files)} files:\n" + "\n".join(failed_files[:5])
#                 if len(failed_files) > 5:
#                     message += f"\n... and {len(failed_files) - 5} more"
#
#             QMessageBox.information(self, "Export Complete", message)
#
#         except Exception as e:
#             QMessageBox.warning(self, "Error", f"Export failed: {str(e)}\n\n{traceback.format_exc()}")
#
#     def export_to_csv(self, column_data, file_name):
#         """Export data dictionary to CSV file"""
#         try:
#             with open(file_name, 'w', newline='') as file:
#                 writer = csv.writer(file)
#                 headers = list(column_data.keys())
#                 writer.writerow(headers)
#                 for row in zip(*column_data.values()):
#                     writer.writerow(row)
#         except Exception as e:
#             raise Exception(f"Error writing CSV: {str(e)}")
#
#     def export_to_xlsx(self, column_data, file_name):
#         """Export data dictionary to Excel file"""
#         try:
#             df = pd.DataFrame(column_data)
#             df.to_excel(file_name, index=False, engine='openpyxl')
#         except Exception as e:
#             raise Exception(f"Error writing Excel: {str(e)}")
#
#     def on_item_selection_changed(self):
#         """Handle file selection in tree - only for left click"""
#         # Don't load table if we're in right-click context menu mode
#         if self._in_context_menu:
#             return
#
#         self.clear_column_selection()
#         selected_items = self.file_tree.selectedItems()
#         if selected_items:
#             selected_item = selected_items[0]
#             self.file_path = selected_item.toolTip(0)
#             self.open_file_in_table(self.file_path)
#
#     def open_context_menu(self, position: QPoint):
#         """Open the context menu on right-click"""
#         index = self.file_tree.indexAt(position)
#         if not index.isValid():
#             return
#
#         # Get the item from the first column
#         item = self.file_tree_model.item(index.row(), 0)
#         if not item:
#             return
#
#         # If clicked item is not in selection, select only it
#         selected_indexes = self.file_tree.selectedIndexes()
#         selected_rows = set(idx.row() for idx in selected_indexes)
#
#         if index.row() not in selected_rows:
#             self.file_tree.clearSelection()
#             self.file_tree.selectRow(index.row())
#
#         # Get all selected items for removal
#         selected_indexes = self.file_tree.selectedIndexes()
#         selected_rows = set(idx.row() for idx in selected_indexes)
#         self._context_menu_items = [
#             self.file_tree_model.item(row, 0) for row in sorted(selected_rows)
#         ]
#
#         menu = QMenu(self)
#
#         # Create remove action with count
#         count = len(self._context_menu_items)
#         if count == 1:
#             remove_text = "🗑️ Remove"
#         else:
#             remove_text = f"🗑️ Remove ({count} files)"
#
#         remove_action = menu.addAction(remove_text)
#         remove_action.triggered.connect(lambda: self.remove_context_items())
#
#         # Execute menu
#         menu.exec(self.file_tree.viewport().mapToGlobal(position))
#
#         if hasattr(self, '_context_menu_items'):
#             delattr(self, '_context_menu_items')
#
#     def remove_context_items(self):
#         """Remove the selected items from context menu"""
#         if not hasattr(self, '_context_menu_items'):
#             return
#
#         items_to_remove = self._context_menu_items
#
#         if not items_to_remove:
#             return
#
#         # Ask for confirmation if removing multiple files
#         if len(items_to_remove) > 1:
#             reply = QMessageBox.question(
#                 self,
#                 "Confirm Deletion",
#                 f"Are you sure you want to remove {len(items_to_remove)} files?",
#                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
#                 QMessageBox.StandardButton.No
#             )
#
#             if reply == QMessageBox.StandardButton.No:
#                 return
#
#         removed_paths = []
#         current_displayed_file = getattr(self, 'file_path', None)
#         should_clear_table = False
#
#         # Remove items in reverse order to maintain correct indices
#         rows_to_remove = sorted([self.file_tree_model.indexFromItem(item).row()
#                                  for item in items_to_remove], reverse=True)
#
#         for row in rows_to_remove:
#             item = self.file_tree_model.item(row, 0)
#             if item:
#                 file_path = item.data(Qt.ItemDataRole.UserRole)
#
#                 # Remove from file list
#                 if file_path in self.file_in_list:
#                     self.file_in_list.remove(file_path)
#                     removed_paths.append(file_path)
#
#                 # Check if we need to clear the table
#                 if current_displayed_file == file_path:
#                     should_clear_table = True
#
#                 # Remove from model
#                 self.file_tree_model.removeRow(row)
#
#         # Clear table if any removed file was being displayed
#         if should_clear_table:
#             self.table_model.clear()
#             self.table_model.setRowCount(0)
#             self.table_model.setColumnCount(0)
#             self.clear_column_selection()
#             if hasattr(self, 'file_path'):
#                 delattr(self, 'file_path')
#
#         # Update display label
#         self.update_file_count_label()
#
#         # Show success message
#         if len(removed_paths) > 0:
#             if len(removed_paths) == 1:
#                 message = f"Removed 1 file"
#             else:
#                 message = f"Removed {len(removed_paths)} files"
#
#             self.file_selection_display_label.setText(message)
#             self.file_selection_display_label.setStyleSheet("""
#                 color: #155724;
#                 font-size: 12px;
#                 background-color: #d4edda;
#                 border-radius: 5px;
#                 padding: 5px;
#             """)
#
#             # Reset label after 3 seconds
#             QTimer.singleShot(3000, lambda: self.update_file_count_label())
#
#     def update_file_count_label(self):
#         """Update the file count label"""
#         count = self.file_tree_model.rowCount()
#         if count == 0:
#             self.file_selection_display_label.setText('Please Upload Files or Directory')
#             self.file_selection_display_label.setStyleSheet("""
#                 color: white;
#                 font-size: 12px;
#                 background-color: #f38d76;
#                 border-radius: 5px;
#                 padding: 5px;
#             """)
#         else:
#             self.file_selection_display_label.setText(f"{count} Files Loaded")
#             self.file_selection_display_label.setStyleSheet("""
#                 color: #4b6172;
#                 font-size: 12px;
#                 background-color: #DfE7Ef;
#                 border-radius: 5px;
#                 padding: 5px;
#             """)
#
#     def rstpage(self):
#         """Reset the page to initial state"""
#         try:
#             # Clear selections
#             self.x_column = None
#             self.y_columns = []
#             self.file_in_list = []
#
#             try:
#                 if hasattr(self, 'drag_drop_widget'):
#                     try:
#                         self.drag_drop_widget.reset()
#                     except:
#                         pass
#
#                 if hasattr(self, 'file_tree_model'):
#                     self.file_tree_model.removeRows(0, self.file_tree_model.rowCount())
#
#                 if hasattr(self, 'table_model'):
#                     self.table_model.clear()
#                     self.table_model.setRowCount(0)
#                     self.table_model.setColumnCount(0)
#
#                 if hasattr(self, 'file_selection_display_label'):
#                     self.file_selection_display_label.setText('Please Upload Files or Directory')
#                     self.file_selection_display_label.setStyleSheet("""
#                         color: white;
#                         font-size: 12px;
#                         background-color: #f38d76;
#                         border-radius: 5px;
#                         padding: 5px;
#                     """)
#
#                 if hasattr(self, 'selection_display'):
#                     self.selection_display.setText("X: None | Y: None")
#
#                 if hasattr(self, 'original_headers'):
#                     self.original_headers = {}
#
#             except Exception as e:
#                 print(f"Reset error: {str(e)}")
#
#         except Exception as e:
#             QMessageBox.warning(self, "Error", f"Reset failed: {str(e)}")
#
#     def clear_layout(self, layout):
#         """Clear all widgets from a layout"""
#         if layout is not None:
#             while layout.count():
#                 child = layout.takeAt(0)
#                 if child.widget() is not None:
#                     child.widget().deleteLater()
#                 if child.layout() is not None:
#                     self.clear_layout(child.layout())
#
# # Main execution
# if __name__ == "__main__":
#     import sys
#
#     app = QApplication(sys.argv)
#     app.setStyle("Fusion")
#
#     # Create main window
#     window = FileExport("Multi-Format")
#     window.setWindowTitle("QuDAP - Data Extraction Tool")
#     window.setGeometry(100, 100, 1200, 900)
#     window.show()
#
#     sys.exit(app.exec())

import pyvisa

# Create a resource manager
rm = pyvisa.ResourceManager()

# List all available VISA resources
resources = rm.list_resources()
print("Available resources:")
for res in resources:
    print(res)

# Connect to the first available instrument (if any)
if resources:
    instr = rm.open_resource(resources[0])
    print(f"Connected to: {resources[0]}")
    print("IDN:", instr.query("*IDN?"))
    instr.close()
else:
    print("No instruments found.")
