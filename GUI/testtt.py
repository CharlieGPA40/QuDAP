import sys
import os
import mimetypes
import psutil
import pyvisa
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QGroupBox, QLabel, QCalendarWidget, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, QDate
from PyQt6.QtGui import QPainter, QPen, QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MatplotlibWidget(FigureCanvas):
    def __init__(self, parent=None):
        fig = Figure(facecolor='white')  # Set the background color to white
        self.axes = fig.add_subplot(111)
        super(MatplotlibWidget, self).__init__(fig)
        self.setParent(parent)
        self.plot_initial()

    def plot_initial(self):
        # Initialize the plot with a dark theme
        self.axes.set_title('CPU and RAM Usage', color='black')
        self.axes.set_xlabel('Time (s)', color='black')
        self.axes.set_ylabel('% Utilization', color='black')
        self.axes.set_xlim(0, 60)
        self.axes.set_ylim(0, 100)
        self.axes.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.axes.set_facecolor('white')
        self.axes.tick_params(axis='x', colors='black')
        self.axes.tick_params(axis='y', colors='black')
        self.axes.set_xticklabels([])  # Hide x-tick labels
        self.cpu_usage = []
        self.ram_usage = []
        self.time = []

    def update_plot(self):
        # Update the plot with new data
        self.cpu_usage.append(psutil.cpu_percent())
        self.ram_usage.append(psutil.virtual_memory().percent)
        if len(self.time) > 0:
            self.time.append(self.time[-1] + 1)
        else:
            self.time.append(0)

        if len(self.time) > 60:
            self.time.pop(0)
            self.cpu_usage.pop(0)
            self.ram_usage.pop(0)

        self.axes.cla()
        self.plot_initial()
        self.axes.plot(self.time, self.cpu_usage, label='CPU Usage', color='blue')
        self.axes.fill_between(self.time, self.cpu_usage, color='blue', alpha=0.3)
        self.axes.plot(self.time, self.ram_usage, label='RAM Usage', color='green')
        self.axes.fill_between(self.time, self.ram_usage, color='green', alpha=0.3)
        self.axes.legend(facecolor='white', edgecolor='black')
        self.draw()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('GPIB Connection and System Monitor')
        self.setGeometry(100, 100, 1200, 600)

        main_widget = QWidget(self)
        main_layout = QVBoxLayout(main_widget)

        # GPIB Group Boxes
        hbox = QHBoxLayout()
        self.gpib_boxes = []
        for i in range(4):
            box = QGroupBox(f'GPIB Connection {i + 1}')
            layout = QVBoxLayout(box)
            label = QLabel('Status: Disconnected')
            layout.addWidget(label)
            box.setLayout(layout)
            self.gpib_boxes.append((box, label))
            hbox.addWidget(box)
        self.update_gpib_status()

        # CPU and RAM Usage Chart
        self.chart = MatplotlibWidget(self)
        self.chart_timer = QTimer(self)
        self.chart_timer.timeout.connect(self.chart.update_plot)
        self.chart_timer.start(1000)  # Update every second

        # Add GPIB boxes and chart to main layout
        main_layout.addLayout(hbox)
        main_layout.addWidget(self.chart)

        # Calendar Widget
        calendar_layout = QVBoxLayout()
        calendar_layout.addStretch(1)
        calendar_widget = CustomCalendarWidget(self)
        calendar_layout.addWidget(calendar_widget)
        calendar_layout.addStretch(1)

        # Combine HBox and Calendar into a main layout
        final_layout = QHBoxLayout()
        final_layout.addLayout(main_layout)
        final_layout.addLayout(calendar_layout)
        main_widget.setLayout(final_layout)
        self.setCentralWidget(main_widget)

    def update_gpib_status(self):
        # Update the status of the GPIB connections
        rm = pyvisa.ResourceManager()
        try:
            resources = rm.list_resources()
            for i, (box, label) in enumerate(self.gpib_boxes):
                if i < len(resources):
                    label.setText(f'Status: Connected ({resources[i]})')
                else:
                    label.setText('Status: Disconnected')
        except:
            for box, label in self.gpib_boxes:
                label.setText('Status: Disconnected')

        QTimer.singleShot(5000, self.update_gpib_status)  # Update every 5 seconds


class CustomCalendarWidget(QCalendarWidget):
    def __init__(self, parent=None):
        super(CustomCalendarWidget, self).__init__(parent)
        self.setStyleSheet("background-color: lightorange;")
        self.highlight_today()

    def highlight_today(self):
        today = QDate.currentDate()
        self.setDateTextFormat(today, self.get_highlight_format())

    def get_highlight_format(self):
        format = self.dateTextFormat(QDate.currentDate())
        format.setBackground(QColor('orange'))
        return format

    def paintCell(self, painter, rect, date):
        super().paintCell(painter, rect, date)
        if date == QDate.currentDate():
            painter.setPen(QPen(Qt.PenStyle.NoPen))
            painter.setBrush(QColor('orange'))
            painter.drawEllipse(rect.center(), rect.width() // 4, rect.height() // 4)


def main():
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
