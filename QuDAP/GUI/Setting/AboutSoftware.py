"""
QuDAP - About This Software Page
A modern, aesthetically pleasing about page for the QuDAP software
"""

import sys
from __init__ import __version__
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QGroupBox, QScrollArea, QFrame, QGridLayout,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QUrl
from PyQt6.QtGui import QFont, QPixmap, QPainter, QBrush, QColor, QPalette, QDesktopServices

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

class AboutQuDAP(QWidget):
    """About page for QuDAP software"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setMinimumSize(900, 700)
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

        # Add overview section
        content_layout.addWidget(self.create_overview_section())

        # Add features section
        content_layout.addWidget(self.create_features_section())

        # Add specifications section
        content_layout.addWidget(self.create_specifications_section())

        # Add team section
        content_layout.addWidget(self.create_team_section())

        # Add footer section
        content_layout.addWidget(self.create_footer_section())

        # Set scroll area widget
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

    def create_header_section(self):
        """Create the header section with logo and title"""
        header_card = AnimatedCard()
        header_layout = QVBoxLayout(header_card)
        header_layout.setSpacing(10)
        header_layout.setContentsMargins(40, 40, 40, 40)

        title = QLabel(self)

        # Load the icon image and set it to the QLabel
        pixmap = QPixmap("GUI/Icon/logo.svg")

        resized_pixmap = pixmap.scaled(600, 200, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
        title.setPixmap(resized_pixmap)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Subtitle
        subtitle = QLabel("Quantum Materials Data Acquisition and Processing")
        subtitle_font = QFont("Arial", 18)
        subtitle.setFont(subtitle_font)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; padding: 5px;")

        # Version badge
        version_layout = QHBoxLayout()
        version_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        version_badge = QLabel(f"Version {__version__}")
        version_badge.setFont(QFont("Arial", 12))
        version_badge.setStyleSheet("""
            QLabel {
                background-color: #3498db;
                color: white;
                padding: 5px 15px;
                border-radius: 15px;
            }
        """)
        version_layout.addWidget(version_badge)

        # Add to layout
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        header_layout.addLayout(version_layout)

        return header_card

    def create_overview_section(self):
        """Create the overview section"""
        overview_card = AnimatedCard()
        overview_layout = QVBoxLayout(overview_card)
        overview_layout.setContentsMargins(30, 30, 30, 30)

        # Section title
        section_title = QLabel("Overview")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")

        # Overview text
        overview_text = QLabel(
            "Quantum Materials Data Acquisition and Processing QuDAP, a Python-based and open-source software package," 
            "is designed to control and automate material characterizations based on the Physical Property Measurement System (PPMS). "
            "The software supports major hardware interfaces and protocols (USB, RS232, GPIB, and Ethernet)," 
            "enabling communication with the measurement modules associated with the PPMS. "
            "It integrates multiple Python libraries to realize instrument control, data acquisition, and real-time data visualization." 
            "Here, we present features of QuDAP, including direct control of instruments without relying on proprietary software," 
            "real-time data plotting for immediate verification and analysis, full automation of data acquisition and storage," 
            "and real-time notifications of experiment status and errors. These capabilities enhance experimental efficiency," 
            "reliability, and reproducibility."
        )
        overview_text.setWordWrap(True)
        overview_text.setFont(QFont("Arial", 12))
        overview_text.setStyleSheet("color: #5d6d7e; line-height: 1.6;")

        overview_layout.addWidget(section_title)
        overview_layout.addWidget(overview_text)

        return overview_card

    def create_features_section(self):
        """Create the features section with grid layout"""
        features_card = AnimatedCard()
        features_layout = QVBoxLayout(features_card)
        features_layout.setContentsMargins(30, 30, 30, 30)

        # Section title
        section_title = QLabel("Key Features")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        features_layout.addWidget(section_title)

        # Create grid for features
        features_grid = QGridLayout()
        features_grid.setSpacing(20)

        features = [
            ("🔬", "Direct PPMS Control", "Provide direct Python script communication and control of PPMS and instruments without using the built-in software, which improves the tunability and efficiency of the experiment"),
            ("🧲", "Demagnetization", "Built-in demagnetization protocols for reliable measurements"),
            ("📊", "Real-time Visualization", "Live data plotting and monitoring capabilities"),
            ("🤖", "Full Automation", "Automated measurement sequences and data collection"),
            ("🔔", "Notifications", "Real-time alerts for experiment status and errors"),
            ("🔌", "Multi-Protocol", "Support for USB, RS232, GPIB, and Ethernet interfaces"),
            ("📈", "Data Processing", "Advanced analysis tools for quantum materials research")
        ]

        for i, (icon, title, description) in enumerate(features):
            feature_widget = self.create_feature_item(icon, title, description)
            row = i // 2
            col = i % 2
            features_grid.addWidget(feature_widget, row, col)

        features_layout.addLayout(features_grid)

        return features_card

    def create_feature_item(self, icon, title, description):
        """Create individual feature item"""
        feature_frame = QFrame()
        feature_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
            }
            QFrame:hover {
                background-color: #e8ecef;
            }
        """)

        layout = QHBoxLayout(feature_frame)
        layout.setSpacing(15)

        # Icon
        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 24))
        icon_label.setFixedSize(80, 80)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Text
        text_layout = QVBoxLayout()
        text_layout.setSpacing(5)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 13, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50;")

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #7f8c8d;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout, 1)

        return feature_frame

    def create_specifications_section(self):
        """Create technical specifications section"""
        specs_card = AnimatedCard()
        specs_layout = QVBoxLayout(specs_card)
        specs_layout.setContentsMargins(30, 30, 30, 30)

        # Section title
        section_title = QLabel("Technical Specifications")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        specs_layout.addWidget(section_title)

        # Specifications grid
        specs_grid = QGridLayout()
        specs_grid.setSpacing(15)
        specs_grid.setColumnStretch(1, 1)

        specs = [
            ("Platform:", "Windows 11"),
            ("Python Version:", "3.10 or newer"),
            ("License:", "Apache-2.0 license (Open Source)"),
            ("Data Formats:", "CSV"),
            ("Supported Instruments:", "PPMS, Keithley, Berkeley Nucleonics, Stanford Research"),
            ("PPMS Integration:", "MultiPyVu"),
            ("GUI Framework:", "PyQt6")
        ]

        for i, (label, value) in enumerate(specs):
            label_widget = QLabel(label)
            label_widget.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            label_widget.setStyleSheet("color: #34495e;")

            value_widget = QLabel(value)
            value_widget.setFont(QFont("Arial", 11))
            value_widget.setStyleSheet("color: #7f8c8d;")

            specs_grid.addWidget(label_widget, i, 0, Qt.AlignmentFlag.AlignRight)
            specs_grid.addWidget(value_widget, i, 1, Qt.AlignmentFlag.AlignLeft)

        specs_layout.addLayout(specs_grid)

        return specs_card

    def create_team_section(self):
        """Create team section"""
        team_card = AnimatedCard()
        team_layout = QVBoxLayout(team_card)
        team_layout.setContentsMargins(30, 30, 30, 30)

        # Section title
        section_title = QLabel("Development Team")
        section_title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #2c3e50; margin-bottom: 20px;")
        team_layout.addWidget(section_title)

        # Team members grid
        team_grid = QGridLayout()
        team_grid.setSpacing(20)

        team_members = [
            ("Chunli Tang", "Lead Developer", "Auburn University - ECE", "chunli.tang@auburn.edu"),
            ("Harshil Goyal", "Contribute Developer", "Auburn University - ECE", None),
            ("Skai White", "Developer", "Hampton University", None),
            ("Jingyu Jia", "Developer", "Great Neck South High School", None)
        ]

        advisors = [
            ("Dr. Masoud Mahjouri-Samani", "Advisor", "Auburn University - ECE", "Mahjouri@auburn.edu"),
            ("Dr. Wencan Jin", "Advisor", "Auburn University - Physics", "wjin@auburn.edu")
        ]

        # Add team members
        for i, (name, role, affiliation, email) in enumerate(team_members):
            member_widget = self.create_team_member(name, role, affiliation, email)
            team_grid.addWidget(member_widget, 0, i)

        # Add advisors
        for i, (name, role, affiliation, email) in enumerate(advisors):
            member_widget = self.create_team_member(name, role, affiliation, email)
            team_grid.addWidget(member_widget, 1, i)

        team_layout.addLayout(team_grid)

        return team_card

    def create_team_member(self, name, role, affiliation, email):
        """Create individual team member widget"""
        member_frame = QFrame()
        member_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-radius: 8px;
                padding: 15px;
            }
        """)

        layout = QVBoxLayout(member_frame)
        layout.setSpacing(5)

        name_label = QLabel(name)
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #2c3e50;")

        role_label = QLabel(role)
        role_label.setFont(QFont("Arial", 10))
        role_label.setStyleSheet("color: #3498db;")

        affiliation_label = QLabel(affiliation)
        affiliation_label.setFont(QFont("Arial", 9))
        affiliation_label.setStyleSheet("color: #7f8c8d;")
        affiliation_label.setWordWrap(True)

        layout.addWidget(name_label)
        layout.addWidget(role_label)
        layout.addWidget(affiliation_label)

        if email:
            email_button = QPushButton(email)
            email_button.setFont(QFont("Arial", 9))
            email_button.setCursor(Qt.CursorShape.PointingHandCursor)
            email_button.setStyleSheet("""
                QPushButton {
                    color: #3498db;
                    border: none;
                    text-align: left;
                    padding: 0;
                    text-decoration: underline;
                }
                QPushButton:hover {
                    color: #2980b9;
                }
            """)
            email_button.clicked.connect(lambda: self.open_email(email))
            layout.addWidget(email_button)

        layout.addStretch()

        return


    def create_footer_section(self):
        """Create footer section with links and copyright"""
        footer_card = AnimatedCard()
        footer_layout = QVBoxLayout(footer_card)
        footer_layout.setContentsMargins(30, 30, 30, 30)

        # Links section
        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        links_layout.setSpacing(30)

        links = [
            ("LinkedIn", "https://www.linkedin.com/in/chunlitang"),
            ("GitHub Repository", "https://github.com/CharlieGPA40/QuDAP"),
            ("Documentation", "https://github.com/CharlieGPA40/QuDAP/tree/main/doc"),
            ("Report Issues", "https://github.com/CharlieGPA40/QuDAP/issues"),
            ("PyPI Package", "https://pypi.org/project/QuDAP/")
        ]

        for text, url in links:
            link_button = QPushButton(text)
            link_button.setCursor(Qt.CursorShape.PointingHandCursor)
            link_button.setFont(QFont("Arial", 11))
            link_button.setStyleSheet("""
                QPushButton {
                    color: #3498db;
                    border: 1px solid #3498db;
                    padding: 8px 16px;
                    border-radius: 5px;
                    background-color: white;
                }
                QPushButton:hover {
                    background-color: #3498db;
                    color: white;
                }
            """)
            link_button.clicked.connect(lambda checked, u=url: self.open_url(u))
            links_layout.addWidget(link_button)

        footer_layout.addLayout(links_layout)

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #e0e0e0; margin: 20px 0;")
        footer_layout.addWidget(separator)

        # Copyright and disclaimer
        copyright_label = QLabel(
            "© 2025 Chunli Tang | Auburn University | Electrical and Computer Engineering & Physics Department\n"
            "This software is provided for academic and educational research purposes only.\n"
            "NO WARRANTIES - Use at your own risk."
        )
        copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copyright_label.setFont(QFont("Arial", 10))
        copyright_label.setStyleSheet("color: #7f8c8d;")
        footer_layout.addWidget(copyright_label)
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.addLayout(button_layout)

        return footer_card

    def open_url(self, url):
        """Open URL in default browser"""
        QDesktopServices.openUrl(QUrl(url))

    def open_email(self, email):
        """Open email client"""
        QDesktopServices.openUrl(QUrl(f"mailto:{email}"))


# def main():
#     """Main function to run the application"""
#     app = QApplication(sys.argv)
#
#     # Set application style
#     app.setStyle("Fusion")
#
#     # Create and show window
#     window = AboutQuDAP()
#     window.show()
#
#     sys.exit(app.exec())
#
#
# if __name__ == "__main__":
#     main()