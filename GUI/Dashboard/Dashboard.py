from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QListWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QGroupBox)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QDateTime, QTime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pyvisa
from matplotlib.figure import Figure
import psutil

import sys
class CPU_Display(FigureCanvas):
    def __init__(self, parent=None, cpu=False):
        fig = Figure(facecolor='white')
        self.axes = fig.add_subplot(111)
        super(CPU_Display, self).__init__(fig)
        self.setParent(parent)
        self.cpu_usage = []
        self.ram_usage = []
        self.time = []
        self.cpu = cpu
        self.plot_initial()

    def plot_initial(self):
        # Initialize the plot with a dark theme
        self.axes.set_xlabel('Time (s)', color='white')
        self.axes.set_ylabel('Usage (%)', color='white')
        # self.axes.set_xlim(0, 10)
        self.axes.set_ylim(0, 100)
        self.axes.grid(True, color='gray', linestyle='--', linewidth=0.5)
        self.axes.set_facecolor('white')
        self.axes.set_xticklabels([])
        self.axes.tick_params(axis='x', colors='black')
        self.axes.tick_params(axis='y', colors='black')


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
            # self.plot_initial()

        else:
            self.axes.cla()
            self.axes.set_xlim(0, 60)
        # self.axes.cla()
        self.plot_initial()
        if self.cpu:
            self.axes.plot(self.time, self.cpu_usage, label='CPU Usage', color='green')
            self.axes.fill_between(self.time, self.cpu_usage, color='green', alpha=0.3)
        else:
            self.axes.plot(self.time, self.ram_usage, label='RAM Usage', color='blue')
            self.axes.fill_between(self.time, self.ram_usage, color='blue', alpha=0.3)
        self.draw()

class Dash(QMainWindow):
    def __init__(self):
        super().__init__()

        self.main_layout = QVBoxLayout()
        self.headiing_layout = QVBoxLayout()
        current_time = QTime.currentTime()

        hour = current_time.hour()
        print(hour)
        if 0 <= hour <= 11:
            self.hello_label = QLabel('Good Morning, Colleague!', self)
        elif 11 < hour <= 17:
            self.hello_label = QLabel('Good Afternoon, Colleague!', self)
        else:
            self.hello_label = QLabel('Good Evening, Colleague!', self)

        self.hello_label.setStyleSheet("color: #1c2833; font-weight: bold; font-size: 30px; font-style: italic")
        self.time_label = QLabel('Today is ', self)
        self.time_label.setStyleSheet("color:  #abb2b9 ; font-weight: bold; font-size: 15px;")

        # Center the label horizontally and vertically
        self.hello_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.headiing_layout.addWidget(self.hello_label)
        self.headiing_layout.addWidget(self.time_label)
        self.headiing_layout.addStretch(2)

        self.widget_layout = QHBoxLayout()
        self.gpib_boxes = []
        for i in range(4):
            box = QGroupBox(f'GPIB Connection {i + 1}')
            layout = QVBoxLayout(box)
            label = QLabel('Status: Disconnected')
            layout.addWidget(label)
            box.setLayout(layout)
            self.gpib_boxes.append((box, label))
            self.widget_layout.addWidget(box)
        self.update_gpib_status()

        # CPU and RAM Usage Chart
        self.cpu = CPU_Display(self,cpu=True)
        self.chart_timer = QTimer(self)
        self.chart_timer.timeout.connect(self.cpu.update_plot)
        self.chart_timer.start(1000)  # Update every second

        self.ram = CPU_Display(self, cpu=False)
        self.chart_timer = QTimer(self)
        self.chart_timer.timeout.connect(self.ram.update_plot)
        self.chart_timer.start(1000)  # Update every second

        self.pc_status_layout = QHBoxLayout()
        self.pc_status_layout.addWidget(self.cpu)
        self.pc_status_layout.addWidget(self.ram)

        self.main_layout.addLayout(self.headiing_layout)
        self.main_layout.setContentsMargins(50, 50, 50, 50)
        self.main_layout.addLayout(self.widget_layout)
        self.main_layout.addLayout(self.pc_status_layout)
        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.setCentralWidget(self.container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every 60,000 milliseconds (1 minute)
        self.update_time()


    def update_time(self):
        current_time = QDateTime.currentDateTime()
        time_display = current_time.toString("MM/dd/yyyy hh:mm:ss ")

        self.time_label.setText('Today is ' + time_display)

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