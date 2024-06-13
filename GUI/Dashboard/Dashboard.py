from PyQt6.QtWidgets import (
    QFrame, QMainWindow, QWidget, QCalendarWidget, QListWidgetItem, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QMessageBox)
from PyQt6.QtGui import QPen, QColor
from PyQt6.QtCore import QDate, Qt, QTimer, QDateTime, QTime
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import pyvisa
from matplotlib.figure import Figure
import psutil
from matplotlib.ticker import FuncFormatter


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
        # self.axes.set_xlabel('Time (s)', color='white')
        self.axes.set_ylabel('Usage (%)', color='white')
        # self.axes.set_xlim(0, 10)
        self.axes.set_ylim(0, 100)
        self.axes.grid(True, color='slategrey', linestyle='--', linewidth=0.5)
        self.axes.set_facecolor('white')
        self.axes.set_xticklabels([])
        self.axes.tick_params(axis='x', colors='slategrey')
        self.axes.tick_params(axis='y', colors='slategrey')
        self.axes.spines['top'].set_color('slategrey')
        self.axes.spines['bottom'].set_color('slategrey')
        self.axes.spines['left'].set_color('slategrey')
        self.axes.spines['right'].set_color('slategrey')
        self.axes.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0f}%'))

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
            self.axes.set_title('CPU Utilization (%)', color='lightsteelblue')
            self.axes.plot(self.time, self.cpu_usage, label='CPU Usage', color='lightsteelblue')
            self.axes.fill_between(self.time, self.cpu_usage, color='lightsteelblue', alpha=0.3)
        else:
            self.axes.set_title('RAM Utilization (%)', color='darkviolet')
            self.axes.plot(self.time, self.ram_usage, label='RAM Usage', color='darkviolet')
            self.axes.fill_between(self.time, self.ram_usage, color='darkviolet', alpha=0.3)
        self.draw()


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


