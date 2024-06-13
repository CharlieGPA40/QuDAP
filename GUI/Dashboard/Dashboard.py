from PyQt6.QtWidgets import (
    QFrame, QMainWindow, QWidget, QCalendarWidget, QGraphicsDropShadowEffect, QStackedWidget, QVBoxLayout, QLabel, QHBoxLayout
, QCheckBox, QMessageBox)
from PyQt6.QtGui import QPen, QColor, QIcon, QPixmap
from PyQt6.QtCore import QDate, Qt, QTimer, QDateTime, QTime, QEvent
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
        self.setGeometry(100, 100, 50, 50)
        hour = current_time.hour()
        self.shadow_effects = []
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
        line.setFixedHeight(10)  # Set the thickness of the line
        line.setFixedWidth(1200)  # Set the length of the line
        # Center the label horizontally and vertically
        self.hello_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.headiing_layout.addWidget(self.hello_label)
        self.headiing_layout.addWidget(self.time_label)
        self.headiing_layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignCenter)
        self.headiing_layout.addSpacing(50)
        with open("GUI/Dashboard/QLabel.qss", "r") as file:
            self.IOLabel_stylesheet = file.read()
        with open("GUI/Dashboard/QLabel_1.qss", "r") as file:
            self.IOLabel_1_stylesheet = file.read()
        self.widget_layout = QHBoxLayout()

        #///////////////////
        GPIB_layout = QHBoxLayout()
        # IO
        GPIB_icon_label = QLabel()
        GPIB_pixmap = QPixmap('GUI/Icon/GPIB.svg')
        GPIB_pixmap = GPIB_pixmap.scaled(70, 88, Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
        GPIB_icon_label.setPixmap(GPIB_pixmap)
        GPIB_icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # Value
        GPIB_icon_connection_layout = QVBoxLayout()
        GPIB_icon_connection_layout.addWidget(GPIB_icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        GPIB_layout.addLayout(GPIB_icon_connection_layout)

        GPIB_connection_layout = QVBoxLayout()
        self.GPIB_Label = QLabel('GPIB Connections:')
        self.GPIB_number_Label = QLabel('None')
        self.GPIB_number_Label.setStyleSheet(self.IOLabel_stylesheet)
        GPIB_connection_layout.addWidget(self.GPIB_Label, alignment=Qt.AlignmentFlag.AlignLeft)
        GPIB_connection_layout.addWidget(self.GPIB_number_Label, alignment=Qt.AlignmentFlag.AlignRight)

        GPIB_layout.addLayout(GPIB_connection_layout)
        self.GPIB_ccntainer = QWidget()
        self.GPIB_ccntainer.setStyleSheet(
                                          """ 
                                          QWidget{background-color: #d6eaf8; border-radius: 20px;}
                                           QWidget:hover {
                background-color: #d6eaf8;
                border: 2px solid #ff5733;
            }
                                          """)
        self.GPIB_ccntainer.setLayout(GPIB_layout)
        self.initShadowEffect(self.GPIB_ccntainer)
        self.widget_layout.addWidget(self.GPIB_ccntainer,1)
        # ////////////////

        # ///////////////////
        ASLR_layout = QHBoxLayout()
        # IO
        ASLR_icon_label = QLabel()
        ASLR_pixmap = QPixmap('GUI/Icon/ASLR.svg')
        ASLR_pixmap = ASLR_pixmap.scaled(60, 88, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
        ASLR_icon_label.setPixmap(ASLR_pixmap)
        ASLR_icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # Value
        ASLR_icon_connection_layout = QVBoxLayout()
        ASLR_icon_connection_layout.addWidget(ASLR_icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        ASLR_layout.addLayout(ASLR_icon_connection_layout)
        ASLR_connection_layout = QVBoxLayout()
        self.ASLR_Label = QLabel('ASLR Connections:')
        self.ASLR_number_Label = QLabel('None')
        self.ASLR_number_Label.setStyleSheet(self.IOLabel_stylesheet)
        ASLR_connection_layout.addWidget(self.ASLR_Label, alignment=Qt.AlignmentFlag.AlignLeft)
        ASLR_connection_layout.addWidget(self.ASLR_number_Label, alignment=Qt.AlignmentFlag.AlignRight)
        ASLR_layout.addWidget(ASLR_icon_label)
        ASLR_layout.addLayout(ASLR_connection_layout)
        self.ASLR_ccntainer = QWidget()
        self.ASLR_ccntainer.setStyleSheet(
                                          """ 
                                          QWidget{background-color:lightblue; border-radius: 20px;}
                                           QWidget:hover {
                background-color: lightblue;
                border: 2px solid #ff5733;
            }
                                          """)
        self.ASLR_ccntainer.setLayout(ASLR_layout)
        self.widget_layout.addWidget(self.ASLR_ccntainer,1)
        self.initShadowEffect(self.ASLR_ccntainer)
        # ////////////////

        # ///////////////////
        USB_layout = QHBoxLayout()
        # IO
        USB_icon_label = QLabel()
        USB_pixmap = QPixmap('GUI/Icon/USB.svg')
        USB_pixmap = USB_pixmap.scaled(45,88, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        USB_icon_label.setPixmap(USB_pixmap)
        USB_icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # Value
        USB_icon_connection_layout = QVBoxLayout()
        USB_icon_connection_layout.addWidget(USB_icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        USB_layout.addLayout(USB_icon_connection_layout)
        USB_connection_layout = QVBoxLayout()
        self.USB_Label = QLabel('USB Connections:')
        self.USB_number_Label = QLabel('None')
        self.USB_number_Label.setStyleSheet(self.IOLabel_stylesheet)
        USB_connection_layout.addWidget(self.USB_Label, alignment=Qt.AlignmentFlag.AlignLeft)
        USB_connection_layout.addWidget(self.USB_number_Label, alignment=Qt.AlignmentFlag.AlignRight)
        USB_layout.addWidget(USB_icon_label)
        USB_layout.addLayout(USB_connection_layout)
        self.USB_ccntainer = QWidget()
        self.USB_ccntainer.setStyleSheet(""" 
                                          QWidget{background-color: #e8daef; border-radius: 20px;}
                                           QWidget:hover {
                background-color: #e8daef;
                border: 2px solid #ff5733;
            }
                                          """)
        self.USB_ccntainer.setLayout(USB_layout)
        self.initShadowEffect(self.USB_ccntainer)
        self.widget_layout.addWidget(self.USB_ccntainer,1)
        # ////////////////

        # ///////////////////
        TCPIP_layout = QHBoxLayout()
        # IO
        TCPIP_icon_label = QLabel()
        TCPIP_pixmap = QPixmap('GUI/Icon/TCPIP.svg')
        TCPIP_pixmap = TCPIP_pixmap.scaled(70, 88, Qt.AspectRatioMode.KeepAspectRatio,
                                       Qt.TransformationMode.SmoothTransformation)
        TCPIP_icon_label.setPixmap(TCPIP_pixmap)
        TCPIP_icon_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        # Value
        TCPIP_icon_connection_layout = QVBoxLayout()
        TCPIP_icon_connection_layout.addWidget(TCPIP_icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        TCPIP_layout.addLayout(TCPIP_icon_connection_layout)
        TCPIP_connection_layout = QVBoxLayout()
        self.TCPIP_Label = QLabel('Ethernet Connections:')
        self.TCPIP_number_Label = QLabel('None')
        self.TCPIP_number_Label.setStyleSheet(self.IOLabel_stylesheet)
        TCPIP_connection_layout.addWidget(self.TCPIP_Label, alignment=Qt.AlignmentFlag.AlignLeft)
        TCPIP_connection_layout.addWidget(self.TCPIP_number_Label, alignment=Qt.AlignmentFlag.AlignRight)


        TCPIP_layout.addWidget(TCPIP_icon_label)
        TCPIP_layout.addLayout(TCPIP_connection_layout)
        self.TCPIP_ccntainer = QWidget()
        self.TCPIP_ccntainer.setStyleSheet(""" 
                                          QWidget{background-color: peachpuff; border-radius: 20px;}
                                           QWidget:hover {
                background-color: peachpuff;
                border: 2px solid #ff5733;
            }
                                          """)
        self.TCPIP_ccntainer.setLayout(TCPIP_layout)
        self.initShadowEffect(self.TCPIP_ccntainer)
        self.widget_layout.addWidget(self.TCPIP_ccntainer,1)
        self.update_gpib_status()
        # ////////////////
        self.GPIB_Label.setStyleSheet(self.IOLabel_1_stylesheet)
        self.ASLR_Label.setStyleSheet(self.IOLabel_1_stylesheet)
        self.USB_Label.setStyleSheet(self.IOLabel_1_stylesheet)
        self.TCPIP_Label.setStyleSheet(self.IOLabel_1_stylesheet)



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
        # self.main_layout.setContentsMargins(50, 50, 50, 50)
        self.main_layout.addLayout(self.widget_layout,2)
        self.main_layout.addSpacing(20)
        self.main_layout.addLayout(self.pc_status_layout,4)
        self.main_layout.addStretch(1)
        self.container = QWidget()
        self.container.setLayout(self.main_layout)
        self.container.setGeometry(100, 100, 400, 300)
        self.setCentralWidget(self.container)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every 60,000 milliseconds (1 minute)
        self.update_time()

    def initShadowEffect(self, widget):
        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(15)
        shadow_effect.setXOffset(5)
        shadow_effect.setYOffset(5)
        shadow_effect.setColor(QColor(0, 0, 0, 160))
        widget.setGraphicsEffect(None)

        self.shadow_effects.append(shadow_effect)
        widget.shadow_effect = shadow_effect  # Store shadow effect in widget for easy access
        widget.installEventFilter(self)
        # widget.setAttribute(Qt.WidgetAttribute.WA_Hover)

    def eventFilter(self, obj, event):
        if isinstance(obj, QWidget):
            if event.type() == QEvent.Type.HoverEnter:
                self.applyShadowEffect(obj)
            elif event.type() == QEvent.Type.HoverLeave:
                self.removeShadowEffect(obj)
        return super().eventFilter(obj, event)

    # def event(self, event):
    #     if event.type() == QEvent.Type.HoverEnter:
    #         self.applyShadowEffect(event.target())
    #     elif event.type() == QEvent.Type.HoverLeave:
    #         self.removeShadowEffect(event.target())
    #     return super().event(event)

    def applyShadowEffect(self, widget):
        try:
            widget.setGraphicsEffect(widget.shadow_effect)
        except RuntimeError as e:
            self.initShadowEffect(widget)
            widget.setGraphicsEffect(widget.shadow_effect)

    def removeShadowEffect(self, widget):
        widget.setGraphicsEffect(None)

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
            self.GPIB_number_Label.setText(f'{len(self.gpib_ports)}')
            self.USB_number_Label.setText(f'{len(self.usb_ports)}')
            self.ASLR_number_Label.setText(f'{len(self.ASTL_ports)}')
            self.TCPIP_number_Label.setText(f'{len(self.TCP_ports)}')
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))
        QTimer.singleShot(5000, self.update_gpib_status)  # Update every 5 seconds