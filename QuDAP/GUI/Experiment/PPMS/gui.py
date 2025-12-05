from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QLineEdit, QMessageBox, QScrollArea, QSizePolicy)
from PyQt6.QtGui import QFont, QDoubleValidator
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
import sys
import time
import platform
import random
import threading
import traceback
import subprocess
import os
import pyqtgraph as pg
from datetime import datetime

if platform.system() == 'Windows':
    try:
        import MultiPyVu as mpv
        from MultiPyVu import MultiVuClient as mvc, MultiPyVuError

        MULTIVU_AVAILABLE = True
    except ImportError:
        print("MultiPyVu not available")
        MULTIVU_AVAILABLE = False
else:
    MULTIVU_AVAILABLE = False


# ===================== MultiVu Detection =====================
def is_multivu_running():
    """
    Check if MultiVu application is running
    Returns True if detected, False otherwise
    """
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['tasklist'], capture_output=True, text=True, timeout=5)
            if 'MultiVu.exe' in result.stdout or 'Dynacool.exe' in result.stdout or 'Multivu.exe' in result.stdout or 'PpmsMvu.exe' in result.stdout:
                return True
            return False
        else:  # Linux/Mac
            result = subprocess.run(['pgrep', '-f', 'MultiVu'], capture_output=True, timeout=5)
            return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⚠ Timeout checking for MultiVu")
        return False
    except Exception as e:
        print(f"⚠ Error checking for MultiVu: {e}")
        return False


def find_multivu_path():
    """
    Try to find MultiVu installation path
    Returns path if found, None otherwise
    """
    common_paths = [r"C:\Program Files\Quantum Design\MultiVu\MultiVu.exe",
        r"C:\Program Files (x86)\Quantum Design\MultiVu\MultiVu.exe", r"C:\QD\MultiVu\MultiVu.exe",
        r"C:\QdDynacool\MultiVu\MultiVu.exe", r"C:\QdDynacool\MultiVu\Dynacool.exe"]

    for path in common_paths:
        if os.path.exists(path):
            print(f"✓ Found MultiVu at: {path}")
            return path

    print("✗ MultiVu installation not found")
    return None


# ===================== MultiVu Status Check Thread =====================
class MultiVuStatusThread(QThread):
    """Thread to check MultiVu status periodically"""

    status_signal = pyqtSignal(bool)  # True if running, False if not

    def __init__(self, parent=None):
        super().__init__(parent)
        self.should_stop = False

    def run(self):
        """Check MultiVu status every 5 seconds"""
        while not self.should_stop:
            is_running = is_multivu_running()
            self.status_signal.emit(is_running)
            time.sleep(5)

    def stop(self):
        """Stop checking"""
        self.should_stop = True


# ===================== Thread-Safe PPMS Command Executor =====================
class PPMSCommandExecutor:
    """Executes PPMS commands in a separate thread with timeout protection"""

    def __init__(self, client, notification_callback=None):
        self.client = client
        self.notification_callback = notification_callback
        self.result = None
        self.error = None

    def execute_with_timeout(self, func, args=(), kwargs=None, timeout=30):
        """Execute a function with timeout protection"""
        if kwargs is None:
            kwargs = {}

        self.result = None
        self.error = None

        thread = threading.Thread(target=self._run_function, args=(func, args, kwargs))
        thread.daemon = True
        thread.start()
        thread.join(timeout=timeout)

        if thread.is_alive():
            error_msg = f"Command timeout after {timeout} seconds"
            print(f"⚠ {error_msg}")
            if self.notification_callback:
                self.notification_callback(f"PPMS command timed out: {func.__name__}", 'warning')
            return (False, None)

        if self.error:
            print(f"⚠ Command error: {self.error}")
            if self.notification_callback:
                self.notification_callback(f"PPMS command error: {self.error}", 'critical')
            return (False, None)

        return (True, self.result)

    def _run_function(self, func, args, kwargs):
        """Run function in thread"""
        try:
            self.result = func(*args, **kwargs)
        except SystemExit as e:
            self.error = f"SystemExit: {e}"
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"


