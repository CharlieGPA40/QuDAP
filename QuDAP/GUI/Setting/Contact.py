"""
QuDAP - Contact Page
A modern, aesthetically pleasing contact page for the QuDAP software
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QScrollArea, QFrame, QGridLayout,
    QGraphicsDropShadowEffect, QTextEdit, QLineEdit, QComboBox,
    QCheckBox, QButtonGroup, QRadioButton
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QUrl, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QPainter, QBrush, QColor, QPalette, QDesktopServices, QIcon


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


class ContactQuDAP(QWidget):
    """Contact page for QuDAP software"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setMinimumSize(1000, 800)
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

        # Create two-column layout for main content
        main_content_layout = QHBoxLayout()
        main_content_layout.setSpacing(20)

        # Left column
        left_column = QVBoxLayout()
        left_column.setSpacing(20)
        left_column.addWidget(self.create_contact_section())
        left_column.addWidget(self.create_report_issue_section())

        # Right column
        right_column = QVBoxLayout()
        right_column.setSpacing(20)
        right_column.addWidget(self.create_quick_links_section())
        right_column.addWidget(self.create_contribute_section())
        right_column.addStretch()

        # Add columns to main content
        main_content_layout.addLayout(left_column, 2)
        main_content_layout.addLayout(right_column, 1)

        content_layout.addLayout(main_content_layout)

        # Add community section
        content_layout.addWidget(self.create_community_section())

        # Add footer
        content_layout.addWidget(self.create_footer_section())

        # Set scroll area widget
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def create_header_section(self):
        """Create the header section with logo and title"""
        header_card = AnimatedCard()
        header_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: none;
            }
        """)
        header_layout = QVBoxLayout(header_card)
        header_layout.setSpacing(15)
        header_layout.setContentsMargins(40, 40, 40, 40)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title using logo
        title = QLabel(self)
        pixmap = QPixmap("GUI/Icon/logo.svg")  # Ensure this path is correct
        if not pixmap.isNull():
            resized_pixmap = pixmap.scaled(600, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                           Qt.TransformationMode.SmoothTransformation)
            title.setPixmap(resized_pixmap)
        else:
            # Fallback if logo not found - show text
            title.setText("QuDAP")
            title.setFont(QFont("Arial", 42, QFont.Weight.Bold))
            title.setStyleSheet("color: #1e88e5;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle = QLabel("Get in Touch")
        subtitle_font = QFont("Arial", 24)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 5px;
                border: none;
                background: transparent;
            }
        """)

        # Description
        description = QLabel("We're here to help! Contact us for support, report issues, or learn how to contribute.")
        description.setFont(QFont("Arial", 12))
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        description.setStyleSheet("color: #7f8c8d;")

        # Add to layout
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addWidget(description)

        return header_card

    def create_contact_section(self):
        """Create contact form section"""
        contact_card = AnimatedCard()
        contact_layout = QVBoxLayout(contact_card)
        contact_layout.setContentsMargins(30, 30, 30, 30)
        contact_layout.setSpacing(20)

        # Section title
        section_title = QLabel("📧 Contact Us")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50;")
        contact_layout.addWidget(section_title)

        # Contact form
        form_layout = QVBoxLayout()
        form_layout.setSpacing(15)

        # Name field
        name_label = QLabel("Your Name *")
        name_label.setFont(QFont("Arial", 11))
        name_label.setStyleSheet("color: #5d6d7e;")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your full name")
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #1e88e5;
                background-color: white;
            }
        """)

        # Email field
        email_label = QLabel("Email Address *")
        email_label.setFont(QFont("Arial", 11))
        email_label.setStyleSheet("color: #5d6d7e;")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your.email@example.com")
        self.email_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
                background-color: #f8f9fa;
            }
            QLineEdit:focus {
                border-color: #1e88e5;
                background-color: white;
            }
        """)

        # Subject field
        subject_label = QLabel("Subject *")
        subject_label.setFont(QFont("Arial", 11))
        subject_label.setStyleSheet("color: #5d6d7e;")
        self.subject_combo = QComboBox()
        self.subject_combo.addItems([
            "General Inquiry",
            "Technical Support",
            "Feature Request",
            "Documentation",
            "Collaboration",
            "Other"
        ])
        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            combobox_stylesheet = file.read()
        self.subject_combo.setStyleSheet(combobox_stylesheet)

        # Message field
        message_label = QLabel("Message *")
        message_label.setFont(QFont("Arial", 11))
        message_label.setStyleSheet("color: #5d6d7e;")
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Please describe your inquiry in detail...")
        self.message_input.setMaximumHeight(150)
        self.message_input.setStyleSheet("""
            QTextEdit {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 12px;
                background-color: #f8f9fa;
            }
            QTextEdit:focus {
                border-color: #1e88e5;
                background-color: white;
            }
        """)

        # Add fields to form
        form_layout.addWidget(name_label)
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(email_label)
        form_layout.addWidget(self.email_input)
        form_layout.addWidget(subject_label)
        form_layout.addWidget(self.subject_combo)
        form_layout.addWidget(message_label)
        form_layout.addWidget(self.message_input)

        # Submit button
        submit_button = QPushButton("Send Message")
        submit_button.setFont(QFont("Arial", 12))
        submit_button.setCursor(Qt.CursorShape.PointingHandCursor)
        submit_button.setStyleSheet("""
            QPushButton {
                background-color: #1e88e5;
                color: white;
                padding: 12px 30px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #1565c0;
            }
        """)
        submit_button.clicked.connect(self.send_message)

        contact_layout.addLayout(form_layout)
        contact_layout.addWidget(submit_button, alignment=Qt.AlignmentFlag.AlignRight)

        return contact_card

    def create_report_issue_section(self):
        """Create report issue section"""
        issue_card = AnimatedCard()
        issue_layout = QVBoxLayout(issue_card)
        issue_layout.setContentsMargins(30, 30, 30, 30)
        issue_layout.setSpacing(20)

        # Section title
        section_title = QLabel("🐛 Report an Issue")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50;")
        issue_layout.addWidget(section_title)

        # Description
        description = QLabel(
            "Found a bug or experiencing issues? Help us improve QuDAP by reporting problems you encounter."
        )
        description.setWordWrap(True)
        description.setFont(QFont("Arial", 12))
        description.setStyleSheet("color: #7f8c8d;")
        issue_layout.addWidget(description)

        # Issue type selection
        issue_type_label = QLabel("Issue Type:")
        issue_type_label.setFont(QFont("Arial", 11))
        issue_type_label.setStyleSheet("color: #5d6d7e;")
        issue_layout.addWidget(issue_type_label)

        # Radio buttons for issue types
        issue_types_layout = QVBoxLayout()
        issue_types_layout.setSpacing(10)

        self.issue_type_group = QButtonGroup()
        issue_types = [
            ("🔴 Bug Report", "Something isn't working as expected"),
            ("⚡ Performance Issue", "Slow or unresponsive behavior"),
            ("💥 Crash Report", "Application crashes or freezes"),
            ("📊 Data Issue", "Problems with data processing or visualization"),
            ("🔌 Hardware Issue", "Instrument connection or communication problems")
        ]

        for i, (title, desc) in enumerate(issue_types):
            radio_layout = QHBoxLayout()
            radio = QRadioButton(title)
            radio.setFont(QFont("Arial", 11))
            radio.setStyleSheet("""
                QRadioButton {
                    color: #2c3e50;
                    background-color: #ffffff;
                }
                QRadioButton::indicator {
                    width: 18px;
                    height: 18px;
                }
            """)
            self.issue_type_group.addButton(radio, i)

            desc_label = QLabel(f"- {desc}")
            desc_label.setFont(QFont("Arial", 10))
            desc_label.setStyleSheet("color: #95a5a6;")

            radio_layout.addWidget(radio)
            radio_layout.addWidget(desc_label)
            radio_layout.addStretch()
            issue_types_layout.addLayout(radio_layout)

        issue_layout.addLayout(issue_types_layout)

        # Buttons
        buttons_layout = QHBoxLayout()

        github_issue_btn = QPushButton("📝 Create GitHub Issue")
        github_issue_btn.setFont(QFont("Arial", 11))
        github_issue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_issue_btn.setStyleSheet("""
            QPushButton {
                background-color: #24292e;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1a1e22;
            }
        """)
        github_issue_btn.clicked.connect(lambda: self.open_url("https://github.com/CharlieGPA40/QuDAP/issues/new"))

        view_issues_btn = QPushButton("👀 View Existing Issues")
        view_issues_btn.setFont(QFont("Arial", 11))
        view_issues_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        view_issues_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #24292e;
                padding: 10px 20px;
                border: 2px solid #24292e;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #f6f8fa;
            }
        """)
        view_issues_btn.clicked.connect(lambda: self.open_url("https://github.com/CharlieGPA40/QuDAP/issues"))

        buttons_layout.addWidget(github_issue_btn)
        buttons_layout.addWidget(view_issues_btn)
        buttons_layout.addStretch()

        issue_layout.addLayout(buttons_layout)

        return issue_card

    def create_quick_links_section(self):
        """Create quick links section"""
        links_card = AnimatedCard()
        links_layout = QVBoxLayout(links_card)
        links_layout.setContentsMargins(30, 30, 30, 30)
        links_layout.setSpacing(15)

        # Section title
        section_title = QLabel("🔗 Quick Links")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50;")
        links_layout.addWidget(section_title)

        # Links
        links = [
            ("📚 Documentation", "https://github.com/CharlieGPA40/QuDAP/tree/main/doc"),
            ("💻 Source Code", "https://github.com/CharlieGPA40/QuDAP"),
            ("📦 PyPI Package", "https://pypi.org/project/QuDAP/"),
            ("🔬 Jin Lab", "http://wp.auburn.edu/JinLab/"),
            ("⚡ Mahjouri Lab", "http://wp.auburn.edu/Mahjouri/")
        ]

        for text, url in links:
            link_button = QPushButton(text)
            link_button.setCursor(Qt.CursorShape.PointingHandCursor)
            link_button.setFont(QFont("Arial", 11))
            link_button.setStyleSheet("""
                QPushButton {
                    background-color: #f8f9fa;
                    color: #1e88e5;
                    padding: 10px;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #e8ecef;
                    border-color: #1e88e5;
                }
            """)
            link_button.clicked.connect(lambda checked, u=url: self.open_url(u))
            links_layout.addWidget(link_button)

        links_layout.addStretch()

        return links_card

    def create_contribute_section(self):
        """Create contribute section"""
        contribute_card = AnimatedCard()
        contribute_layout = QVBoxLayout(contribute_card)
        contribute_layout.setContentsMargins(30, 30, 30, 30)
        contribute_layout.setSpacing(15)

        # Section title
        section_title = QLabel("🤝 Contribute")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50;")
        contribute_layout.addWidget(section_title)

        # Description
        description = QLabel(
            "QuDAP is open source and welcomes contributions from the community!"
        )
        description.setWordWrap(True)
        description.setFont(QFont("Arial", 12))
        description.setStyleSheet("color: #7f8c8d;")
        contribute_layout.addWidget(description)

        # Ways to contribute
        ways_label = QLabel("Ways to Contribute:")
        ways_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        ways_label.setStyleSheet("color: #5d6d7e;")
        contribute_layout.addWidget(ways_label)

        ways = [
            "🐛 Report bugs",
            "💡 Suggest features",
            "📝 Improve documentation",
            "💻 Submit code patches",
            "🧪 Write tests",
            "⭐ Star the repository"
        ]

        for way in ways:
            way_label = QLabel(way)
            way_label.setFont(QFont("Arial", 10))
            way_label.setStyleSheet("color: #7f8c8d; padding-left: 20px;")
            contribute_layout.addWidget(way_label)

        # Fork button
        fork_button = QPushButton("🍴 Fork on GitHub")
        fork_button.setFont(QFont("Arial", 11))
        fork_button.setCursor(Qt.CursorShape.PointingHandCursor)
        fork_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        fork_button.clicked.connect(lambda: self.open_url("https://github.com/CharlieGPA40/QuDAP/fork"))

        contribute_layout.addWidget(fork_button)
        contribute_layout.addStretch()

        return contribute_card

    def create_community_section(self):
        """Create community section"""
        community_card = AnimatedCard()
        community_layout = QVBoxLayout(community_card)
        community_layout.setContentsMargins(30, 30, 30, 30)
        community_layout.setSpacing(20)

        # Section title
        section_title = QLabel("👥 Join Our Community")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50;")
        community_layout.addWidget(section_title)

        # Community cards grid
        community_grid = QGridLayout()
        community_grid.setSpacing(20)

        communities = [
            ("📧 Email Support", "chunli.tang@auburn.edu", "Direct support from the development team", "#0b2341"),
            ("💬 Discussions", "GitHub Discussions", "Ask questions and share ideas", "#e86100"),
            ("📢 Announcements", "GitHub Releases", "Stay updated with latest releases", "#dba43d"),
            ("🎓 Academic", "Auburn University", "Research collaboration opportunities", "#006860")
        ]

        for i, (icon_title, platform, description, color) in enumerate(communities):
            community_item = self.create_community_item(icon_title, platform, description, color)
            row = i // 2
            col = i % 2
            community_grid.addWidget(community_item, row, col)

        community_layout.addLayout(community_grid)

        return community_card

    def create_community_item(self, icon_title, platform, description, color):
        """Create individual community item"""
        item_frame = QFrame()
        item_frame.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-left: 4px solid {color};
                border-radius: 5px;
                padding: 15px;
            }}
            QFrame:hover {{
                background-color: #f8f9fa;
            }}
        """)

        layout = QVBoxLayout(item_frame)
        layout.setSpacing(5)

        title_label = QLabel(icon_title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {color};")

        platform_label = QLabel(platform)
        platform_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        platform_label.setStyleSheet("color: #2c3e50;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d;")

        layout.addWidget(title_label)
        layout.addWidget(platform_label)
        layout.addWidget(desc_label)

        return item_frame

    def create_footer_section(self):
        """Create footer section"""
        footer_card = AnimatedCard()
        footer_layout = QVBoxLayout(footer_card)
        footer_layout.setContentsMargins(30, 30, 30, 30)
        footer_layout.setSpacing(20)

        # Contact information grid
        contact_grid = QGridLayout()
        contact_grid.setSpacing(30)

        # Primary contacts
        contacts = [
            ("Lead Developer", "Chunli Tang", "chunli.tang@auburn.edu"),
            ("Advisor", "Dr. Masoud Mahjouri-Samani", "Mahjouri@auburn.edu"),
            ("Advisor", "Dr. Wencan Jin", "wjin@auburn.edu")
        ]

        for i, (role, name, email) in enumerate(contacts):
            contact_layout = QVBoxLayout()

            role_label = QLabel(role)
            role_label.setFont(QFont("Arial", 10))
            role_label.setStyleSheet("color: #95a5a6;")

            name_label = QLabel(name)
            name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            name_label.setStyleSheet("color: #2c3e50;")

            email_button = QPushButton(email)
            email_button.setFont(QFont("Arial", 10))
            email_button.setCursor(Qt.CursorShape.PointingHandCursor)
            email_button.setStyleSheet("""
                QPushButton {
                    color: #1e88e5;
                    background-color: #ffffff;
                    border: none;
                    text-align: left;
                    padding: 0;
                }
                QPushButton:hover {
                    text-decoration: underline;
                }
            """)
            email_button.clicked.connect(lambda checked, e=email: self.open_email(e))

            contact_layout.addWidget(role_label)
            contact_layout.addWidget(name_label)
            contact_layout.addWidget(email_button)

            contact_grid.addLayout(contact_layout, 0, i)

        footer_layout.addLayout(contact_grid)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e0e0e0;")
        footer_layout.addWidget(separator)

        # Copyright
        copyright_label = QLabel(
            "© 2025 Chunli Tang | Auburn University | QuDAP - Quantum Materials Data Acquisition and Processing\n"
            "We welcome all feedback and contributions to improve QuDAP!"
        )
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setFont(QFont("Arial", 10))
        copyright_label.setStyleSheet("color: #7f8c8d;")
        footer_layout.addWidget(copyright_label)

        return footer_card

    def send_message(self):
        """Handle message sending"""
        name = self.name_input.text()
        email = self.email_input.text()
        subject = self.subject_combo.currentText()
        message = self.message_input.toPlainText()

        if not all([name, email, message]):
            # Show error for empty fields
            return

        # Construct email
        email_subject = f"QuDAP Contact: {subject}"
        email_body = f"From: {name}\nEmail: {email}\n\nMessage:\n{message}"

        # Open email client
        mailto = f"mailto:chunli.tang@auburn.edu?subject={email_subject}&body={email_body}"
        QDesktopServices.openUrl(QUrl(mailto))

        # Clear form
        self.name_input.clear()
        self.email_input.clear()
        self.message_input.clear()
        self.subject_combo.setCurrentIndex(0)

    def open_url(self, url):
        """Open URL in default browser"""
        QDesktopServices.openUrl(QUrl(url))

    def open_email(self, email):
        """Open email client"""
        QDesktopServices.openUrl(QUrl(f"mailto:{email}"))


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle("Fusion")

    # Create and show window
    window = ContactQuDAP()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()