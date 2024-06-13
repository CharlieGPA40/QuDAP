import sys
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt
import calendar
from datetime import datetime


class DayWidget(QWidget):
    def __init__(self, day, data):
        super().__init__()
        self.initUI(day, data)

    def initUI(self, day, data):
        layout = QVBoxLayout()

        day_label = QLabel(str(day))
        day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        day_label.setStyleSheet("font-size: 18px; font-weight: bold;")

        data_label = QLabel(data)
        data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        data_label.setStyleSheet("font-size: 14px;")

        layout.addWidget(day_label)
        layout.addWidget(data_label)

        self.setLayout(layout)
        self.setStyleSheet("""
            QWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
                background-color: #f9f9f9;
            }
        """)


class CalendarWidget(QWidget):
    def __init__(self, year, month, month_data):
        super().__init__()
        self.year = year
        self.month = month
        self.month_data = month_data
        self.initUI()

    def initUI(self):
        layout = QGridLayout()

        # Add day labels (Sun, Mon, Tue, etc.)
        days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for i, day in enumerate(days_of_week):
            label = QLabel(day)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("font-size: 16px; font-weight: bold;")
            layout.addWidget(label, 0, i)

        # Get the first day of the month and the number of days in the month
        cal = calendar.Calendar()
        month_days = cal.monthdayscalendar(self.year, self.month)

        # Add day widgets
        for week_num, week in enumerate(month_days):
            for day_num, day in enumerate(week):
                if day != 0:
                    data = self.month_data.get(day, "")
                    day_widget = DayWidget(day, data)
                    layout.addWidget(day_widget, week_num + 1, day_num)

        self.setLayout(layout)
        self.setWindowTitle(f"Calendar - {calendar.month_name[self.month]} {self.year}")
        self.setGeometry(100, 100, 800, 600)


def main():
    app = QApplication(sys.argv)

    # Example data for the month
    month_data = {
        1: "Event 1",
        5: "Event 2",
        10: "Event 3",
        15: "Event 4",
        20: "Event 5",
        25: "Event 6"
    }

    year = datetime.now().year
    month = datetime.now().month

    window = CalendarWidget(year, month, month_data)
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