class ThreadSafePPMSCommands:
    """Thread-safe wrapper for PPMS commands"""

    def __init__(self, client, notification_callback=None):
        self.client = client
        self.notification_callback = notification_callback
        self.executor = PPMSCommandExecutor(client, notification_callback)

    def get_chamber_status(self, timeout=10):
        """Get chamber status with timeout protection"""

        def _get_chamber():
            return self.client.get_chamber()

        success, result = self.executor.execute_with_timeout(_get_chamber, timeout=timeout)
        return success, result

    def read_temperature(self, timeout=10):
        """Read temperature with timeout protection"""

        def _read_temp():
            temperature, status = self.client.get_temperature()
            return (temperature, status)

        success, result = self.executor.execute_with_timeout(_read_temp, timeout=timeout)
        if success and result:
            return (True,) + result
        return (False, None, None)

    def read_field(self, timeout=10):
        """Read magnetic field with timeout protection"""

        def _read_field():
            field, status = self.client.get_field()
            return (field, status)

        success, result = self.executor.execute_with_timeout(_read_field, timeout=timeout)
        if success and result:
            return (True,) + result
        return (False, None, None)

    def set_temperature(self, set_point, temp_rate, mode, timeout=30):
        """Set temperature with timeout protection"""

        def _set_temp():
            self.client.set_temperature(set_point, temp_rate, mode)
            print(f"✓ Temperature set to {set_point} K")

        success, _ = self.executor.execute_with_timeout(_set_temp, timeout=timeout)
        return success

    def set_field(self, set_point, field_rate, mode, timeout=30):
        """Set field with timeout protection"""

        def _set_field():
            self.client.set_field(set_point, field_rate, mode)
            print(f"✓ Field set to {set_point} Oe")

        success, _ = self.executor.execute_with_timeout(_set_field, timeout=timeout)
        return success


# ===================== Reading Thread =====================
class PPMSReadingThread(QThread):
    """Thread to continuously read PPMS parameters"""

    update_data = pyqtSignal(float, str, float, str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, safe_commands, parent=None):
        super().__init__(parent)
        self.safe_commands = safe_commands
        self.should_stop = False

    def run(self):
        """Continuously read PPMS parameters"""
        while not self.should_stop:
            try:
                # Read temperature
                success_t, temp, temp_status = self.safe_commands.read_temperature(timeout=5)
                if not success_t:
                    temp, temp_status = 0.0, "Error"

                # Read field
                success_f, field, field_status = self.safe_commands.read_field(timeout=5)
                if not success_f:
                    field, field_status = 0.0, "Error"

                # Read chamber
                success_c, chamber = self.safe_commands.get_chamber_status(timeout=5)
                if not success_c:
                    chamber = "Unknown"

                self.update_data.emit(temp, temp_status, field, field_status, chamber)
                time.sleep(1)

            except Exception as e:
                self.error_signal.emit(f"Reading error: {str(e)}")
                break

    def stop(self):
        """Stop reading"""
        self.should_stop = True