class Dash(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setStyleSheet("background-color: whitesmoke;")
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
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)  # Horizontal line
        # line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("color: #ff5733;")  # Set the color of the line
        line.setFixedHeight(5)  # Set the thickness of the line
        line.setFixedWidth(1150)  # Set the length of the line
        # Center the label horizontally and vertically
        self.hello_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.headiing_layout.addWidget(self.hello_label)
        self.headiing_layout.addWidget(self.time_label)
        self.headiing_layout.addWidget(line)
        self.headiing_layout.addSpacing(70)
        with open("GUI/Dashboard/QGroupbox.qss", "r") as file:
            self.IOGroup_stylesheet = file.read()
            print(self.IOGroup_stylesheet)
        self.widget_layout = QHBoxLayout()

        #///////////////////
        io_layout = QVBoxLayout()
        # IO
        io_label = QLabel('Available Connection')
        # Value

        i_o_connection_layout = QVBoxLayout()
        self.GPIB_Label = QLabel('Current GPIB Connection: none')
        self.USB_Label = QLabel('Current USB Connection: none')
        self.ASRL_Label = QLabel('Current ASRL Connection: none')
        self.TCPIP_Label = QLabel('Current TCP/IP Connection: none')
        i_o_connection_layout.addWidget(self.GPIB_Label)
        i_o_connection_layout.addWidget(self.USB_Label)
        i_o_connection_layout.addWidget(self.ASRL_Label)
        i_o_connection_layout.addWidget(self.TCPIP_Label)
        self.update_gpib_status()


        io_layout.addWidget(io_label)
        io_layout.addLayout(i_o_connection_layout)
        self.io_ccntainer = QWidget()
        self.io_ccntainer.setStyleSheet(f"background-color: #FFCCCC; border-radius: 10px;")
        self.io_ccntainer.setLayout(io_layout)
        self.widget_layout.addWidget(self.io_ccntainer)
        # ////////////////

        # ///////////////////
        io_layout = QVBoxLayout()
        # IO
        io_label = QLabel('Available Connection')
        # Value

        i_o_connection_layout = QVBoxLayout()
        self.GPIB_Label = QLabel('Current GPIB Connection: none')
        self.USB_Label = QLabel('Current USB Connection: none')
        self.ASRL_Label = QLabel('Current ASRL Connection: none')
        self.TCPIP_Label = QLabel('Current TCP/IP Connection: none')
        i_o_connection_layout.addWidget(self.GPIB_Label)
        i_o_connection_layout.addWidget(self.USB_Label)
        i_o_connection_layout.addWidget(self.ASRL_Label)
        i_o_connection_layout.addWidget(self.TCPIP_Label)
        self.update_gpib_status()

        io_layout.addWidget(io_label)
        io_layout.addLayout(i_o_connection_layout)
        self.io_ccntainer = QWidget()
        self.io_ccntainer.setStyleSheet(f"background-color: #FFCCCC; border-radius: 10px;")
        self.io_ccntainer.setLayout(io_layout)
        self.widget_layout.addWidget(self.io_ccntainer)
        # ////////////////

        # ///////////////////
        io_layout = QVBoxLayout()
        # IO
        io_label = QLabel('Available Connection')
        # Value

        i_o_connection_layout = QVBoxLayout()
        self.GPIB_Label = QLabel('Current GPIB Connection: none')
        self.USB_Label = QLabel('Current USB Connection: none')
        self.ASRL_Label = QLabel('Current ASRL Connection: none')
        self.TCPIP_Label = QLabel('Current TCP/IP Connection: none')
        i_o_connection_layout.addWidget(self.GPIB_Label)
        i_o_connection_layout.addWidget(self.USB_Label)
        i_o_connection_layout.addWidget(self.ASRL_Label)
        i_o_connection_layout.addWidget(self.TCPIP_Label)
        self.update_gpib_status()

        io_layout.addWidget(io_label)
        io_layout.addLayout(i_o_connection_layout)
        self.io_ccntainer = QWidget()
        self.io_ccntainer.setStyleSheet(f"background-color: #FFCCCC; border-radius: 10px;")
        self.io_ccntainer.setLayout(io_layout)
        self.widget_layout.addWidget(self.io_ccntainer)
        # ////////////////

        # ///////////////////
        io_layout = QVBoxLayout()
        # IO
        io_label = QLabel('Available Connection')
        # Value

        i_o_connection_layout = QVBoxLayout()
        self.GPIB_Label = QLabel('Current GPIB Connection: none')
        self.USB_Label = QLabel('Current USB Connection: none')
        self.ASRL_Label = QLabel('Current ASRL Connection: none')
        self.TCPIP_Label = QLabel('Current TCP/IP Connection: none')
        i_o_connection_layout.addWidget(self.GPIB_Label)
        i_o_connection_layout.addWidget(self.USB_Label)
        i_o_connection_layout.addWidget(self.ASRL_Label)
        i_o_connection_layout.addWidget(self.TCPIP_Label)
        self.update_gpib_status()

        io_layout.addWidget(io_label)
        io_layout.addLayout(i_o_connection_layout)
        self.io_ccntainer = QWidget()
        self.io_ccntainer.setStyleSheet(f"background-color: #FFCCCC; border-radius: 10px;")
        self.io_ccntainer.setLayout(io_layout)
        self.widget_layout.addWidget(self.io_ccntainer)
        # ////////////////
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
        rm = pyvisa.ResourceManager('@sim')
        try:
            resources = rm.list_resources()

            self.gpib_ports = [instr for instr in resources if 'GPIB' in instr]
            self.usb_ports = [instr for instr in resources if 'USB' in instr]
            self.ASTL_ports = [instr for instr in resources if 'ASRL' in instr]
            self.TCP_ports = [instr for instr in resources if 'TCPIP' in instr]
            self.GPIB_Label.setText(f'Current GPIB Connection: {len(self.gpib_ports)}')
            self.USB_Label.setText(f'Current USB Connection: {len(self.usb_ports)}')
            self.ASRL_Label.setText(f'Current ASRL Connection: {len(self.ASTL_ports)}')
            self.TCPIP_Label.setText(f'Current TCP/IP Connection: {len(self.TCP_ports)}')
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        QTimer.singleShot(5000, self.update_gpib_status)  # Update every 5 seconds