# ===================== Main PPMS Widget =====================
class PPMS(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PPMS Control Interface")
        self.setGeometry(100, 100, 1600, 900)

        # State variables
        self.server = None
        self.client = None
        self.safe_commands = None
        self.reading_thread = None
        self.multivu_status_thread = None
        self.isConnect = False
        self.server_running = False
        self.client_running = False
        self.multivu_running = False

        # Data storage for plots
        self.time_data = []
        self.temp_data = []
        self.field_data = []
        self.start_time = time.time()

        self.font = QFont("Arial", 10)
        self.titlefont = QFont("Arial", 14)
        self.titlefont.setBold(True)

        # Load stylesheets
        try:
            with open("GUI/QSS/QScrollbar.qss", "r") as file:
                self.scrollbar_stylesheet = file.read()
        except:
            self.scrollbar_stylesheet = """
                QScrollBar:vertical {
                    border: none;
                    background: #f0f0f0;
                    width: 10px;
                    margin: 0px;
                }
                QScrollBar::handle:vertical {
                    background: #c0c0c0;
                    min-height: 20px;
                    border-radius: 5px;
                }
                QScrollBar::handle:vertical:hover {
                    background: #a0a0a0;
                }
            """

        try:
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.combo_stylesheet = file.read()
        except:
            self.combo_stylesheet = ""

        try:
            with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                self.button_stylesheet = file.read()
        except:
            self.button_stylesheet = ""

        self.init_ui()

        # Start MultiVu status monitoring
        if MULTIVU_AVAILABLE:
            self.start_multivu_monitoring()

    def init_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Left panel with scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setStyleSheet(self.scrollbar_stylesheet)
        self.scroll_area.setFixedWidth(500)

        left_content = QWidget()
        left_content.setMaximumWidth(480)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setSpacing(10)

        # Title
        title = QLabel("Physical Property Measurement System")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Setup all sections
        self.setup_multivu_status_section(self.left_layout)
        self.setup_connection_section(self.left_layout)
        self.setup_readings_section(self.left_layout)
        self.setup_temperature_control_section(self.left_layout)
        self.setup_field_control_section(self.left_layout)
        self.setup_chamber_control_section(self.left_layout)
        self.setup_data_control_section(self.left_layout)

        self.left_layout.addStretch()

        left_content.setLayout(self.left_layout)
        self.scroll_area.setWidget(left_content)

        # Right panel - Plots
        right_panel = self.create_plot_panel()

        main_layout.addWidget(self.scroll_area)
        main_layout.addWidget(right_panel, 1)

        central_widget.setLayout(main_layout)

    def setup_multivu_status_section(self, parent_layout):
        """Setup MultiVu status indicator section"""
        status_group = QGroupBox("MultiVu Status")
        status_layout = QHBoxLayout()

        status_label = QLabel("Status:")
        status_label.setFont(self.font)
        status_label.setFixedWidth(100)

        self.multivu_status_label = QLabel("Checking...")
        self.multivu_status_label.setFont(self.font)
        self.multivu_status_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                border-radius: 3px;
                background-color: #FFA500;
                color: white;
                font-weight: bold;
            }
        """)

        self.check_multivu_btn = QPushButton("Check Now")
        self.check_multivu_btn.clicked.connect(self.check_multivu_now)
        self.check_multivu_btn.setFont(self.font)
        self.check_multivu_btn.setMinimumHeight(30)
        # self.check_multivu_btn.setStyleSheet(self.button_stylesheet)

        status_layout.addWidget(status_label)
        status_layout.addWidget(self.multivu_status_label, 1)
        status_layout.addWidget(self.check_multivu_btn)

        status_group.setLayout(status_layout)
        parent_layout.addWidget(status_group)

    def setup_connection_section(self, parent_layout):
        """Setup device connection section"""
        connection_group = QGroupBox("Device Connection")
        connection_layout = QVBoxLayout()

        # Host and Port
        host_layout = QHBoxLayout()
        host_label = QLabel("Host:")
        host_label.setFont(self.font)
        host_label.setFixedWidth(100)
        self.host_entry = QLineEdit("127.0.0.1")
        self.host_entry.setFont(self.font)
        self.host_entry.setFixedHeight(30)
        host_layout.addWidget(host_label)
        host_layout.addWidget(self.host_entry, 1)
        connection_layout.addLayout(host_layout)

        port_layout = QHBoxLayout()
        port_label = QLabel("Port:")
        port_label.setFont(self.font)
        port_label.setFixedWidth(100)
        self.port_entry = QLineEdit("5000")
        self.port_entry.setFont(self.font)
        self.port_entry.setFixedHeight(30)
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_entry, 1)
        connection_layout.addLayout(port_layout)

        # Buttons
        button_layout = QHBoxLayout()
        self.server_btn = QPushButton("Start Server")
        self.server_btn.clicked.connect(self.toggle_server)
        self.server_btn.setFont(self.font)
        self.server_btn.setMinimumHeight(30)
        # self.server_btn.setStyleSheet(self.button_stylesheet)

        self.client_btn = QPushButton("Connect Client")
        self.client_btn.clicked.connect(self.toggle_client)
        self.client_btn.setEnabled(False)
        self.client_btn.setFont(self.font)
        self.client_btn.setMinimumHeight(30)
        # self.client_btn.setStyleSheet(self.button_stylesheet)

        button_layout.addWidget(self.server_btn)
        button_layout.addWidget(self.client_btn)
        connection_layout.addLayout(button_layout)

        connection_group.setLayout(connection_layout)
        parent_layout.addWidget(connection_group)

    def setup_readings_section(self, parent_layout):
        """Setup current readings section"""
        readings_group = QGroupBox("Current Readings")
        readings_layout = QVBoxLayout()

        # Temperature
        temp_layout = QHBoxLayout()
        temp_label = QLabel("Temperature:")
        temp_label.setFont(self.font)
        temp_label.setFixedWidth(100)
        self.temp_reading_label = QLabel("N/A K")
        self.temp_reading_label.setFont(self.font)
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temp_reading_label, 1)
        readings_layout.addLayout(temp_layout)

        temp_status_layout = QHBoxLayout()
        temp_status_label = QLabel("Status:")
        temp_status_label.setFont(self.font)
        temp_status_label.setFixedWidth(100)
        self.temp_status_label = QLabel("Unknown")
        self.temp_status_label.setFont(self.font)
        temp_status_layout.addWidget(temp_status_label)
        temp_status_layout.addWidget(self.temp_status_label, 1)
        readings_layout.addLayout(temp_status_layout)

        # Field
        field_layout = QHBoxLayout()
        field_label = QLabel("Field:")
        field_label.setFont(self.font)
        field_label.setFixedWidth(100)
        self.field_reading_label = QLabel("N/A Oe")
        self.field_reading_label.setFont(self.font)
        field_layout.addWidget(field_label)
        field_layout.addWidget(self.field_reading_label, 1)
        readings_layout.addLayout(field_layout)

        field_status_layout = QHBoxLayout()
        field_status_label = QLabel("Status:")
        field_status_label.setFont(self.font)
        field_status_label.setFixedWidth(100)
        self.field_status_label = QLabel("Unknown")
        self.field_status_label.setFont(self.font)
        field_status_layout.addWidget(field_status_label)
        field_status_layout.addWidget(self.field_status_label, 1)
        readings_layout.addLayout(field_status_layout)

        # Chamber
        chamber_layout = QHBoxLayout()
        chamber_label = QLabel("Chamber:")
        chamber_label.setFont(self.font)
        chamber_label.setFixedWidth(100)
        self.chamber_reading_label = QLabel("Unknown")
        self.chamber_reading_label.setFont(self.font)
        chamber_layout.addWidget(chamber_label)
        chamber_layout.addWidget(self.chamber_reading_label, 1)
        readings_layout.addLayout(chamber_layout)

        readings_group.setLayout(readings_layout)
        parent_layout.addWidget(readings_group)

    def setup_temperature_control_section(self, parent_layout):
        """Setup temperature control section"""
        temp_group = QGroupBox("Temperature Control")
        temp_layout = QVBoxLayout()

        # Target temperature
        target_layout = QHBoxLayout()
        target_label = QLabel("Target (K):")
        target_label.setFont(self.font)
        target_label.setFixedWidth(100)
        self.temp_target_entry = QLineEdit()
        self.temp_target_entry.setFont(self.font)
        self.temp_target_entry.setFixedHeight(30)
        self.temp_target_entry.setPlaceholderText("1.8 - 400")
        temp_validator = QDoubleValidator(1.8, 400.0, 2)
        self.temp_target_entry.setValidator(temp_validator)
        k_label = QLabel("K")
        k_label.setFont(self.font)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.temp_target_entry, 1)
        target_layout.addWidget(k_label)
        temp_layout.addLayout(target_layout)

        # Rate and mode
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate (K/min):")
        rate_label.setFont(self.font)
        rate_label.setFixedWidth(100)
        self.temp_rate_entry = QLineEdit()
        self.temp_rate_entry.setFont(self.font)
        self.temp_rate_entry.setFixedHeight(30)
        self.temp_rate_entry.setPlaceholderText("1 - 50")
        rate_validator = QDoubleValidator(0, 50.0, 2)
        self.temp_rate_entry.setValidator(rate_validator)

        self.temp_mode_combo = QComboBox()
        self.temp_mode_combo.setFont(self.font)
        self.temp_mode_combo.setStyleSheet(self.combo_stylesheet)
        self.temp_mode_combo.addItems(["Fast Settle", "No Overshoot"])

        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.temp_rate_entry, 1)
        rate_layout.addWidget(self.temp_mode_combo, 1)
        temp_layout.addLayout(rate_layout)

        # Set button
        self.set_temp_btn = QPushButton("Set Temperature")
        self.set_temp_btn.clicked.connect(self.set_temperature)
        self.set_temp_btn.setFont(self.font)
        self.set_temp_btn.setMinimumHeight(30)
        # self.set_temp_btn.setStyleSheet(self.button_stylesheet)
        temp_layout.addWidget(self.set_temp_btn)

        temp_group.setLayout(temp_layout)
        parent_layout.addWidget(temp_group)

    def setup_field_control_section(self, parent_layout):
        """Setup field control section"""
        field_group = QGroupBox("Field Control")
        field_layout = QVBoxLayout()

        # Target field
        target_layout = QHBoxLayout()
        target_label = QLabel("Target (Oe):")
        target_label.setFont(self.font)
        target_label.setFixedWidth(100)
        self.field_target_entry = QLineEdit()
        self.field_target_entry.setFont(self.font)
        self.field_target_entry.setFixedHeight(30)
        self.field_target_entry.setPlaceholderText("-90000 to 90000")
        field_validator = QDoubleValidator(-90000.0, 90000.0, 2)
        self.field_target_entry.setValidator(field_validator)
        oe_label = QLabel("Oe")
        oe_label.setFont(self.font)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.field_target_entry, 1)
        target_layout.addWidget(oe_label)
        field_layout.addLayout(target_layout)

        # Rate and mode
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Rate (Oe/s):")
        rate_label.setFont(self.font)
        rate_label.setFixedWidth(100)
        self.field_rate_entry = QLineEdit()
        self.field_rate_entry.setFont(self.font)
        self.field_rate_entry.setFixedHeight(30)
        self.field_rate_entry.setPlaceholderText("0 - 220")
        rate_validator = QDoubleValidator(0, 220.0, 2)
        self.field_rate_entry.setValidator(rate_validator)

        self.field_mode_combo = QComboBox()
        self.field_mode_combo.setFont(self.font)
        self.field_mode_combo.setStyleSheet(self.combo_stylesheet)
        self.field_mode_combo.addItems(["Linear", "No Overshoot", "Oscillate"])

        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.field_rate_entry, 1)
        rate_layout.addWidget(self.field_mode_combo, 1)
        field_layout.addLayout(rate_layout)

        # Set button
        self.set_field_btn = QPushButton("Set Field")
        self.set_field_btn.clicked.connect(self.set_field)
        self.set_field_btn.setFont(self.font)
        self.set_field_btn.setMinimumHeight(30)
        # self.set_field_btn.setStyleSheet(self.button_stylesheet)
        field_layout.addWidget(self.set_field_btn)

        field_group.setLayout(field_layout)
        parent_layout.addWidget(field_group)

    def setup_chamber_control_section(self, parent_layout):
        """Setup chamber control section"""
        chamber_group = QGroupBox("Chamber Control")
        chamber_layout = QVBoxLayout()

        # Chamber mode
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Mode:")
        mode_label.setFont(self.font)
        mode_label.setFixedWidth(100)
        self.chamber_mode_combo = QComboBox()
        self.chamber_mode_combo.setFont(self.font)
        self.chamber_mode_combo.setStyleSheet(self.combo_stylesheet)
        self.chamber_mode_combo.addItems(
            ["Select", "Seal", "Purge/Seal", "Vent/Seal", "Pump Continuous", "Vent Continuous", "High Vacuum"])
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.chamber_mode_combo, 1)
        chamber_layout.addLayout(mode_layout)

        # Set button
        self.set_chamber_btn = QPushButton("Set Chamber")
        self.set_chamber_btn.clicked.connect(self.set_chamber)
        self.set_chamber_btn.setFont(self.font)
        self.set_chamber_btn.setMinimumHeight(30)
        # self.set_chamber_btn.setStyleSheet(self.button_stylesheet)
        chamber_layout.addWidget(self.set_chamber_btn)

        chamber_group.setLayout(chamber_layout)
        parent_layout.addWidget(chamber_group)

    def setup_data_control_section(self, parent_layout):
        """Setup data control section"""
        data_group = QGroupBox("Data Control")
        data_layout = QVBoxLayout()

        self.clear_data_btn = QPushButton("Clear Plot Data")
        self.clear_data_btn.clicked.connect(self.clear_plot_data)
        self.clear_data_btn.setFont(self.font)
        self.clear_data_btn.setMinimumHeight(30)
        # self.clear_data_btn.setStyleSheet(self.button_stylesheet)

        self.save_data_btn = QPushButton("Save Data")
        self.save_data_btn.clicked.connect(self.save_data)
        self.save_data_btn.setFont(self.font)
        self.save_data_btn.setMinimumHeight(30)
        # self.save_data_btn.setStyleSheet(self.button_stylesheet)

        data_layout.addWidget(self.clear_data_btn)
        data_layout.addWidget(self.save_data_btn)

        data_group.setLayout(data_layout)
        parent_layout.addWidget(data_group)

    def create_plot_panel(self):
        """Create the plot panel with two PyQtGraph plots"""
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        plot_title = QLabel("PPMS Real-time Monitoring")
        plot_title_font = QFont()
        plot_title_font.setPointSize(12)
        plot_title_font.setBold(True)
        plot_title.setFont(plot_title_font)
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_layout.addWidget(plot_title)

        # Temperature plot
        self.temp_plot_widget = pg.PlotWidget()
        self.temp_plot_widget.setBackground('w')
        self.temp_plot_widget.setLabel('left', 'Temperature', units='K')
        self.temp_plot_widget.setLabel('bottom', 'Time', units='s')
        self.temp_plot_widget.setTitle('Temperature vs Time')
        self.temp_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.temp_plot_widget.addLegend()

        self.temp_curve = self.temp_plot_widget.plot(pen=pg.mkPen(color=(255, 0, 0), width=2), symbol='o', symbolSize=4,
            symbolBrush=(255, 0, 0), name='Temperature')

        # Field plot
        self.field_plot_widget = pg.PlotWidget()
        self.field_plot_widget.setBackground('w')
        self.field_plot_widget.setLabel('left', 'Field', units='Oe')
        self.field_plot_widget.setLabel('bottom', 'Time', units='s')
        self.field_plot_widget.setTitle('Magnetic Field vs Time')
        self.field_plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.field_plot_widget.addLegend()

        self.field_curve = self.field_plot_widget.plot(pen=pg.mkPen(color=(0, 0, 255), width=2), symbol='o',
            symbolSize=4, symbolBrush=(0, 0, 255), name='Field')

        right_layout.addWidget(self.temp_plot_widget)
        right_layout.addWidget(self.field_plot_widget)

        right_panel.setLayout(right_layout)
        return right_panel

    def start_multivu_monitoring(self):
        """Start MultiVu status monitoring thread"""
        self.multivu_status_thread = MultiVuStatusThread()
        self.multivu_status_thread.status_signal.connect(self.update_multivu_status)
        self.multivu_status_thread.start()

    def check_multivu_now(self):
        """Manually check MultiVu status"""
        is_running = is_multivu_running()
        self.update_multivu_status(is_running)

        if is_running:
            path = find_multivu_path()
            if path:
                QMessageBox.information(self, "MultiVu Status", f"MultiVu is running\nPath: {path}")
            else:
                QMessageBox.information(self, "MultiVu Status", "MultiVu is running")
        else:
            QMessageBox.warning(self, "MultiVu Status",
                                "MultiVu is not running\n\nPlease start MultiVu before connecting to PPMS")

    def update_multivu_status(self, is_running):
        """Update MultiVu status indicator"""
        self.multivu_running = is_running

        if is_running:
            self.multivu_status_label.setText("✓ Running")
            self.multivu_status_label.setStyleSheet("""
                QLabel {
                    padding: 5px;
                    border-radius: 3px;
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                }
            """)
            self.server_btn.setEnabled(True)
        else:
            self.multivu_status_label.setText("✗ Not Running")
            self.multivu_status_label.setStyleSheet("""
                QLabel {
                    padding: 5px;
                    border-radius: 3px;
                    background-color: #F44336;
                    color: white;
                    font-weight: bold;
                }
            """)
            # Disable server button if MultiVu is not running
            if not self.server_running:
                self.server_btn.setEnabled(False)

    def toggle_server(self):
        """Toggle PPMS server"""
        if not MULTIVU_AVAILABLE:
            QMessageBox.warning(self, "Error", "MultiPyVu library is not available")
            return

        if not self.multivu_running and not self.server_running:
            QMessageBox.warning(self, "MultiVu Not Running",
                                "MultiVu is not running. Please start MultiVu before starting the server.")
            return

        if not self.server_running:
            try:
                self.server = mpv.Server()
                self.server.open()
                self.server_btn.setText("Stop Server")
                self.server_running = True
                self.client_btn.setEnabled(True)
                QMessageBox.information(self, "Success", "Server started successfully")
            except SystemExit as e:
                QMessageBox.critical(self, "Error",
                                     "No running instance of MultiVu detected.\nPlease start MultiVu and retry.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to start server:\n{str(e)}")
        else:
            try:
                if self.client_running:
                    self.toggle_client()
                if self.server:
                    self.server.close_server()
                self.server_btn.setText("Start Server")
                self.server_running = False
                self.client_btn.setEnabled(False)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to stop server:\n{str(e)}")

    def toggle_client(self):
        """Toggle PPMS client connection"""
        if not MULTIVU_AVAILABLE:
            QMessageBox.warning(self, "Error", "MultiPyVu library is not available")
            return

        if not self.client_running:
            try:
                host = self.host_entry.text()
                port = int(self.port_entry.text())

                self.client = mpv.Client(host=host, port=port)
                self.client.open()

                # Create thread-safe command wrapper
                self.safe_commands = ThreadSafePPMSCommands(self.client, notification_callback=self.show_notification)

                # Start reading thread
                self.reading_thread = PPMSReadingThread(self.safe_commands)
                self.reading_thread.update_data.connect(self.update_readings)
                self.reading_thread.error_signal.connect(self.on_reading_error)
                self.reading_thread.start()

                self.client_btn.setText("Disconnect Client")
                self.client_running = True
                self.server_btn.setEnabled(False)

                # Reset start time for plots
                self.start_time = time.time()

                QMessageBox.information(self, "Success", "Client connected successfully")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to connect client:\n{str(e)}")
        else:
            try:
                if self.reading_thread and self.reading_thread.isRunning():
                    self.reading_thread.stop()
                    self.reading_thread.wait()

                if self.client:
                    self.client.close_client()
                    self.client = None

                self.safe_commands = None
                self.client_btn.setText("Connect Client")
                self.client_running = False
                self.server_btn.setEnabled(True)

                # Reset readings
                self.temp_reading_label.setText("N/A K")
                self.temp_status_label.setText("Unknown")
                self.field_reading_label.setText("N/A Oe")
                self.field_status_label.setText("Unknown")
                self.chamber_reading_label.setText("Unknown")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to disconnect client:\n{str(e)}")

    def update_readings(self, temp, temp_status, field, field_status, chamber):
        """Update readings from PPMS"""
        # Update labels
        self.temp_reading_label.setText(f"{temp:.2f} K")
        self.temp_status_label.setText(temp_status)
        self.field_reading_label.setText(f"{field:.1f} Oe")
        self.field_status_label.setText(field_status)
        self.chamber_reading_label.setText(chamber)

        # Update plots
        elapsed_time = time.time() - self.start_time
        self.time_data.append(elapsed_time)
        self.temp_data.append(temp)
        self.field_data.append(field)

        self.temp_curve.setData(self.time_data, self.temp_data)
        self.field_curve.setData(self.time_data, self.field_data)

    def on_reading_error(self, error_msg):
        """Handle reading error"""
        print(f"Reading error: {error_msg}")

    def show_notification(self, message, level='info'):
        """Show notification message"""
        print(f"[{level.upper()}] {message}")

    def set_temperature(self):
        """Set temperature"""
        if not self.client_running or not self.safe_commands:
            QMessageBox.warning(self, "Error", "Please connect to PPMS client first")
            return

        target = self.temp_target_entry.text()
        rate = self.temp_rate_entry.text()

        if not target or not rate:
            QMessageBox.warning(self, "Error", "Please enter target temperature and rate")
            return

        try:
            target = float(target)
            rate = float(rate)

            # Get mode
            mode_idx = self.temp_mode_combo.currentIndex()
            if mode_idx == 0:
                mode = self.client.temperature.approach_mode.fast_settle
            else:
                mode = self.client.temperature.approach_mode.no_overshoot

            # Stop reading thread
            if self.reading_thread and self.reading_thread.isRunning():
                self.reading_thread.stop()
                self.reading_thread.wait()

            # Set temperature
            success = self.safe_commands.set_temperature(target, rate, mode, timeout=30)

            if success:
                QMessageBox.information(self, "Success", f"Temperature set to {target} K")
            else:
                QMessageBox.warning(self, "Error", "Failed to set temperature")

            # Restart reading thread
            self.reading_thread = PPMSReadingThread(self.safe_commands)
            self.reading_thread.update_data.connect(self.update_readings)
            self.reading_thread.error_signal.connect(self.on_reading_error)
            self.reading_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set temperature:\n{str(e)}")

    def set_field(self):
        """Set magnetic field"""
        if not self.client_running or not self.safe_commands:
            QMessageBox.warning(self, "Error", "Please connect to PPMS client first")
            return

        target = self.field_target_entry.text()
        rate = self.field_rate_entry.text()

        if not target or not rate:
            QMessageBox.warning(self, "Error", "Please enter target field and rate")
            return

        try:
            target = float(target)
            rate = float(rate)

            # Get mode
            mode_idx = self.field_mode_combo.currentIndex()
            if mode_idx == 0:
                mode = self.client.field.approach_mode.linear
            elif mode_idx == 1:
                mode = self.client.field.approach_mode.no_overshoot
            else:
                mode = self.client.field.approach_mode.oscillate

            # Stop reading thread
            if self.reading_thread and self.reading_thread.isRunning():
                self.reading_thread.stop()
                self.reading_thread.wait()

            # Set field
            success = self.safe_commands.set_field(target, rate, mode, timeout=30)

            if success:
                QMessageBox.information(self, "Success", f"Field set to {target} Oe")
            else:
                QMessageBox.warning(self, "Error", "Failed to set field")

            # Restart reading thread
            self.reading_thread = PPMSReadingThread(self.safe_commands)
            self.reading_thread.update_data.connect(self.update_readings)
            self.reading_thread.error_signal.connect(self.on_reading_error)
            self.reading_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set field:\n{str(e)}")

    def set_chamber(self):
        """Set chamber mode"""
        if not self.client_running or not self.safe_commands:
            QMessageBox.warning(self, "Error", "Please connect to PPMS client first")
            return

        mode_idx = self.chamber_mode_combo.currentIndex()
        if mode_idx == 0:
            QMessageBox.warning(self, "Error", "Please select a chamber mode")
            return

        try:
            # Stop reading thread
            if self.reading_thread and self.reading_thread.isRunning():
                self.reading_thread.stop()
                self.reading_thread.wait()
                time.sleep(1)

            # Set chamber based on selection
            modes = [None, self.client.chamber.mode.seal, self.client.chamber.mode.purge_seal,
                self.client.chamber.mode.vent_seal, self.client.chamber.mode.pump_continuous,
                self.client.chamber.mode.vent_continuous, self.client.chamber.mode.high_vacuum]

            if mode_idx < len(modes):
                self.client.set_chamber(modes[mode_idx])
                QMessageBox.information(self, "Success", "Chamber mode set successfully")

            # Restart reading thread
            time.sleep(1)
            self.reading_thread = PPMSReadingThread(self.safe_commands)
            self.reading_thread.update_data.connect(self.update_readings)
            self.reading_thread.error_signal.connect(self.on_reading_error)
            self.reading_thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to set chamber:\n{str(e)}")

    def clear_plot_data(self):
        """Clear plot data"""
        self.time_data = []
        self.temp_data = []
        self.field_data = []
        self.temp_curve.setData([], [])
        self.field_curve.setData([], [])
        self.start_time = time.time()
        QMessageBox.information(self, "Success", "Plot data cleared")

    def save_data(self):
        """Save data to CSV"""
        if not self.time_data:
            QMessageBox.warning(self, "No Data", "No data to save")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ppms_data_{timestamp}.csv"

            with open(filename, 'w') as f:
                f.write("Time (s),Temperature (K),Field (Oe)\n")
                for i in range(len(self.time_data)):
                    f.write(f"{self.time_data[i]},{self.temp_data[i]},{self.field_data[i]}\n")

            QMessageBox.information(self, "Success",
                                    f"Data saved to:\n{filename}\n\nTotal points: {len(self.time_data)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data:\n{str(e)}")

    def closeEvent(self, event):
        """Handle window close"""
        # Stop MultiVu monitoring
        if self.multivu_status_thread and self.multivu_status_thread.isRunning():
            self.multivu_status_thread.stop()
            self.multivu_status_thread.wait()

        # Stop reading thread
        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()

        # Close client
        if self.client:
            try:
                self.client.close_client()
            except:
                pass

        # Close server
        if self.server:
            try:
                self.server.close_server()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PPMS()
    window.show()
    sys.exit(app.exec())