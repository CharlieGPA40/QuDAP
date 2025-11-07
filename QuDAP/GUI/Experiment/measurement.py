import sys
import csv
from typing import Optional, Dict, Any, List, Tuple
import subprocess
import random
import time
import platform
import datetime
import traceback
import os
import requests
import threading

import pyvisa as visa
import matplotlib
import numpy as np
if platform.system() == 'Windows':
    import MultiPyVu as mpv  # Uncommented it on the server computer
    from MultiPyVu import MultiVuClient as mvc, MultiPyVuError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from PyQt6.QtWidgets import (
    QSizePolicy, QWidget, QMessageBox, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout,
    QCheckBox, QTextEdit, QPushButton, QComboBox, QLineEdit, QScrollArea, QDialog, QRadioButton, QMainWindow,
    QDialogButtonBox, QProgressBar, QButtonGroup, QApplication, QCompleter, QToolButton
)
from PyQt6.QtGui import QIcon, QFont, QDoubleValidator, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread, QSettings, QSize
from PyQt6.QtGui import QKeyEvent

# for simulation purpose
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
try:
    # from GUI.Experiment.BNC845RF import COMMAND
    from QuDAP.GUI.Experiment.rigol_experiment import RIGOL_Measurement
    from QuDAP.GUI.Experiment.fmr_measurement import FMR_Measurement
    from QuDAP.instrument.BK_precision_9129B import BK_9129_COMMAND
    from QuDAP.instrument.rigol_spectrum_analyzer import RIGOL_COMMAND
    from QuDAP.instrument.BNC845 import BNC_845M_COMMAND
except ImportError:
    # from QuDAP.GUI.Experiment.BNC845RF import COMMAND
    from GUI.Experiment.rigol_experiment import RIGOL_Measurement
    from GUI.Experiment.fmr_measurement import FMR_Measurement
    from instrument.BK_precision_9129B import BK_9129_COMMAND
    from instrument.rigol_spectrum_analyzer import RIGOL_COMMAND
    from instrument.BNC845 import BNC_845M_COMMAND
    

class ExitProtection:
    def __init__(self):
        self.original_exit = sys.exit

    def install(self):
        sys.exit = self._protected_exit
        # print("✓ Exit protection installed")

    def uninstall(self):
        sys.exit = self.original_exit

    def _protected_exit(self, code=0):
        print(f"⚠ Prevented sys.exit({code}) - Application continues running")
        return  # Don't actually exit

def is_multivu_running():
    """
    Check if MultiVu application is running
    Returns True if detected, False otherwise
    """
    try:
        if os.name == 'nt':  # Windows

            result = subprocess.run(
                ['tasklist'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if 'MultiVu.exe' in result.stdout or 'Dynacool.exe' in result.stdout or 'Multivu.exe' in result.stdout:
                is_running = True
            else:
                is_running = False

            return is_running

        else:  # Linux/Mac
            result = subprocess.run(
                ['pgrep', '-f', 'MultiVu'],
                capture_output=True,
                timeout=5
            )
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
    common_paths = [
        r"C:\Program Files\Quantum Design\MultiVu\MultiVu.exe",
        r"C:\Program Files (x86)\Quantum Design\MultiVu\MultiVu.exe",
        r"C:\QD\MultiVu\MultiVu.exe",
        r"C:\QdDynacool\MultiVu\MultiVu.exe",
        r"C:\QdDynacool\MultiVu\Dynacool.exe"
    ]

    for path in common_paths:
        if os.path.exists(path):
            print(f"✓ Found MultiVu at: {path}")
            return path

    print("✗ MultiVu installation not found")
    return None

class PPMSCommandExecutor:
    """
    Executes PPMS commands in a separate thread with timeout protection
    """

    def __init__(self, client, notification_manager=None):
        """
        Args:
            client: MultiPyVu client instance
            notification_manager: NotificationManager instance for alerts
        """
        self.client = client
        self.notification_manager = notification_manager
        self.result = None
        self.error = None

    def execute_with_timeout(self, func, args=(), kwargs=None, timeout=30):
        """
        Execute a function with timeout protection

        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            timeout: Timeout in seconds

        Returns:
            Tuple (success: bool, result: any)
        """
        if kwargs is None:
            kwargs = {}

        self.result = None
        self.error = None

        # Create thread
        thread = threading.Thread(
            target=self._run_function,
            args=(func, args, kwargs)
        )
        thread.daemon = True

        # Start thread
        thread.start()

        # Wait with timeout
        thread.join(timeout=timeout)

        # Check if still running
        if thread.is_alive():
            error_msg = f"Command timeout after {timeout} seconds"
            print(f"⚠ {error_msg}")

            if self.notification_manager:
                self.notification_manager.send_message(
                    f"PPMS command timed out: {func.__name__}",
                    'warning'
                )

            return (False, None)

        # Check for errors
        if self.error:
            print(f"⚠ Command error: {self.error}")

            if self.notification_manager:
                self.notification_manager.send_message(
                    f"PPMS command error: {self.error}",
                    'critical'
                )

            return (False, None)

        return (True, self.result)

    def _run_function(self, func, args, kwargs):
        """Run function in thread (internal use)"""
        try:
            self.result = func(*args, **kwargs)
        except SystemExit as e:
            self.error = f"SystemExit: {e}"
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}\n{traceback.format_exc()}"

class ThreadSafePPMSCommands:
    """
    Thread-safe wrapper for your PPMS commands
    """

    def __init__(self, client, notification_manager=None):
        self.client = client
        self.notification_manager = notification_manager
        self.executor = PPMSCommandExecutor(client, notification_manager)

    def get_chamber_status(self, timeout=10):
        """
        Get chamber status with timeout protection

        Args:
            timeout: Timeout in seconds

        Returns:
            Tuple (success: bool, chamber_status: any)
        """

        def _get_chamber():
            try:
                return self.client.get_chamber()
            except SystemExit as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Chamber status error: {e}", 'critical'
                    )
                raise
            except Exception as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Chamber status error: {e}", 'critical'
                    )
                raise

        success, result = self.executor.execute_with_timeout(
            _get_chamber,
            timeout=timeout
        )

        return success, result

    def set_temperature(self, set_point, temp_rate, timeout=30):
        """
        Set temperature with timeout protection

        Args:
            set_point: Target temperature (K)
            temp_rate: Temperature rate (K/min)
            timeout: Timeout in seconds

        Returns:
            bool: Success status
        """

        def _set_temp():
            try:
                self.client.set_temperature(
                    set_point,
                    temp_rate,
                    self.client.temperature.approach_mode.fast_settle
                )
                print(f"✓ Temperature set to {set_point} K")
            except SystemExit as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Temperature set error: {e}", 'critical'
                    )
                raise
            except Exception as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Temperature status error: {e}", 'critical'
                    )
                raise

        success, _ = self.executor.execute_with_timeout(
            _set_temp,
            timeout=timeout
        )

        return success

    def set_field(self, set_point, field_rate, append_text_func=None, timeout=30):
        """
        Set magnetic field with timeout protection

        Args:
            set_point: Target field (Oe)
            field_rate: Field rate (Oe/s)
            append_text_func: Optional function to append text to GUI
            timeout: Timeout in seconds

        Returns:
            bool: Success status
        """

        def _set_field():
            try:
                self.client.set_field(
                    set_point,
                    field_rate,
                    self.client.field.approach_mode.linear,
                    self.client.field.driven_mode.driven
                )

                if append_text_func:
                    append_text_func(f'Setting Field to {set_point} Oe... \n', 'orange')
                else:
                    print(f"✓ Field set to {set_point} Oe")

            except SystemExit as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Field set error: {e}", 'critical'
                    )
                raise
            except Exception as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Field status error: {e}", 'critical'
                    )
                raise

        success, _ = self.executor.execute_with_timeout(
            _set_field,
            timeout=timeout
        )

        return success

    def read_temperature(self, timeout=10):
        """
        Read temperature with timeout protection

        Args:
            timeout: Timeout in seconds

        Returns:
            Tuple (success: bool, temperature: float, status: str, unit: str)
        """

        def _read_temp():
            try:
                temperature, status = self.client.get_temperature()
                temp_unit = self.client.temperature.units
                return (temperature, status, temp_unit)
            except SystemExit as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Temperature read error: {e}", 'critical'
                    )
                raise
            except Exception as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Temperature status error: {e}", 'critical'
                    )
                raise

        success, result = self.executor.execute_with_timeout(
            _read_temp,
            timeout=timeout
        )

        if success and result:
            return (True,) + result
        else:
            return (False, None, None, None)

    def read_field(self, timeout=10):
        """
        Read magnetic field with timeout protection

        Args:
            timeout: Timeout in seconds

        Returns:
            Tuple (success: bool, field: float, status: str, unit: str)
        """

        def _read_field():
            try:
                field, status = self.client.get_field()
                field_unit = self.client.field.units
                return (field, status, field_unit)
            except SystemExit as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Field read error: {e}", 'critical'
                    )
                raise
            except Exception as e:
                tb_str = traceback.format_exc()
                if self.notification_manager:
                    self.notification_manager.send_message(
                        f"Field status error: {e}", 'critical'
                    )
                raise

        success, result = self.executor.execute_with_timeout(
            _read_field,
            timeout=timeout
        )

        if success and result:
            return (True,) + result
        else:
            return (False, None, None, None)

    def wait_for_temperature(self, target_temp, tolerance=0.5, max_wait=600, check_interval=2):
        """
        Wait for temperature to stabilize with timeout

        Args:
            target_temp: Target temperature (K)
            tolerance: Acceptable deviation (K)
            max_wait: Maximum wait time (seconds)
            check_interval: Time between checks (seconds)

        Returns:
            bool: True if reached, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            success, temp, status, _ = self.read_temperature(timeout=10)

            if not success:
                print("⚠ Failed to read temperature")
                time.sleep(check_interval)
                continue

            print(f"  Current: {temp:.2f} K → Target: {target_temp:.2f} K")

            if abs(temp - target_temp) <= tolerance:
                print(f"✓ Temperature stabilized at {temp:.2f} K")
                return True

            time.sleep(check_interval)

        print(f"⚠ Temperature wait timeout after {max_wait}s")
        return False

    def wait_for_field(self, target_field, tolerance=10, max_wait=600, check_interval=2):
        """
        Wait for field to stabilize with timeout

        Args:
            target_field: Target field (Oe)
            tolerance: Acceptable deviation (Oe)
            max_wait: Maximum wait time (seconds)
            check_interval: Time between checks (seconds)

        Returns:
            bool: True if reached, False if timeout
        """
        start_time = time.time()

        while time.time() - start_time < max_wait:
            success, field, status, _ = self.read_field(timeout=10)

            if not success:
                print("⚠ Failed to read field")
                time.sleep(check_interval)
                continue

            print(f"  Current: {field:.1f} Oe → Target: {target_field:.1f} Oe")

            if abs(field - target_field) <= tolerance:
                print(f"✓ Field stabilized at {field:.1f} Oe")
                return True

            time.sleep(check_interval)

        print(f"⚠ Field wait timeout after {max_wait}s")
        return False

class NotificationManager:
    def __init__(self):
        self.settings = QSettings('QuDAP', 'NotificationSettings')
        self.enabled_channels = self._load_enabled_channels()

    def _load_enabled_channels(self) -> Dict[str, bool]:
        return {
            'email': self.settings.value('email/enabled', False, bool),
            'telegram': self.settings.value('telegram/enabled', False, bool),
            'discord': self.settings.value('discord/enabled', False, bool),
        }

    # PRIMARY FUNCTIONS - Choose between these two

    def send_message(self, message: str, priority: str = "normal"):
        """Send text-only notification to all enabled channels"""
        # timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        timestamp = datetime.datetime.now()
        formatted_message = f"{message}\n\nTime: {timestamp}"

        # Send to each enabled channel (text only)
        if self.enabled_channels.get('email'):
            self._send_email(formatted_message, priority)
        if self.enabled_channels.get('telegram'):
            self._send_telegram(formatted_message, priority)
        if self.enabled_channels.get('discord'):
            self._send_discord(formatted_message, priority)

    def send_message_with_image(self, message: str, image_path: str, priority: str = "normal"):
        """Send notification with image to all enabled channels"""
        if not self._is_valid_image(image_path):
            print(f"Invalid image path: {image_path}. Sending text-only notification.")
            self.send_message(message, priority)
            return

        # timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        timestamp = datetime.datetime.now()
        formatted_message = f"{message}\n\nTime: {timestamp}"

        # Send to each enabled channel (with image)
        if self.enabled_channels.get('email'):
            self._send_email(formatted_message, priority, image_path)
        if self.enabled_channels.get('telegram'):
            self._send_telegram(formatted_message, priority, image_path)
        if self.enabled_channels.get('discord'):
            self._send_discord(formatted_message, priority, image_path)

    # LEGACY FUNCTION - Keep for backward compatibility
    def send_notification(self, message: str, priority: str = "normal", image_path: str = None):
        """Legacy function - automatically chooses between text-only and image based on image_path"""
        if image_path:
            self.send_message_with_image(message, image_path, priority)
        else:
            self.send_message(message, priority)

    def _send_email(self, body: str, priority: str, image_path: str = None):
        try:
            # Get settings
            smtp_server = self.settings.value('email/smtp_server', '')
            smtp_port = self.settings.value('email/smtp_port', 587, int)
            use_ssl = self.settings.value('email/smtp_ssl', True, bool)
            username = self.settings.value('email/username', '')
            password = self.settings.value('email/password', '')
            from_email = self.settings.value('email/from_email', username)
            to_emails = self.settings.value('email/to_emails', '').split('\n')

            if not all([smtp_server, username, password, to_emails]):
                return

            # Create message
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = ', '.join(filter(None, to_emails))
            msg['Subject'] = f"[QuDAP {priority.upper()}] Updates"

            # Add priority headers
            if priority == "critical":
                msg['X-Priority'] = '1'
                msg['Importance'] = 'high'
            elif priority == "high":
                msg['X-Priority'] = '2'
                msg['Importance'] = 'high'

            msg.attach(MIMEText(body, 'plain'))

            # Attach image if provided
            if image_path and os.path.exists(image_path):
                try:
                    with open(image_path, 'rb') as f:
                        img_data = f.read()

                    # Determine image type
                    image_type = Path(image_path).suffix.lower()
                    if image_type in ['.jpg', '.jpeg']:
                        img = MIMEImage(img_data, 'jpeg')
                    elif image_type == '.png':
                        img = MIMEImage(img_data, 'png')
                    elif image_type == '.gif':
                        img = MIMEImage(img_data, 'gif')
                    else:
                        img = MIMEBase('application', 'octet-stream')
                        img.set_payload(img_data)
                        encoders.encode_base64(img)

                    img.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(image_path)}"')
                    msg.attach(img)
                except Exception as e:
                    print(f"Error attaching image to email: {e}")

            with smtplib.SMTP(smtp_server, smtp_port) as server:
                if use_ssl:
                    server.starttls()
                server.login(username, password)
                server.sendmail(from_email, to_emails, msg.as_string())

        except Exception as e:
            print(f"Email notification error: {e}")

    def _send_telegram(self, message: str, priority: str, image_path: str = None):
        try:
            token = self.settings.value('telegram/token', '')
            chat_id = self.settings.value('telegram/chat_id', '')

            if not all([token, chat_id]):
                return

            priority_emoji = {
                'low': '🔵',
                'normal': '🟢',
                'high': '🟠',
                'critical': '🔴'
            }.get(priority, '⚪')

            formatted_message = f"{priority_emoji} {message}"

            if image_path and os.path.exists(image_path):
                # Send photo with caption
                url = f"https://api.telegram.org/bot{token}/sendPhoto"

                with open(image_path, 'rb') as photo_file:
                    files = {'photo': photo_file}
                    data = {
                        'chat_id': chat_id,
                        'caption': formatted_message
                    }
                    response = requests.post(url, data=data, files=files, timeout=30)
            else:
                # Send text message only
                url = f"https://api.telegram.org/bot{token}/sendMessage"
                data = {
                    'chat_id': chat_id,
                    'text': formatted_message
                }
                response = requests.post(url, data=data, timeout=10)

            response.raise_for_status()

        except Exception as e:
            print(f"Telegram notification error: {e}")

    def _send_discord(self, message: str, priority: str, image_path: str = None):
        try:
            webhook_url = self.settings.value('discord/webhook', '')
            bot_name = self.settings.value('discord/name', 'QuDAP Bot')

            if not webhook_url:
                return

            color_map = {
                'low': 0x3498db,  # Blue
                'normal': 0x4CBB17,  # Green
                'high': 0xe67e22,  # Orange
                'critical': 0xe74c3c  # Red
            }

            embed = {
                'title': 'Measurement Status Update',
                'description': f"```\n{message}\n```",
                'color': color_map.get(priority, 0x95a5a6),
                'footer': {'text': 'QuDAP Notification System'},
                'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat()
            }

            if image_path and os.path.exists(image_path):
                # Upload image as attachment and reference it in embed
                with open(image_path, 'rb') as image_file:
                    files = {'file': (os.path.basename(image_path), image_file, 'image/png')}

                    # Add image to embed
                    embed['image'] = {'url': f"attachment://{os.path.basename(image_path)}"}

                    payload = {
                        'username': bot_name,
                        'embeds': [embed]
                    }

                    response = requests.post(
                        webhook_url,
                        data={'payload_json': str(payload).replace("'", '"')},
                        files=files,
                        timeout=30
                    )
            else:
                # Send without image
                data = {
                    'username': bot_name,
                    'embeds': [embed]
                }
                response = requests.post(webhook_url, json=data, timeout=10)

            response.raise_for_status()

        except Exception as e:
            print(f"Discord notification error: {e}")

    def _is_valid_image(self, image_path: str) -> bool:
        """Check if the file exists and has a valid image extension"""
        if not image_path or not os.path.exists(image_path):
            return False

        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        return Path(image_path).suffix.lower() in valid_extensions

    def refresh_enabled_channels(self):
        """Reload enabled channels from settings"""
        self.enabled_channels = self._load_enabled_channels()

class WideComboBox(QComboBox):
    def showPopup(self):
        # Get the popup view
        popup = self.view()
        # Resize the popup width
        popup.setMinimumWidth(300)  # Set desired width here
        super().showPopup()

class Worker(QThread):
    progress_update = pyqtSignal(int)
    append_text = pyqtSignal(str, str)
    stop_measurment = pyqtSignal()
    update_ppms_temp_reading_label = pyqtSignal(str, str, str)
    update_ppms_field_reading_label = pyqtSignal(str, str, str)
    update_ppms_chamber_reading_label = pyqtSignal(str)
    update_nv_channel_1_label = pyqtSignal(str)
    update_nv_channel_2_label = pyqtSignal(str)
    update_lockin_label = pyqtSignal(str, str, str, str)
    clear_plot = pyqtSignal()
    update_plot = pyqtSignal(list, list, str, bool, bool)
    save_plot = pyqtSignal(list, list, str, bool, bool, bool, str, str)
    measurement_finished = pyqtSignal()
    error_message = pyqtSignal(str, str)
    update_measurement_progress = pyqtSignal(float, float, float, float)
    update_dsp7265_freq_label = pyqtSignal(str)
    update_keithley_6221_update_label = pyqtSignal(str, str)

    def __init__(self, measurement_instance, keithley_6221, keithley_2182nv, DSP_7265, current, TempList, topField, botField,
                 folder_path, client, tempRate, current_mag, current_unit, file_name, run, number_of_field,
                 field_mode_fixed, nv_channel_1_enabled, nv_channel_2_enabled,nv_NPLC, ppms_field_One_zone_radio_enabled,
                 ppms_field_Two_zone_radio_enabled, ppms_field_Three_zone_radio_enabled, zone1_step_field, zone2_step_field,
                 zone3_step_field, zone1_top_field, zone2_top_field, zone3_top_field, zone1_field_rate, zone2_field_rate,
                 zone3_field_rate, Keithley_2182_Connected, Ketihley_6221_Connected, dsp7265_current_time_constant,
                 DSP7265_Connected, demo, keithley_6221_dc_config, keithley_6221_ac_config, ac_current_waveform, ac_current_freq,
                 ac_current_offset, eto_number_of_avg, init_temp_rate, demag_field, record_zero_field):
        super().__init__()
        self.measurement_instance = measurement_instance
        self.running = True
        self.keithley_6221 = keithley_6221
        self.keithley_2182nv = keithley_2182nv
        self.DSP7265 = DSP_7265
        self.current = current
        self.TempList = TempList
        self.topField = topField
        self.botField = botField
        self.folder_path = folder_path
        self.client = client
        self.tempRate = tempRate
        self.current_mag = current_mag
        self.current_unit = current_unit
        self.file_name = file_name
        self.run = run
        self.number_of_field = number_of_field
        self.field_mode_fixed = field_mode_fixed
        self.nv_channel_1_enabled = nv_channel_1_enabled
        self.nv_channel_2_enabled = nv_channel_2_enabled
        self.nv_NPLC = nv_NPLC
        self.ppms_field_One_zone_radio_enabled = ppms_field_One_zone_radio_enabled
        self.ppms_field_Two_zone_radio_enabled = ppms_field_Two_zone_radio_enabled
        self.ppms_field_Three_zone_radio_enabled = ppms_field_Three_zone_radio_enabled
        self.zone1_step_field = zone1_step_field
        self.zone2_step_field = zone2_step_field
        self.zone3_step_field = zone3_step_field
        self.zone1_top_field = zone1_top_field
        self.zone1_top_field = zone1_top_field
        self.zone2_top_field = zone2_top_field
        self.zone3_top_field = zone3_top_field
        self.zone1_field_rate = zone1_field_rate
        self.zone2_field_rate = zone2_field_rate
        self.zone3_field_rate = zone3_field_rate
        self.Keithley_2182_Connected = Keithley_2182_Connected
        self.Ketihley_6221_Connected = Ketihley_6221_Connected
        self.dsp7265_current_time_constant = dsp7265_current_time_constant
        self.DSP7265_Connected = DSP7265_Connected
        self.demo = demo
        self.keithley_6221_dc_config = keithley_6221_dc_config
        self.keithley_6221_ac_config = keithley_6221_ac_config
        self.ac_current_waveform = ac_current_waveform
        self.ac_current_freq = ac_current_freq
        self.ac_current_offset = ac_current_offset
        self.eto_number_of_avg = eto_number_of_avg
        self.init_temp_rate = init_temp_rate
        self.demag_field = demag_field
        self.record_zero_field = record_zero_field


    def run(self):
        try:
            self.measurement_instance.run_ETO(self.append_text.emit, self.progress_update.emit,
                                              self.stop_measurment.emit, self.update_ppms_temp_reading_label.emit,
                                              self.update_ppms_field_reading_label.emit,
                                              self.update_ppms_chamber_reading_label.emit,
                                              self.update_nv_channel_1_label.emit,
                                              self.update_nv_channel_2_label.emit,
                                              self.update_lockin_label.emit,
                                              self.clear_plot.emit, self.update_plot.emit, self.save_plot.emit,
                                              self.measurement_finished.emit,
                                              self.error_message.emit,
                                              self.update_measurement_progress.emit,
                                              self.update_dsp7265_freq_label.emit,
                                              self.update_keithley_6221_update_label.emit,
                                              keithley_6221 =self.keithley_6221,
                                              keithley_2182nv=self.keithley_2182nv,
                                              DSP7265=self.DSP7265,
                                              current=self.current, TempList=self.TempList, topField=self.topField,
                                              botField=self.botField,
                                              folder_path=self.folder_path, client=self.client,
                                              tempRate=self.tempRate, current_mag=self.current_mag,
                                              current_unit=self.current_unit, file_name=self.file_name,
                                              run=self.run, number_of_field=self.number_of_field,
                                              field_mode_fixed=self.field_mode_fixed,
                                              nv_channel_1_enabled=self.nv_channel_1_enabled,
                                              nv_channel_2_enabled=self.nv_channel_2_enabled,
                                              nv_NPLC=self.nv_NPLC,
                                              ppms_field_One_zone_radio_enabled=self.ppms_field_One_zone_radio_enabled,
                                              ppms_field_Two_zone_radio_enabled=self.ppms_field_Two_zone_radio_enabled,
                                              ppms_field_Three_zone_radio_enabled=self.ppms_field_Three_zone_radio_enabled,
                                              zone1_step_field=self.zone1_step_field,
                                              zone2_step_field=self.zone2_step_field,
                                              zone3_step_field=self.zone3_step_field,
                                              zone1_top_field=self.zone1_top_field,
                                              zone2_top_field=self.zone2_top_field,
                                              zone3_top_field=self.zone3_top_field,
                                              zone1_field_rate=self.zone1_field_rate,
                                              zone2_field_rate=self.zone2_field_rate,
                                              zone3_field_rate=self.zone3_field_rate,
                                              Keithley_2182_Connected=self.Keithley_2182_Connected,
                                              Ketihley_6221_Connected=self.Ketihley_6221_Connected,
                                              dsp7265_current_time_constant=self.dsp7265_current_time_constant,
                                              DSP7265_Connected=self.DSP7265_Connected,
                                              running=lambda: self.running,
                                              demo=self.demo,
                                              keithley_6221_dc_config=self.keithley_6221_dc_config,
                                              keithley_6221_ac_config=self.keithley_6221_ac_config,
                                              ac_current_waveform=self.ac_current_waveform,
                                              ac_current_freq=self.ac_current_freq,
                                              ac_current_offset=self.ac_current_offset,
                                              eto_number_of_avg=self.eto_number_of_avg,
                                              init_temp_rate=self.init_temp_rate,
                                              demag_field=self.demag_field,
                                              record_zero_field=self.record_zero_field
                                              )
            self.running = False
            self.stop()
            return
        except SystemExit as e:
            print(e)
        except Exception as e:
            tb_str = traceback.format_exc()
            print(f'{tb_str} {str(e)}')

    def stop(self):
        self.running = False
        print("STOP")

class LogWindow(QDialog):
    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.SETTINGS = QSettings('QuDAP', 'LogSettings')

        self.setWindowTitle('Log Window')
        self.font = QFont("Arial", 13)
        self.sample_id = None
        self.measurement = None
        self.run = None
        self.folder_path = None
        self.setStyleSheet('Background: white')
        with open("GUI/SHG/QButtonWidget.qss", "r") as file:
            self.Browse_Button_stylesheet = file.read()
        self.init_ui()
        # # Load settings after UI is initialized
        # QTimer.singleShot(0, self.load_settings)

    def init_ui(self):
        self.log_box_layout = QVBoxLayout()
        self.user_layout = QHBoxLayout()
        self.user_label = QLabel('User: ')
        self.user_label.setFont(self.font)
        self.user_entry_box = QLineEdit(self)
        self.user_entry_box.setFont(self.font)
        self.user_layout.addWidget(self.user_label)
        self.user_layout.addWidget(self.user_entry_box)

        user_hints = ["Chunli Tang"]
        user_completer = QCompleter(user_hints, self.user_entry_box)
        self.user_entry_box.setCompleter(user_completer)

        self.output_folder_layout = QHBoxLayout()
        self.output_folder_label = QLabel('Output Folder: ')
        self.output_folder_label.setFont(self.font)
        self.folder_entry_box = QLineEdit(self)
        self.folder_entry_box.setFont(self.font)
        self.folder_entry_box.setEnabled(False)
        self.browse_button = QPushButton('Browse')
        self.browse_button.setStyleSheet(self.Browse_Button_stylesheet)
        self.browse_button.clicked.connect(self.open_folder_dialog)
        self.output_folder_layout.addWidget(self.output_folder_label)
        self.output_folder_layout.addWidget(self.folder_entry_box)
        self.output_folder_layout.addWidget(self.browse_button)

        today = datetime.datetime.today()
        self.formatted_date = today.strftime("%m%d%Y")
        self.date_layout = QHBoxLayout()
        self.date_label = QLabel("Today's Date:")
        self.date_label.setFont(self.font)
        self.date_entry_box = QLineEdit(self)
        self.date_entry_box.setFont(self.font)
        self.date_entry_box.setEnabled(False)
        self.date_entry_box.setText(str(self.formatted_date))
        self.date_layout.addWidget(self.date_label)
        self.date_layout.addWidget(self.date_entry_box)

        self.sample_id_layout = QHBoxLayout()
        self.sample_id_label = QLabel("Sample ID:")
        self.sample_id_label.setFont(self.font)
        self.sample_id_entry_box = QLineEdit(self)
        self.sample_id_entry_box.setFont(self.font)
        self.sample_id_entry_box.textChanged.connect(self.update_id)
        self.sample_id_layout.addWidget(self.sample_id_label)
        self.sample_id_layout.addWidget(self.sample_id_entry_box)

        self.measurement_type_layout = QHBoxLayout()
        self.measurement_type_label = QLabel("Measurement Type:")
        self.measurement_type_label.setFont(self.font)
        self.measurement_type_entry_box = QLineEdit(self)
        self.measurement_type_entry_box.setFont(self.font)
        self.measurement_type_entry_box.textChanged.connect(self.update_measurement)
        self.measurement_type_layout.addWidget(self.measurement_type_label)
        self.measurement_type_layout.addWidget(self.measurement_type_entry_box)

        measurement_hints = ["ETO", "ETO_Rxx_in_plane", "ETO_Rxx_out_of_plane", "ETO_Rxy_in_plane","ETO_Rxy_out_of_plane", 
                             "ETO_Rxy_Rxx_in_plane", "ETO_Rxy_Rxx_out_of_plane", "FMR_field_mod_in_plane", "FMR_field_mod_out_of_plane",
                             "FMR_amp_mod_in_plane", "FMR_amp_mod_out_of_plane"]
        measurement_completer = QCompleter(measurement_hints, self.measurement_type_entry_box)
        self.measurement_type_entry_box.setCompleter(measurement_completer)

        self.run_number_layout = QHBoxLayout()
        self.run_number_label = QLabel("Run Number:")
        self.run_number_label.setFont(self.font)
        self.run_number_entry_box = QLineEdit(self)
        self.run_number_entry_box.setFont(self.font)
        self.run_number_entry_box.textChanged.connect(self.update_run_number)
        self.run_number_layout.addWidget(self.run_number_label)
        self.run_number_layout.addWidget(self.run_number_entry_box)

        self.comment_layout = QHBoxLayout()
        self.comment_label = QLabel("Comment:")
        self.comment_label.setFont(self.font)
        self.comment_entry_box = QLineEdit(self)
        self.comment_entry_box.setFont(self.font)
        self.comment_layout.addWidget(self.comment_label)
        self.comment_layout.addWidget(self.comment_entry_box)

        self.example_file_name = QLabel()

        self.random_number = random.randint(100000, 999999)
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.sample_id}_{self.measurement}_300_K_20_uA_Run_{self.run}.txt"

        self.load_log_info_button_layout = QHBoxLayout()
        self.submit_dialog_button = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.submit_dialog_button.setStyleSheet(self.Browse_Button_stylesheet)
        self.load_log_info_button = QPushButton('Load Previous Info')
        self.load_log_info_button.setStyleSheet(self.Browse_Button_stylesheet)
        self.load_log_info_button.clicked.connect(self.load_settings)
        self.load_log_info_button_layout.addWidget(self.load_log_info_button)
        self.load_log_info_button_layout.addWidget(self.submit_dialog_button)

        self.example_file_name.setText(self.file_name)
        self.log_box_layout.addLayout(self.user_layout)
        self.log_box_layout.addLayout(self.output_folder_layout)
        self.log_box_layout.addLayout(self.date_layout)
        self.log_box_layout.addLayout(self.sample_id_layout)
        self.log_box_layout.addLayout(self.measurement_type_layout)
        self.log_box_layout.addLayout(self.run_number_layout)
        self.log_box_layout.addLayout(self.comment_layout)
        self.log_box_layout.addLayout(self.load_log_info_button_layout)
        self.log_box_layout.addWidget(self.example_file_name)

        self.setLayout(self.log_box_layout)

        self.submit_dialog_button.accepted.connect(self.accept)
        self.submit_dialog_button.rejected.connect(self.reject)

    def update_id(self, text):
        # Replace spaces with underscores in the text
        self.sample_id = self.sample_id_entry_box.text()
        self.sample_id = text.replace(" ", "_")
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.sample_id}_{self.measurement}_300_K_20_uA_Run_{self.run}.txt"
        self.example_file_name.setText(self.file_name)

    def update_measurement(self, text):
        # Replace spaces with underscores in the text
        self.measurement = self.measurement_type_entry_box.text()
        self.measurement = text.replace(" ", "_")
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.sample_id}_{self.measurement}_300_K_20_uA_Run_{self.run}.txt"
        self.example_file_name.setText(self.file_name)

    def update_run_number(self, text):
        # Replace spaces with underscores in the text
        self.run = self.run_number_entry_box.text()
        self.run = text.replace(" ", "_")
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.sample_id}_{self.measurement}_300_K_20_uA_Run_{self.run}.csv"
        self.example_file_name.setText(self.file_name)

    def open_folder_dialog(self):
        self.folder_path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if self.folder_path:
            self.folder_path = self.folder_path +'/'
            self.folder_entry_box.setText(self.folder_path)

    def load_settings(self):
        try:
            self.user = self.SETTINGS.value('log/username', '')
            self.user_entry_box.setText(self.user)
            self.folder_path = self.SETTINGS.value('log/folder_path', '')
            self.folder_entry_box.setText(self.folder_path)
            self.sample_id = self.SETTINGS.value('log/sample_id', '')
            self.sample_id_entry_box.setText(self.sample_id)
            self.measurement = self.SETTINGS.value('log/measurement', '')
            self.measurement_type_entry_box.setText(self.measurement)
            self.run = self.SETTINGS.value('log/run', '')
            self.run_number_entry_box.setText(self.run)
        except SystemExit as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, 'Warning', f'No record found! {tb_str}')


    def accept(self):
        self.user = self.user_entry_box.text()
        self.comment = self.comment_entry_box.text()
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.sample_id}_{self.measurement}"
        # Call the inherited accept method to close the dialog
        if self.user != '' and self.folder_path != '' and self.sample_id != '' and self.measurement != '' and self.run != '':
            self.SETTINGS.setValue('log/username', self.user)
            self.SETTINGS.setValue('log/folder_path', self.folder_path)
            self.SETTINGS.setValue('log/sample_id', self.sample_id)
            self.SETTINGS.setValue('log/measurement', self.measurement)
            self.SETTINGS.setValue('log/run', self.run)
            self.settings_saved.emit()
            super().accept()
        else:
            QMessageBox.warning(self, 'Warning', 'Please enter the log completely!')

    def get_text(self):
        return self.folder_path, self.file_name, self.formatted_date, self.sample_id, self.measurement, self.run, self.comment, self.user

class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=100, height=4, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class Measurement(QMainWindow):
    def __init__(self):
        super().__init__()
        ExitProtection().install()
        try:
            self.PRESET = False
            self.ETO_SELECTED = False
            self.FMR_SELECTED = False
            self.CUSTOMIZE_SELECTED = False
            self.ETO_IV = False
            self.ETO_FIELD_DEP = False
            self.ETO_TEMP_DEP = False
            self.FMR_ST_FMR = False
            self.CUSTOMIZED_1 = False
            self.demo_mode = False
            self.Keithley_2182_Connected = False
            self.Ketihley_6221_Connected = False
            self.BNC845RF_CONNECTED = False
            self.DSP7265_Connected = False
            self.BK9129B_CONNECTED = False
            self.RIGOLDSA875_CONNECTED = False
            self.field_mode_fixed = None
            self.keithley_2182nv = None
            self.keithley_6221 = None
            self.DSP7265 = None
            self.rigol_dsa875 = None
            self.bk9129 = None
            self.client = None
            self.worker = None  # Initialize the worker to None
            self.notification = NotificationManager()
            self.disable_combobox_scrolling()
            self.init_ui()
            self.ppms_field_One_zone_radio_enabled = False
            self.ppms_field_Two_zone_radio_enabled = False
            self.ppms_field_Three_zone_radio_enabled = False
            self.nv_channel_1_enabled = None
            self.nv_channel_2_enabled = None
            self.nv_NPLC = None
            self.keithley_6221_dc_config = False
            self.keithley_6221_ac_config = False
            self.ac_current_freq = None
            self.ac_current_offset = None
            self.ac_current_waveform = None
            self.KEITHLEY_6221_TEST_ON = False
            self.BNC845_AM_ON = False
            self.always_enabled_widgets = []
            self.INSTRUMENT_RS232_PRESETS = {
                "DSP 7265 Lock-in": {
                    'baud_rate': 9600,
                    'data_bits': 8,
                    'parity': 'None',
                    'stop_bits': 1.0,
                    'flow_control': 'None',
                    'id_command': 'ID'
                },
                "BNC 845 RF": {
                    'baud_rate': 9600,
                    'data_bits': 8,
                    'parity': 'None',
                    'stop_bits': 1.0,
                    'flow_control': 'None',
                    'id_command': '*IDN?'
                },
                "B&K Precision 9205B": {
                    'baud_rate': 9600,
                    'data_bits': 8,
                    'parity': 'None',
                    'stop_bits': 1.0,
                    'flow_control': 'None',
                    'id_command': '*IDN?'
                }
            }
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
            return

    def disable_combobox_scrolling(self):
        """Disable mouse wheel scrolling for all combo boxes"""
        QApplication.instance().installEventFilter(self)

    def eventFilter(self, obj, event):
        """Filter out wheel events for combo boxes"""
        # Check if it's a combo box and a wheel event
        if isinstance(obj, QComboBox) and event.type() == event.Type.Wheel:
            # Ignore the wheel event
            return True

        # Pass all other events through
        return super().eventFilter(obj, event)

    def init_ui(self):
        titlefont = QFont("Arial", 20)
        self.font = QFont("Arial", 13)
        self.setStyleSheet("background-color: white;")
        with open("GUI/QSS/QScrollbar.qss", "r") as file:
            self.scrollbar_stylesheet = file.read()
        # Create a QScrollArea
        self.scroll_area = QScrollArea()
        # self.scroll_area.setFixedSize(1200,920)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(self.scrollbar_stylesheet)
        # Create a widget to hold the main layout
        self.content_widget = QWidget()
        self.scroll_area.setWidget(self.content_widget)

        # Create main vertical layout with centered alignment
        self.main_layout = QVBoxLayout(self.content_widget)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Set the content widget to expand
        self.content_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        #  ---------------------------- PART 1 --------------------------------
        self.current_intrument_label = QLabel("Start Measurement")
        self.current_intrument_label.setFont(titlefont)
        self.current_intrument_label.setStyleSheet("""
                                                    QLabel{
                                                        background-color: white;
                                                        }
                                                        """)

        #  ---------------------------- PART 2 --------------------------------
        with open("GUI/QSS/QButtonWidget.qss", "r") as file:
            self.Button_stylesheet = file.read()
        with open("GUI/QSS/QComboWidget.qss", "r") as file:
            self.QCombo_stylesheet = file.read()
        self.preset_group_box = QGroupBox("Experiment Preset")
        self.preset_group_box.setStyleSheet("""                                     
                                                QGroupBox {
                                                    background-color: white;
                                                }
                                                            """)
        self.eto_radio_button = QRadioButton("ETO")
        self.eto_radio_button.setFont(self.font)
        self.eto_radio_button.toggled.connect(self.eto_measurement_selection)
        self.fmr_radio_button = QRadioButton("FMR")
        self.fmr_radio_button.setFont(self.font)
        self.fmr_radio_button.toggled.connect(self.fmr_measurement_selection)
        self.customize_radio_button = QRadioButton("Customize")
        self.customize_radio_button.setFont(self.font)
        self.customize_radio_button.toggled.connect(self.customize_measurement_selection)
        self.demo_radio_buttom = QRadioButton("Demo")
        self.demo_radio_buttom.setFont(self.font)
        self.demo_radio_buttom.toggled.connect(self.demo_selection)

        self.reset_preset_buttom = QPushButton("Reset")
        self.select_preset_buttom = QPushButton("Select")
        self.select_preset_buttom.setEnabled(False)
        self.select_preset_buttom.setStyleSheet(self.Button_stylesheet)
        self.reset_preset_buttom.setStyleSheet(self.Button_stylesheet)

        self.reset_preset_buttom.clicked.connect(self.preset_reset)
        self.select_preset_buttom.clicked.connect(self.preset_select)

        self.preset_layout = QVBoxLayout()
        self.radio_btn_layout = QHBoxLayout()
        self.radio_btn_layout.addStretch(2)
        self.radio_btn_layout.addWidget(self.eto_radio_button)

        self.radio_btn_layout.addStretch(1)
        self.radio_btn_layout.addWidget(self.fmr_radio_button)
        self.radio_btn_layout.addStretch(2)
        self.radio_btn_layout.addWidget(self.customize_radio_button)
        self.radio_btn_layout.addWidget(self.demo_radio_buttom)

        self.measurement_type_layout = QHBoxLayout()

        self.select_preset_btn_layout = QHBoxLayout()
        self.select_preset_btn_layout.addWidget(self.reset_preset_buttom)
        self.select_preset_btn_layout.addWidget(self.select_preset_buttom)

        self.preset_layout.addLayout(self.radio_btn_layout)
        self.preset_layout.addLayout(self.measurement_type_layout)
        self.preset_layout.addLayout(self.select_preset_btn_layout)
        self.preset_group_box.setLayout(self.preset_layout)

        self.preset_container = QWidget()
        self.preset_container.setFixedSize(380, 200)

        self.preset_container_layout = QHBoxLayout()
        self.preset_container_layout.addWidget(self.preset_group_box, 1)
        self.preset_container.setLayout(self.preset_container_layout)

        self.instrument_connection_layout = QHBoxLayout()
        self.instrument_connection_layout.addWidget(self.preset_container)
        self.Instruments_Content_Layout = QVBoxLayout()
        self.main_layout.addWidget(self.current_intrument_label, alignment=Qt.AlignmentFlag.AlignTop)
        self.main_layout.addLayout(self.instrument_connection_layout)
        self.main_layout.addLayout(self.Instruments_Content_Layout)

        # Set the scroll area as the central widget of the main window
        self.setCentralWidget(self.scroll_area)

    def eto_measurement_selection(self):
        try:
            self.select_preset_buttom.setEnabled(False)
            self.FMR_SELECTED = False
            self.ETO_SELECTED = True
            self.CUSTOMIZE_SELECTED = False
            eto_measurement_layout = QHBoxLayout()
            eto_measurement_label = QLabel('Measurement Type:')
            eto_measurement_label.setFont(self.font)
            self.eto_measurement_combo_box = WideComboBox()
            self.eto_measurement_combo_box.setFont(self.font)
            self.eto_measurement_combo_box.setStyleSheet(self.QCombo_stylesheet)
            self.eto_measurement_combo_box.addItems(
                [" ", "I-V", "ETO Field Dependence", "ETO Temperature Dependence"])
            self.eto_measurement_combo_box.currentIndexChanged.connect(self.preset_validation)
            eto_measurement_layout.addWidget(eto_measurement_label)
            eto_measurement_layout.addWidget(self.eto_measurement_combo_box)
            self.clear_layout(self.measurement_type_layout)
            self.measurement_type_layout.addLayout(eto_measurement_layout)

        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def fmr_measurement_selection(self):
        try:
            self.select_preset_buttom.setEnabled(False)
            self.ETO_SELECTED = False
            self.FMR_SELECTED = True
            self.CUSTOMIZE_SELECTED = False
            fmr_measurement_layout = QHBoxLayout()
            fmr_measurement_label = QLabel('Measurement Type:')
            fmr_measurement_label.setFont(self.font)
            self.fmr_measurement_combo_box = QComboBox()
            self.fmr_measurement_combo_box.setFont(self.font)
            self.fmr_measurement_combo_box.setStyleSheet(self.QCombo_stylesheet)
            self.fmr_measurement_combo_box.addItems(
                [" ", "ST-FMR", "Coming Soon"])
            self.fmr_measurement_combo_box.currentIndexChanged.connect(self.preset_validation)
            fmr_measurement_layout.addWidget(fmr_measurement_label)
            fmr_measurement_layout.addWidget(self.fmr_measurement_combo_box)
            self.clear_layout(self.measurement_type_layout)
            self.measurement_type_layout.addLayout(fmr_measurement_layout)

        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def customize_measurement_selection(self):
        try:
            self.select_preset_buttom.setEnabled(False)
            self.ETO_SELECTED = False
            self.FMR_SELECTED = False
            self.CUSTOMIZE_SELECTED = True
            customize_measurement_layout = QHBoxLayout()
            customize_measurement_label = QLabel('Measurement Type:')
            customize_measurement_label.setFont(self.font)
            self.customize_measurement_combo_box = QComboBox()
            self.customize_measurement_combo_box.setFont(self.font)
            self.customize_measurement_combo_box.setStyleSheet(self.QCombo_stylesheet)
            self.customize_measurement_combo_box.addItems(
                [" ", "Customized 1", "Coming Soon"])
            self.customize_measurement_combo_box.currentIndexChanged.connect(self.preset_validation)
            customize_measurement_layout.addWidget(customize_measurement_label)
            customize_measurement_layout.addWidget(self.customize_measurement_combo_box)
            self.clear_layout(self.measurement_type_layout)
            self.measurement_type_layout.addLayout(customize_measurement_layout)

        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def demo_selection(self):
        self.ETO_SELECTED = False
        self.FMR_SELECTED = False
        self.clear_layout(self.measurement_type_layout)
        self.select_preset_buttom.setEnabled(True)

    def preset_reset(self):
        """Reset all preset configurations, widgets, and instrument connections"""

        def reset_button(button):
            """Reset radio button state"""
            if button is not None:
                button.setAutoExclusive(False)
                button.setChecked(False)
                button.setAutoExclusive(True)

        def safe_remove_widget(layout, widget_attr_name):
            """Safely remove and delete a widget if it exists"""
            if hasattr(self, widget_attr_name):
                widget = getattr(self, widget_attr_name)
                if widget is not None:
                    try:
                        layout.removeWidget(widget)
                        # widget.setParent(None)
                        widget.deleteLater()
                        setattr(self, widget_attr_name, None)
                        return True
                    except Exception as e:
                        print(f"Error removing {widget_attr_name}: {e}")
            return False

        def safe_clear_layout(layout_attr_name):
            """Safely clear a layout if it exists"""
            if hasattr(self, layout_attr_name):
                layout = getattr(self, layout_attr_name)
                if layout is not None:
                    try:
                        self.clear_layout(layout)
                        # QApplication.processEvents()
                        return True
                    except Exception as e:
                        print(f"Error clearing {layout_attr_name}: {e}")
            return False

        def safe_close_instrument(instrument_attr_name):
            """Safely close an instrument if it exists and is connected"""
            if hasattr(self, instrument_attr_name):
                instrument = getattr(self, instrument_attr_name)
                if instrument is not None:
                    try:
                        instrument.close()
                        print(f"Closed {instrument_attr_name}")
                        setattr(self, instrument_attr_name, None)
                        return True
                    except Exception as e:
                        print(f"Error closing {instrument_attr_name}: {e}")
            return False

        try:
            # Reset flags
            self.select_preset_buttom.setEnabled(True)
            self.PRESET = False
            self.running = False
            self.ETO_IV = False
            self.ETO_FIELD_DEP = False
            self.ETO_TEMP_DEP = False
            self.FMR_ST_FMR = False
            self.CUSTOMIZED_1 = False

            # Clear layouts
            safe_clear_layout('Instruments_Content_Layout')
            safe_clear_layout('measurement_type_layout')

            safe_clear_layout('graphing_layout')
            safe_clear_layout('buttons_layout')
            safe_clear_layout('customize_layout_class')

            QApplication.processEvents()
            # Reset radio buttons
            if hasattr(self, 'eto_radio_button'):
                reset_button(self.eto_radio_button)
            if hasattr(self, 'fmr_radio_button'):
                reset_button(self.fmr_radio_button)
            if hasattr(self, 'demo_radio_buttom'):
                reset_button(self.demo_radio_buttom)
            if hasattr(self, 'customize_radio_button'):
                reset_button(self.customize_radio_button)

            # Remove and delete widgets
            if hasattr(self, 'instrument_connection_layout'):
                safe_remove_widget(self.instrument_connection_layout, 'instrument_container')
                safe_remove_widget(self.instrument_connection_layout, 'ppms_container')

            if hasattr(self, 'measurement_type_layout'):
                safe_remove_widget(self.measurement_type_layout, 'measurement_type_label')
                safe_remove_widget(self.measurement_type_layout, 'measurement_type_entry_box')

            if hasattr(self, 'main_layout'):
                safe_remove_widget(self.main_layout, 'button_container')
                safe_remove_widget(self.main_layout, 'log_box')
                safe_remove_widget(self.main_layout, 'progress_bar')

            # QApplication.processEvents()

            # Stop measurement if running
            if hasattr(self, 'stop_measurement'):
                try:
                    self.stop_measurement()
                except Exception as e:
                    print(f"Error stopping measurement: {e}")

            # Close all instruments
            instruments_to_close = [
                'keithley_6221',
                'keithley_2182nv',
                'DSP7265',
                'bnc845rf',
                'rigol_dsa875',
                'bk_precision_9205b'
            ]

            for instrument_name in instruments_to_close:
                safe_close_instrument(instrument_name)

        except Exception as e:
            tb_str = traceback.format_exc()
            print(f"Error during preset_reset: {tb_str}")
            QMessageBox.warning(self, "Reset Error", f'Error during reset:\n{str(e)}')

    def preset_validation(self):
        if self.ETO_SELECTED:
            if self.eto_measurement_combo_box.currentIndex() == 0:
                self.select_preset_buttom.setEnabled(False)
            else:
                self.select_preset_buttom.setEnabled(True)
        elif self.FMR_SELECTED:
            if self.fmr_measurement_combo_box.currentIndex() == 0:
                self.select_preset_buttom.setEnabled(False)
            else:
                self.select_preset_buttom.setEnabled(True)
        elif self.CUSTOMIZE_SELECTED:
            if self.customize_measurement_combo_box.currentIndex() == 0:
                self.select_preset_buttom.setEnabled(False)
            else:
                self.select_preset_buttom.setEnabled(True)

    def preset_select(self):
        self.select_preset_buttom.setEnabled(False)
        if self.ETO_SELECTED:
            if self.eto_measurement_combo_box.currentIndex() == 1:
                self.ETO_IV = True
            elif self.eto_measurement_combo_box.currentIndex() == 2:
                self.ETO_FIELD_DEP = True
            elif self.eto_measurement_combo_box.currentIndex() == 3:
                self.ETO_TEMP_DEP = True
            else:
                self.ETO_IV = False
                self.ETO_FIELD_DEP = False
                self.ETO_TEMP_DEP = False
        elif self.FMR_SELECTED:
            if self.fmr_measurement_combo_box.currentIndex() == 1:
                self.FMR_ST_FMR = True
            else:
                self.FMR_ST_FMR = False
        elif self.CUSTOMIZE_SELECTED:
            if self.customize_measurement_combo_box.currentIndex() == 1:
                self.CUSTOMIZED_1 = True
            else:
                self.CUSTOMIZED_1 = False
        else:
            self.ETO_IV = False
            self.ETO_FIELD_DEP = False
            self.ETO_TEMP_DEP = False
            self.FMR_ST_FMR = False
            self.CUSTOMIZED_1 = False

        try:
            if self.PRESET == False:
                self.PRESET = True

                # --------------------------------------- Part connection ----------------------------
                if not self.CUSTOMIZE_SELECTED:
                    self.ppms_container = QWidget()
                    self.ppms_main_layout = QHBoxLayout()
                    self.connection_group_box = QGroupBox("PPMS Connection")
                    self.connection_box_layout = QVBoxLayout()

                    # --------------------------------------- Part connection_PPMS ----------------------------
                    if self.demo_radio_buttom.isChecked():
                        self.demo_mode = True
                        self.ppms_connection = QVBoxLayout()
                        self.ppms_host_connection_layout = QHBoxLayout()
                        self.ppms_port_connection_layout = QHBoxLayout()
                        self.ppms_connection_button_layout = QHBoxLayout()
                        self.host_label = QLabel("PPMS Host:")
                        self.host_label.setFont(self.font)
                        self.host_entry_box = QLineEdit("127.0.0.1")
                        self.host_entry_box.setFont(self.font)
                        self.host_entry_box.setFixedHeight(30)
                        self.port_label = QLabel("PPMS Port:")
                        self.port_label.setFont(self.font)
                        self.port_entry_box = QLineEdit("5000")
                        self.port_entry_box.setFont(self.font)
                        self.port_entry_box.setFixedHeight(30)
                        self.server_btn = QPushButton('Start Server')
                        self.server_btn_clicked = False
                        self.server_btn.clicked.connect(self.start_server)
                        self.connect_btn = QPushButton('Client Connect')
                        self.connect_btn.setEnabled(False)
                        self.connect_btn_clicked = False
                        self.connect_btn.clicked.connect(self.connect_client)

                        self.ppms_host_connection_layout.addWidget(self.host_label, 1)
                        self.ppms_host_connection_layout.addWidget(self.host_entry_box, 2)

                        self.ppms_port_connection_layout.addWidget(self.port_label, 1)
                        self.ppms_port_connection_layout.addWidget(self.port_entry_box, 2)

                        self.ppms_connection_button_layout.addWidget(self.server_btn)
                        self.ppms_connection_button_layout.addWidget(self.connect_btn)

                        self.ppms_connection.addLayout(self.ppms_host_connection_layout)
                        self.ppms_connection.addLayout(self.ppms_port_connection_layout)
                        self.ppms_connection.addLayout(self.ppms_connection_button_layout)

                        self.connection_group_box.setLayout(self.ppms_connection)
                        self.ppms_main_layout.addWidget(self.connection_group_box)
                        self.ppms_container.setFixedSize(380, 200)
                        self.ppms_container.setLayout(self.ppms_main_layout)

                        self.instrument_connection_layout.addWidget(self.ppms_container)
                        self.server_btn.setStyleSheet(self.Button_stylesheet)
                        self.connect_btn.setStyleSheet(self.Button_stylesheet)
                    else:
                        self.ppms_connection = QVBoxLayout()
                        self.ppms_host_connection_layout = QHBoxLayout()
                        self.ppms_port_connection_layout = QHBoxLayout()
                        self.ppms_connection_button_layout = QHBoxLayout()
                        self.host_label = QLabel("PPMS Host:")
                        self.host_label.setFont(self.font)
                        self.host_entry_box = QLineEdit("127.0.0.1")
                        self.host_entry_box.setFont(self.font)
                        self.host_entry_box.setFixedHeight(30)
                        self.port_label = QLabel("PPMS Port:")
                        self.port_label.setFont(self.font)
                        self.port_entry_box = QLineEdit("5000")
                        self.port_entry_box.setFont(self.font)
                        self.port_entry_box.setFixedHeight(30)
                        self.server_btn = QPushButton('Start Server')
                        self.server_btn_clicked = False
                        self.server_btn.clicked.connect(self.start_server)
                        self.connect_btn = QPushButton('Client Connect')
                        self.connect_btn.setEnabled(False)
                        self.connect_btn_clicked = False
                        self.connect_btn.clicked.connect(self.connect_client)

                        self.ppms_host_connection_layout.addWidget(self.host_label, 1)
                        self.ppms_host_connection_layout.addWidget(self.host_entry_box, 2)

                        self.ppms_port_connection_layout.addWidget(self.port_label, 1)
                        self.ppms_port_connection_layout.addWidget(self.port_entry_box, 2)

                        self.ppms_connection_button_layout.addWidget(self.server_btn)
                        self.ppms_connection_button_layout.addWidget(self.connect_btn)

                        self.ppms_connection.addLayout(self.ppms_host_connection_layout)
                        self.ppms_connection.addLayout(self.ppms_port_connection_layout)
                        self.ppms_connection.addLayout(self.ppms_connection_button_layout)

                        self.connection_group_box.setLayout(self.ppms_connection)
                        self.ppms_main_layout.addWidget(self.connection_group_box)
                        self.ppms_container.setFixedSize(380, 200)
                        self.ppms_container.setLayout(self.ppms_main_layout)

                        self.instrument_connection_layout.addWidget(self.ppms_container)
                        self.server_btn.setStyleSheet(self.Button_stylesheet)
                        self.connect_btn.setStyleSheet(self.Button_stylesheet)

                    self.instrument_container = QWidget()
                    self.instrument_main_layout = QHBoxLayout()
                    self.instrument_connection_group_box = QGroupBox("Select Instruments")
                    self.instrument_connection_box_layout = QVBoxLayout()

                    self.Instru_main_layout = QVBoxLayout()
                    self.instru_select_layout = QHBoxLayout()
                    self.instru_connection_layout = QHBoxLayout()
                    self.instru_cnt_btn_layout = QHBoxLayout()
                    self.Instruments_sel_label = QLabel("Select Instruments:")
                    self.Instruments_sel_label.setFont(self.font)
                    self.instruments_selection_combo_box = QComboBox()
                    self.instruments_selection_combo_box.setFont(self.font)
                    self.instruments_selection_combo_box.setStyleSheet(self.QCombo_stylesheet)
                    if self.eto_radio_button.isChecked():
                        self.instruments_selection_combo_box.addItems(
                            ["Select Instruments", "Keithley 2182 nv", "Keithley 6221", "DSP 7265 Lock-in"])
                    elif self.fmr_radio_button.isChecked():
                        self.instruments_selection_combo_box.addItems(["Select Instruments","BNC 845 RF", "DSP 7265 Lock-in"])
                    elif self.demo_radio_buttom.isChecked():
                        self.instruments_selection_combo_box.addItems(["Select Instruments", "Keithley 2182 nv", "Keithley 6221", "DSP 7265 Lock-in"])
                    self.instruments_selection_combo_box.currentIndexChanged.connect(self.instru_combo_index_change)
                    self.Instruments_port_label = QLabel("Channel:")
                    self.Instruments_port_label.setFont(self.font)
                    self.connection_combo = WideComboBox()
                    self.connection_combo.setStyleSheet(self.QCombo_stylesheet)
                    self.connection_combo.setFont(self.font)
                    self.connection_combo.currentIndexChanged.connect(self.instrument_connection_modification)
                    self.refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))
                    self.refresh_btn.clicked.connect(self.refresh_Connection_List)
                    self.instru_connect_btn = QPushButton('Connect')
                    self.instru_connect_btn.clicked.connect(self.connect_devices)
                    self.instru_select_layout.addWidget(self.Instruments_sel_label, 1)
                    self.instru_select_layout.addWidget(self.instruments_selection_combo_box, 2)

                    self.instru_connection_layout.addWidget(self.Instruments_port_label, 1)
                    self.instru_connection_layout.addWidget(self.connection_combo, 3)
                    self.refresh_Connection_List()
                    self.instru_cnt_btn_layout.addWidget(self.refresh_btn, 2)
                    self.instru_cnt_btn_layout.addWidget(self.instru_connect_btn, 2)
                    self.Instru_main_layout.addLayout(self.instru_select_layout)
                    self.Instru_main_layout.addLayout(self.instru_connection_layout)
                    self.instrument_rs232_layout = QHBoxLayout()
                    self.Instru_main_layout.addLayout(self.instrument_rs232_layout)
                    self.Instru_main_layout.addLayout(self.instru_cnt_btn_layout)
                    self.instrument_connection_group_box.setLayout(self.Instru_main_layout)
                    self.instrument_main_layout.addWidget(self.instrument_connection_group_box)
                    self.instrument_container.setFixedSize(380, 200)
                    self.instrument_container.setLayout(self.instrument_main_layout)
                    self.instrument_connection_layout.addWidget(self.instrument_container)

                    # self.PPMS_measurement_setup_layout = QHBoxLayout()
                    self.eto_ppms_layout = QVBoxLayout()
                    self.fmr_ppms_layout = QVBoxLayout()
                    self.Instruments_Content_Layout.addLayout(self.eto_ppms_layout)
                    self.Instruments_Content_Layout.addLayout(self.fmr_ppms_layout)

                    self.Instruments_measurement_setup_layout = QVBoxLayout()
                    self.Instruments_Content_Layout.addLayout(self.Instruments_measurement_setup_layout)

                    self.main_layout.addLayout(self.Instruments_Content_Layout)

                    self.graphing_layout = QHBoxLayout()

                    figure_group_box = QGroupBox("Graph")
                    if self.FMR_ST_FMR:
                        figure_content_layout = QHBoxLayout()
                        cumulative_figure_Layout = QVBoxLayout()
                        self.cumulative_canvas = MplCanvas(self, width=10, height=10, dpi=100)
                        cumulative_toolbar = NavigationToolbar(self.cumulative_canvas, self)
                        cumulative_toolbar.setStyleSheet("""
                                                                                                        QWidget {
                                                                                                            border: None;
                                                                                                        }
                                                                                                    """)
                        cumulative_figure_Layout.addWidget(cumulative_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
                        cumulative_figure_Layout.addWidget(self.cumulative_canvas,
                                                           alignment=Qt.AlignmentFlag.AlignCenter)
                        figure_content_layout.addLayout(cumulative_figure_Layout)

                        single_figure_Layout = QVBoxLayout()
                        self.single_canvas = MplCanvas(self, width=10, height=10, dpi=100)
                        single_toolbar = NavigationToolbar(self.single_canvas, self)
                        single_toolbar.setStyleSheet("""
                                                                                                               QWidget {
                                                                                                                   border: None;
                                                                                                               }
                                                                                                           """)
                        single_figure_Layout.addWidget(single_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
                        single_figure_Layout.addWidget(self.single_canvas, alignment=Qt.AlignmentFlag.AlignCenter)
                        figure_content_layout.addLayout(single_figure_Layout)
                        figure_group_box.setLayout(figure_content_layout)
                    else:
                        figure_Layout = QVBoxLayout()
                        self.canvas = MplCanvas(self, width=100, height=10, dpi=100)
                        self.canvas.axes_2 = self.canvas.axes.twinx()
                        toolbar = NavigationToolbar(self.canvas, self)
                        toolbar.setStyleSheet("""
                                                         QWidget {
                                                             border: None;
                                                         }
                                                     """)
                        figure_Layout.addWidget(toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
                        figure_Layout.addWidget(self.canvas, alignment=Qt.AlignmentFlag.AlignCenter)
                        figure_group_box.setLayout(figure_Layout)
                    figure_group_box.setFixedSize(1150,500)
                    self.figure_container_layout = QHBoxLayout()
                    self.figure_container = QWidget(self)
                    self.buttons_layout = QHBoxLayout()
                    self.start_measurement_btn = QPushButton('Start')
                    if self.ETO_IV:
                        self.start_measurement_btn.clicked.connect(self.start_measurement)
                    elif self.ETO_FIELD_DEP:
                        self.start_measurement_btn.clicked.connect(self.start_measurement)
                    elif self.ETO_TEMP_DEP:
                        self.start_measurement_btn.clicked.connect(self.start_measurement)
                    elif self.FMR_ST_FMR:
                        self.start_measurement_btn.clicked.connect(self.start_st_fmr_measurement)
                    self.stop_btn = QPushButton('Stop')
                    self.stop_btn.setEnabled(False)
                    self.stop_btn.clicked.connect(self.stop_measurement)
                    self.rst_btn = QPushButton('Reset')
                    self.rst_btn.clicked.connect(self.rst)
                    self.start_measurement_btn.setStyleSheet(self.Button_stylesheet)
                    self.stop_btn.setStyleSheet(self.Button_stylesheet)
                    self.rst_btn.setStyleSheet(self.Button_stylesheet)
                    self.buttons_layout.addStretch(4)
                    self.buttons_layout.addWidget(self.rst_btn)
                    self.buttons_layout.addWidget(self.stop_btn)
                    self.buttons_layout.addWidget(self.start_measurement_btn)

                    self.button_container = QWidget()
                    self.button_container.setLayout(self.buttons_layout)
                    self.button_container.setFixedSize(1150,80)
                    self.figure_container_layout.addWidget(figure_group_box)
                    self.figure_container.setLayout(self.figure_container_layout)
                    self.graphing_layout.addWidget(self.figure_container)
                    self.main_layout.addLayout(self.graphing_layout)
                    self.main_layout.addWidget(self.button_container)

                    self.setCentralWidget(self.scroll_area)
                    self.select_preset_buttom.setStyleSheet(self.Button_stylesheet)
                    self.instru_connect_btn.setStyleSheet(self.Button_stylesheet)
                    self.refresh_btn.setStyleSheet(self.Button_stylesheet)
                else:
                    if self.CUSTOMIZED_1:
                        self.instrument_container = QWidget()
                        self.instrument_main_layout = QHBoxLayout()
                        self.instrument_connection_group_box = QGroupBox("Select Instruments")
                        self.instrument_connection_box_layout = QVBoxLayout()

                        self.Instru_main_layout = QVBoxLayout()
                        self.instru_select_layout = QHBoxLayout()
                        self.instru_connection_layout = QHBoxLayout()
                        self.instru_cnt_btn_layout = QHBoxLayout()
                        self.Instruments_sel_label = QLabel("Select Instruments:")
                        self.Instruments_sel_label.setFont(self.font)
                        self.instruments_selection_combo_box = QComboBox()
                        self.instruments_selection_combo_box.setFont(self.font)
                        self.instruments_selection_combo_box.setStyleSheet(self.QCombo_stylesheet)
                        if self.CUSTOMIZED_1:
                            self.instruments_selection_combo_box.addItems(
                                ["Select Instruments", "Rigol DSA875", "B&K Precision 9205B"])
                        self.instruments_selection_combo_box.currentIndexChanged.connect(self.instru_combo_index_change)
                        self.Instruments_port_label = QLabel("Channel:")
                        self.Instruments_port_label.setFont(self.font)
                        self.connection_combo = WideComboBox()
                        self.connection_combo.setStyleSheet(self.QCombo_stylesheet)
                        self.connection_combo.setFont(self.font)
                        self.connection_combo.currentIndexChanged.connect(self.instrument_connection_modification)

                        self.refresh_btn = QPushButton(icon=QIcon("GUI/Icon/refresh.svg"))
                        self.refresh_btn.clicked.connect(self.refresh_Connection_List)
                        self.instru_connect_btn = QPushButton('Connect')
                        self.instru_connect_btn.clicked.connect(self.connect_devices)
                        self.instru_select_layout.addWidget(self.Instruments_sel_label, 1)
                        self.instru_select_layout.addWidget(self.instruments_selection_combo_box, 2)

                        self.instru_connection_layout.addWidget(self.Instruments_port_label, 1)
                        self.instru_connection_layout.addWidget(self.connection_combo, 3)
                        self.refresh_Connection_List()
                        self.instru_cnt_btn_layout.addWidget(self.refresh_btn, 2)
                        self.instru_cnt_btn_layout.addWidget(self.instru_connect_btn, 2)
                        self.Instru_main_layout.addLayout(self.instru_select_layout)
                        self.Instru_main_layout.addLayout(self.instru_connection_layout)
                        self.instrument_rs232_layout = QHBoxLayout()
                        self.Instru_main_layout.addLayout(self.instrument_rs232_layout)
                        self.Instru_main_layout.addLayout(self.instru_cnt_btn_layout)
                        self.instrument_connection_group_box.setLayout(self.Instru_main_layout)
                        self.instrument_main_layout.addWidget(self.instrument_connection_group_box)
                        self.instrument_container.setFixedSize(770, 200)
                        self.instrument_container.setLayout(self.instrument_main_layout)
                        self.instrument_connection_layout.addWidget(self.instrument_container)

                        # self.PPMS_measurement_setup_layout = QHBoxLayout()
                        self.customize_layout = QVBoxLayout()
                        self.Instruments_Content_Layout.addLayout(self.customize_layout)

                        self.Instruments_measurement_setup_layout = QVBoxLayout()
                        self.Instruments_Content_Layout.addLayout(self.Instruments_measurement_setup_layout)

                        self.main_layout.addLayout(self.Instruments_Content_Layout)
                        # self.rigol_measurement = RIGOL_Measurement(True, True)
                        # self.customize_layout_class = self.rigol_measurement.init_ui()
                        # self.main_layout.addLayout(self.customize_layout_class)
                        # self.setCentralWidget(self.scroll_area)
                        self.instru_connect_btn.setStyleSheet(self.Button_stylesheet)
                        self.refresh_btn.setStyleSheet(self.Button_stylesheet)
                        self.setCentralWidget(self.scroll_area)

        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')




    def eto_setup_ui(self):
        eto_reading_setting_layout = QHBoxLayout()
        eto_status_reading_group_box = QGroupBox('Measurement Status')
        eto_status_reading_group_box.setLayout(self.eto_measurement_status_ui())
        if self.ETO_IV:
            eto_status_setting_group_box = QGroupBox('ETO I-V Setting')
            eto_status_setting_group_box.setLayout(self.eto_field_dep_setting_ui())
        elif self.ETO_FIELD_DEP or self.demo_mode:
            eto_status_setting_group_box = QGroupBox('ETO Field Dependence Setting')
            eto_status_setting_group_box.setLayout(self.eto_field_dep_setting_ui())
        elif self.ETO_TEMP_DEP:
            eto_status_setting_group_box = QGroupBox('ETO Temperature Dependence Setting')
            eto_status_setting_group_box.setLayout(self.eto_field_dep_setting_ui())
        else:
            eto_status_setting_group_box = QGroupBox('ETO Setting')

        eto_status_reading_group_box.setFixedWidth(560)
        eto_status_setting_group_box.setFixedWidth(560)

        eto_reading_setting_layout.addWidget(eto_status_reading_group_box)
        eto_reading_setting_layout.addWidget(eto_status_setting_group_box)

        return eto_reading_setting_layout

    def fmr_setup_ui(self):
        fmr_main_ui_class = FMR_Measurement()
        fmr_reading_setting_layout = QHBoxLayout()
        fmr_status_reading_group_box = QGroupBox('Measurement Status')
        fmr_measurement_status_layout, self.fmr_measurement_status_repetition_reading_label, self.fmr_measurement_status_time_remaining_in_days_reading_label, self.fmr_measurement_status_time_remaining_in_hours_reading_label, self.fmr_measurement_status_time_remaining_in_mins_reading_label, self.fmr_measurement_status_cur_percent_reading_label = fmr_main_ui_class.fmr_measurement_status_ui()
        fmr_status_reading_group_box.setLayout(fmr_measurement_status_layout)
        if self.FMR_ST_FMR:
            fmr_status_setting_group_box = QGroupBox('ST FMR Setting')
            fmr_setting_layout, self.fmr_setting_average_line_edit, self.fmr_setting_init_temp_rate_line_edit = fmr_main_ui_class.st_fmr_setting_ui()
            fmr_status_setting_group_box.setLayout(fmr_setting_layout)
        else:
            fmr_status_setting_group_box = QGroupBox('FMR Setting')

        fmr_status_reading_group_box.setFixedWidth(560)
        fmr_status_setting_group_box.setFixedWidth(560)

        fmr_reading_setting_layout.addWidget(fmr_status_reading_group_box)
        fmr_reading_setting_layout.addWidget(fmr_status_setting_group_box)

        return fmr_reading_setting_layout

    def eto_measurement_status_ui(self):
        eto_measurement_status_layout = QVBoxLayout()

        eto_measurement_status_average_layout = QHBoxLayout()
        eto_measurement_status_average_label = QLabel('Number of Average:')
        eto_measurement_status_average_label.setFont(self.font)
        self.eto_measurement_status_average_reading_label = QLabel('NA')
        self.eto_measurement_status_average_reading_label.setFont(self.font)
        eto_measurement_status_average_layout.addWidget(eto_measurement_status_average_label)
        eto_measurement_status_average_layout.addWidget(self.eto_measurement_status_average_reading_label)

        eto_measurement_status_time_remaining_layout = QHBoxLayout()
        eto_measurement_status_time_remaining_label = QLabel('Estimated Time Remaining')
        eto_measurement_status_time_remaining_label.setFont(self.font)
        eto_measurement_status_time_remaining_layout.addWidget(eto_measurement_status_time_remaining_label)

        eto_measurement_status_time_remaining_in_days_layout = QHBoxLayout()
        eto_measurement_status_time_remaining_in_days_label = QLabel('In Days:')
        eto_measurement_status_time_remaining_in_days_label.setFont(self.font)
        self.eto_measurement_status_time_remaining_in_days_reading_label = QLabel('NA')
        self.eto_measurement_status_time_remaining_in_days_reading_label.setFont(self.font)
        eto_measurement_status_time_remaining_in_days_layout.addWidget(eto_measurement_status_time_remaining_in_days_label)
        eto_measurement_status_time_remaining_in_days_layout.addWidget(self.eto_measurement_status_time_remaining_in_days_reading_label)

        eto_measurement_status_time_remaining_in_hours_layout = QHBoxLayout()
        eto_measurement_status_time_remaining_in_hours_label = QLabel('In Hours:')
        eto_measurement_status_time_remaining_in_hours_label.setFont(self.font)
        self.eto_measurement_status_time_remaining_in_hours_reading_label = QLabel('NA')
        self.eto_measurement_status_time_remaining_in_hours_reading_label.setFont(self.font)
        eto_measurement_status_time_remaining_in_hours_layout.addWidget(
            eto_measurement_status_time_remaining_in_hours_label)
        eto_measurement_status_time_remaining_in_hours_layout.addWidget(
            self.eto_measurement_status_time_remaining_in_hours_reading_label)

        eto_measurement_status_time_remaining_in_mins_layout = QHBoxLayout()
        eto_measurement_status_time_remaining_in_mins_label = QLabel('In Minutes:')
        eto_measurement_status_time_remaining_in_mins_label.setFont(self.font)
        self.eto_measurement_status_time_remaining_in_mins_reading_label = QLabel('NA')
        self.eto_measurement_status_time_remaining_in_mins_reading_label.setFont(self.font)
        eto_measurement_status_time_remaining_in_mins_layout.addWidget(
            eto_measurement_status_time_remaining_in_mins_label)
        eto_measurement_status_time_remaining_in_mins_layout.addWidget(
            self.eto_measurement_status_time_remaining_in_mins_reading_label)

        eto_measurement_status_cur_percent_layout = QHBoxLayout()
        eto_measurement_status_cur_percent_label = QLabel('Current Percentage:')
        eto_measurement_status_cur_percent_label.setFont(self.font)
        self.eto_measurement_status_cur_percent_reading_label = QLabel('NA')
        self.eto_measurement_status_cur_percent_reading_label.setFont(self.font)
        eto_measurement_status_cur_percent_layout.addWidget(
            eto_measurement_status_cur_percent_label)
        eto_measurement_status_cur_percent_layout.addWidget(
            self.eto_measurement_status_cur_percent_reading_label)

        eto_measurement_status_layout.addLayout(eto_measurement_status_average_layout)
        eto_measurement_status_layout.addLayout(eto_measurement_status_time_remaining_layout)
        eto_measurement_status_layout.addLayout(eto_measurement_status_time_remaining_in_days_layout)
        eto_measurement_status_layout.addLayout(eto_measurement_status_time_remaining_in_hours_layout)
        eto_measurement_status_layout.addLayout(eto_measurement_status_time_remaining_in_mins_layout)
        eto_measurement_status_layout.addLayout(eto_measurement_status_cur_percent_layout)
        return eto_measurement_status_layout

    def eto_field_dep_setting_ui(self):
        eto_setting_layout = QVBoxLayout()

        eto_setting_average_layout = QHBoxLayout()
        eto_setting_average_label = QLabel('Number of Average')
        eto_setting_average_label.setToolTip('This setting only works for fixed field selection')
        eto_setting_average_label.setFont(self.font)
        self.eto_setting_average_line_edit = QLineEdit('21')
        self.eto_setting_average_line_edit.setFont(self.font)
        eto_setting_average_layout.addWidget(eto_setting_average_label)
        eto_setting_average_layout.addStretch(1)
        eto_setting_average_layout.addWidget(self.eto_setting_average_line_edit)
        eto_setting_layout.addLayout(eto_setting_average_layout)

        eto_setting_init_temp_rate_layout = QHBoxLayout()
        eto_setting_init_temp_rate_label = QLabel('Temperature Ramping Rate (K/min):')
        eto_setting_init_temp_rate_label.setFont(self.font)
        self.eto_setting_init_temp_rate_line_edit = QLineEdit('50')
        self.eto_setting_init_temp_rate_line_edit.setFont(self.font)
        eto_setting_init_temp_rate_layout.addWidget(eto_setting_init_temp_rate_label)
        eto_setting_init_temp_rate_layout.addStretch(1)
        eto_setting_init_temp_rate_layout.addWidget(self.eto_setting_init_temp_rate_line_edit)
        eto_setting_layout.addLayout(eto_setting_init_temp_rate_layout)

        eto_setting_demag_field_layout = QHBoxLayout()
        eto_setting_demag_field_label = QLabel('Demagnetization Field (Oe):')
        eto_setting_demag_field_label.setFont(self.font)
        self.eto_setting_demag_field_line_edit = QLineEdit('10000')
        self.eto_setting_demag_field_line_edit.setFont(self.font)
        eto_setting_demag_field_layout.addWidget(eto_setting_demag_field_label)
        eto_setting_demag_field_layout.addStretch(1)
        eto_setting_demag_field_layout.addWidget(self.eto_setting_demag_field_line_edit)
        eto_setting_layout.addLayout(eto_setting_demag_field_layout)

        if self.ETO_FIELD_DEP or self.demo_mode:
            self.eto_setting_zero_field_record_check_box = QCheckBox('Record Zero Field')
            self.eto_setting_zero_field_record_check_box.setFont(self.font)
            eto_setting_layout.addWidget(self.eto_setting_zero_field_record_check_box)

        return eto_setting_layout

    # ---------------------------------------------------------------------------------
    #  Instrument Connection
    # ---------------------------------------------------------------------------------
    def start_server(self):
        if not is_multivu_running():
            reply = QMessageBox.question(
                self,
                "MultiVu Not Running",
                "MultiVu application is not running!\n\n"
                "MultiVu must be running before starting the server.\n\n"
                "Would you like to:\n"
                "• Yes - Try to start MultiVu automatically\n"
                "• No - Cancel and start it manually",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                # Try to start MultiVu
                multivu_path = find_multivu_path()

                if multivu_path:
                    try:
                        subprocess.Popen([multivu_path])
                        QMessageBox.information(
                            self,
                            "Starting MultiVu",
                            "MultiVu is starting...\n\n"
                            "Please wait for it to fully load,\n"
                            "then click 'Start Server' again."
                        )
                    except Exception as e:
                        QMessageBox.warning(
                            self, "Error",
                            f"Failed to start MultiVu:\n{e}"
                        )
                else:
                    QMessageBox.warning(
                        self,
                        "MultiVu Not Found",
                        "Could not find MultiVu installation.\n"
                        "Please start MultiVu manually."
                    )

            return
        if self.server_btn_clicked == False:
            try:
                # self.start_server_thread()
                if self.demo_mode:
                    self.server_btn.setText('Stop Server')
                    self.server_btn_clicked = True
                    self.connect_btn.setEnabled(True)
                else:
                    self.server = mpv.Server()
                    self.server.open()
                    self.server_btn.setText('Stop Server')
                    self.server_btn_clicked = True
                    self.connect_btn.setEnabled(True)
            except SystemExit as e:
                QMessageBox.critical(self, 'No Server detected', 'No running instance of MultiVu '
                                                                 'was detected. Please start MultiVu and retry without administration')
                self.server_btn.setText('Start Server')
                event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(self, event)
                event = QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
                QApplication.sendEvent(self, event)
                if not self.demo_mode:
                    self.server.close()
                self.server_btn_clicked = False
                self.connect_btn.setEnabled(False)
                return
        elif self.server_btn_clicked == True:
            if not self.demo_mode:
                self.server.close()
            event = QKeyEvent(QKeyEvent.Type.KeyPress, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(self, event)
            event = QKeyEvent(QKeyEvent.Type.KeyRelease, Qt.Key.Key_Escape, Qt.KeyboardModifier.NoModifier)
            QApplication.sendEvent(self, event)
            self.server_btn.setText('Start Server')
            self.server_btn_clicked = False
            self.connect_btn.setEnabled(False)

    def connect_client(self):
        self.host = self.host_entry_box.displayText()
        self.port = self.port_entry_box.displayText()
        if self.connect_btn_clicked == False:
            try:
                if not self.demo_mode:
                    self.client = mpv.Client(host=self.host, port=int(self.port))
                    self.client.open()
                else:
                    self.client = None
                self.PPMS_measurement_setup_layout = QHBoxLayout()
                self.connect_btn.setText('Stop Client')
                self.connect_btn_clicked = True
                self.server_btn.setEnabled(False)
                self.client_keep_going = True
                self.ppms_reading_group_box = QGroupBox('PPMS Status')
                self.ppms_temp_group_box = QGroupBox('Temperature Setup')
                self.ppms_field_group_box = QGroupBox('Field Setup')

                self.ppms_reading_group_box.setLayout(self.ppms_status_reading_ui())
                self.ppms_temp_group_box.setLayout(self.ppms_temperature_setup_ui())
                self.ppms_field_group_box.setLayout(self.ppms_field_setup_ui())

                self.ppms_reading_group_box.setFixedWidth(340)
                self.ppms_temp_group_box.setFixedWidth(350)
                self.ppms_field_group_box.setFixedWidth(420)

                self.PPMS_measurement_setup_layout.addWidget(self.ppms_reading_group_box)
                self.PPMS_measurement_setup_layout.addWidget(self.ppms_temp_group_box)
                self.PPMS_measurement_setup_layout.addWidget(self.ppms_field_group_box)
                if self.ETO_SELECTED or self.demo_mode:
                    self.eto_ppms_layout.addLayout(self.eto_setup_ui())
                    self.eto_ppms_layout.addLayout(self.PPMS_measurement_setup_layout)
                elif self.FMR_SELECTED:
                    self.fmr_ppms_layout.addLayout(self.fmr_setup_ui())
                    self.fmr_ppms_layout.addLayout(self.PPMS_measurement_setup_layout)


            except SystemExit as e:
                QMessageBox.critical(self, 'Client connection failed!', 'Please try again')

        elif self.connect_btn_clicked == True:
            if self.client is not None:
                if not self.demo_mode:
                    self.client.close_client()
                    self.client = None
            self.clear_layout(self.eto_ppms_layout)
            self.clear_layout(self.fmr_ppms_layout)
            self.client_keep_going = False
            self.connect_btn.setText('Start Client')
            self.connect_btn_clicked = False
            self.server_btn.setEnabled(True)

    def connect_devices(self):
        # self.rm = visa.ResourceManager('GUI/Experiment/visa_simulation.yaml@sim')
        self.rm = visa.ResourceManager()
        self.current_connection_index = self.instruments_selection_combo_box.currentIndex()
        self.current_connection = self.connection_combo.currentText()
        if self.eto_radio_button.isChecked():
            try:
                if self.current_connection_index == 0:
                    return None
                elif self.current_connection_index == 1:
                    try:
                        self.connect_keithley_2182()
                    except Exception as e:
                        self.Keithley_2182_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 2:
                    try:
                        self.connect_keithley_6221()
                    except Exception as e:
                        self.Ketihley_6221_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 3:
                    try:
                        self.connect_dsp7265()
                    except Exception as e:
                        self.DSP7265_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        elif self.fmr_radio_button.isChecked():
            try:
                if self.current_connection_index == 0:
                    return None
                elif self.current_connection_index == 1:
                    try:
                        self.connect_bnc_845_rf()
                    except Exception as e:
                        self.BNC845RF_CONNECTED = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
                elif self.current_connection_index == 2:
                    try:
                        self.connect_dsp7265()
                    except Exception as e:
                        self.DSP7265_Connected = False
                        tb_str = traceback.format_exc()
                        QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                        self.instru_connect_btn.setText('Connect')
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        elif self.demo_radio_buttom.isChecked():

            if self.current_connection_index == 0:
                return None
            elif self.current_connection_index == 1:
                try:
                    self.connect_keithley_2182()
                except Exception as e:
                    self.Keithley_2182_Connected = False
                    tb_str = traceback.format_exc()
                    QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                    self.instru_connect_btn.setText('Connect')
            elif self.current_connection_index == 2:
                try:
                    self.connect_keithley_6221()
                except Exception as e:
                    self.Ketihley_6221_Connected = False
                    tb_str = traceback.format_exc()
                    QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                    self.instru_connect_btn.setText('Connect')
            elif self.current_connection_index == 3:
                try:
                    self.connect_dsp7265()
                except Exception as e:
                    self.DSP7265_Connected = False
                    tb_str = traceback.format_exc()
                    QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                    self.instru_connect_btn.setText('Connect')

        elif self.CUSTOMIZED_1:
            if self.CUSTOMIZED_1:
                try:
                    if self.current_connection_index == 0:
                        return None
                    elif self.current_connection_index == 1:
                        try:
                            self.connect_rigol_dsa875()
                        except Exception as e:
                            self.RIGOLDSA875_CONNECTED = False
                            tb_str = traceback.format_exc()
                            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                            self.instru_connect_btn.setText('Connect')
                    elif self.current_connection_index == 2:
                        try:
                            self.connect_bk9129()
                        except Exception as e:
                            self.BK9129B_CONNECTED = False
                            tb_str = traceback.format_exc()
                            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
                            self.instru_connect_btn.setText('Connect')
                except visa.errors.VisaIOError:
                    QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")

    def instrument_connection_modification(self):
        connection_string = self.connection_combo.currentText()
        current_instrument = self.instruments_selection_combo_box.currentText()
        if "ASRL" in connection_string or "COM" in connection_string:
            self.safe_clear_layout("instrument_rs232_layout")
            self.instrument_rs232_layout.addLayout(self.create_rs232_settings_ui())
            self.apply_preset_rs232_settings(current_instrument)
        else:
            self.safe_clear_layout("instrument_rs232_layout")

    def apply_preset_rs232_settings(self, instrument_name):
        """Apply preset RS232 settings for known instruments"""
        if instrument_name in self.INSTRUMENT_RS232_PRESETS:
            preset = self.INSTRUMENT_RS232_PRESETS[instrument_name]
            self.baud_rate_combo.setCurrentText(str(preset['baud_rate']))
            self.data_bits_combo.setCurrentText(str(preset['data_bits']))
            self.parity_combo.setCurrentText(preset['parity'])
            self.stop_bits_combo.setCurrentText(str(preset['stop_bits']))
            self.flow_control_combo.setCurrentText(preset['flow_control'])

    def create_rs232_settings_ui(self):
        """Create RS232 configuration UI"""
        # Clear existing layout

        # RS232 Settings Layout
        rs232_main_layout = QHBoxLayout()

        # Baud Rate
        baud_rate_label = QLabel("Baud Rate:")
        baud_rate_label.setFont(self.font)
        self.baud_rate_combo = QComboBox()
        self.baud_rate_combo.setFont(self.font)
        self.baud_rate_combo.setStyleSheet(self.QCombo_stylesheet)
        self.baud_rate_combo.addItems([
            "300", "1200", "2400", "4800", "9600",
            "19200", "38400", "57600", "115200"
        ])
        self.baud_rate_combo.setCurrentText("9600")  # Default

        # Data Bits
        data_bits_label = QLabel("Data Bits:")
        data_bits_label.setFont(self.font)
        self.data_bits_combo = QComboBox()
        self.data_bits_combo.setFont(self.font)
        self.data_bits_combo.setStyleSheet(self.QCombo_stylesheet)
        self.data_bits_combo.addItems(["5", "6", "7", "8"])
        self.data_bits_combo.setCurrentText("8")  # Default

        # Parity
        parity_label = QLabel("Parity:")
        parity_label.setFont(self.font)
        self.parity_combo = QComboBox()
        self.parity_combo.setFont(self.font)
        self.parity_combo.setStyleSheet(self.QCombo_stylesheet)
        self.parity_combo.addItems(["None", "Even", "Odd", "Mark", "Space"])
        self.parity_combo.setCurrentText("None")  # Default

        # Stop Bits
        stop_bits_label = QLabel("Stop Bits:")
        stop_bits_label.setFont(self.font)
        self.stop_bits_combo = QComboBox()
        self.stop_bits_combo.setFont(self.font)
        self.stop_bits_combo.setStyleSheet(self.QCombo_stylesheet)
        self.stop_bits_combo.addItems(["1", "1.5", "2"])
        self.stop_bits_combo.setCurrentText("1")  # Default

        # Flow Control
        flow_control_label = QLabel("Flow Control:")
        flow_control_label.setFont(self.font)
        self.flow_control_combo = QComboBox()
        self.flow_control_combo.setFont(self.font)
        self.flow_control_combo.setStyleSheet(self.QCombo_stylesheet)
        self.flow_control_combo.addItems(["None", "Hardware (RTS/CTS)", "Software (XON/XOFF)"])
        self.flow_control_combo.setCurrentText("None")  # Default

        # Add widgets to layout
        rs232_main_layout.addWidget(baud_rate_label)
        rs232_main_layout.addWidget(self.baud_rate_combo)
        rs232_main_layout.addWidget(data_bits_label)
        rs232_main_layout.addWidget(self.data_bits_combo)
        rs232_main_layout.addWidget(parity_label)
        rs232_main_layout.addWidget(self.parity_combo)
        rs232_main_layout.addWidget(stop_bits_label)
        rs232_main_layout.addWidget(self.stop_bits_combo)
        rs232_main_layout.addWidget(flow_control_label)
        rs232_main_layout.addWidget(self.flow_control_combo)
        return rs232_main_layout

    def refresh_Connection_List(self):
        try:
            self.clear_layout(self.Instruments_measurement_setup_layout)
        except AttributeError:
            pass
        # rm = visa.ResourceManager('GUI/Experiment/visa_simulation.yaml@sim')
        rm = visa.ResourceManager()
        instruments = rm.list_resources()
        self.connection_ports = [instr for instr in instruments]
        self.Keithley_2182_Connected = False
        self.Ketihley_6221_Connected = False
        self.BNC845RF_CONNECTED = False
        self.DSP7265_Connected = False
        self.instru_connect_btn.setText('Connect')
        self.connection_combo.clear()
        self.connection_combo.addItems(["None"])
        self.connection_combo.addItems(self.connection_ports)
        if self.demo_mode:
            self.connection_combo.addItems(["K2182 Demo"])
            self.connection_combo.addItems(["K6221 Demo"])
            self.connection_combo.addItems(["DSP7265 Demo"])

    def get_rs232_settings(self):
        """Get current RS232 settings as a dictionary"""
        if not hasattr(self, 'baud_rate_combo'):
            return None

        return {
            'baud_rate': int(self.baud_rate_combo.currentText()),
            'data_bits': int(self.data_bits_combo.currentText()),
            'parity': self.parity_combo.currentText(),
            'stop_bits': float(self.stop_bits_combo.currentText()),
            'flow_control': self.flow_control_combo.currentText()
        }

    def connect_rs232_instrument(self, instrument):
        """Connect to instrument via RS232 using PyVISA"""
        try:
            settings = self.get_rs232_settings()
            if settings:
                instrument.baud_rate = settings['baud_rate']
                instrument.data_bits = settings['data_bits']

                # Set parity
                parity_map = {
                    'None': visa.constants.Parity.none,
                    'Even': visa.constants.Parity.even,
                    'Odd': visa.constants.Parity.odd,
                    'Mark': visa.constants.Parity.mark,
                    'Space': visa.constants.Parity.space
                }
                instrument.parity = parity_map[settings['parity']]

                # Set stop bits
                stopbits_map = {
                    1.0: visa.constants.StopBits.one,
                    1.5: visa.constants.StopBits.one_and_a_half,
                    2.0: visa.constants.StopBits.two
                }
                instrument.stop_bits = stopbits_map[settings['stop_bits']]

                # Set flow control
                if settings['flow_control'] == 'Hardware (RTS/CTS)':
                    instrument.flow_control = visa.constants.ControlFlow.rts_cts
                elif settings['flow_control'] == 'Software (XON/XOFF)':
                    instrument.flow_control = visa.constants.ControlFlow.xon_xoff
                else:
                    instrument.flow_control = visa.constants.ControlFlow.none

            # Set timeout (milliseconds)
            instrument.timeout = 5000
            return instrument

        except visa.Error as e:
            QMessageBox.critical(self, "Connection Error", f"Failed to connect:\n{str(e)}")
            return None
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Unexpected error:\n{str(e)}")
            return None

    def connect_keithley_2182(self):
        if self.Keithley_2182_Connected == False:
            try:
                if not self.demo_mode:
                    self.keithley_2182nv = self.rm.open_resource(self.current_connection)
                    if "ASRL" in self.current_connection or "COM" in self.current_connection:
                        self.connect_rs232_instrument(self.keithley_2182nv)
                    self.keithley_2182nv.timeout=10000
                    time.sleep(2)
                    model_2182 = self.keithley_2182nv.query('*IDN?')
                    QMessageBox.information(self, "Connected", F"Connected to {model_2182}")
                else:
                    QMessageBox.information(self, "Connected", F"Connected to Model K2182 Demo")
                #  Simulation pysim----------------------------------------------------------
                # self.keithley_2182nv = self.rm.open_resource(self.current_connection, timeout=10000,  read_termination='\n')
                # ------------------------------------------------------------------
                time.sleep(2)
                self.Keithley_2182_Connected = True
                self.instru_connect_btn.setText('Disconnect')
                self.keithley2182_window_ui()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_keithley_2182()
            self.Keithley_2182_Connected = False

    def connect_keithley_6221(self):
        if self.Ketihley_6221_Connected == False:
            try:
                if not self.demo_mode:
                    self.keithley_6221 = self.rm.open_resource(self.current_connection)
                    if "ASRL" in self.current_connection or "COM" in self.current_connection:
                        self.connect_rs232_instrument(self.keithley_6221)
                    self.keithley_6221.timeout=10000
                    time.sleep(2)
                    Model_6221 = self.keithley_6221.query('*IDN?')
                    QMessageBox.information(self, "Connected", F"Connected to {Model_6221}")
                else:
                    QMessageBox.information(self, "Connected", F"Connected to Model K6221 Demo")
                #  Simulation pysim ------------------------------------------------------
                # self.keithley_2182nv = self.rm.open_resource(self.current_connection, timeout=10000,
                #                                              read_termination='\n')
                # ---------------------------------------------------------
                time.sleep(2)
                self.Ketihley_6221_Connected = True
                self.instru_connect_btn.setText('Disconnect')
                self.keithley6221_window_ui()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
                self.Ketihley_6221_Connected = False
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_keithley_6221()
            self.Ketihley_6221_Connected = False

    def connect_dsp7265(self):
        if self.DSP7265_Connected == False:
            try:
                if not self.demo_mode:
                    self.DSP7265 = self.rm.open_resource(self.current_connection)
                    if "ASRL" in self.current_connection or "COM" in self.current_connection:
                        self.connect_rs232_instrument(self.DSP7265)
                    self.DSP7265.timeout = 10000
                    time.sleep(2)
                    DSPModel = self.DSP7265.query('ID')
                    QMessageBox.information(self, "Connected", F"Connected to {DSPModel}")
                    self.dsp7265_ref_source, self.dsp7265_ref_freq, self.dsp7265_current_time_constant, self.dsp7265_current_sensitvity, self.dsp7265_measurement_type = self.read_sr7265_settings(self.DSP7265)

                    # cur_freq = float(self.DSP7265.query('FRQ[.]')) / 1000
                    # self.dsp7265_ref_freq = str(cur_freq)
                    # cur_sense = float(self.DSP7265.query('SEN.')) / 1000
                    # self.dsp7265_cur_sense = str(cur_sense)
                    # cur_tc = float(self.DSP7265.query('TC.')) / 1000
                    # self.dsp7265_cur_tc = str(cur_tc)
                else:
                    QMessageBox.information(self, "Connected", F"Connected to Model DSP 7265")
                    self.dsp7265_ref_freq = '1000'
                    self.dsp7265_current_sensitvity = '1 V'
                    self.dsp7265_current_time_constant = '20 ms'
                    self.dsp7265_ref_source = 'internal'
                    self.dsp7265_measurement_type = 'Voltage'
                self.DSP7265_Connected = True
                self.instru_connect_btn.setText('Disconnect')

                self.dsp7265_window()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_dsp7265()
            self.DSP7265_Connected = False

    def connect_bnc_845_rf(self):
        if self.BNC845RF_CONNECTED == False:
            try:
                self.bnc845rf = self.rm.open_resource(self.current_connection)
                if "ASRL" in self.current_connection or "COM" in self.current_connection:
                    self.connect_rs232_instrument(self.bnc845rf)
                self.bnc845rf.timeout = 10000
                time.sleep(2)
                self.bnc845rf_command = BNC_845M_COMMAND()
                bnc845rf_model = self.bnc845rf_command.get_id(instrument=self.bnc845rf)
                self.BNC845RF_CONNECTED = True
                QMessageBox.information(self, "Connected", F"Connected to {bnc845rf_model}")
                self.instru_connect_btn.setText('Disconnect')
                self.bnc845rf_window_ui()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_bnc8465rf()
            self.BNC845RF_CONNECTED = False

    def connect_bk9129(self):
        if self.BK9129B_CONNECTED == False:
            try:
                self.bk9129 = self.rm.open_resource(self.current_connection)
                if "ASRL" in self.current_connection or "COM" in self.current_connection:
                    self.connect_rs232_instrument(self.bk9129)
                self.bk9129.timeout = 10000
                time.sleep(2)
                bk9129_model = BK_9129_COMMAND().get_id(self.bk9129)
                self.BK9129B_CONNECTED = True
                QMessageBox.information(self, "Connected", F"Connected to {bk9129_model}")
                self.instru_connect_btn.setText('Disconnect')
                self.customized_1_ui()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_bk9129()
            self.BK9129B_CONNECTED = False

    def connect_rigol_dsa875(self):
        if self.RIGOLDSA875_CONNECTED == False:
            try:
                self.rigol_dsa875 = self.rm.open_resource(self.current_connection)
                if "ASRL" in self.current_connection or "COM" in self.current_connection:
                    self.connect_rs232_instrument(self.rigol_dsa875)
                self.rigol_dsa875.timeout = 10000
                time.sleep(2)
                rigol_dsa875_model = RIGOL_COMMAND().get_id(self.rigol_dsa875)
                self.RIGOLDSA875_CONNECTED = True
                QMessageBox.information(self, "Connected", F"Connected to {rigol_dsa875_model}")
                self.instru_connect_btn.setText('Disconnect')
                self.customized_1_ui()
            except visa.errors.VisaIOError:
                QMessageBox.warning(self, "Connection Fail!", "Please try to reconnect")
        else:
            self.instru_connect_btn.setText('Connect')
            self.close_rigol_dsa875()
            self.RIGOLDSA875_CONNECTED = False

    def close_rigol_dsa875(self):
        try:
            self.rigol_dsa875.close()
            self.RIGOLDSA875_CONNECTED = False
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def close_bk9129(self):
        try:
            self.bk9129.close()
            self.BK9129B_CONNECTED = False
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def close_keithley_2182(self):
        try:
            if not self.demo_mode:
                self.keithley_2182nv.close()
            self.Keithley_2182_Connected = False
            self.clear_layout(self.keithley_2182_contain_layout)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def close_keithley_6221(self):
        try:
            if not self.demo_mode:
                self.keithley_6221.close()
                self.update_keithley_6221_update_label('N/A', 'OFF')
            self.Ketihley_6221_Connected = False
            self.clear_layout(self.keithley6221_main_layout)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def close_dsp7265(self):
        try:
            if not self.demo_mode:
                self.DSP7265.close()
            self.DSP7265_Connected = False
            self.clear_layout(self.dsp7265_main_layout)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def close_bnc8465rf(self):
        try:
            self.bnc845rf.close()
            self.BNC845RF_CONNECTED = False
            # self.clear_layout(self.bnc845rf_main_layout)
            if hasattr(self, 'fmr_widget') and self.fmr_widget is not None:
                # Remove from layout
                self.Instruments_measurement_setup_layout.removeWidget(self.fmr_widget)

                # Delete the widget
                self.fmr_widget.deleteLater()

                # Clear reference
                self.fmr_widget = None
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def instru_combo_index_change(self):
        self.current_connection_index = self.instruments_selection_combo_box.currentIndex()
        if self.eto_radio_button.isChecked() or self.demo_radio_buttom.isChecked():
            if self.current_connection_index == 1:
                if self.Keithley_2182_Connected:
                    self.instru_connect_btn.setText('Disconnect')
                else:
                    self.instru_connect_btn.setText('Connect')
            elif self.current_connection_index == 2:
                if self.Ketihley_6221_Connected:
                    self.instru_connect_btn.setText('Disconnect')
                else:
                    self.instru_connect_btn.setText('Connect')

            elif self.current_connection_index == 3:
                if self.DSP7265_Connected:
                    self.instru_connect_btn.setText('Disconnect')
                else:
                    self.instru_connect_btn.setText('Connect')
        elif self.fmr_radio_button.isChecked():
            if self.current_connection_index == 1:
                if self.BNC845RF_CONNECTED:
                    self.instru_connect_btn.setText('Disconnect')
                else:
                    self.instru_connect_btn.setText('Connect')

            elif self.current_connection_index == 2:
                if self.DSP7265_Connected:
                    self.instru_connect_btn.setText('Disconnect')
                else:
                    self.instru_connect_btn.setText('Connect')
        elif self.CUSTOMIZED_1:
            if self.current_connection_index == 1:
                if self.RIGOLDSA875_CONNECTED:
                    self.instru_connect_btn.setText('Disconnect')
                else:
                    self.instru_connect_btn.setText('Connect')

            elif self.current_connection_index == 2:
                if self.BK9129B_CONNECTED:
                    self.instru_connect_btn.setText('Disconnect')
                else:
                    self.instru_connect_btn.setText('Connect')

    # ---------------------------------------------------------------------------------
    #  Customized Experiment
    # ---------------------------------------------------------------------------------

    def customized_1_ui(self):
        if self.rigol_dsa875 and self.bk9129:
            self.rigol_measurement = RIGOL_Measurement(self.rigol_dsa875, self.bk9129)
            self.customize_layout_class = self.rigol_measurement.init_ui()
            self.main_layout.addLayout(self.customize_layout_class)

    # ---------------------------------------------------------------------------------
    #  BNC 845 Portion
    # ---------------------------------------------------------------------------------
    def start_st_fmr_measurement(self):
        if self.client is None:
            QMessageBox.warning(self, "Missing Connection ",
                                f"Please connect to PPMS client before start")
            return
        temp_field_dict = self.get_combined_field_temp_lists()
        print(temp_field_dict)
        if self.ppms_field_unidirectional_mode_radio_button.isChecked():
            field_list = temp_field_dict['field_settings']['full_sweep_unidirectional']
        if self.ppms_field_bidirectional_mode_radio_button.isChecked():
            field_list = temp_field_dict['field_settings']['full_sweep_bidirectional']
        temp_list = temp_field_dict['all_temps']
        if hasattr(self, 'ppms_zone1_temp_rate_entry'):
            rate = self.ppms_zone1_temp_rate_entry.text()
        elif hasattr(self,'ppms_zone_cus_temp_rate_entry'):
            rate = self.ppms_zone_cus_temp_rate_entry.text()
        else:
            rate = 5

        if self.BNC845RF_CONNECTED == False:
            QMessageBox.warning(self, "Missing Connection ",
                                f"Please connect to Rf source before start")
            return

            # Validate all settings
        is_valid, settings, errors = self.fmr_widget.validate_and_get_all_settings()

        if not is_valid:
            # Show error messages to user
            error_msg = "\n".join(errors)
            QMessageBox.warning(self, "Validation Failed",
                                f"Please fix the following issues:\n\n{error_msg}")
            return

        # All settings are valid, proceed with measurement
        print(f"Settings: {settings}")
        self.fmr_widget.apply_modulation_settings_to_instrument(settings=settings, instrument=self.bnc845rf, bnc_cmd=self.bnc845rf_command)
        # reading = self.fmr_widget._get_modulation_readings_from_instrument(instrument=self.bnc845rf, bnc_cmd=self.bnc845rf_command)
        self.fmr_widget.update_ui_from_instrument(instrument=self.bnc845rf, bnc_cmd=self.bnc845rf_command)

        if self.DSP7265_Connected == False:
            QMessageBox.warning(self, "Missing Connection ",
                                f"Please connect to lock-in amplifier client before start")
            return

    def bnc845rf_window_ui(self):
        self.fmr_widget = FMR_Measurement(bnc845=self.bnc845rf)
        self.Instruments_measurement_setup_layout.addWidget(self.fmr_widget)

    # ---------------------------------------------------------------------------------
    #  DSP 7265 Portion
    # ---------------------------------------------------------------------------------

    def dsp7265_window(self):
        self.dsp7265_reading_groupbox = QGroupBox('DSP 7265 Reading')
        self.dsp7265_setting_groupbox = QGroupBox('DSP 7265 Setting')

        self.dsp7265_setting_layout = QVBoxLayout()
        self.dsp7265_setting_layout.addLayout(self.dsp7265_imode_ui())
        self.dsp7265_mode_contain_layout = QVBoxLayout()
        self.dsp7265_setting_layout.addLayout(self.dsp7265_mode_contain_layout)
        # Line Filter
        self.dsp7265_setting_layout.addLayout(self.dsp7265_line_filter_ui())
        # Sensitivity
        self.dsp7265_setting_layout.addLayout(self.dsp7265_sensitivity_ui())
        # TC
        self.dsp7265_setting_layout.addLayout(self.dsp7265_time_constant_ui())
        # frequency
        self.dsp7265_setting_layout.addLayout(self.dsp7265_frequency_ui())
        # Float
        self.dsp7265_setting_layout.addLayout(self.dsp7265_float_control_ui())
        # device
        self.dsp7265_setting_layout.addLayout(self.dsp7265_device_control_ui())
        # auto sensitivity
        self.dsp7265_setting_layout.addWidget(self.dsp7265_auto_sensitivity_ui())

        # reading
        self.dsp7265_reading_parameter_layout = QVBoxLayout()
        self.dsp7265_reading_parameter_layout.addLayout(self.dsp7265_reading_ui())

        self.dsp7265_setting_groupbox.setLayout(self.dsp7265_setting_layout)
        self.dsp7265_reading_groupbox.setLayout(self.dsp7265_reading_parameter_layout)

        self.dsp7265_reading_groupbox.setFixedWidth(520)
        self.dsp7265_setting_groupbox.setFixedWidth(620)

        self.dsp7265_main_layout = QHBoxLayout()
        self.dsp7265_main_layout.addWidget(self.dsp7265_reading_groupbox)
        self.dsp7265_main_layout.addWidget(self.dsp7265_setting_groupbox)
        self.Instruments_measurement_setup_layout.addLayout(self.dsp7265_main_layout)

    def dsp7265_imode_ui(self):
        self.dsp726_IMODE_layout = QHBoxLayout()
        self.dsp7265_IMODE_combo = QComboBox()
        self.dsp7265_IMODE_combo.setFont(self.font)
        self.dsp7265_IMODE_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_IMODE_combo.addItems(
            ["Select Input Mode", "Current mode off", "High bandwidth current mode", "Low noise current mode"])
        self.dsp7265_IMODE_combo.currentIndexChanged.connect(self.dsp7265_imode_selection)
        self.dsp_imode_text = QLabel('IMODE:')
        self.dsp_imode_text.setFont(self.font)
        self.dsp726_IMODE_layout.addWidget(self.dsp_imode_text)
        self.dsp726_IMODE_layout.addWidget(self.dsp7265_IMODE_combo)
        return self.dsp726_IMODE_layout

    def dsp7265_sensitivity_ui(self):
        self.dsp7265_sens_layout = QHBoxLayout()
        self.dsp7265_sens_combo = QComboBox()
        self.dsp7265_sens_combo.setFont(self.font)
        self.dsp7265_sens_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_sens_combo.addItems(
            ["Select Sensitivity", "2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV",
             "1 \u00B5V", "2 \u00B5V", "5 \u00B5V", "10 \u00B5V", "20 \u00B5V", "50 \u00B5V", "100 \u00B5V",
             "200 \u00B5V", "500 \u00B5V", "1 mV", "2 mV", "5 mV", "10 mV", "20 mV", "50 mV", "100 mV", "200 mV",
             "500 mV",
             "1 V", "Auto"])
        self.dsp7265_sens_combo.currentIndexChanged.connect(self.dsp7265_sens_selection)
        self.dsp_sens_text = QLabel('Sensitivity:')
        self.dsp_sens_text.setFont(self.font)
        self.dsp7265_sens_layout.addWidget(self.dsp_sens_text)
        self.dsp7265_sens_layout.addWidget(self.dsp7265_sens_combo)
        return self.dsp7265_sens_layout

    def dsp7265_time_constant_ui(self):
        self.dsp7265_tc_layout = QHBoxLayout()
        self.dsp_tc_text = QLabel('Time constant:')
        self.dsp_tc_text.setFont(self.font)
        self.dsp_tc_text.setToolTip("Select the time constant that is 5 to 10 times larger than 1/f")

        self.dsp7265_TC_combo = QComboBox()
        self.dsp7265_TC_combo.setFont(self.font)
        self.dsp7265_TC_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_TC_combo.addItems(
            ["Select Input Mode", "10 \u00B5s", "20 \u00B5s", "40 \u00B5s", "80 \u00B5s", "160 \u00B5s"
                , "320 \u00B5s", "640 \u00B5s", "5 ms", "10 ms", "20 ms", "50 ms", "100 ms", "200 ms", "500 ms"
                , "1 s", "2 s", "5 s", "10 s", "20 s", "50 s", "100 s", "200 s", "500 s", "1 ks", "2 ks", '5 ks',
             "10 ks", "20 ks", "50 ks", "100 ks"])
        self.dsp7265_TC_combo.currentIndexChanged.connect(self.dsp7265_tc_selection)

        self.dsp7265_tc_layout.addWidget(self.dsp_tc_text)
        self.dsp7265_tc_layout.addWidget(self.dsp7265_TC_combo)
        return self.dsp7265_tc_layout

    def dsp7265_line_filter_ui(self):
        self.dsp7265_lf_layout = QHBoxLayout()
        self.dsp7265_lf_n1_combo = WideComboBox()
        self.dsp7265_lf_n1_combo.setFont(self.font)
        self.dsp7265_lf_n1_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_lf_n1_combo.addItems(
            ["Select Line Frequency", "off", "Enable 50 or 60 Hz notch filter", "Enable 100 or 120 Hz notch filter",
             "Enable both filter"])

        self.dsp7265_lf_n2_combo = WideComboBox()
        self.dsp7265_lf_n2_combo.setFont(self.font)
        self.dsp7265_lf_n2_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_lf_n2_combo.addItems(
            ["Select Center Frequency", "60 Hz (and/or 120 Hz)", "50 Hz (and/or 100 Hz)"])
        self.dsp7265_lf_submit_button = QPushButton('Submit')
        self.dsp7265_lf_submit_button.setStyleSheet(self.Button_stylesheet)
        self.dsp7265_lf_submit_button.clicked.connect(self.dsp7265_lf_selection)

        self.dsp_lf_n1_text = QLabel('Line Filter:')
        self.dsp_lf_n1_text.setFont(self.font)
        self.dsp7265_lf_layout.addWidget(self.dsp_lf_n1_text)
        self.dsp7265_lf_layout.addWidget(self.dsp7265_lf_n1_combo)
        self.dsp7265_lf_layout.addWidget(self.dsp7265_lf_n2_combo)
        self.dsp7265_lf_layout.addWidget(self.dsp7265_lf_submit_button)
        return self.dsp7265_lf_layout

    def dsp7265_frequency_ui(self):
        self.dsp7265_freq_layout = QHBoxLayout()
        self.dsp7265_freq_text = QLabel('Frequency:')
        self.dsp7265_freq_text.setFont(self.font)
        self.dsp7265_freq_entry_box = QLineEdit()
        self.dsp7265_freq_entry_box.setFont(self.font)
        self.dsp7265_freq_unit_text = QLabel('Hz')
        self.dsp7265_freq_unit_text.setFont(self.font)
        self.dsp7265_ref_channel_combo = QComboBox()
        self.dsp7265_ref_channel_combo.setFont(self.font)
        self.dsp7265_ref_channel_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_ref_channel_combo.addItems(
            ["Select Ref Channel", "INT", "EXT REAR", "EXT FRONT"])
        self.dsp7265_ref_channel_combo.currentIndexChanged.connect(self.dsp7265_ref_channel_selection)

        self.dsp7265_submit_button = QPushButton('Submit')
        self.dsp7265_submit_button.setStyleSheet(self.Button_stylesheet)
        self.dsp7265_submit_button.clicked.connect(self.dsp7265_freq_setting)

        self.dsp7265_freq_layout.addWidget(self.dsp7265_freq_text)
        self.dsp7265_freq_layout.addWidget(self.dsp7265_freq_entry_box)
        self.dsp7265_freq_layout.addWidget(self.dsp7265_freq_unit_text)
        self.dsp7265_freq_layout.addWidget(self.dsp7265_submit_button)
        self.dsp7265_freq_layout.addWidget(self.dsp7265_ref_channel_combo)

        return self.dsp7265_freq_layout

    def dsp7265_float_control_ui(self):
        self.dsp7265_float_layout = QHBoxLayout()
        self.dsp7265_float_text = QLabel('Float/Ground Control:')
        self.dsp7265_float_text.setFont(self.font)
        self.dsp7265_float_channel_combo = WideComboBox()
        self.dsp7265_float_channel_combo.setFont(self.font)
        self.dsp7265_float_channel_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_float_channel_combo.addItems(
            ["Selection", "Ground", "Float (connect to ground via 1 k\u03A9 resistor)"])
        self.dsp7265_float_channel_combo.currentIndexChanged.connect(self.dsp7265_float_control)

        self.dsp7265_float_layout.addWidget(self.dsp7265_float_text)
        self.dsp7265_float_layout.addWidget(self.dsp7265_float_channel_combo)
        return self.dsp7265_float_layout

    def dsp7265_device_control_ui(self):
        self.dsp7265_device_layout = QHBoxLayout()
        self.dsp7265_device_text = QLabel('Input Device Control:')
        self.dsp7265_device_text.setFont(self.font)
        self.dsp7265_device_channel_combo = WideComboBox()
        self.dsp7265_device_channel_combo.setFont(self.font)
        self.dsp7265_device_channel_combo.setStyleSheet(self.QCombo_stylesheet)
        self.dsp7265_device_channel_combo.addItems(
            ["Selection", "Bipolar Device, 10 k\u03A9 input impedance",
             "FET, 10 M\u03A9 input impedance"])
        self.dsp7265_device_channel_combo.currentIndexChanged.connect(self.dsp7265_device_control)

        self.dsp7265_device_layout.addWidget(self.dsp7265_device_text)
        self.dsp7265_device_layout.addWidget(self.dsp7265_device_channel_combo)
        return self.dsp7265_device_layout

    def dsp7265_auto_sensitivity_ui(self):
        self.dsp7265_auto_button_layout = QHBoxLayout()
        self.dsp7265_auto_sense = QPushButton('Auto Sens.')
        self.dsp7265_auto_sense.setStyleSheet(self.Button_stylesheet)
        self.dsp7265_auto_sense.clicked.connect(self.dsp725_auto_sens)

        self.dsp7265_auto_phase = QPushButton('Auto Phase')
        self.dsp7265_auto_phase.setStyleSheet(self.Button_stylesheet)
        self.dsp7265_auto_phase.clicked.connect(self.dsp7265_auto_phase)

        self.dsp7265_auto_Measurement = QPushButton('Auto Meas.')
        self.dsp7265_auto_Measurement.setStyleSheet(self.Button_stylesheet)
        self.dsp7265_auto_Measurement.clicked.connect(self.dsp7265_auto_meas)

        self.dsp7265_auto_button_layout.addWidget(self.dsp7265_auto_sense)
        self.dsp7265_auto_button_layout.addWidget(self.dsp7265_auto_phase)
        self.dsp7265_auto_button_layout.addWidget(self.dsp7265_auto_Measurement)
        self.dsp7265_button_container = QWidget()
        self.dsp7265_button_container.setLayout(self.dsp7265_auto_button_layout)
        self.dsp7265_button_container.setFixedHeight(50)
        return self.dsp7265_button_container

    def dsp7265_reading_ui(self):
        self.dsp7265_reading_layout = QVBoxLayout()

        self.dsp7265_x_reading_layout = QHBoxLayout()
        self.dsp7265_x_reading_label = QLabel('X: ')
        self.dsp7265_x_reading_value_label = QLabel('N/A')
        self.dsp7265_x_reading_label.setFont(self.font)
        self.dsp7265_x_reading_value_label.setFont(self.font)
        self.dsp7265_x_reading_layout.addWidget(self.dsp7265_x_reading_label)
        self.dsp7265_x_reading_layout.addWidget(self.dsp7265_x_reading_value_label)

        self.dsp7265_y_reading_layout = QHBoxLayout()
        self.dsp7265_y_reading_label = QLabel('Y: ')
        self.dsp7265_y_reading_value_label = QLabel('N/A')
        self.dsp7265_y_reading_label.setFont(self.font)
        self.dsp7265_y_reading_value_label.setFont(self.font)
        self.dsp7265_y_reading_layout.addWidget(self.dsp7265_y_reading_label)
        self.dsp7265_y_reading_layout.addWidget(self.dsp7265_y_reading_value_label)

        self.dsp7265_mag_reading_layout = QHBoxLayout()
        self.dsp7265_mag_reading_label = QLabel('Magnitude: ')
        self.dsp7265_mag_reading_value_label = QLabel('N/A')
        self.dsp7265_mag_reading_label.setFont(self.font)
        self.dsp7265_mag_reading_value_label.setFont(self.font)
        self.dsp7265_mag_reading_layout.addWidget(self.dsp7265_mag_reading_label)
        self.dsp7265_mag_reading_layout.addWidget(self.dsp7265_mag_reading_value_label)

        self.dsp7265_phase_reading_layout = QHBoxLayout()
        self.dsp7265_phase_reading_label = QLabel('Phase: ')
        self.dsp7265_phase_reading_value_label = QLabel('N/A')
        self.dsp7265_phase_reading_label.setFont(self.font)
        self.dsp7265_phase_reading_value_label.setFont(self.font)
        self.dsp7265_phase_reading_layout.addWidget(self.dsp7265_phase_reading_label)
        self.dsp7265_phase_reading_layout.addWidget(self.dsp7265_phase_reading_value_label)

        self.dsp7265_freq_reading_layout = QHBoxLayout()
        self.dsp7265_freq_reading_label = QLabel('Frequency: ')
        self.dsp7265_freq_reading_value_label = QLabel('N/A')
        # self.dsp7265_freq_reading_unit_label = QLabel('Hz')
        self.dsp7265_freq_reading_label.setFont(self.font)
        self.dsp7265_freq_reading_value_label.setFont(self.font)
        # self.dsp7265_freq_reading_unit_label.setFont(self.font)
        self.dsp7265_freq_reading_layout.addWidget(self.dsp7265_freq_reading_label)
        self.dsp7265_freq_reading_layout.addWidget(self.dsp7265_freq_reading_value_label)
        # self.dsp7265_freq_reading_layout.addWidget(self.dsp7265_freq_reading_unit_label)
        self.dsp7265_freq_reading_value_label.setText(self.dsp7265_ref_freq + ' Hz')

        self.dsp7265_sensitivity_reading_layout = QHBoxLayout()
        self.dsp7265_sensitivity_reading_label = QLabel('Sensitivity: ')
        self.dsp7265_sensitivity_reading_value_label = QLabel('N/A')
        self.dsp7265_sensitivity_reading_label.setFont(self.font)
        self.dsp7265_sensitivity_reading_value_label.setFont(self.font)
        self.dsp7265_sensitivity_reading_layout.addWidget(self.dsp7265_sensitivity_reading_label)
        self.dsp7265_sensitivity_reading_layout.addWidget(self.dsp7265_sensitivity_reading_value_label)
        self.dsp7265_sensitivity_reading_value_label.setText(self.dsp7265_current_sensitvity)

        self.dsp7265_time_constant_reading_layout = QHBoxLayout()
        self.dsp7265_time_constant_reading_label = QLabel('Time Constant: ')
        self.dsp7265_time_constant_reading_value_label = QLabel('N/A')
        self.dsp7265_time_constant_reading_label.setFont(self.font)
        self.dsp7265_time_constant_reading_value_label.setFont(self.font)
        self.dsp7265_time_constant_reading_layout.addWidget(self.dsp7265_time_constant_reading_label)
        self.dsp7265_time_constant_reading_layout.addWidget(self.dsp7265_time_constant_reading_value_label)
        self.dsp7265_time_constant_reading_value_label.setText(self.dsp7265_current_time_constant)

        self.dsp7265_reference_layout = QHBoxLayout()
        self.dsp7265_reference_label = QLabel('Reference: ')
        self.dsp7265_reference_value_label = QLabel('N/A')
        self.dsp7265_reference_label.setFont(self.font)
        self.dsp7265_reference_value_label.setFont(self.font)
        self.dsp7265_reference_layout.addWidget(self.dsp7265_reference_label)
        self.dsp7265_reference_layout.addWidget(self.dsp7265_reference_value_label)
        self.dsp7265_reference_value_label.setText(self.dsp7265_ref_source)

        self.dsp7265_reading_layout.addLayout(self.dsp7265_x_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_y_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_mag_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_phase_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_freq_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_sensitivity_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_time_constant_reading_layout)
        self.dsp7265_reading_layout.addLayout(self.dsp7265_reference_layout)
        return self.dsp7265_reading_layout

    def read_sr7265_settings(self, instrument):
        # Frequency
        cur_freq = float(instrument.query('FRQ[.]')) / 1000
        ref_freq = str(cur_freq)

        # Reference source
        ref = int(instrument.query("IE"))
        ref_sources = {0: "Internal", 1: "External TTL", 2: "External Analog"}
        ref_source = ref_sources.get(ref, "Unknown")

        # Time constant
        tc_idx = int(instrument.query("TC"))
        tc_values = ["10 \u00B5s", "20 \u00B5s", "40 \u00B5s", "80 \u00B5s", "160 \u00B5s"
                , "320 \u00B5s", "640 \u00B5s", "5 ms", "10 ms", "20 ms", "50 ms", "100 ms", "200 ms", "500 ms"
                , "1 s", "2 s", "5 s", "10 s", "20 s", "50 s", "100 s", "200 s", "500 s", "1 ks", "2 ks", '5 ks',
             "10 ks", "20 ks", "50 ks", "100 ks"]
        time_constant = tc_values[tc_idx] if tc_idx < len(tc_values) else "Unknown"

        # Sensitivity
        sen_idx = int(instrument.query("SEN"))
        mode = int(instrument.query("IMODE"))

        if mode > 0:  # Current mode
            sen_values = ["2fA", "5fA", "10fA", "20fA", "50fA", "100fA", "200fA",
                          "500fA", "1pA", "2pA", "5pA", "10pA", "20pA", "50pA",
                          "100pA", "200pA", "500pA", "1nA", "2nA", "5nA", "10nA",
                          "20nA", "50nA", "100nA", "200nA", "500nA", "1\u00B5A"]
        else:  # Voltage mode
            sen_values = ["Unknown", "2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV",
             "1 \u00B5V", "2 \u00B5V", "5 \u00B5V", "10 \u00B5V", "20 \u00B5V", "50 \u00B5V", "100 \u00B5V",
             "200 \u00B5V", "500 \u00B5V", "1 mV", "2 mV", "5 mV", "10 mV", "20 mV", "50 mV", "100 mV", "200 mV",
             "500 mV",
             "1 V", "Auto"]

        sensitivity = sen_values[sen_idx] if sen_idx < len(sen_values) else "Unknown"

        return ref_source, ref_freq, time_constant, sensitivity, "Current" if mode > 0 else "Voltage"

    def dsp7265_imode_selection(self):
        try:
            self.clear_layout(self.dsp7265_mode_contain_layout)
        except Exception as e:
            pass

        self.dsp_IMODE_index = self.dsp7265_IMODE_combo.currentIndex()
        if self.dsp_IMODE_index == 1:
            self.DSP7265.write('IMODE 0')

            self.dsp726_VMODE_layout = QHBoxLayout()
            self.dsp7265_VMODE_combo = QComboBox()
            self.dsp7265_VMODE_combo.setFont(self.font)
            self.dsp7265_VMODE_combo.setStyleSheet(self.QCombo_stylesheet)
            self.dsp7265_VMODE_combo.addItems(
                ["Select Input Mode", "Both grounded", "A", "-B", "A-B"])
            self.dsp7265_VMODE_combo.currentIndexChanged.connect(self.dsp7265_vmode_selection)
            self.dsp_VMODE_text = QLabel('VMODE:')
            self.dsp_VMODE_text.setFont(self.font)
            self.dsp726_IMODE_layout.addWidget(self.dsp_VMODE_text)
            self.dsp726_IMODE_layout.addWidget(self.dsp7265_VMODE_combo)
            self.dsp7265_mode_contain_layout.addLayout(self.dsp726_IMODE_layout)

        elif self.dsp_IMODE_index == 2:
            self.DSP7265.write('IMODE 1')

            self.dsp726_VMODE_layout = QHBoxLayout()
            self.dsp7265_VMODE_combo = QComboBox()
            self.dsp7265_VMODE_combo.setFont(self.font)
            self.dsp7265_VMODE_combo.setStyleSheet(self.QCombo_stylesheet)
            self.dsp7265_VMODE_combo.addItems(
                ["Select Input Mode", "Both grounded", "A", "-B", "A-B"])
            self.dsp7265_VMODE_combo.currentIndexChanged.connect(self.dsp7265_vmode_selection)
            self.dsp_VMODE_text = QLabel('VMODE:')
            self.dsp_VMODE_text.setFont(self.font)
            self.dsp726_IMODE_layout.addWidget(self.dsp_VMODE_text)
            self.dsp726_IMODE_layout.addWidget(self.dsp7265_VMODE_combo)
            self.dsp7265_mode_contain_layout.addLayout(self.dsp726_IMODE_layout)


        elif self.dsp_IMODE_index == 3:
            self.DSP7265.write('IMODE 2')

    def dsp7265_vmode_selection(self):
        self.dsp_VMODE_index = self.dsp7265_VMODE_combo.currentIndex()
        if self.dsp_VMODE_index == 1:
            self.DSP7265.write('VMODE 0')
        elif self.dsp_VMODE_index == 2:
            self.DSP7265.write('VMODE 1')
        elif self.dsp_VMODE_index == 3:
            self.DSP7265.write('VMODE 2')
        elif self.dsp_VMODE_index == 4:
            self.DSP7265.write('VMODE 3')

    def dsp7265_sens_selection(self):
        self.dsp_sens_index = self.dsp7265_sens_combo.currentIndex()
        self.dsp_sens_text = self.dsp7265_sens_combo.currentText()
        if self.dsp_sens_index != 0:
            self.DSP7265.write(f'SEN {str(self.dsp_sens_index)}')
            sen_idx = int(self.DSP7265.query("SEN"))
            mode = int(self.DSP7265.query("IMODE"))

            if mode > 0:  # Current mode
                sen_values = ["2fA", "5fA", "10fA", "20fA", "50fA", "100fA", "200fA",
                              "500fA", "1pA", "2pA", "5pA", "10pA", "20pA", "50pA",
                              "100pA", "200pA", "500pA", "1nA", "2nA", "5nA", "10nA",
                              "20nA", "50nA", "100nA", "200nA", "500nA", "1\u00B5A"]
            else:  # Voltage mode
                sen_values = ["Unknown", "2 nV", "5 nV", "10 nV", "20 nV", "50 nV", "100 nV", "200 nV", "500 nV",
                              "1 \u00B5V", "2 \u00B5V", "5 \u00B5V", "10 \u00B5V", "20 \u00B5V", "50 \u00B5V",
                              "100 \u00B5V",
                              "200 \u00B5V", "500 \u00B5V", "1 mV", "2 mV", "5 mV", "10 mV", "20 mV", "50 mV", "100 mV",
                              "200 mV",
                              "500 mV",
                              "1 V", "Auto"]

            sensitivity_read = sen_values[sen_idx] if sen_idx < len(sen_values) else "Unknown"
            self.dsp7265_sensitivity_reading_value_label.setText(sensitivity_read)
            if sen_idx != self.dsp_sens_index:
                QMessageBox.warning(self, "Sensitivity Setting Error!",
                                    "Please try to turn on the source and try again!")
        elif self.dsp_sens_index > 27:
            self.DSP7265.write('AS')

    def dsp7265_tc_selection(self):
        self.dsp_tc_index = self.dsp7265_TC_combo.currentIndex()
        self.dsp_tc_text = self.dsp7265_TC_combo.currentText()
        if self.dsp_tc_index != 0:
            self.DSP7265.write(f'TC {str(self.dsp_tc_index-1)}')
            tc_idx = int(self.DSP7265.query("TC"))
            tc_values = ["10 \u00B5s", "20 \u00B5s", "40 \u00B5s", "80 \u00B5s", "160 \u00B5s"
                , "320 \u00B5s", "640 \u00B5s", "5 ms", "10 ms", "20 ms", "50 ms", "100 ms", "200 ms", "500 ms"
                , "1 s", "2 s", "5 s", "10 s", "20 s", "50 s", "100 s", "200 s", "500 s", "1 ks", "2 ks", '5 ks',
                         "10 ks", "20 ks", "50 ks", "100 ks"]
            time_constant_read = tc_values[tc_idx] if tc_idx < len(tc_values) else "Unknown"
            self.dsp7265_time_constant_reading_value_label.setText(time_constant_read)
            if tc_idx != self.dsp_tc_index-1:
                QMessageBox.warning(self, "Time Constant Setting Error!", "Please try to turn on the source and try again!")

    def dsp7265_ref_channel_selection(self):
        self.dsp_ref_channel_index = self.dsp7265_ref_channel_combo.currentIndex()
        self.dsp_ref_channel_text = self.dsp7265_ref_channel_combo.currentText()
        if self.dsp_ref_channel_index != 0:
            self.DSP7265.write(f'IE {str(self.dsp_ref_channel_index - 1)}')
            self.dsp7265_reference_value_label.setText(self.dsp_ref_channel_text)
            # cur_freq = float(self.DSP7265.query('FRQ[.]'))/1000
            #
            # self.dsp7265_freq_reading_value_label.setText(str(cur_freq))

    def dsp7265_lf_selection(self):
        self.dsp7265_lf_n1_index = self.dsp7265_lf_n1_combo.currentIndex()
        self.dsp7265_lf_n2_index = self.dsp7265_lf_n2_combo.currentIndex()
        if self.dsp7265_lf_n1_index != 0:
            if self.dsp7265_lf_n2_index == 0:
                self.DSP7265.write(f'LF {str(self.dsp7265_lf_n1_index - 1)} 0')
            else:
                self.DSP7265.write(f'LF {str(self.dsp7265_lf_n1_index - 1)} {str(self.dsp7265_lf_n2_index - 1)}')

    def dsp725_auto_sens(self):
        self.DSP7265.write('AS')

    def dsp7265_device_control(self):
        self.dsp7265_device_index = self.dsp7265_device_channel_combo.currentIndex()
        if self.dsp7265_device_index != 0:
            self.DSP7265.write(f'FET {str(self.dsp7265_device_index - 1)}')

    def dsp7265_float_control(self):
        self.dsp7265_float_index = self.dsp7265_float_channel_combo.currentIndex()
        if self.dsp7265_float_index != 0:
            self.DSP7265.write(f'FLOAT {str(self.dsp7265_float_index - 1)}')

    def dsp7265_auto_phase(self):
        self.DSP7265.write('AQN')

    def dsp7265_auto_meas(self):
        self.DSP7265.write('ASM')

    def dsp7265_freq_setting(self):
        freq = self.dsp7265_freq_entry_box.text()
        if freq is None:
            QMessageBox.warning(self, 'Warning', 'Frequency not set')
        else:
            self.DSP7265.write(f'OF. {freq}')
            cur_freq = float(self.DSP7265.query('FRQ[.]')) / 1000
            self.dsp7265_freq_reading_value_label.setText(str(cur_freq) + ' Hz')

    # ---------------------------------------------------------------------------------
    #  Keithley 2182 Portion
    # ---------------------------------------------------------------------------------

    def keithley2182_window_ui(self):
        self.Keithley_2182_Container = QWidget(self)
        self.keithley_2182_groupbox = QGroupBox('Keithley 2182nv')

        # NPLC is for integration time selection
        self.NPLC_layout = QHBoxLayout()
        self.NPLC_Label = QLabel('NPLC:')
        self.NPLC_Label.setFont(self.font)
        self.NPLC_Label.setToolTip("Number of power line cycle (Integration time - N/60 or N/50);\n"
                               "1). 0.1 for fast speed high noise;\n"
                               "2). 1 for medium integration time\n"
                               "3). 5 for slow integration time.")
        self.NPLC_entry = QLineEdit()
        self.NPLC_entry.setFont(self.font)
        self.NPLC_entry.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.NPLC_entry.setFont(self.font)
        self.NPLC_entry.setText('5')
        self.NPLC_layout.addWidget(self.NPLC_Label)
        self.NPLC_layout.addStretch(1)
        self.NPLC_layout.addWidget(self.NPLC_entry)
        self.NPLC_layout.addStretch(1)

        # This section for line sync
        self.keithley_2182_lsync_layout = QHBoxLayout()
        self.keithley_2182_lsync_checkbox = QCheckBox('Line Synchronization')
        self.keithley_2182_lsync_checkbox.setFont(self.font)
        self.keithley_2182_lsync_checkbox.setToolTip("This is the filter to synchronize the power line frequency.")
        self.keithley_2182_lsync_checkbox.setChecked(True)
        self.keithley_2182_lsync_layout.addWidget(self.keithley_2182_lsync_checkbox)

        # This section for line sync
        self.keithley_2182_filter_layout = QHBoxLayout()
        self.keithley_2182_digital_filter_radio = QRadioButton("Digital Filter")
        self.keithley_2182_digital_filter_radio.setFont(self.font)
        self.keithley_2182_analog_filter_radio = QRadioButton("Analog Filter")
        self.keithley_2182_analog_filter_radio.setFont(self.font)
        self.keithley_2182_no_filter_radio = QRadioButton("OFF")
        self.keithley_2182_no_filter_radio.setFont(self.font)
        self.keithley_2182_no_filter_radio.setChecked(True)
        self.keithley_2182_filter_layout.addWidget(self.keithley_2182_digital_filter_radio)
        self.keithley_2182_filter_layout.addWidget(self.keithley_2182_analog_filter_radio)
        self.keithley_2182_filter_layout.addWidget(self.keithley_2182_no_filter_radio)

        self.keithley_2182_filter_button_group = QButtonGroup()
        self.keithley_2182_filter_button_group.addButton(self.keithley_2182_digital_filter_radio, 0)
        self.keithley_2182_filter_button_group.addButton(self.keithley_2182_analog_filter_radio, 1)
        self.keithley_2182_filter_button_group.addButton(self.keithley_2182_no_filter_radio, 2)

        self.keithley_2182_channel_1_layout = QHBoxLayout()
        self.keithley_2182_channel_1_checkbox = QCheckBox('Channel 1:')
        self.keithley_2182_channel_1_checkbox.setFont(self.font)
        self.keithley_2182_channel_1_reading_label = QLabel('N/A')
        self.keithley_2182_channel_1_reading_label.setFont(self.font)
        self.keithley_2182_channel_1_layout.addWidget(self.keithley_2182_channel_1_checkbox)
        self.keithley_2182_channel_1_layout.addWidget(self.keithley_2182_channel_1_reading_label)

        self.keithley_2182_channel_2_layout = QHBoxLayout()
        self.keithley_2182_channel_2_checkbox = QCheckBox('Channel 2:')
        self.keithley_2182_channel_2_checkbox.setFont(self.font)
        self.keithley_2182_channel_2_reading_label = QLabel('N/A')
        self.keithley_2182_channel_2_reading_label.setFont(self.font)
        self.keithley_2182_channel_2_layout.addWidget(self.keithley_2182_channel_2_checkbox)
        self.keithley_2182_channel_2_layout.addWidget(self.keithley_2182_channel_2_reading_label)

        self.keithley_2182_main_layout = QVBoxLayout()
        self.keithley_2182_main_layout.addLayout(self.NPLC_layout)
        self.keithley_2182_main_layout.addLayout(self.keithley_2182_lsync_layout)
        self.keithley_2182_main_layout.addLayout(self.keithley_2182_filter_layout)
        self.keithley_2182_main_layout.addLayout(self.keithley_2182_channel_1_layout)
        self.keithley_2182_main_layout.addLayout(self.keithley_2182_channel_2_layout)
        self.keithley_2182_groupbox.setLayout(self.keithley_2182_main_layout)
        self.keithley_2182_groupbox.setFixedWidth(500)
        self.keithley_2182_contain_layout = QHBoxLayout()
        self.keithley_2182_contain_layout.addWidget(self.keithley_2182_groupbox)
        self.Instruments_measurement_setup_layout.addLayout(self.keithley_2182_contain_layout)

    # ---------------------------------------------------------------------------------
    #  Keithley 6221 Portion
    # ---------------------------------------------------------------------------------

    def keithley6221_window_ui(self):
        self.keithley6221_reading_groupbox = QGroupBox('Keithley 6221 Reading')
        self.keithley6221_setting_groupbox = QGroupBox('Keithley 6221 Setting')

        self.keithley6221_setting_layout = QVBoxLayout()
        self.keithley6221_setting_layout.addLayout(self.keithley6221_setting_window_ui())

        # reading
        self.keithley6221_reading_layout = QVBoxLayout()
        self.keithley6221_reading_layout.addLayout(self.keithley6221_reading_window_ui())

        self.keithley6221_setting_groupbox.setLayout(self.keithley6221_setting_layout)
        self.keithley6221_reading_groupbox.setLayout(self.keithley6221_reading_layout)

        self.keithley6221_reading_groupbox.setFixedWidth(520)
        self.keithley6221_setting_groupbox.setFixedWidth(620)

        self.keithley6221_main_layout = QHBoxLayout()
        self.keithley6221_main_layout.addWidget(self.keithley6221_reading_groupbox)
        self.keithley6221_main_layout.addWidget(self.keithley6221_setting_groupbox)
        self.Instruments_measurement_setup_layout.addLayout(self.keithley6221_main_layout)

    def keithley6221_reading_window_ui(self):
        keithley_reading_layout = QVBoxLayout()

        keithley_reading_current_layout = QHBoxLayout()
        keithley_reading_current_label = QLabel('Current:')
        keithley_reading_current_label.setFont(self.font)
        self.keithley_reading_current_reading_label = QLabel('N/A')
        self.keithley_reading_current_reading_label.setFont(self.font)
        keithley_reading_current_layout.addWidget(keithley_reading_current_label)
        keithley_reading_current_layout.addWidget(self.keithley_reading_current_reading_label)
        keithley_reading_layout.addLayout(keithley_reading_current_layout)

        keithley_reading_state_layout = QHBoxLayout()
        keithley_reading_state_label = QLabel('State:')
        keithley_reading_state_label.setFont(self.font)
        self.keithley_reading_state_reading_label = QLabel('N/A')
        self.keithley_reading_state_reading_label.setFont(self.font)
        keithley_reading_state_layout.addWidget(keithley_reading_state_label)
        keithley_reading_state_layout.addWidget(self.keithley_reading_state_reading_label)
        keithley_reading_layout.addLayout(keithley_reading_state_layout)
        return keithley_reading_layout

    def keithley6221_setting_window_ui(self):
        self.Keithey_6221_main_layout = QVBoxLayout()
        self.keithley_6221_DC_radio = QRadioButton("DC")
        self.keithley_6221_DC_radio.setFont(self.font)
        self.keithley_6221_DC_radio.toggled.connect(self.keithley_6221_dc)
        self.keithley_6221_ac_radio = QRadioButton("AC")
        self.keithley_6221_ac_radio.setFont(self.font)
        self.keithley_6221_ac_radio.toggled.connect(self.keithley_6221_ac)
        self.keithley_6221_radio_button_layout = QHBoxLayout()
        self.keithley_6221_radio_button_layout.addWidget(self.keithley_6221_DC_radio)
        self.keithley_6221_radio_button_layout.addWidget(self.keithley_6221_ac_radio)
        self.Keithey_6221_main_layout.addLayout(self.keithley_6221_radio_button_layout)
        self.Keithey_curSour_layout = QVBoxLayout()
        self.Keithey_6221_main_layout.addLayout(self.Keithey_curSour_layout)


        return self.Keithey_6221_main_layout

    def keithley_6221_test_button_ui(self):
        self.keithley_6221_test_layout_container = QWidget()
        self.keithley_6221_test_layout_container.setMinimumHeight(60)
        self.keithley_6221_test_layout = QHBoxLayout()
        self.keithley_6221_test_button = QPushButton("Test")
        self.keithley_6221_test_button.setFont(self.font)
        self.keithley_6221_test_button.setStyleSheet(self.Button_stylesheet)
        self.keithley_6221_test_button.clicked.connect(self.keithley_6221_test_on_off)
        self.keithley_6221_test_layout.addStretch(1)
        self.keithley_6221_test_layout.addWidget(self.keithley_6221_test_button)
        self.keithley_6221_test_layout_container.setLayout(self.keithley_6221_test_layout)
        return self.keithley_6221_test_layout_container

    def keithley_6221_dc(self):
        try:
            self.clear_layout(self.Keithey_curSour_layout)
        except Exception as e:
            pass
        self.keithley_6221_DC_range_single_layout = QVBoxLayout()
        self.keithley_6221_DC_range_layout = QHBoxLayout()
        self.keithley_6221_DC_range_checkbox = QRadioButton('Range')
        # self.keithley_6221_DC_range_checkbox.stateChanged.connect(self.on_6221_DC_toggle)
        self.keithley_6221_DC_range_checkbox.setFont(self.font)
        self.keithley_6221_DC_range_from_label = QLabel('From:')
        self.keithley_6221_DC_range_from_label.setFont(self.font)
        self.keithley_6221_DC_range_init_entry = QLineEdit()
        self.keithley_6221_DC_range_init_entry.setFont(self.font)
        self.keithley_6221_DC_range_to_label = QLabel('to')
        self.keithley_6221_DC_range_to_label.setFont(self.font)
        self.keithley_6221_DC_range_final_entry = QLineEdit()
        self.keithley_6221_DC_range_final_entry.setFont(self.font)
        self.keithley_6221_DC_range_step_label = QLabel('Step Size:')
        self.keithley_6221_DC_range_step_label.setFont(self.font)
        self.keithley_6221_DC_range_step_entry = QLineEdit()
        self.keithley_6221_DC_range_step_entry.setFont(self.font)
        self.keithley_6221_DC_range_combobox = QComboBox()
        self.keithley_6221_DC_range_combobox.setFont(self.font)
        self.keithley_6221_DC_range_combobox.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_DC_range_combobox.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_checkbox)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_from_label)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_init_entry)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_to_label)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_final_entry)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_step_label)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_step_entry)
        self.keithley_6221_DC_range_layout.addWidget(self.keithley_6221_DC_range_combobox)
        self.keithley_6221_DC_range_single_layout.addLayout(self.keithley_6221_DC_range_layout)
        self.keithley_6221_DC_single_layout = QHBoxLayout()
        self.keithley_6221_DC_single_checkbox = QRadioButton('List')
        # self.keithley_6221_DC_single_checkbox.stateChanged.connect(self.on_6221_DC_toggle)
        self.keithley_6221_DC_single_checkbox.setFont(self.font)

        self.keithley_6221_DC_single_entry = QLineEdit()
        self.keithley_6221_DC_single_entry.setFont(self.font)
        self.keithley_6221_DC_single_combobox = QComboBox()
        self.keithley_6221_DC_single_combobox.setFont(self.font)
        self.keithley_6221_DC_single_combobox.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_DC_single_combobox.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.keithley_6221_DC_single_layout.addWidget(self.keithley_6221_DC_single_checkbox)
        self.keithley_6221_DC_single_layout.addWidget(self.keithley_6221_DC_single_entry)
        self.keithley_6221_DC_single_layout.addWidget(self.keithley_6221_DC_single_combobox)
        self.keithley_6221_DC_range_single_layout.addLayout(self.keithley_6221_DC_single_layout)
        self.Keithey_curSour_layout.addLayout(self.keithley_6221_DC_range_single_layout)
        self.Keithey_curSour_layout.addWidget(self.keithley_6221_test_button_ui())

        self.keithley_6221_DC_selection_btn_group = QButtonGroup()
        self.keithley_6221_DC_selection_btn_group.addButton(self.keithley_6221_DC_range_checkbox)
        self.keithley_6221_DC_selection_btn_group.addButton(self.keithley_6221_DC_single_checkbox)

    def keithley_6221_ac(self):
        try:
            self.clear_layout(self.Keithey_curSour_layout)
        except Exception as e:
            pass

        self.keithley_6221_ac_range_single_layout = QVBoxLayout()
        self.keithley_6221_ac_range_layout = QHBoxLayout()
        self.keithley_6221_ac_range_checkbox = QRadioButton('Range')
        # self.keithley_6221_ac_range_checkbox.stateChanged.connect(self.on_6221_ac_toggle)
        self.keithley_6221_ac_range_checkbox.setFont(self.font)
        self.keithley_6221_ac_range_from_label = QLabel('From:')
        self.keithley_6221_ac_range_from_label.setFont(self.font)
        self.keithley_6221_ac_range_init_entry = QLineEdit()
        self.keithley_6221_ac_range_init_entry.setFont(self.font)
        self.keithley_6221_ac_range_to_label = QLabel('to')
        self.keithley_6221_ac_range_to_label.setFont(self.font)
        self.keithley_6221_ac_range_final_entry = QLineEdit()
        self.keithley_6221_ac_range_final_entry.setFont(self.font)
        self.keithley_6221_ac_range_step_label = QLabel('Step Size:')
        self.keithley_6221_ac_range_step_label.setFont(self.font)
        self.keithley_6221_ac_range_step_entry = QLineEdit()
        self.keithley_6221_ac_range_step_entry.setFont(self.font)
        self.keithley_6221_ac_range_combobox = QComboBox()
        self.keithley_6221_ac_range_combobox.setFont(self.font)
        self.keithley_6221_ac_range_combobox.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_ac_range_combobox.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.keithley_6221_ac_range_layout.addWidget(self.keithley_6221_ac_range_checkbox)
        self.keithley_6221_ac_range_layout.addWidget(self.keithley_6221_ac_range_from_label)
        self.keithley_6221_ac_range_layout.addWidget(self.keithley_6221_ac_range_init_entry)
        self.keithley_6221_ac_range_layout.addWidget(self.keithley_6221_ac_range_to_label)
        self.keithley_6221_ac_range_layout.addWidget(self.keithley_6221_ac_range_final_entry)
        self.keithley_6221_ac_range_layout.addWidget(self.keithley_6221_ac_range_step_label)
        self.keithley_6221_ac_range_layout.addWidget(self.keithley_6221_ac_range_step_entry)
        self.keithley_6221_ac_range_layout.addWidget(self.keithley_6221_ac_range_combobox)
        self.keithley_6221_ac_range_single_layout.addLayout(self.keithley_6221_ac_range_layout)
        self.keithley_6221_ac_single_layout = QHBoxLayout()
        self.keithley_6221_ac_single_checkbox = QRadioButton('List')
        # self.keithley_6221_ac_single_checkbox.stateChanged.connect(self.on_6221_ac_toggle)
        self.keithley_6221_ac_single_checkbox.setFont(self.font)

        self.keithley_6221_ac_single_entry = QLineEdit()
        self.keithley_6221_ac_single_entry.setFont(self.font)
        self.keithley_6221_ac_single_combobox = QComboBox()
        self.keithley_6221_ac_single_combobox.setFont(self.font)
        self.keithley_6221_ac_single_combobox.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_ac_single_combobox.addItems(["Select Units", "mA", "µA", "nA", "pA"])
        self.keithley_6221_ac_single_layout.addWidget(self.keithley_6221_ac_single_checkbox)
        self.keithley_6221_ac_single_layout.addWidget(self.keithley_6221_ac_single_entry)
        self.keithley_6221_ac_single_layout.addWidget(self.keithley_6221_ac_single_combobox)
        self.keithley_6221_ac_range_single_layout.addLayout(self.keithley_6221_ac_single_layout)

        self.keithley_6221_ac_wave_func_layout = QHBoxLayout()
        self.keithley_6221_ac_wave_func_label = QLabel("Wave Function:")
        self.keithley_6221_ac_wave_func_label.setFont(self.font)
        self.keithley_6221_ac_waveform_combo_box = QComboBox()
        self.keithley_6221_ac_waveform_combo_box.setFont(self.font)
        self.keithley_6221_ac_waveform_combo_box.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_ac_waveform_combo_box.addItems(["Select Funcs"])  # 0
        self.keithley_6221_ac_waveform_combo_box.addItems(["SINE"])  # 1
        self.keithley_6221_ac_waveform_combo_box.addItems(["SQUARE"])  # 2
        self.keithley_6221_ac_waveform_combo_box.addItems(["RAMP"])  # 3
        self.keithley_6221_ac_waveform_combo_box.addItems(["ARB(x)"])  # 3
        self.keithley_6221_ac_wave_func_layout.addWidget(self.keithley_6221_ac_wave_func_label)
        self.keithley_6221_ac_wave_func_layout.addWidget(self.keithley_6221_ac_waveform_combo_box)
        self.keithley_6221_ac_range_single_layout.addLayout(self.keithley_6221_ac_wave_func_layout)

        # self.keithley_6221_ac_amp_layout = QHBoxLayout()
        # self.keithley_6221_ac_amp_label = QLabel("Amplitude:")
        # self.keithley_6221_ac_amp_label.setFont(self.font)
        # self.keithley_6221_ac_amp_entry_box = QLineEdit()
        # self.keithley_6221_ac_amp_entry_box.setFont(self.font)
        # self.keithley_6221_ac_amp_validator = QDoubleValidator(0, 105, 10)
        # self.keithley_6221_ac_amp_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        # self.keithley_6221_ac_amp_entry_box.setValidator(self.keithley_6221_ac_amp_validator)
        # self.keithley_6221_ac_amp_entry_box.setPlaceholderText("2pA to 105mA")
        # self.keithley_6221_ac_amp_entry_box.setFixedHeight(30)
        # self.keithley_6221_ac_amp_units_combo = QComboBox()
        # self.keithley_6221_ac_amp_units_combo.setFont(self.font)
        # self.keithley_6221_ac_amp_units_combo.setStyleSheet(self.QCombo_stylesheet)
        # self.keithley_6221_ac_amp_units_combo.addItems(["Select Units"])  # 0
        # self.keithley_6221_ac_amp_units_combo.addItems(["mA"])  # 1
        # self.keithley_6221_ac_amp_units_combo.addItems(["µA"])  # 2
        # self.keithley_6221_ac_amp_units_combo.addItems(["nA"])  # 3
        # self.keithley_6221_ac_amp_units_combo.addItems(["pA"])  # 3
        # self.keithley_6221_ac_amp_layout.addWidget(self.keithley_6221_ac_amp_label)
        # self.keithley_6221_ac_amp_layout.addWidget(self.keithley_6221_ac_amp_entry_box)
        # self.keithley_6221_ac_amp_layout.addWidget(self.keithley_6221_ac_amp_units_combo)
        # self.keithley_6221_ac_range_single_layout.addLayout(self.keithley_6221_ac_amp_layout)

        self.keithley_6221_ac_freq_layout = QHBoxLayout()
        self.keithley_6221_ac_freq_label = QLabel("Frequency:")
        self.keithley_6221_ac_freq_label.setFont(self.font)
        self.keithley_6221_ac_freq_entry_box = QLineEdit()
        self.keithley_6221_ac_freq_entry_box.setFont(self.font)
        self.keithley_6221_ac_freq_validator = QDoubleValidator(0.00, 100000, 5)
        self.keithley_6221_ac_freq_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.keithley_6221_ac_freq_entry_box.setValidator(self.keithley_6221_ac_freq_validator)
        self.keithley_6221_ac_freq_entry_box.setPlaceholderText("0Hz to 100KHz")
        self.keithley_6221_ac_freq_entry_box.setFixedHeight(30)
        self.keithley_6221_ac_freq_unit_label = QLabel("Hz")
        self.keithley_6221_ac_freq_unit_label.setFont(self.font)
        self.keithley_6221_ac_freq_layout.addWidget(self.keithley_6221_ac_freq_label)
        self.keithley_6221_ac_freq_layout.addWidget(self.keithley_6221_ac_freq_entry_box)
        self.keithley_6221_ac_freq_layout.addWidget(self.keithley_6221_ac_freq_unit_label)
        self.keithley_6221_ac_range_single_layout.addLayout(self.keithley_6221_ac_freq_layout)

        self.keithley_6221_ac_offset_layout = QHBoxLayout()
        self.keithley_6221_ac_offset_label = QLabel("Offset:")
        self.keithley_6221_ac_offset_label.setFont(self.font)
        self.keithley_6221_ac_offset_entry_box = QLineEdit('0')
        self.keithley_6221_ac_offset_entry_box.setFont(self.font)
        # self.cur_field_entry_box.setValidator(IntegerValidator(-10000, 10000))
        self.keithley_6221_ac_offset_validator = QDoubleValidator(-105, 105, 10)
        self.keithley_6221_ac_offset_validator.setNotation(QDoubleValidator.Notation.StandardNotation)
        self.keithley_6221_ac_offset_entry_box.setValidator(self.keithley_6221_ac_offset_validator)
        self.keithley_6221_ac_offset_entry_box.setPlaceholderText("0 to ±105mA")
        self.keithley_6221_ac_offset_entry_box.setFixedHeight(30)
        self.keithley_6221_ac_offset_units_combo = QComboBox()
        self.keithley_6221_ac_offset_units_combo.setFont(self.font)
        self.keithley_6221_ac_offset_units_combo.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_ac_offset_units_combo.addItems(["Select Units"])  # 0
        self.keithley_6221_ac_offset_units_combo.addItems(["mA"])  # 1
        self.keithley_6221_ac_offset_units_combo.addItems(["µA"])  # 2
        self.keithley_6221_ac_offset_units_combo.addItems(["nA"])  # 3
        self.keithley_6221_ac_offset_units_combo.addItems(["pA"])  # 3
        self.keithley_6221_ac_offset_layout.addWidget(self.keithley_6221_ac_offset_label)
        self.keithley_6221_ac_offset_layout.addWidget(self.keithley_6221_ac_offset_entry_box)
        self.keithley_6221_ac_offset_layout.addWidget(self.keithley_6221_ac_offset_units_combo)
        self.keithley_6221_ac_range_single_layout.addLayout(self.keithley_6221_ac_offset_layout)

        self.keithley_6221_ac_phase_maker_layout = QHBoxLayout()
        self.keithley_6221_ac_phase_maker_label = QLabel("Phase Maker:")
        self.keithley_6221_ac_phase_maker_label.setFont(self.font)
        self.keithley_6221_ac_phase_maker_on_radio_button = QRadioButton("ON")
        self.keithley_6221_ac_phase_maker_on_radio_button.setFont(self.font)
        self.keithley_6221_ac_phase_maker_off_radio_button = QRadioButton("OFF")
        self.keithley_6221_ac_phase_maker_off_radio_button.setFont(self.font)
        self.keithley_6221_ac_phase_maker_on_radio_button.toggled.connect(self.select_keithley6221_phase_maker)
        self.keithley_6221_ac_phase_maker_off_radio_button.toggled.connect(self.select_keithley6221_phase_maker)
        self.keithley_6221_ac_phase_maker_button_group = QButtonGroup()
        self.keithley_6221_ac_phase_maker_button_group.addButton(self.keithley_6221_ac_phase_maker_on_radio_button)
        self.keithley_6221_ac_phase_maker_button_group.addButton(self.keithley_6221_ac_phase_maker_off_radio_button)
        self.keithley_6221_ac_phase_maker_layout.addWidget(self.keithley_6221_ac_phase_maker_label)
        self.keithley_6221_ac_phase_maker_layout.addWidget(self.keithley_6221_ac_phase_maker_on_radio_button)
        self.keithley_6221_ac_phase_maker_layout.addWidget(self.keithley_6221_ac_phase_maker_off_radio_button)
        self.keithley_6221_ac_range_single_layout.addLayout(self.keithley_6221_ac_phase_maker_layout)

        self.keithley_6221_ac_phase_maker_trigger_layout = QHBoxLayout()
        self.keithley_6221_ac_phase_maker_trigger_label = QLabel("Phase Maker Tigger Line:")
        self.keithley_6221_ac_phase_maker_trigger_label.setFont(self.font)
        self.keithley_6221_ac_phase_maker_trigger_combo_box = QComboBox()
        self.keithley_6221_ac_phase_maker_trigger_combo_box.setFont(self.font)
        self.keithley_6221_ac_phase_maker_trigger_combo_box.setStyleSheet(self.QCombo_stylesheet)
        self.keithley_6221_ac_phase_maker_trigger_combo_box.addItems(
            [" ", "1", "2", "3", "4", "5", "6"])
        self.keithley_6221_ac_phase_maker_trigger_combo_box.currentIndexChanged.connect(self.select_keithley6221_phase_maker_trigger)

        self.keithley_6221_ac_phase_maker_trigger_layout.addWidget(self.keithley_6221_ac_phase_maker_trigger_label)
        self.keithley_6221_ac_phase_maker_trigger_layout.addWidget(self.keithley_6221_ac_phase_maker_trigger_combo_box)
        self.keithley_6221_ac_range_single_layout.addLayout(self.keithley_6221_ac_phase_maker_trigger_layout)

        self.Keithey_curSour_layout.addLayout(self.keithley_6221_ac_range_single_layout)
        self.Keithey_curSour_layout.addWidget(self.keithley_6221_test_button_ui())

        self.keithley_6221_ac_selection_btn_group = QButtonGroup()
        self.keithley_6221_ac_selection_btn_group.addButton(self.keithley_6221_ac_range_checkbox)
        self.keithley_6221_ac_selection_btn_group.addButton(self.keithley_6221_ac_single_checkbox)

    def keithley_6221_test_on_off(self):
        if not self.KEITHLEY_6221_TEST_ON:
            self.KEITHLEY_6221_TEST_ON = True
            self.keithley_6221_test_button.setText('OFF')
            if not self.demo_mode:
                if self.keithley_6221_DC_radio.isChecked():
                    if self.keithley_6221_DC_range_checkbox.isChecked():
                        init_current = float(self.keithley_6221_DC_range_init_entry.text())
                        dc_range_unit = self.keithley_6221_DC_range_combobox.currentIndex()
                        if dc_range_unit != 0:
                            if dc_range_unit == 1:  # mA
                                DC_range_selected_unit = 'e-3'
                            elif dc_range_unit == 2:  # uA
                                DC_range_selected_unit = 'e-6'
                            elif dc_range_unit == 3:  # nA
                                DC_range_selected_unit = 'e-9'
                            elif dc_range_unit == 4:  # pA
                                DC_range_selected_unit = 'e-12'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.keithley_6221_test_button.setText('Test')
                            self.KEITHLEY_6221_TEST_ON = False
                            return
                        current = [f"{init_current}{DC_range_selected_unit}"]
                    elif self.keithley_6221_DC_single_checkbox.isChecked():
                        single_dc_current = self.keithley_6221_DC_single_entry.text()
                        single_dc_current = single_dc_current.replace(" ", "")
                        single_dc_current = [float(item) for item in single_dc_current.split(',')]
                        signle_dc_unit = self.keithley_6221_DC_single_combobox.currentIndex()
                        if signle_dc_unit != 0:
                            if signle_dc_unit == 1:  # mA
                                DC_single_selected_unit = 'e-3'
                            elif signle_dc_unit == 2:  # uA
                                DC_single_selected_unit = 'e-6'
                            elif signle_dc_unit == 3:  # nA
                                DC_single_selected_unit = 'e-9'
                            elif signle_dc_unit == 4:  # pA
                                DC_single_selected_unit = 'e-12'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.keithley_6221_test_button.setText('Test')
                            self.KEITHLEY_6221_TEST_ON = False
                            return
                        current = [f"{single_dc_current[0]}{DC_single_selected_unit}"]
                    else:
                        QMessageBox.warning(self, 'Warning', 'Please choose one of the options')
                        self.keithley_6221_test_button.setText('Test')
                        self.KEITHLEY_6221_TEST_ON = False
                        return
                    if current:
                        self.keithley_6221.write(":OUTP OFF")  # Set source function to current
                        self.keithley_6221.write("CURRent:RANGe:AUTO ON \n")
                        self.keithley_6221.write(f'CURR {current[0]} \n')
                        self.keithley_6221.write(":OUTP ON")  # Turn on the output
                    else:
                        QMessageBox.warning(self, 'Warning', 'Please enter the current')
                        self.keithley_6221_test_button.setText('Test')
                        self.KEITHLEY_6221_TEST_ON = False
                elif self.keithley_6221_ac_radio.isChecked():
                    if self.keithley_6221_ac_range_checkbox.isChecked():
                        init_current = float(self.keithley_6221_ac_range_init_entry.text())
                        ac_range_unit = self.keithley_6221_ac_range_combobox.currentIndex()
                        if ac_range_unit != 0:
                            if ac_range_unit == 1:  # mA
                                ac_range_selected_unit = 'e-3'
                            elif ac_range_unit == 2:  # uA
                                ac_range_selected_unit = 'e-6'
                            elif ac_range_unit == 3:  # nA
                                ac_range_selected_unit = 'e-9'
                            elif ac_range_unit == 4:  # pA
                                ac_range_selected_unit = 'e-12'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.keithley_6221_test_button.setText('Test')
                            self.KEITHLEY_6221_TEST_ON = False
                            return
                        current = [f"{init_current}{ac_range_selected_unit}"]
                    elif self.keithley_6221_ac_single_checkbox.isChecked():
                        single_ac_current = self.keithley_6221_ac_single_entry.text()
                        single_ac_current = single_ac_current.replace(" ", "")
                        single_ac_current = [float(item) for item in single_ac_current.split(',')]
                        ac_single_unit = self.keithley_6221_ac_single_combobox.currentIndex()
                        if ac_single_unit != 0:
                            if ac_single_unit == 1:  # mA
                                ac_range_selected_unit = 'e-3'
                            elif ac_single_unit == 2:  # uA
                                ac_range_selected_unit = 'e-6'
                            elif ac_single_unit == 3:  # nA
                                ac_range_selected_unit = 'e-9'
                            elif ac_single_unit == 4:  # pA
                                ac_range_selected_unit = 'e-12'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.keithley_6221_test_button.setText('Test')
                            self.KEITHLEY_6221_TEST_ON = False
                            return
                        current = [f"{single_ac_current[0]}{ac_range_selected_unit}"]
                    else:
                        QMessageBox.warning(self, 'Warning', 'Please choose one of the options')
                        self.keithley_6221_test_button.setText('Test')
                        self.KEITHLEY_6221_TEST_ON = False
                        return

                    ac_current_waveform_index = self.keithley_6221_ac_waveform_combo_box.currentIndex()
                    if ac_current_waveform_index != 0:
                        if ac_current_waveform_index == 1:  # sine
                            ac_current_waveform = "SIN"
                        elif ac_current_waveform_index == 2:  # square
                            ac_current_waveform = "SQU"
                        elif ac_current_waveform_index == 3:  # ramp
                            ac_current_waveform = "RAMP"
                        elif ac_current_waveform_index == 4:  # arbx
                            ac_current_waveform = "ARB0"
                        else:
                            ac_current_waveform = None

                    ac_current_freq = self.keithley_6221_ac_freq_entry_box.text()
                    ac_current_offset = self.keithley_6221_ac_offset_entry_box.text()
                    ac_offset_unit = self.keithley_6221_ac_offset_units_combo.currentIndex()
                    if ac_offset_unit == 0:
                        ac_offset_unit = ''
                    elif ac_offset_unit == 1:  # mA
                        ac_offset_unit = 'e-3'
                    elif ac_offset_unit == 2:  # uA
                        ac_offset_unit = 'e-6'
                    elif ac_offset_unit == 3:  # nA
                        ac_offset_unit = 'e-9'
                    elif ac_offset_unit == 4:  # pA
                        ac_offset_unit = 'e-12'
                    ac_current_offset = ac_current_offset + ac_offset_unit
                    if current and ac_current_waveform and ac_current_freq:
                        self.keithley_6221.write("SOUR:WAVE:ABOR \n")
                        self.keithley_6221.write('CURR:RANG:AUTO ON \n')
                        self.keithley_6221.write(f'SOUR:WAVE:FUNC {ac_current_waveform} \n')
                        self.keithley_6221.write(f'SOUR:WAVE:AMPL {current[0]} \n')
                        self.keithley_6221.write(f'SOUR:WAVE:FREQ {ac_current_freq} \n')
                        self.keithley_6221.write(f'SOUR:WAVE:OFFset {ac_current_offset} \n')
                        self.keithley_6221.write('SOUR:WAVE:RANG BEST \n')
                        self.keithley_6221.write('SOUR:WAVE:ARM \n')
                        self.keithley_6221.write('SOUR:WAVE:INIT \n')
                    else:
                        QMessageBox.warning(self, 'Warning', 'Missing Items')
                        self.keithley_6221_test_button.setText('Test')
                        self.KEITHLEY_6221_TEST_ON = False
                if self.DSP7265:
                    time.sleep(5)
                    cur_freq = float(self.DSP7265.query('FRQ[.]')) / 1000
                    self.dsp7265_freq_reading_value_label.setText(str(cur_freq) + ' Hz')
        else:
            self.KEITHLEY_6221_TEST_ON = False
            self.keithley_6221_test_button.setText('Test')
            try:
                if not self.demo_mode:
                    self.keithley_6221.write(":OUTP OFF")  # Set source function to current
                    self.keithley_6221.write("SOUR:WAVE:ABOR \n")
                    if self.DSP7265:
                        time.sleep(2)
                        cur_freq = float(self.DSP7265.query('FRQ[.]')) / 1000
                        self.dsp7265_freq_reading_value_label.setText(str(cur_freq) + ' Hz')
            except Exception as e:
                None

    def select_keithley6221_phase_maker(self):
        if self.keithley_6221_ac_phase_maker_on_radio_button.isChecked():
            self.keithley_6221.write('SOUR:WAVE:PMAR:STAT ON')
        else:
            self.keithley_6221.write('SOUR:WAVE:PMAR:STAT OFF')

    def select_keithley6221_phase_maker_trigger(self):
        self.pm_trigger = self.keithley_6221_ac_phase_maker_trigger_combo_box.currentIndex()
        if self.pm_trigger != 0:
            self.keithley_6221.write(f'SOUR:WAVE:PMAR:OLIN {self.pm_trigger}')

    def on_6221_DC_toggle(self):
        if self.keithley_6221_DC_range_checkbox.isChecked():
            self.keithley_6221_DC_single_checkbox.setEnabled(False)
            self.keithley_6221_DC_single_entry.setEnabled(False)
            self.keithley_6221_DC_single_combobox.setEnabled(False)
        else:
            self.keithley_6221_DC_single_checkbox.setEnabled(True)
            self.keithley_6221_DC_single_entry.setEnabled(True)
            self.keithley_6221_DC_single_combobox.setEnabled(True)

        if self.keithley_6221_DC_single_checkbox.isChecked():
            self.keithley_6221_DC_range_checkbox.setEnabled(False)
            self.keithley_6221_DC_range_init_entry.setEnabled(False)
            self.keithley_6221_DC_range_final_entry.setEnabled(False)
            self.keithley_6221_DC_range_step_entry.setEnabled(False)
            self.keithley_6221_DC_range_combobox.setEnabled(False)
        else:
            self.keithley_6221_DC_range_checkbox.setEnabled(True)
            self.keithley_6221_DC_range_init_entry.setEnabled(True)
            self.keithley_6221_DC_range_final_entry.setEnabled(True)
            self.keithley_6221_DC_range_step_entry.setEnabled(True)
            self.keithley_6221_DC_range_combobox.setEnabled(True)

    # ---------------------------------------------------------------------------------
    #  PPMS Portion
    # ---------------------------------------------------------------------------------

    def ppms_status_reading_ui(self):
        self.ppms_reading_layout = QVBoxLayout()
        self.ppms_temp_layout = QHBoxLayout()
        self.ppms_temp_label = QLabel('Temperature (K):')
        self.ppms_temp_label.setFont(self.font)
        self.ppms_reading_temp_label = QLabel('N/A K')
        self.ppms_reading_temp_label.setFont(self.font)
        self.ppms_temp_layout.addWidget(self.ppms_temp_label)
        self.ppms_temp_layout.addWidget(self.ppms_reading_temp_label)
        self.ppms_field_layout = QHBoxLayout()
        self.ppms_field_label = QLabel('Field (Oe):')
        self.ppms_field_label.setFont(self.font)
        self.ppms_reading_field_label = QLabel('N/A Oe')
        self.ppms_reading_field_label.setFont(self.font)
        self.ppms_field_layout.addWidget(self.ppms_field_label)
        self.ppms_field_layout.addWidget(self.ppms_reading_field_label)

        self.ppms_chamber_layout = QHBoxLayout()
        self.ppms_chamber_label = QLabel('Chamber Status:')
        self.ppms_chamber_label.setFont(self.font)
        self.ppms_reading_chamber_label = QLabel('N/A')
        self.ppms_reading_chamber_label.setFont(self.font)
        self.ppms_chamber_layout.addWidget(self.ppms_chamber_label)
        self.ppms_chamber_layout.addWidget(self.ppms_reading_chamber_label)

        self.ppms_reading_layout.addLayout(self.ppms_temp_layout)
        self.ppms_reading_layout.addLayout(self.ppms_field_layout)
        self.ppms_reading_layout.addLayout(self.ppms_chamber_layout)
        return self.ppms_reading_layout

    def ppms_temperature_setup_ui(self):
        # if self.ETO_FIELD_DEP:
        self.ppms_temp_setting_layout = QVBoxLayout()
        self.ppms_temp_radio_buttom_layout = QHBoxLayout()
        self.ppms_zone_temp_layout = QVBoxLayout()
        self.Temp_setup_Zone_1 = False
        self.Temp_setup_Zone_2 = False
        self.Temp_setup_Zone_3 = False
        self.Temp_setup_Zone_Cus = False
        self.ppms_temp_zone_number_label = QLabel('Number of Independent Step Regions:')
        self.ppms_temp_zone_number_label.setFont(self.font)
        self.ppms_temp_One_zone_radio = QRadioButton("1")
        self.ppms_temp_One_zone_radio.setFont(self.font)
        self.ppms_temp_One_zone_radio.toggled.connect(self.temp_zone_selection)
        self.ppms_temp_Two_zone_radio = QRadioButton("2")
        self.ppms_temp_Two_zone_radio.setFont(self.font)
        self.ppms_temp_Two_zone_radio.toggled.connect(self.temp_zone_selection)
        self.ppms_temp_Three_zone_radio = QRadioButton("3")
        self.ppms_temp_Three_zone_radio.setFont(self.font)
        self.ppms_temp_Three_zone_radio.toggled.connect(self.temp_zone_selection)
        self.ppms_temp_Customize_zone_radio = QRadioButton("Customize")
        self.ppms_temp_Customize_zone_radio.setFont(self.font)
        self.ppms_temp_Customize_zone_radio.toggled.connect(self.temp_zone_selection)
        self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_One_zone_radio)
        self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Two_zone_radio)
        self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Three_zone_radio)
        self.ppms_temp_radio_buttom_layout.addWidget(self.ppms_temp_Customize_zone_radio)
        self.ppms_temp_setting_layout.addWidget(self.ppms_temp_zone_number_label)
        self.ppms_temp_setting_layout.addLayout(self.ppms_temp_radio_buttom_layout)
        self.ppms_temp_setting_layout.addLayout(self.ppms_zone_temp_layout)

        return self.ppms_temp_setting_layout

    def ppms_field_setup_ui(self):
        try:
            self.ppms_field_setting_init_layout = QVBoxLayout()
            self.ppms_field_direction_button_layout = QHBoxLayout()
            self.ppms_field_bidirectional_mode_radio_button = QRadioButton("Bidirectional")
            self.ppms_field_bidirectional_mode_radio_button.setFont(self.font)
            # self.ppms_field_bidirectional_mode_radio_button.setChecked(True)
            self.ppms_field_bidirectional_mode_radio_button.toggled.connect(self.ppms_field_mode_setup_ui)

            self.ppms_field_unidirectional_mode_radio_button = QRadioButton("Unidirectional")
            self.ppms_field_unidirectional_mode_radio_button.setFont(self.font)
            self.ppms_field_unidirectional_mode_radio_button.toggled.connect(self.ppms_field_mode_setup_ui)

            self.ppms_field_direction_button_layout.addWidget(self.ppms_field_bidirectional_mode_radio_button)
            self.ppms_field_direction_button_layout.addWidget(self.ppms_field_unidirectional_mode_radio_button)
            self.ppms_field_direction_button_group = QButtonGroup()
            self.ppms_field_direction_button_group.addButton(self.ppms_field_bidirectional_mode_radio_button)
            self.ppms_field_direction_button_group.addButton(self.ppms_field_unidirectional_mode_radio_button)
            self.ppms_field_setting_init_layout.addLayout(self.ppms_field_direction_button_layout)

            self.ppms_field_setting_layout = QVBoxLayout()
            self.ppms_field_setting_init_layout.addLayout(self.ppms_field_setting_layout)
            return self.ppms_field_setting_init_layout
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def ppms_field_mode_setup_ui(self):
        # if self.ETO_FIELD_DEP:
        # self.ppms_field_setting_layout = QVBoxLayout()
        self.clear_layout(self.ppms_field_setting_layout)
        self.ppms_field_mode_buttom_layout = QHBoxLayout()
        self.ppms_field_radio_buttom_layout = QHBoxLayout()
        self.ppms_zone_field_layout = QVBoxLayout()

        self.Field_setup_Zone_1 = False
        self.Field_setup_Zone_2 = False
        self.Field_setup_Zone_3 = False
        self.Field_setup_customized = False

        self.ppms_field_cointinous_mode_radio_button = QRadioButton("Continuous Sweep")
        self.ppms_field_cointinous_mode_radio_button.setFont(self.font)
        self.ppms_field_cointinous_mode_radio_button.setChecked(True)
        self.ppms_field_cointinous_mode_radio_button.toggled.connect(self.disable_step_field)

        self.ppms_field_fixed_mode_radio_button = QRadioButton("Fixed Field")
        self.ppms_field_fixed_mode_radio_button.setFont(self.font)
        self.ppms_field_fixed_mode_radio_button.toggled.connect(self.disable_step_field)

        self.ppms_field_mode_buttom_layout.addWidget(self.ppms_field_cointinous_mode_radio_button)
        self.ppms_field_mode_buttom_layout.addWidget(self.ppms_field_fixed_mode_radio_button)
        self.ppms_field_mode_buttom_group = QButtonGroup()
        self.ppms_field_mode_buttom_group.addButton(self.ppms_field_cointinous_mode_radio_button)
        self.ppms_field_mode_buttom_group.addButton(self.ppms_field_fixed_mode_radio_button)

        if self.ppms_field_unidirectional_mode_radio_button.isChecked():
            self.ppms_field_customized_mode_radio_button = QRadioButton("Customize")
            self.ppms_field_customized_mode_radio_button.setFont(self.font)
            self.ppms_field_customized_mode_radio_button.toggled.connect(self.disable_step_field)
            self.ppms_field_mode_buttom_layout.addWidget(self.ppms_field_customized_mode_radio_button)
            self.ppms_field_mode_buttom_group.addButton(self.ppms_field_customized_mode_radio_button)

        self.ppms_field_zone_number_label = QLabel('Number of Independent Step Regions:')
        self.ppms_field_zone_number_label.setFont(self.font)
        self.ppms_field_One_zone_radio = QRadioButton("1")
        self.ppms_field_One_zone_radio.setFont(self.font)
        self.ppms_field_One_zone_radio.toggled.connect(self.field_zone_selection)
        self.ppms_field_Two_zone_radio = QRadioButton("2")
        self.ppms_field_Two_zone_radio.setFont(self.font)
        self.ppms_field_Two_zone_radio.toggled.connect(self.field_zone_selection)
        self.ppms_field_Three_zone_radio = QRadioButton("3")
        self.ppms_field_Three_zone_radio.setFont(self.font)
        self.ppms_field_Three_zone_radio.toggled.connect(self.field_zone_selection)
        self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_One_zone_radio)
        self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Two_zone_radio)
        self.ppms_field_radio_buttom_layout.addWidget(self.ppms_field_Three_zone_radio)
        self.ppms_field_setting_layout.addLayout(self.ppms_field_mode_buttom_layout)
        self.ppms_field_setting_layout.addWidget(self.ppms_field_zone_number_label)
        self.ppms_field_setting_layout.addLayout(self.ppms_field_radio_buttom_layout)
        self.ppms_field_setting_layout.addLayout(self.ppms_zone_field_layout)

    def disable_step_field(self):
        if self.ppms_field_cointinous_mode_radio_button.isChecked():
            if self.ppms_field_One_zone_radio.isChecked():
                self.ppms_zone1_field_step_entry.setEnabled(False)
            elif self.ppms_field_Two_zone_radio.isChecked():
                self.ppms_zone1_field_step_entry.setEnabled(False)
                self.ppms_zone2_field_step_entry.setEnabled(False)
            elif self.ppms_field_Three_zone_radio.isChecked():
                self.ppms_zone1_field_step_entry.setEnabled(False)
                self.ppms_zone2_field_step_entry.setEnabled(False)
                self.ppms_zone3_field_step_entry.setEnabled(False)
        elif self.ppms_field_fixed_mode_radio_button.isChecked():
            if self.ppms_field_One_zone_radio.isChecked():
                self.ppms_zone1_field_step_entry.setEnabled(True)
            elif self.ppms_field_Two_zone_radio.isChecked():
                self.ppms_zone1_field_step_entry.setEnabled(True)
                self.ppms_zone2_field_step_entry.setEnabled(True)
            elif self.ppms_field_Three_zone_radio.isChecked():
                self.ppms_zone1_field_step_entry.setEnabled(True)
                self.ppms_zone2_field_step_entry.setEnabled(True)
                self.ppms_zone3_field_step_entry.setEnabled(True)

    def field_zone_selection(self):
        if self.ppms_field_One_zone_radio.isChecked() and self.Field_setup_Zone_1 == False:
            self.ppms_field_One_zone_radio.setChecked(False)
            self.Field_setup_Zone_1 = True
            self.Field_setup_Zone_2 = False
            self.Field_setup_Zone_3 = False
            self.field_one_zone()
            self.ppms_field_One_zone_radio.setChecked(False)
        elif self.ppms_field_Two_zone_radio.isChecked() and self.Field_setup_Zone_2 == False:
            self.ppms_field_Two_zone_radio.setChecked(False)
            self.Field_setup_Zone_1 = False
            self.Field_setup_Zone_2 = True
            self.Field_setup_Zone_3 = False
            self.field_two_zone()
            self.ppms_field_Two_zone_radio.setChecked(False)
        elif self.ppms_field_Three_zone_radio.isChecked() and self.Field_setup_Zone_3 == False:
            self.ppms_field_Three_zone_radio.setChecked(False)
            self.Field_setup_Zone_1 = False
            self.Field_setup_Zone_2 = False
            self.Field_setup_Zone_3 = True
            self.field_three_zone()
            self.ppms_field_Three_zone_radio.setChecked(False)

    def field_one_zone(self):
        if self.ppms_field_bidirectional_mode_radio_button.isChecked() or self.ppms_field_unidirectional_mode_radio_button.isChecked():
            self.ppms_zone1_field_layout = QVBoxLayout()
            self.ppms_zone1_field_range_layout = QHBoxLayout()
            if self.ppms_field_unidirectional_mode_radio_button.isChecked():
                self.ppms_zone1_from_label = QLabel('Range (Oe): From')
                self.ppms_zone1_from_label.setFont(self.font)
                self.ppms_zone1_from_entry = QLineEdit()
                self.ppms_zone1_from_entry.setFont(self.font)
                self.ppms_zone1_from_entry.setPlaceholderText("3000 Oe")
                self.ppms_zone1_to_label = QLabel(' to ')
                self.ppms_zone1_to_label.setFont(self.font)
                self.ppms_zone1_to_entry = QLineEdit()
                self.ppms_zone1_to_entry.setFont(self.font)
                self.ppms_zone1_to_entry.setPlaceholderText("-3000 Oe")
                self.ppms_zone1_to_entry.setEnabled(True)
            elif self.ppms_field_bidirectional_mode_radio_button.isChecked():
                self.ppms_zone1_from_label = QLabel('Range (Oe): Top')
                self.ppms_zone1_from_label.setFont(self.font)
                self.ppms_zone1_from_entry = QLineEdit()
                self.ppms_zone1_from_entry.setFont(self.font)
                self.ppms_zone1_from_entry.setPlaceholderText("3000 Oe")
                self.ppms_zone1_to_label = QLabel(' Bottom ')
                self.ppms_zone1_to_label.setFont(self.font)
                self.ppms_zone1_to_entry = QLineEdit()
                self.ppms_zone1_to_entry.setFont(self.font)
                self.ppms_zone1_to_entry.setPlaceholderText("0 Oe")
                self.ppms_zone1_to_entry.setText("0")
                self.ppms_zone1_to_entry.setEnabled(False)
            self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_from_label)
            self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_from_entry)
            self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_to_label)
            self.ppms_zone1_field_range_layout.addWidget(self.ppms_zone1_to_entry)

            self.ppms_zone1_field_step_layout = QHBoxLayout()
            self.ppms_zone1_field_step_label = QLabel('Step Size (Oe): ')
            self.ppms_zone1_field_step_label.setFont(self.font)
            self.ppms_zone1_field_step_entry = QLineEdit()
            self.ppms_zone1_field_step_entry.setFont(self.font)
            if self.ppms_field_cointinous_mode_radio_button.isChecked():
                self.ppms_zone1_field_step_entry.setEnabled(False)
            else:
                self.ppms_zone1_field_step_entry.setEnabled(True)
            self.ppms_zone1_field_rate_label = QLabel('Rate (Oe/sec): ')
            self.ppms_zone1_field_rate_label.setFont(self.font)
            self.ppms_zone1_field_rate_entry = QLineEdit()
            self.ppms_zone1_field_rate_entry.setFont(self.font)
            self.ppms_zone1_field_rate_entry.setText('220')
            self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_step_label)
            self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_step_entry)
            self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_rate_label)
            self.ppms_zone1_field_step_layout.addWidget(self.ppms_zone1_field_rate_entry)

            self.ppms_zone1_field_layout.addLayout(self.ppms_zone1_field_range_layout)
            self.ppms_zone1_field_layout.addLayout(self.ppms_zone1_field_step_layout)
            self.clear_layout(self.ppms_zone_field_layout)
            self.ppms_zone_field_layout.addLayout(self.ppms_zone1_field_layout)
        else:
            QMessageBox.warning(
                self, "Error",
                f"Please Select the field direction!\n"
            )

    def field_two_zone(self):
        if self.ppms_field_bidirectional_mode_radio_button.isChecked() or self.ppms_field_unidirectional_mode_radio_button.isChecked():
            self.field_one_zone()
            self.ppms_zone1_from_entry.setPlaceholderText("3000 Oe")
            self.ppms_zone1_to_entry.setPlaceholderText("2000 Oe")
            self.ppms_zone2_field_layout = QVBoxLayout()
            self.ppms_zone2_field_range_layout = QHBoxLayout()

            if self.ppms_field_unidirectional_mode_radio_button.isChecked():
                self.ppms_zone2_from_label = QLabel('Range 2 (Oe): From')
                self.ppms_zone2_from_label.setFont(self.font)
                self.ppms_zone2_from_entry = QLineEdit()
                self.ppms_zone2_from_entry.setFont(self.font)
                self.ppms_zone2_to_label = QLabel(' to ')
                self.ppms_zone2_to_label.setFont(self.font)
                self.ppms_zone2_to_entry = QLineEdit()
                self.ppms_zone2_to_entry.setFont(self.font)
                self.ppms_zone2_from_entry.setPlaceholderText("2000 Oe")
                self.ppms_zone2_to_entry.setEnabled(True)
            elif self.ppms_field_bidirectional_mode_radio_button.isChecked():
                self.ppms_zone1_to_entry.setText("")
                self.ppms_zone1_to_entry.setPlaceholderText("2000 Oe")
                self.ppms_zone1_to_entry.setEnabled(True)
                self.ppms_zone2_from_label = QLabel('Range 2 (Oe): Top')
                self.ppms_zone2_from_label.setFont(self.font)
                self.ppms_zone2_from_entry = QLineEdit()
                self.ppms_zone2_from_entry.setFont(self.font)
                self.ppms_zone2_to_label = QLabel(' Bottom ')
                self.ppms_zone2_to_label.setFont(self.font)
                self.ppms_zone2_to_entry = QLineEdit()
                self.ppms_zone2_to_entry.setFont(self.font)
                self.ppms_zone2_from_entry.setPlaceholderText("2000 Oe")
                self.ppms_zone2_to_entry.setText("0")
                self.ppms_zone2_to_entry.setEnabled(False)
            self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_from_label)
            self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_from_entry)
            self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_to_label)
            self.ppms_zone2_field_range_layout.addWidget(self.ppms_zone2_to_entry)

            self.ppms_zone2_field_step_layout = QHBoxLayout()
            self.ppms_zone2_field_step_label = QLabel('Step Size 2 (Oe): ')
            self.ppms_zone2_field_step_label.setFont(self.font)
            self.ppms_zone2_field_step_entry = QLineEdit()
            self.ppms_zone2_field_step_entry.setFont(self.font)
            if self.ppms_field_cointinous_mode_radio_button.isChecked():
                self.ppms_zone2_field_step_entry.setEnabled(False)
            else:
                self.ppms_zone2_field_step_entry.setEnabled(True)
            self.ppms_zone2_field_rate_label = QLabel('Rate (Oe/sec): ')
            self.ppms_zone2_field_rate_label.setFont(self.font)
            self.ppms_zone2_field_rate_entry = QLineEdit()
            self.ppms_zone2_field_rate_entry.setFont(self.font)
            self.ppms_zone2_field_rate_entry.setText('220')
            self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_step_label)
            self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_step_entry)
            self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_rate_label)
            self.ppms_zone2_field_step_layout.addWidget(self.ppms_zone2_field_rate_entry)

            self.ppms_zone2_field_layout.addLayout(self.ppms_zone2_field_range_layout)
            self.ppms_zone2_field_layout.addLayout(self.ppms_zone2_field_step_layout)
            self.ppms_zone_field_layout.addLayout(self.ppms_zone2_field_layout)
        else:
            QMessageBox.warning(
                self, "Error",
                f"Please Select the field direction!\n"
            )

    def field_three_zone(self):
        if self.ppms_field_bidirectional_mode_radio_button.isChecked() or self.ppms_field_unidirectional_mode_radio_button.isChecked():
            self.field_two_zone()
            self.ppms_zone1_from_entry.setPlaceholderText("3000 Oe")
            self.ppms_zone1_to_entry.setPlaceholderText("2000 Oe")
            self.ppms_zone2_from_entry.setPlaceholderText("2000 Oe")
            self.ppms_zone2_to_entry.setPlaceholderText("1000 Oe")
            self.ppms_zone2_to_entry.clear()
            self.ppms_zone2_to_entry.setEnabled(True)
            self.ppms_zone3_field_layout = QVBoxLayout()
            self.ppms_zone3_field_range_layout = QHBoxLayout()
            if self.ppms_field_unidirectional_mode_radio_button.isChecked():
                self.ppms_zone3_from_label = QLabel('Range 3 (Oe): From')
                self.ppms_zone3_from_label.setFont(self.font)
                self.ppms_zone3_from_entry = QLineEdit()
                self.ppms_zone3_from_entry.setFont(self.font)
                self.ppms_zone3_to_label = QLabel(' to ')
                self.ppms_zone3_to_label.setFont(self.font)
                self.ppms_zone3_to_entry = QLineEdit()
                self.ppms_zone3_to_entry.setFont(self.font)
                self.ppms_zone3_from_entry.setPlaceholderText("1000 Oe")
                self.ppms_zone3_to_entry.setEnabled(True)
            elif self.ppms_field_bidirectional_mode_radio_button.isChecked():
                self.ppms_zone3_from_label = QLabel('Range 3 (Oe): Top')
                self.ppms_zone3_from_label.setFont(self.font)
                self.ppms_zone3_from_entry = QLineEdit()
                self.ppms_zone3_from_entry.setFont(self.font)
                self.ppms_zone3_to_label = QLabel(' Bottom ')
                self.ppms_zone3_to_label.setFont(self.font)
                self.ppms_zone3_to_entry = QLineEdit()
                self.ppms_zone3_to_entry.setFont(self.font)
                self.ppms_zone3_from_entry.setPlaceholderText("1000 Oe")
                self.ppms_zone3_to_entry.setText("0")
                self.ppms_zone3_to_entry.setEnabled(False)
            self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_from_label)
            self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_from_entry)
            self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_to_label)
            self.ppms_zone3_field_range_layout.addWidget(self.ppms_zone3_to_entry)

            self.ppms_zone3_field_step_layout = QHBoxLayout()
            self.ppms_zone3_field_step_label = QLabel('Step Size 3 (Oe): ')
            self.ppms_zone3_field_step_label.setFont(self.font)
            self.ppms_zone3_field_step_entry = QLineEdit()
            self.ppms_zone3_field_step_entry.setFont(self.font)
            if self.ppms_field_cointinous_mode_radio_button.isChecked():
                self.ppms_zone3_field_step_entry.setEnabled(False)
            else:
                self.ppms_zone3_field_step_entry.setEnabled(True)

            self.ppms_zone3_field_rate_label = QLabel('Rate (Oe/sec): ')
            self.ppms_zone3_field_rate_label.setFont(self.font)
            self.ppms_zone3_field_rate_entry = QLineEdit()
            self.ppms_zone3_field_rate_entry.setFont(self.font)
            self.ppms_zone3_field_rate_entry.setText('220')

            self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_step_label)
            self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_step_entry)
            self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_rate_label)
            self.ppms_zone3_field_step_layout.addWidget(self.ppms_zone3_field_rate_entry)

            self.ppms_zone3_field_layout.addLayout(self.ppms_zone3_field_range_layout)
            self.ppms_zone3_field_layout.addLayout(self.ppms_zone3_field_step_layout)
            self.ppms_zone_field_layout.addLayout(self.ppms_zone3_field_layout)
        else:
            QMessageBox.warning(
                self, "Error",
                f"Please Select the field direction!\n"
            )

    def temp_zone_selection(self):
        if self.ppms_temp_One_zone_radio.isChecked() and self.Temp_setup_Zone_1 == False:
            self.ppms_temp_One_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = True
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = False
            self.Temp_setup_Zone_Cus = False
            self.temp_one_zone()
            self.ppms_temp_One_zone_radio.setChecked(False)
        elif self.ppms_temp_Two_zone_radio.isChecked() and self.Temp_setup_Zone_2 == False:
            self.ppms_temp_Two_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = True
            self.Temp_setup_Zone_3 = False
            self.Temp_setup_Zone_Cus = False
            self.temp_two_zone()
            self.ppms_temp_Two_zone_radio.setChecked(False)
        elif self.ppms_temp_Three_zone_radio.isChecked() and self.Temp_setup_Zone_3 == False:
            self.ppms_temp_Three_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = True
            self.Temp_setup_Zone_Cus = False
            self.temp_three_zone()
            self.ppms_temp_Three_zone_radio.setChecked(False)
        elif self.ppms_temp_Customize_zone_radio.isChecked() and self.Temp_setup_Zone_Cus == False:
            self.ppms_temp_Customize_zone_radio.setChecked(False)
            self.Temp_setup_Zone_1 = False
            self.Temp_setup_Zone_2 = False
            self.Temp_setup_Zone_3 = False
            self.Temp_setup_Zone_Cus = True
            self.temp_customize_zone()
            self.ppms_temp_Customize_zone_radio.setChecked(False)

    def temp_one_zone(self):
        self.ppms_zone1_temp_layout = QVBoxLayout()
        self.ppms_zone1_temp_range_layout = QHBoxLayout()
        self.ppms_zone1_temp_from_label = QLabel('Range (K): From')
        self.ppms_zone1_temp_from_label.setFont(self.font)
        self.ppms_zone1_temp_from_entry = QLineEdit()
        self.ppms_zone1_temp_from_entry.setFont(self.font)
        self.ppms_zone1_temp_to_label = QLabel(' to ')
        self.ppms_zone1_temp_to_label.setFont(self.font)
        self.ppms_zone1_temp_to_entry = QLineEdit()
        self.ppms_zone1_temp_to_entry.setFont(self.font)
        self.ppms_zone1_temp_range_layout.addWidget(self.ppms_zone1_temp_from_label)
        self.ppms_zone1_temp_range_layout.addWidget(self.ppms_zone1_temp_from_entry)
        self.ppms_zone1_temp_range_layout.addWidget(self.ppms_zone1_temp_to_label)
        self.ppms_zone1_temp_range_layout.addWidget(self.ppms_zone1_temp_to_entry)

        self.ppms_zone1_temp_step_layout = QHBoxLayout()
        self.ppms_zone1_temp_step_label = QLabel('Step Size (K): ')
        self.ppms_zone1_temp_step_label.setFont(self.font)
        self.ppms_zone1_temp_step_entry = QLineEdit()
        self.ppms_zone1_temp_step_entry.setFont(self.font)

        self.ppms_zone1_temp_rate_label = QLabel('Rate (K/min): ')
        self.ppms_zone1_temp_rate_label.setFont(self.font)
        self.ppms_zone1_temp_rate_entry = QLineEdit()
        self.ppms_zone1_temp_rate_entry.setFont(self.font)
        self.ppms_zone1_temp_rate_entry.setText('5')

        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_step_label)
        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_step_entry)
        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_rate_label)
        self.ppms_zone1_temp_step_layout.addWidget(self.ppms_zone1_temp_rate_entry)

        self.ppms_zone1_temp_layout.addLayout(self.ppms_zone1_temp_range_layout)
        self.ppms_zone1_temp_layout.addLayout(self.ppms_zone1_temp_step_layout)
        self.clear_layout(self.ppms_zone_temp_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone1_temp_layout)

    def temp_two_zone(self):
        self.temp_one_zone()
        self.ppms_zone2_temp_layout = QVBoxLayout()
        self.ppms_zone2_temp_range_layout = QHBoxLayout()
        self.ppms_zone2_temp_from_label = QLabel('Range 2 (K): From')
        self.ppms_zone2_temp_from_label.setFont(self.font)
        self.ppms_zone2_temp_from_entry = QLineEdit()
        self.ppms_zone2_temp_from_entry.setFont(self.font)
        self.ppms_zone2_temp_to_label = QLabel(' to ')
        self.ppms_zone2_temp_to_label.setFont(self.font)
        self.ppms_zone2_temp_to_entry = QLineEdit()
        self.ppms_zone2_temp_to_entry.setFont(self.font)
        self.ppms_zone2_temp_range_layout.addWidget(self.ppms_zone2_temp_from_label)
        self.ppms_zone2_temp_range_layout.addWidget(self.ppms_zone2_temp_from_entry)
        self.ppms_zone2_temp_range_layout.addWidget(self.ppms_zone2_temp_to_label)
        self.ppms_zone2_temp_range_layout.addWidget(self.ppms_zone2_temp_to_entry)

        self.ppms_zone2_temp_step_layout = QHBoxLayout()
        self.ppms_zone2_temp_step_label = QLabel('Step Size 2 (K): ')
        self.ppms_zone2_temp_step_label.setFont(self.font)
        self.ppms_zone2_temp_step_entry = QLineEdit()
        self.ppms_zone2_temp_step_entry.setFont(self.font)

        # self.ppms_zone2_temp_rate_label = QLabel('Temp Rate (K/min): ')
        # self.ppms_zone2_temp_rate_label.setFont(self.font)
        # self.ppms_zone2_temp_rate_entry = QLineEdit()
        # self.ppms_zone2_temp_rate_entry.setFont(self.font)
        # self.ppms_zone2_temp_rate_entry.setText('50')

        self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_step_label)
        self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_step_entry)
        # self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_rate_label)
        # self.ppms_zone2_temp_step_layout.addWidget(self.ppms_zone2_temp_rate_entry)

        self.ppms_zone2_temp_layout.addLayout(self.ppms_zone2_temp_range_layout)
        self.ppms_zone2_temp_layout.addLayout(self.ppms_zone2_temp_step_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone2_temp_layout)

    def temp_three_zone(self):
        self.temp_two_zone()
        self.ppms_zone3_temp_layout = QVBoxLayout()
        self.ppms_zone3_temp_range_layout = QHBoxLayout()
        self.ppms_zone3_temp_from_label = QLabel('Range 3 (K): From')
        self.ppms_zone3_temp_from_label.setFont(self.font)
        self.ppms_zone3_temp_from_entry = QLineEdit()
        self.ppms_zone3_temp_from_entry.setFont(self.font)
        self.ppms_zone3_temp_to_label = QLabel(' to ')
        self.ppms_zone3_temp_to_label.setFont(self.font)
        self.ppms_zone3_temp_to_entry = QLineEdit()
        self.ppms_zone3_temp_to_entry.setFont(self.font)
        self.ppms_zone3_temp_range_layout.addWidget(self.ppms_zone3_temp_from_label)
        self.ppms_zone3_temp_range_layout.addWidget(self.ppms_zone3_temp_from_entry)
        self.ppms_zone3_temp_range_layout.addWidget(self.ppms_zone3_temp_to_label)
        self.ppms_zone3_temp_range_layout.addWidget(self.ppms_zone3_temp_to_entry)

        self.ppms_zone3_temp_step_layout = QHBoxLayout()
        self.ppms_zone3_temp_step_label = QLabel('Step Size 3 (K): ')
        self.ppms_zone3_temp_step_label.setFont(self.font)
        self.ppms_zone3_temp_step_entry = QLineEdit()
        self.ppms_zone3_temp_step_entry.setFont(self.font)

        # self.ppms_zone3_temp_rate_label = QLabel('Temp Rate (K/min): ')
        # self.ppms_zone3_temp_rate_label.setFont(self.font)
        # self.ppms_zone3_temp_rate_entry = QLineEdit()
        # self.ppms_zone3_temp_rate_entry.setFont(self.font)
        # self.ppms_zone3_temp_rate_entry.setText('50')

        self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_step_label)
        self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_step_entry)
        # self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_rate_label)
        # self.ppms_zone3_temp_step_layout.addWidget(self.ppms_zone3_temp_rate_entry)

        self.ppms_zone3_temp_layout.addLayout(self.ppms_zone3_temp_range_layout)
        self.ppms_zone3_temp_layout.addLayout(self.ppms_zone3_temp_step_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone3_temp_layout)

    def temp_customize_zone(self):
        self.ppms_zone_cus_temp_layout = QVBoxLayout()
        self.ppms_zone_cus_temp_list_layout = QHBoxLayout()
        self.ppms_zone_cus_temp_list_from_label = QLabel('Temperature List (K): [')
        self.ppms_zone_cus_temp_list_from_label.setFont(self.font)
        self.ppms_zone_cus_temp_list_entry = QLineEdit()
        self.ppms_zone_cus_temp_list_entry.setFont(self.font)
        self.ppms_zone_cus_temp_end_label = QLabel(']')
        self.ppms_zone_cus_temp_end_label.setFont(self.font)
        self.ppms_zone_cus_temp_list_layout.addWidget(self.ppms_zone_cus_temp_list_from_label)
        self.ppms_zone_cus_temp_list_layout.addWidget(self.ppms_zone_cus_temp_list_entry)
        self.ppms_zone_cus_temp_list_layout.addWidget(self.ppms_zone_cus_temp_end_label)

        self.ppms_zone_cus_temp_rate_layout = QHBoxLayout()
        self.ppms_zone_cus_temp_rate_label = QLabel('Rate (K/min): ')
        self.ppms_zone_cus_temp_rate_label.setFont(self.font)
        self.ppms_zone_cus_temp_rate_entry = QLineEdit()
        self.ppms_zone_cus_temp_rate_entry.setFont(self.font)
        self.ppms_zone_cus_temp_rate_entry.setText('5')

        self.ppms_zone_cus_temp_rate_layout.addWidget(self.ppms_zone_cus_temp_rate_label)
        self.ppms_zone_cus_temp_rate_layout.addWidget(self.ppms_zone_cus_temp_rate_entry)

        self.ppms_zone_cus_temp_layout.addLayout(self.ppms_zone_cus_temp_list_layout)
        self.ppms_zone_cus_temp_layout.addLayout(self.ppms_zone_cus_temp_rate_layout)
        self.clear_layout(self.ppms_zone_temp_layout)
        self.ppms_zone_temp_layout.addLayout(self.ppms_zone_cus_temp_layout)

    def get_ppms_field_settings(self):
        """
        Get all PPMS field settings and return them as a dictionary.
        Field values are returned as lists in Oersteds (Oe).

        Returns:
            Dictionary with field zone configuration
        """
        settings = {}

        try:
            # Determine which field zone is selected
            if hasattr(self, 'Field_setup_Zone_1') and self.Field_setup_Zone_1:
                settings['field_zone_count'] = 1
                zone_1 = self._get_field_zone_one()
                settings['field_zones'] = {
                    'zone_1': zone_1
                }
                # Create full sweep: from → to → from
                settings['full_sweep_unidirectional'], settings['full_sweep_bidirectional'] = self._create_bidirectional_sweep_no_duplicates([zone_1])

            elif hasattr(self, 'Field_setup_Zone_2') and self.Field_setup_Zone_2:
                settings['field_zone_count'] = 2
                zone_1 = self._get_field_zone_one()
                zone_2 = self._get_field_zone_two()
                settings['field_zones'] = {
                    'zone_1': zone_1,
                    'zone_2': zone_2
                }
                # Create full sweep: zone1(from→to) → zone2(from→to) → zone2(to→from) → zone1(to→from)
                settings['full_sweep_unidirectional'], settings['full_sweep_bidirectional'] = self._create_bidirectional_sweep_no_duplicates([zone_1, zone_2])

            elif hasattr(self, 'Field_setup_Zone_3') and self.Field_setup_Zone_3:
                settings['field_zone_count'] = 3
                zone_1 = self._get_field_zone_one()
                zone_2 = self._get_field_zone_two()
                zone_3 = self._get_field_zone_three()
                settings['field_zones'] = {
                    'zone_1': zone_1,
                    'zone_2': zone_2,
                    'zone_3': zone_3
                }
                # Create full sweep: z1 → z2 → z3 → z3(reverse) → z2(reverse) → z1(reverse)
                settings['full_sweep_unidirectional'], settings['full_sweep_bidirectional'] = self._create_bidirectional_sweep_no_duplicates([zone_1, zone_2, zone_3])

            # Get field mode (continuous or stepped)
            if hasattr(self, 'ppms_field_cointinous_mode_radio_button'):
                settings[
                    'field_mode'] = 'continuous' if self.ppms_field_cointinous_mode_radio_button.isChecked() else 'stepped'

            return settings

        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            print(f"Error getting PPMS field settings: {tb_str} {str(e)}")
            return {}

    def _create_bidirectional_sweep_no_duplicates(self, zones):
        """
        Create bidirectional sweep with no duplicate points at zone boundaries,
        but keeps the turning point (maximum field) duplicated.

        Example:
            Zone 1: [0, 100, 200]
            Zone 2: [200, 300, 400]
            Forward: [0, 100, 200, 300, 400]  (200 only once at boundary)
            Add duplicate at turning point: [0, 100, 200, 300, 400, 400]
            Reverse: [300, 200, 100, 0]
            Full: [0, 100, 200, 300, 400, 400, 300, 200, 100, 0]
        """
        try:
            # Build forward sweep, removing duplicates at boundaries
            forward_sweep = []
            for i, zone in enumerate(zones):
                if 'field_list' in zone and zone['field_list']:
                    if i == 0:
                        # First zone: add all points
                        forward_sweep.extend(zone['field_list'])
                    else:
                        # Subsequent zones: skip first point if it matches last point
                        if forward_sweep and zone['field_list'][0] == forward_sweep[-1]:
                            forward_sweep.extend(zone['field_list'][1:])
                        else:
                            forward_sweep.extend(zone['field_list'])

            if not forward_sweep:
                return []

            # Build reverse sweep (excluding the last point to avoid it being there 3 times)
            reverse_sweep = forward_sweep[:-1][::-1]

            # Combine: forward + duplicate turning point + reverse
            # This creates: [0, 100, 200, 300, 400] + [400] + [300, 200, 100, 0]
            # full_sweep_unidirectional = forward_sweep + [forward_sweep[-1]] + reverse_sweep
            full_sweep_unidirectional = forward_sweep
            bidirectional_forward_sweep_negative = [x * -1 for x in forward_sweep[:-1][::-1]]
            bidirectional_forward_sweep = forward_sweep + bidirectional_forward_sweep_negative
            bidirectional_reverse_sweep = bidirectional_forward_sweep[:-1][::-1]
            full_sweep_bidirectional = bidirectional_forward_sweep + [bidirectional_forward_sweep[-1]] + bidirectional_reverse_sweep

            return full_sweep_unidirectional,full_sweep_bidirectional

        except Exception as e:
            print(f"Error creating bidirectional sweep: {str(e)}")
            return []

    def _get_field_zone_one(self):
        """Get field zone 1 settings and return as dictionary with field list"""
        try:
            zone_data = {
                'from': float(self.ppms_zone1_from_entry.text()),
                'to': float(self.ppms_zone1_to_entry.text()),
                'step': float(self.ppms_zone1_field_step_entry.text()),
                'unit': 'Oe'  # Assuming Oersteds
            }

            # Generate field list
            zone_data['field_list'] = self._generate_field_list(
                zone_data['from'],
                zone_data['to'],
                zone_data['step']
            )

            return zone_data

        except Exception as e:
            print(f"Error getting field zone 1: {str(e)}")
            return {}

    def _get_field_zone_two(self):
        """Get field zone 2 settings and return as dictionary with field list"""
        try:
            zone_data = {
                'from': float(self.ppms_zone2_from_entry.text()),
                'to': float(self.ppms_zone2_to_entry.text()),
                'step': float(self.ppms_zone2_field_step_entry.text()),
                'unit': 'Oe'
            }

            zone_data['field_list'] = self._generate_field_list(
                zone_data['from'],
                zone_data['to'],
                zone_data['step']
            )

            return zone_data

        except Exception as e:
            print(f"Error getting field zone 2: {str(e)}")
            return {}

    def _get_field_zone_three(self):
        """Get field zone 3 settings and return as dictionary with field list"""
        try:
            zone_data = {
                'from': float(self.ppms_zone3_from_entry.text()),
                'to': float(self.ppms_zone3_to_entry.text()),
                'step': float(self.ppms_zone3_field_step_entry.text()),
                'unit': 'Oe'
            }

            zone_data['field_list'] = self._generate_field_list(
                zone_data['from'],
                zone_data['to'],
                zone_data['step']
            )

            return zone_data

        except Exception as e:
            print(f"Error getting field zone 3: {str(e)}")
            return {}

    def _generate_field_list(self, from_val, to_val, step_val):
        """
        Generate a list of field values from start to end with given step.
        Handles both positive and negative sweeps.

        Args:
            from_val: Starting field value
            to_val: Ending field value
            step_val: Step size (always positive)

        Returns:
            List of field values
        """
        try:
            import numpy as np

            # Ensure step is positive
            step = abs(step_val)

            # Determine direction
            if from_val <= to_val:
                # Positive sweep
                # Add small epsilon to include endpoint
                field_list = np.arange(from_val, to_val + step / 2, step).tolist()
            else:
                # Negative sweep
                field_list = np.arange(from_val, to_val - step / 2, -step).tolist()

            return field_list

        except Exception as e:
            print(f"Error generating field list: {str(e)}")
            return []

    def get_ppms_temperature_settings(self):
        """
        Get all PPMS temperature settings and return them as a dictionary.
        Temperature values are returned as lists in Kelvin (K).

        Returns:
            Dictionary with temperature zone configuration
        """
        settings = {}

        try:
            # Determine which temperature zone is selected
            if hasattr(self, 'Temp_setup_Zone_1') and self.Temp_setup_Zone_1:
                settings['temp_zone_count'] = 1
                settings['temp_zones'] = {'zone_1': self._get_temp_zone_one()}

            elif hasattr(self, 'Temp_setup_Zone_2') and self.Temp_setup_Zone_2:
                settings['temp_zone_count'] = 2
                settings['temp_zones'] = {
                    'zone_1': self._get_temp_zone_one(),
                    'zone_2': self._get_temp_zone_two()
                }

            elif hasattr(self, 'Temp_setup_Zone_3') and self.Temp_setup_Zone_3:
                settings['temp_zone_count'] = 3
                settings['temp_zones'] = {
                    'zone_1': self._get_temp_zone_one(),
                    'zone_2': self._get_temp_zone_two(),
                    'zone_3': self._get_temp_zone_three()
                }

            elif hasattr(self, 'Temp_setup_Zone_Cus') and self.Temp_setup_Zone_Cus:
                settings['temp_zone_count'] = 'customized'
                settings['temp_zones'] = {
                    'customized': self._get_temp_zone_customized()
                }

            return settings

        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            print(f"Error getting PPMS temperature settings: {tb_str} {str(e)}")
            return {}

    def _get_temp_zone_one(self):
        """Get temperature zone 1 settings and return as list"""
        zone_data = {
            'from': self.ppms_zone1_temp_from_entry.text() if hasattr(self, 'ppms_zone1_temp_from_entry') else '',
            'to': self.ppms_zone1_temp_to_entry.text() if hasattr(self, 'ppms_zone1_temp_to_entry') else '',
            'step': self.ppms_zone1_temp_step_entry.text() if hasattr(self, 'ppms_zone1_temp_step_entry') else '',
            'rate': self.ppms_zone1_temp_rate_entry.text() if hasattr(self, 'ppms_zone1_temp_rate_entry') else '5',
            'unit': 'K'
        }

        # Generate temperature list
        zone_data['temp_list'] = self._generate_temp_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step']
        )

        return zone_data

    def _get_temp_zone_two(self):
        """Get temperature zone 2 settings and return as list"""
        zone_data = {
            'from': self.ppms_zone2_temp_from_entry.text() if hasattr(self, 'ppms_zone2_temp_from_entry') else '',
            'to': self.ppms_zone2_temp_to_entry.text() if hasattr(self, 'ppms_zone2_temp_to_entry') else '',
            'step': self.ppms_zone2_temp_step_entry.text() if hasattr(self, 'ppms_zone2_temp_step_entry') else '',
            'unit': 'K'
        }

        # Generate temperature list
        zone_data['temp_list'] = self._generate_temp_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step']
        )

        return zone_data

    def _get_temp_zone_three(self):
        """Get temperature zone 3 settings and return as list"""
        zone_data = {
            'from': self.ppms_zone3_temp_from_entry.text() if hasattr(self, 'ppms_zone3_temp_from_entry') else '',
            'to': self.ppms_zone3_temp_to_entry.text() if hasattr(self, 'ppms_zone3_temp_to_entry') else '',
            'step': self.ppms_zone3_temp_step_entry.text() if hasattr(self, 'ppms_zone3_temp_step_entry') else '',
            'unit': 'K'
        }

        # Generate temperature list
        zone_data['temp_list'] = self._generate_temp_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step']
        )

        return zone_data

    def _get_temp_zone_customized(self):
        """Get customized temperature zone settings"""
        zone_data = {
            'raw_input': self.ppms_zone_cus_temp_list_entry.text() if hasattr(self,
                                                                              'ppms_zone_cus_temp_list_entry') else '',
            'rate': self.ppms_zone_cus_temp_rate_entry.text() if hasattr(self,
                                                                         'ppms_zone_cus_temp_rate_entry') else '5',
            'unit': 'K'
        }

        # Parse the temperature list from the entry
        temp_str = zone_data['raw_input']
        zone_data['temp_list'] = self._parse_custom_list(temp_str)

        return zone_data

    def _generate_temp_list(self, from_val, to_val, step_val):
        """
        Generate a list of temperature values from start to end with given step.
        Returns list in Kelvin (K).

        Args:
            from_val: Starting temperature (string)
            to_val: Ending temperature (string)
            step_val: Step size (string)

        Returns:
            List of temperature values in K
        """
        try:
            start = float(from_val) if from_val else 0
            end = float(to_val) if to_val else 0
            step = float(step_val) if step_val else 0

            if step == 0:
                return []

            # Generate list
            temp_list = []
            current = start

            # Determine direction
            if start < end:
                # Going up
                while current <= end:
                    temp_list.append(current)
                    current += step
            else:
                # Going down
                while current >= end:
                    temp_list.append(current)
                    current -= step

            return temp_list

        except (ValueError, TypeError):
            return []

    def get_combined_field_temp_lists(self):
        """
        Get combined field and temperature lists for experiment iteration.

        Returns:
            Dictionary with combined field and temperature configurations
        """
        combined = {
            'field_settings': self.get_ppms_field_settings(),
            'temp_settings': self.get_ppms_temperature_settings()
        }

        # Generate complete field list (all zones combined)
        all_fields = []
        field_settings = combined['field_settings']
        if 'field_zones' in field_settings:
            for zone_name in sorted(field_settings['field_zones'].keys()):
                zone = field_settings['field_zones'][zone_name]
                field_list = zone.get('field_list', [])
                all_fields.extend(field_list)

        combined['all_fields'] = all_fields

        # Generate complete temperature list (all zones combined)
        all_temps = []
        temp_settings = combined['temp_settings']
        if 'temp_zones' in temp_settings:
            for zone_name in sorted(temp_settings['temp_zones'].keys()):
                zone = temp_settings['temp_zones'][zone_name]
                temp_list = zone.get('temp_list', [])
                all_temps.extend(temp_list)

        combined['all_temps'] = all_temps

        # Calculate total measurement points
        # combined['total_field_points'] = len(all_fields)
        # combined['total_temp_points'] = len(all_temps)
        # combined['total_measurements'] = len(all_fields) * len(all_temps) if all_temps else len(all_fields)

        return combined

    # ---------------------------------------------------------------------------------
    #  MISC
    # ---------------------------------------------------------------------------------
    def _parse_custom_list(self, list_string):
        """
        Parse a comma-separated string of values into a list of floats.
        Example: "1.0, 2.5, 3.7, 5.0" -> [1.0, 2.5, 3.7, 5.0]
        """
        try:
            # Remove brackets if present
            list_string = list_string.strip('[]')

            # Split by comma and convert to float
            values = [float(x.strip()) for x in list_string.split(',') if x.strip()]

            return values

        except (ValueError, TypeError, AttributeError):
            return []

    def rst(self):
        try:
            self.worker = None
        except Exception:
            pass
        self.timer = QTimer()
        self.timer.stop()
        self.canvas.axes.cla()
        self.canvas.axes_2.cla()
        self.canvas.draw()
        self.ppms_field_One_zone_radio_enabled = False
        self.ppms_field_Two_zone_radio_enabled = False
        self.ppms_field_Three_zone_radio_enabled = False
        self.nv_channel_1_enabled = None
        self.nv_channel_2_enabled = None
        try:
            self.keithley_6221.write(":OUTP OFF")
            self.keithley_6221.write("SOUR:WAVE:ABOR \n")
            # self.keithley_2182nv.write("*RST")
            self.keithley_2182nv.write("*CLS")
            self.update_keithley_6221_update_label('N/A', 'OFF')

            # self.keithley_6221.close()
            # self.keithley_2182nv.close()
            # self.DSP7265.close()
        except Exception:
            pass

    def clear_layout(self, layout):
        """Clear layout properly"""
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.setParent(None)
                widget.deleteLater()
            else:
                child_layout = item.layout()
                if child_layout:
                    self.clear_layout(child_layout)

        # QApplication.processEvents()

    def safe_clear_layout(self, layout_attr_name):
        """Safely clear a layout if it exists"""
        if hasattr(self, layout_attr_name):
            layout = getattr(self, layout_attr_name)
            if layout is not None:
                try:
                    self.clear_layout(layout)
                    # QApplication.processEvents()
                    return True
                except Exception as e:
                    print(f"Error clearing {layout_attr_name}: {e}")
        return False

    def stop_measurement(self):
        try:
            if hasattr(self, 'keithley_6221'):
                self.keithley_6221.write(":OUTP OFF")
                self.keithley_6221.write("SOUR:WAVE:ABOR \n")
                self.update_keithley_6221_update_label('N/A', 'OFF')
            if hasattr(self, 'keithley_2182nv'):
                self.keithley_2182nv.write("*CLS")
        except Exception:
            pass

        self.running = False
        self.measurement_active = False
        self.set_all_inputs_enabled(True)

        # Update buttons
        if hasattr(self, 'start_measurement_btn'):
            self.start_measurement_btn.setEnabled(True)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(False)

        self.ppms_field_One_zone_radio_enabled = False
        self.ppms_field_Two_zone_radio_enabled = False
        self.ppms_field_Three_zone_radio_enabled = False
        self.nv_channel_1_enabled = None
        self.nv_channel_2_enabled = None

        if hasattr(self, 'canvas'):
            self.canvas.figure.savefig(
                self.folder_path + "{}_{}_run{}.png".format(self.sample_id, self.measurement, self.run))
            time.sleep(5)
            image_path = r"{}{}_{}_run{}.png".format(self.folder_path, self.sample_id, self.measurement, self.run)
            if not os.path.exists(image_path):
                print("No Such File.")
            caption = f"Data preview"
            NotificationManager().send_message_with_image(message=f"Data Saved - {caption}", image_path=image_path)
        try:
            if self.worker is not None:
                self.worker.stop()
                self.worker = None
                NotificationManager().send_message("Experiment Stop!", 'critical')
        except Exception:
            QMessageBox.warning(self, 'Fail', "Fail to stop the experiment")
        # try:
        #     self.canvas.axes.cla()
        #     self.canvas.axes_2.cla()
        #     self.canvas.draw()
        # except Exception:
        #     pass

    def set_all_inputs_enabled(self, enabled):
        """
        Master method: Automatically enable/disable ALL input widgets

        Args:
            enabled (bool): True to enable, False to disable
        """
        # Get the central widget (contains all UI elements)
        central_widget = self.centralWidget()

        if central_widget is None:
            print("Warning: No central widget found")
            return

        # Build list of widgets that should never be disabled
        self._build_always_enabled_list()

        # Recursively process all widgets
        self._recursive_set_enabled(central_widget, enabled)

    def _build_always_enabled_list(self):
        """
        Build list of widgets that should NEVER be disabled
        These are typically: Start, Stop, Reset buttons and status displays
        """
        self.always_enabled_widgets = []

        # Add control buttons (always keep enabled)
        widgets_to_keep = [
            'start_measurement_btn',
            'stop_btn',
            'rst_btn',
            # Add other buttons that should stay enabled
        ]

        for widget_name in widgets_to_keep:
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                if widget is not None:
                    self.always_enabled_widgets.append(widget)

    def _recursive_set_enabled(self, parent_widget, enabled):
        """
        Recursively find and enable/disable all input widgets

        Args:
            parent_widget (QWidget): Parent widget to search
            enabled (bool): True to enable, False to disable
        """
        # Define which widget types are "input widgets"
        input_widget_types = (
            QLineEdit,  # Text input boxes
            QComboBox,  # Dropdown menus
            # QSpinBox,  # Integer spinners
            # QDoubleSpinBox,  # Float spinners
            QRadioButton,  # Radio buttons
            QCheckBox,  # Checkboxes
            QPushButton,  # Buttons (except control buttons)
        )

        # Find all child widgets of input types
        for child in parent_widget.findChildren(QWidget):
            # Check if it's an input widget type
            if isinstance(child, input_widget_types):
                # Check if it should be excluded
                if child not in self.always_enabled_widgets:
                    # Set enabled state
                    child.setEnabled(enabled)

    def _should_widget_be_disabled(self, widget):
        """
        Optional: Add custom logic to determine if a widget should be disabled

        Args:
            widget (QWidget): Widget to check

        Returns:
            bool: True if widget should be disabled, False to skip
        """
        # Don't disable if in always-enabled list
        if widget in self.always_enabled_widgets:
            return False

        # Don't disable if widget is hidden
        if not widget.isVisible():
            return False

        # Don't disable buttons with specific text
        if isinstance(widget, QPushButton):
            button_text = widget.text().lower()
            if button_text in ['start', 'stop', 'reset', 'cancel']:
                return False

        # Custom rule: Don't disable widgets with specific object names
        if widget.objectName() in ['status_display', 'log_viewer']:
            return False

        # Default: widget should be disabled
        return True

    def disable_specific_section(self, section_name, enabled=False):
        """
        Optional: Disable only a specific section of the UI

        Args:
            section_name (str): Name of the container widget/layout
            enabled (bool): True to enable, False to disable
        """
        if hasattr(self, section_name):
            section_widget = getattr(self, section_name)
            if isinstance(section_widget, QWidget):
                self._recursive_set_enabled(section_widget, enabled)

    def get_all_disabled_widgets(self):
        """
        Optional: Get a list of all currently disabled widgets
        Useful for debugging

        Returns:
            list: List of disabled widgets
        """
        central = self.centralWidget()
        if not central:
            return []

        disabled_widgets = []
        for widget in central.findChildren(QWidget):
            if not widget.isEnabled():
                disabled_widgets.append(widget)

        return disabled_widgets

    def start_measurement(self):
        dialog = LogWindow()
        if dialog.exec():
            try:
                if self.worker is not None:
                    self.stop_measurement()
                try:
                    self.main_layout.removeWidget(self.log_box)
                    self.log_box.deleteLater()
                    self.main_layout.removeWidget(self.progress_bar)
                    self.progress_bar.deleteLater()
                except Exception:
                    pass

                self.set_all_inputs_enabled(False)
                self.measurement_active = True

                # Update buttons
                if hasattr(self, 'start_measurement_btn'):
                    self.start_measurement_btn.setEnabled(False)
                if hasattr(self, 'stop_btn'):
                    self.stop_btn.setEnabled(True)
                self.running = True
                self.folder_path, self.file_name, self.formatted_date, self.sample_id, self.measurement, self.run, self.comment, self.user = dialog.get_text()
                self.log_box = QTextEdit(self)
                self.log_box.setReadOnly(True)  # Make the log box read-only
                self.progress_bar = QProgressBar(self)
                self.progress_bar.setMinimum(0)
                self.progress_bar.setMaximum(100)
                self.progress_bar.setFixedWidth(1140)
                self.progress_value = 0
                self.progress_bar.setValue(self.progress_value)
                self.progress_bar.setStyleSheet("""
                            QProgressBar {
                                border: 1px solid #8f8f91;
                                border-radius: 5px;
                                background-color: #e0e0e0;
                                text-align: center;
                            }

                            QProgressBar::chunk {
                                background-color:  #3498db;
                                width: 5px;
                            }
                        """)
                self.log_box.setFixedSize(1140, 150)
                self.main_layout.addWidget(self.progress_bar)
                self.main_layout.addWidget(self.log_box, alignment=Qt.AlignmentFlag.AlignCenter)
                self.log_box.clear()

                self.folder_path = self.folder_path + f'Run_{self.run}/'
                os.makedirs(self.folder_path, exist_ok=True)
                self.random_number = random.randint(100000, 999999)

                f = open(self.folder_path + f'{self.random_number}_Experiment_Log.txt', "a")
                today = datetime.datetime.today()
                self.formatted_date_csv = today.strftime("%m-%Y-%d %H:%M:%S")
                f.write(f"User: {self.user}\n")
                f.write(f"Today's Date: {self.formatted_date_csv}\n")
                f.write(f"Sample ID: {self.sample_id}\n")
                f.write(f"Measurement Type: {self.measurement}\n")
                f.write(f"Run: {self.run}\n")
                f.write(f"Comment: {self.comment}\n")

                eto_number_of_avg = self.update_eto_average_label()
                f.write(f"Number of Average: {eto_number_of_avg}\n")

                init_temp_rate = float(self.eto_setting_init_temp_rate_line_edit.text())
                demag_field = float(self.eto_setting_demag_field_line_edit.text())
                f.write(f"Demagnetization Field: {demag_field}\n")
                # self.notification.send_notification(message="Measurement Start")
                if self.eto_setting_zero_field_record_check_box.isChecked():
                    record_zero_field = True
                    f.write(f"Record Zero Field: Yes\n")
                else:
                    record_zero_field = False
                    f.write(f"Record Zero Field: No\n")
                if self.Ketihley_6221_Connected:
                    self.append_text('Check Connection of Keithley 6221....\n', 'yellow')
                    if self.demo_mode:
                        self.append_text("Model 6221 Demo", 'green')
                    else:
                        try:
                            model_6221 = self.keithley_6221.query('*IDN?')
                            self.append_text(str(model_6221), 'green')

                        except visa.errors.VisaIOError as e:
                            QMessageBox.warning(self, 'Fail to connect Keithley 6221', str(e))
                            self.stop_measurement()
                            return
                    self.append_text('Keithley 6221 connected!\n', 'green')
                if self.Keithley_2182_Connected:
                    self.append_text('Check Connection of Keithley 2182....\n', 'yellow')
                    if self.demo_mode:
                        self.append_text("Model 2182 Demo", 'green')
                    else:
                        try:
                            model_2182 = self.keithley_2182nv.query('*IDN?')
                            self.keithley_2182nv.write(':SYST:BEEP:STAT 0')
                            self.log_box.append(str(model_2182))
                            # Initialize and configure the instrument
                            # self.keithley_2182nv.write("*RST")
                            self.keithley_2182nv.write("*CLS")
                            f.write(f"Instrument: Keithley 2182nv enabled\n")
                            self.nv_NPLC = self.NPLC_entry.text()
                            f.write(f"\tNPLC (time constant): {self.nv_NPLC} \n")
                            if self.keithley_2182_lsync_checkbox.isChecked():
                                self.keithley_2182nv.write(":SYST:LSYNC ON")
                                f.write(f"\tLine Synchronization: Enabled \n")
                            else:
                                self.keithley_2182nv.write(":SYST:LSYNC OFF")
                                f.write(f"\tLine Synchronization: Disabled \n")
                            keithley_2182_filter_index = self.keithley_2182_filter_button_group.checkedId()
                            if keithley_2182_filter_index == 0:
                                f.write(f"\tFilter: Digital Filter On \n")
                                if self.keithley_2182_channel_1_checkbox.isChecked():
                                    self.keithley_2182nv.write(":SENS:VOLT:CHAN1:DFIL:STAT ON")
                                    self.keithley_2182nv.write(":SENS:VOLT:CHAN1:LPAS:STAT OFF")
                                elif self.keithley_2182_channel_2_checkbox.isChecked():
                                    self.keithley_2182nv.write(":SENS:VOLT:CHAN2:DFIL:STAT ON")
                                    self.keithley_2182nv.write(":SENS:VOLT:CHAN2:LPAS:STAT OFF")
                            elif keithley_2182_filter_index == 1:
                                f.write(f"\tFilter: Analog Filter On \n")
                                if self.keithley_2182_channel_1_checkbox.isChecked():
                                    self.keithley_2182nv.write(":SENS:VOLT:CHAN1:DFIL:STAT OFF")
                                    self.keithley_2182nv.write(":SENS:VOLT:CHAN1:LPAS:STAT ON")
                                elif self.keithley_2182_channel_2_checkbox.isChecked():
                                    self.keithley_2182nv.write(":SENS:VOLT:CHAN2:DFIL:STAT OFF")
                                    self.keithley_2182nv.write(":SENS:VOLT:CHAN2:LPAS:STAT ON")
                            elif keithley_2182_filter_index == 2:
                                f.write(f"\tFilter: All Filters Off \n")
                                self.keithley_2182nv.write(":SENS:VOLT:CHAN1:DFIL:STAT OFF")
                                self.keithley_2182nv.write(":SENS:VOLT:CHAN2:DFIL:STAT OFF")
                                self.keithley_2182nv.write(":SENS:VOLT:CHAN1:LPAS:STAT OFF")
                                self.keithley_2182nv.write(":SENS:VOLT:CHAN2:LPAS:STAT OFF")
                            if self.keithley_2182_channel_1_checkbox.isChecked():
                                self.nv_channel_1_enabled = True
                                f.write(f"\tChannel 1: enabled \n")
                            else:
                                self.nv_channel_1_enabled = False
                                f.write(f"\tChannel 1: disabled \n")

                            if self.keithley_2182_channel_2_checkbox.isChecked():
                                self.nv_channel_2_enabled = True
                                f.write(f"\tChannel 2: enabled \n")
                            else:
                                self.nv_channel_2_enabled = False
                                f.write(f"\tChannel 2: disabled \n")
                            time.sleep(2)  # Wait for the reset to complete.
                        except visa.errors.VisaIOError as e:
                            QMessageBox.warning(self, 'Fail to connect Keithley 2182', str(e))
                            self.stop_measurement()
                            return
                    self.append_text('Keithley 2182 connected!\n', 'green')
                dsp7265_current_time_constant = None
                if self.DSP7265_Connected:
                    self.append_text('Check Connection of DSP Lock-in 7265....\n', 'yellow')
                    if self.demo_mode:
                        self.append_text("Model DSP 7265 Demo", 'green')
                    else:
                        try:
                            model_7265 = self.DSP7265.query('ID')
                            self.log_box.append(str(model_7265))
                            f.write(f"Instrument: DSP 7265 enabled\n")
                            time.sleep(2)  # Wait for the reset to complete
                            dsp7265_ref_source, dsp7265_ref_freq, dsp7265_current_time_constant, dsp7265_current_sensitvity, dsp7265_measurement_type = self.read_sr7265_settings(
                                self.DSP7265)
                            f.write(f"\tDSP 7264 reference source: {dsp7265_ref_source}\n")
                            f.write(f"\tDSP 7264 reference frequency: {dsp7265_ref_freq} Hz\n")
                            f.write(f"\tDSP 7264 time constant: {dsp7265_current_time_constant}\n")
                            f.write(f"\tDSP 7264 sensitivity: {dsp7265_current_sensitvity}\n")
                            f.write(f"\tDSP 7264 measurement type: {dsp7265_measurement_type}\n")
                        except visa.errors.VisaIOError as e:
                            QMessageBox.warning(self, 'Fail to connectDSP Lock-in 7265', str(e))
                            self.stop_measurement()
                            return
                    self.append_text('DSP Lock-in 7265 connected!\n', 'green')

                def float_range(start, stop, step):
                    current = start
                    while current < stop:
                        yield current
                        current += step
                try:
                    self.append_text('Start initializing parameters...!\n', 'orange')
                    self.append_text('Start initializing Temperatures...!\n', 'blue')
                    TempList = []
                    if self.ppms_temp_One_zone_radio.isChecked():

                        zone_1_start = float(self.ppms_zone1_temp_from_entry.text())
                        zone_1_end = float(self.ppms_zone1_temp_to_entry.text()) + float(
                            self.ppms_zone1_temp_step_entry.text())
                        zone_1_step = float(self.ppms_zone1_temp_step_entry.text())
                        TempList = [round(float(i), 2) for i in float_range(zone_1_start, zone_1_end, zone_1_step)]
                        tempRate = round(float(self.ppms_zone1_temp_rate_entry.text()), 2)
                    elif self.ppms_temp_Two_zone_radio.isChecked():
                        zone_1_start = float(self.ppms_zone1_temp_from_entry.text())
                        zone_1_end = float(self.ppms_zone1_temp_to_entry.text())
                        zone_1_step = float(self.ppms_zone1_temp_step_entry.text())
                        zone_2_start = float(self.ppms_zone2_temp_from_entry.text())
                        zone_2_end = float(self.ppms_zone2_temp_to_entry.text())
                        zone_2_step = float(self.ppms_zone2_temp_step_entry.text())
                        if zone_1_end == zone_2_start:
                            zone_1_end = zone_1_end
                        else:
                            zone_1_end = zone_1_end + zone_1_step
                        TempList = [round(float(i), 2) for i in float_range(zone_1_start, zone_1_end, zone_1_step)]
                        TempList += [round(float(i), 2) for i in
                                     float_range(zone_2_start, zone_2_end + zone_2_step, zone_2_step)]
                        tempRate = round(float(self.ppms_zone1_temp_rate_entry.text()), 2)
                    elif self.ppms_temp_Three_zone_radio.isChecked():
                        zone_1_start = float(self.ppms_zone1_temp_from_entry.text())
                        zone_1_end = float(self.ppms_zone1_temp_to_entry.text())
                        zone_1_step = float(self.ppms_zone1_temp_step_entry.text())

                        zone_2_start = float(self.ppms_zone2_temp_from_entry.text())
                        zone_2_end = float(self.ppms_zone2_temp_to_entry.text())
                        zone_2_step = float(self.ppms_zone2_temp_step_entry.text())

                        zone_3_start = float(self.ppms_zone3_temp_from_entry.text())
                        zone_3_end = float(self.ppms_zone3_temp_to_entry.text()) + float(
                            self.ppms_zone3_temp_step_entry.text())
                        zone_3_step = float(self.ppms_zone3_temp_step_entry.text())

                        if zone_1_end == zone_2_start:
                            zone_1_end = zone_1_end
                        else:
                            zone_1_end = zone_1_end + zone_1_step

                        if zone_2_end == zone_3_start:
                            zone_2_end = zone_2_end
                        else:
                            zone_2_end = zone_2_end + zone_2_step

                        TempList = [round(float(i), 2) for i in float_range(zone_1_start, zone_1_end, zone_1_step)]
                        TempList += [round(float(i), 2) for i in float_range(zone_2_start, zone_2_end, zone_2_step)]
                        TempList += [round(float(i), 2) for i in float_range(zone_3_start, zone_3_end, zone_3_step)]
                        tempRate = round(float(self.ppms_zone1_temp_rate_entry.text()), 2)
                    elif self.ppms_temp_Customize_zone_radio.isChecked():
                        templist = self.ppms_zone_cus_temp_list_entry.text()
                        templist = templist.replace(" ", "")
                        TempList = [round(float(item), 2) for item in templist.split(',')]
                        tempRate = round(float(self.ppms_zone_cus_temp_rate_entry.text()), 2)
                except Exception as e:
                    self.stop_measurement()
                    tb_str = traceback.format_exc()
                    QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

                self.append_text('Start initializing Field...!\n', 'blue')
                if self.ppms_field_One_zone_radio.isChecked():
                    self.zone1_top_field = float(self.ppms_zone1_from_entry.text())
                    self.zone1_bot_field = float(self.ppms_zone1_to_entry.text())
                    self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
                    if self.ppms_field_fixed_mode_radio_button.isChecked():
                        self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
                    else:
                        self.zone1_step_field = 1.0
                    number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
                    number_of_field = np.abs(number_of_field_zone1)
                elif self.ppms_field_Two_zone_radio.isChecked():
                    self.zone1_top_field = float(self.ppms_zone1_from_entry.text())
                    self.zone1_bot_field = float(self.ppms_zone1_to_entry.text())
                    if self.ppms_field_fixed_mode_radio_button.isChecked():
                        self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
                    else:
                        self.zone1_step_field = 1.0
                    self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
                    self.zone2_top_field = float(self.ppms_zone2_from_entry.text())
                    self.zone2_bot_field = float(self.ppms_zone2_to_entry.text())
                    if self.ppms_field_fixed_mode_radio_button.isChecked():
                        self.zone2_step_field = float(self.ppms_zone2_field_step_entry.text())
                    else:
                        self.zone2_step_field = 1.0
                    self.zone2_field_rate = float(self.ppms_zone2_field_rate_entry.text())
                    # Need to think about it
                    number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
                    number_of_field_zone2 = 2 * (self.zone2_top_field - self.zone2_bot_field) / self.zone2_step_field
                    number_of_field = np.abs(number_of_field_zone1) + np.abs(number_of_field_zone2)
                elif self.ppms_field_Three_zone_radio.isChecked():
                    self.zone1_top_field = float(self.ppms_zone1_from_entry.text())
                    self.zone1_bot_field = float(self.ppms_zone1_to_entry.text())
                    if self.ppms_field_fixed_mode_radio_button.isChecked():
                        self.zone1_step_field = float(self.ppms_zone1_field_step_entry.text())
                    else:
                        self.zone1_step_field = 1.0
                    self.zone1_field_rate = float(self.ppms_zone1_field_rate_entry.text())
                    self.zone2_top_field = float(self.ppms_zone2_from_entry.text())
                    self.zone2_bot_field = float(self.ppms_zone2_to_entry.text())
                    if self.ppms_field_fixed_mode_radio_button.isChecked():
                        self.zone2_step_field = float(self.ppms_zone2_field_step_entry.text())
                    else:
                        self.zone2_step_field = 1.0
                    self.zone2_field_rate = float(self.ppms_zone2_field_rate_entry.text())
                    self.zone2_field_rate = float(self.ppms_zone1_field_rate_entry.text())
                    self.zone3_top_field = float(self.ppms_zone3_from_entry.text())
                    self.zone3_bot_field = float(self.ppms_zone3_to_entry.text())
                    if self.ppms_field_fixed_mode_radio_button.isChecked():
                        self.zone3_step_field = float(self.ppms_zone3_field_step_entry.text())
                    else:
                        self.zone3_step_field = 1.0
                    self.zone2_field_rate = float(self.ppms_zone2_field_rate_entry.text())
                    self.zone3_field_rate = float(self.ppms_zone3_field_rate_entry.text())
                    # Need to think about it
                    number_of_field_zone1 = 2 * (self.zone1_top_field - self.zone1_bot_field) / self.zone1_step_field
                    number_of_field_zone2 = 2 * (self.zone2_top_field - self.zone2_bot_field) / self.zone2_step_field
                    number_of_field_zone3 = 2 * (self.zone3_top_field - self.zone3_bot_field) / self.zone3_step_field
                    number_of_field = np.abs(number_of_field_zone1) + np.abs(number_of_field_zone2) + np.abs(
                        number_of_field_zone3)

                topField = self.zone1_top_field
                if self.ppms_field_One_zone_radio.isChecked():
                    botField = self.zone1_bot_field
                else:
                    botField = -1 * self.zone1_top_field

                self.append_text('Start initializing Current...!\n', 'blue')
                # =============================== Set the current ==================================== #
                f.write(f"Instrument: Keithley 6221 enabled\n")
                if self.keithley_6221_DC_radio.isChecked():
                    f.write(f"\tKeithley 6221 DC current: enabled\n")
                    self.keithley_6221_dc_config = True
                    if self.keithley_6221_DC_range_checkbox.isChecked():
                        init_current = float(self.keithley_6221_DC_range_init_entry.text())
                        final_current = float(self.keithley_6221_DC_range_final_entry.text())
                        step_current = float(self.keithley_6221_DC_range_step_entry.text())
                        self.DC_Range_unit = self.keithley_6221_DC_range_combobox.currentIndex()
                        if self.DC_Range_unit != 0:
                            if self.DC_Range_unit == 1:  # mA
                                DC_range_selected_unit = 'e-3'
                                self.current_unit = 'mA'
                            elif self.DC_Range_unit == 2:  # uA
                                DC_range_selected_unit = 'e-6'
                                self.current_unit = 'uA'
                            elif self.DC_Range_unit == 3:  # nA
                                DC_range_selected_unit = 'e-9'
                                self.current_unit = 'nA'
                            elif self.DC_Range_unit == 4:  # pA
                                DC_range_selected_unit = 'e-12'
                                self.current_unit = 'pA'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.stop_measurement()
                            return
                        current = [f"{i}{DC_range_selected_unit}" for i in
                                   float_range(init_current, final_current + step_current, step_current)]
                        current_mag = [f"{i}" for i in
                                       float_range(init_current, final_current + step_current, step_current)]
                    elif self.keithley_6221_DC_single_checkbox.isChecked():

                        self.single_DC_current = self.keithley_6221_DC_single_entry.text()
                        self.single_DC_current = self.single_DC_current.replace(" ", "")
                        self.single_DC_current = [float(item) for item in self.single_DC_current.split(',')]
                        self.DC_Single_unit = self.keithley_6221_DC_single_combobox.currentIndex()
                        if self.DC_Single_unit != 0:
                            if self.DC_Single_unit == 1:  # mA
                                DC_single_selected_unit = 'e-3'
                                self.current_unit = 'mA'
                            elif self.DC_Single_unit == 2:  # uA
                                DC_single_selected_unit = 'e-6'
                                self.current_unit = 'uA'
                            elif self.DC_Single_unit == 3:  # nA
                                DC_single_selected_unit = 'e-9'
                                self.current_unit = 'nA'
                            elif self.DC_Single_unit == 4:  # pA
                                DC_single_selected_unit = 'e-12'
                                self.current_unit = 'pA'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.stop_measurement()
                            return
                        current = [f"{self.single_DC_current[i]}{DC_single_selected_unit}" for i in
                                   range(len(self.single_DC_current))]
                        current_mag = [f"{self.single_DC_current[i]}" for i in range(len(self.single_DC_current))]
                    else:
                        QMessageBox.warning(self, 'Warning', 'Please choose one of the options')
                        self.stop_measurement()
                        return
                elif self.keithley_6221_ac_radio.isChecked():
                    self.select_keithley6221_phase_maker()
                    f.write(f"\tKeithley 6221 AC current: enabled\n")
                    self.keithley_6221_ac_config = True
                    if self.keithley_6221_ac_range_checkbox.isChecked():
                        init_current = float(self.keithley_6221_ac_range_init_entry.text())
                        final_current = float(self.keithley_6221_ac_range_final_entry.text())
                        step_current = float(self.keithley_6221_ac_range_step_entry.text())
                        self.ac_range_unit = self.keithley_6221_ac_range_combobox.currentIndex()
                        if self.ac_range_unit != 0:
                            if self.ac_range_unit == 1:  # mA
                                ac_range_selected_unit = 'e-3'
                                self.current_unit = 'mA'
                            elif self.ac_range_unit == 2:  # uA
                                ac_range_selected_unit = 'e-6'
                                self.current_unit = 'uA'
                            elif self.ac_range_unit == 3:  # nA
                                ac_range_selected_unit = 'e-9'
                                self.current_unit = 'nA'
                            elif self.ac_range_unit == 4:  # pA
                                ac_range_selected_unit = 'e-12'
                                self.current_unit = 'pA'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.stop_measurement()
                            return
                        current = [f"{i}{ac_range_selected_unit}" for i in
                                   float_range(init_current, final_current + step_current, step_current)]
                        current_mag = [f"{i}" for i in
                                       float_range(init_current, final_current + step_current, step_current)]
                    elif self.keithley_6221_ac_single_checkbox.isChecked():
                        self.single_ac_current = self.keithley_6221_ac_single_entry.text()
                        self.single_ac_current = self.single_ac_current.replace(" ", "")
                        self.single_ac_current = [float(item) for item in self.single_ac_current.split(',')]
                        self.ac_single_unit = self.keithley_6221_ac_single_combobox.currentIndex()
                        if self.ac_single_unit != 0:
                            if self.ac_single_unit == 1:  # mA
                                ac_range_selected_unit = 'e-3'
                                self.current_unit = 'mA'
                            elif self.ac_single_unit == 2:  # uA
                                ac_range_selected_unit = 'e-6'
                                self.current_unit = 'uA'
                            elif self.ac_single_unit == 3:  # nA
                                ac_range_selected_unit = 'e-9'
                                self.current_unit = 'nA'
                            elif self.ac_single_unit == 4:  # pA
                                ac_range_selected_unit = 'e-12'
                                self.current_unit = 'pA'
                        else:
                            QMessageBox.warning(self, "Missing Items",
                                                "Please select all the required parameter - missing current unit")
                            self.stop_measurement()
                            return
                        current = [f"{self.single_ac_current[i]}{ac_range_selected_unit}" for i in
                                   range(len(self.single_ac_current))]
                        current_mag = [f"{self.single_ac_current[i]}" for i in range(len(self.single_ac_current))]

                    else:
                        QMessageBox.warning(self, 'Warning', 'Please choose one of the options')
                        self.stop_measurement()
                        return

                    ac_current_waveform_index = self.keithley_6221_ac_waveform_combo_box.currentIndex()
                    if ac_current_waveform_index !=0:
                        if ac_current_waveform_index == 1:  # sine
                            self.ac_current_waveform = "SIN"
                            f.write("\tKeithley 6221 AC waveform: SIN\n")
                        elif ac_current_waveform_index == 2:  # square
                            self.ac_current_waveform = "SQU"
                            f.write("\tKeithley 6221 AC waveform: SQU\n")
                        elif ac_current_waveform_index == 3:  # ramp
                            self.ac_current_waveform = "RAMP"
                            f.write("\tKeithley 6221 AC waveform: RAMP\n")
                        elif ac_current_waveform_index == 4:  # arbx
                            self.ac_current_waveform = "ARB0"
                            f.write("\tKeithley 6221 AC waveform: ARB0\n")

                    self.ac_current_freq = self.keithley_6221_ac_freq_entry_box.text()
                    f.write(f"\tKeithley 6221 AC frequency: {self.ac_current_freq}\n")
                    self.ac_current_offset = self.keithley_6221_ac_offset_entry_box.text()
                    self.ac_offset_unit = self.keithley_6221_ac_offset_units_combo.currentIndex()
                    if self.ac_offset_unit == 0:
                        ac_offset_unit = ''
                    elif self.ac_offset_unit == 1:  # mA
                        ac_offset_unit = 'e-3'
                    elif self.ac_offset_unit == 2:  # uA
                        ac_offset_unit = 'e-6'
                    elif self.ac_offset_unit == 3:  # nA
                        ac_offset_unit = 'e-9'
                    elif self.ac_offset_unit == 4:  # pA
                        ac_offset_unit = 'e-12'
                    self.ac_current_offset = self.ac_current_offset + ac_offset_unit
                    f.write(f"\tKeithley 6221 AC offset: {self.ac_current_offset}\n")

                if self.ppms_field_One_zone_radio.isChecked():
                    self.ppms_field_One_zone_radio_enabled = True
                    self.ppms_field_Two_zone_radio_enabled = False
                    self.ppms_field_Three_zone_radio_enabled = False
                    self.zone2_step_field = self.zone1_step_field
                    self.zone3_step_field = self.zone1_step_field
                    self.zone2_field_rate = self.zone1_field_rate
                    self.zone3_field_rate = self.zone1_field_rate
                    self.zone2_top_field = self.zone1_top_field
                    self.zone3_top_field = self.zone1_top_field
                elif self.ppms_field_Two_zone_radio.isChecked():
                    self.ppms_field_Two_zone_radio_enabled = True
                    self.ppms_field_One_zone_radio_enabled = False
                    self.ppms_field_Three_zone_radio_enabled = False
                    self.zone3_step_field = self.zone2_step_field
                    self.zone3_field_rate = self.zone2_field_rate
                    self.zone3_top_field = self.zone2_top_field
                elif self.ppms_field_Three_zone_radio.isChecked():
                    self.ppms_field_Three_zone_radio_enabled = True
                    self.ppms_field_Two_zone_radio_enabled = False
                    self.ppms_field_One_zone_radio_enabled = False
                # Function to convert
                def listToString(s):
                    # initialize an empty string
                    str1 = ""
                    # return string
                    return (str1.join(s))

                temp_log = str(TempList)
                self.append_text('Create Log...!\n', 'green')


                f.write(f"Experiment Field (Oe): {topField} to {botField}\n")
                f.write(f"Experiment Temperature (K): {temp_log}\n")
                if self.ppms_field_fixed_mode_radio_button.isChecked():
                    self.field_mode_fixed = True
                    f.write(f"Experiment Field Mode: Fixed field mode\n")
                else:
                    self.field_mode_fixed = False
                    f.write(f"Experiment Field Mode: Continuous sweep\n")

                    f.write(f"Experiment Current: {listToString(current)}\n")
                if self.BNC845RF_CONNECTED:
                    f.write(f"Instrument: BNC845RF\n")
                if self.DSP7265_Connected:
                    f.write(f"Instrument: DSP 7265 Lock-in\n")
                f.close()
                NotificationManager().send_message(f"{self.user} is running {self.measurement} on {self.sample_id}")

                self.canvas.axes.cla()
                self.canvas.axes_2.cla()
                self.canvas.draw()
                self.worker = Worker(self, self.keithley_6221, self.keithley_2182nv, self.DSP7265, current, TempList, topField,
                                     botField, self.folder_path, self.client, tempRate, current_mag, self.current_unit,
                                     self.file_name, self.run, number_of_field, self.field_mode_fixed,
                                     self.nv_channel_1_enabled, self.nv_channel_2_enabled, self.nv_NPLC,
                                     self.ppms_field_One_zone_radio_enabled, self.ppms_field_Two_zone_radio_enabled,
                                     self.ppms_field_Three_zone_radio_enabled, self.zone1_step_field,
                                     self.zone2_step_field, self.zone3_step_field, self.zone1_top_field,
                                     self.zone2_top_field, self.zone3_top_field, self.zone1_field_rate,
                                     self.zone2_field_rate,self.zone3_field_rate, self.Keithley_2182_Connected,
                                     self.Ketihley_6221_Connected,dsp7265_current_time_constant,self.DSP7265_Connected, self.demo_mode,
                                     self.keithley_6221_dc_config, self.keithley_6221_ac_config, self.ac_current_waveform,
                                     self.ac_current_freq, self.ac_current_offset, eto_number_of_avg, init_temp_rate,
                                     demag_field, record_zero_field)  # Create a worker instance
                self.worker.progress_update.connect(self.update_progress)
                self.worker.append_text.connect(self.append_text)
                self.worker.stop_measurment.connect(self.stop_measurement)
                self.worker.update_ppms_temp_reading_label.connect(self.update_ppms_temp_reading_label)
                self.worker.update_ppms_field_reading_label.connect(self.update_ppms_field_reading_label)
                self.worker.update_ppms_chamber_reading_label.connect(self.update_ppms_chamber_reading_label)
                self.worker.update_nv_channel_1_label.connect(self.update_nv_channel_1_label)
                self.worker.update_nv_channel_2_label.connect(self.update_nv_channel_2_label)
                self.worker.update_lockin_label.connect(self.update_lockin_label)
                self.worker.update_plot.connect(self.update_plot)
                self.worker.save_plot.connect(self.save_plot)
                self.worker.clear_plot.connect(self.clear_plot)
                self.worker.measurement_finished.connect(self.measurement_finished)
                self.worker.error_message.connect(self.error_popup)
                self.worker.update_measurement_progress.connect(self.update_measurement_progress)
                self.worker.update_dsp7265_freq_label.connect(self.update_dsp7265_freq_label)
                self.worker.update_keithley_6221_update_label.connect(self.update_keithley_6221_update_label)
                self.worker.start()  # Start the worker thread
                # self.worker.wait()
                # self.stop_measurement()
            except SystemExit as e:
                QMessageBox.critical(self, 'Possible Client Error', 'Check the client')
                self.stop_measurement()
                self.notification.send_notification(message="Your measurement went wrong, possible PPMS client lost connection")
                self.client_keep_going = False
                self.connect_btn.setText('Start Client')
                self.connect_btn_clicked = False
                self.server_btn.setEnabled(True)

            except Exception as e:
                tb_str = traceback.format_exc()
                self.stop_measurement()
                QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

                self.notification.send_notification(message=f"Error-{tb_str} {str(e)}")

    def save_plot(self, x_data, y_data, color, channel_1_enabled, channel_2_enabled, save, temp, current):

        if channel_1_enabled:
            self.canvas.axes.plot(x_data, y_data, color, marker='s')
            self.canvas.axes.set_ylabel('Voltage (v)', color=color)

        if channel_2_enabled:
            self.canvas.axes_2.plot(x_data, y_data, color, marker='s')
            self.canvas.axes_2.set_ylabel('Voltage (v)', color=color)

        self.canvas.axes.set_xlabel('Field (Oe)')
        self.canvas.axes.legend([f'{temp}K {current}A'])
        self.canvas.figure.tight_layout()
        self.canvas.draw()

        if save:
            self.canvas.figure.savefig(self.folder_path +"{}_{}_run{}_{}K_{}A.png".format(self.sample_id, self.measurement, self.run, temp, current))
            time.sleep(5)

            image_path = r"{}{}_{}_run{}_{}K_{}A.png".format(self.folder_path, self.sample_id, self.measurement, self.run, temp, current)
            if not os.path.exists(image_path):
                print("No Such File.")
            caption = f"Data preview"
            NotificationManager().send_message_with_image(message=f"Data Saved - {caption}", image_path=image_path)

    def update_plot(self, x_data, y_data, color, channel_1_enabled, channel_2_enabled):

        if channel_1_enabled:
            self.canvas.axes.plot(x_data, y_data, color, marker='s')
            self.canvas.axes.set_ylabel('Voltage (v)', color=color)

        if channel_2_enabled:
            self.canvas.axes_2.plot(x_data, y_data, color, marker='s')
            self.canvas.axes_2.set_ylabel('Voltage (v)', color=color)

        self.canvas.axes.set_xlabel('Field (Oe)')
        self.canvas.figure.tight_layout()
        self.canvas.draw()

    def error_popup(self, e, tb_str):
        self.stop_measurement()
        QMessageBox.warning(self, str(e), f'{tb_str}')

    def clear_plot(self):
        self.canvas.axes.cla()
        self.canvas.axes_2.cla()

    def update_nv_channel_1_label(self, chanel1):
        self.keithley_2182_channel_1_reading_label.setText(chanel1)

    def update_nv_channel_2_label(self, chanel2):
        self.keithley_2182_channel_2_reading_label.setText(chanel2)

    def update_progress(self, value):
        self.progress_bar.setValue(int(value))

    def show_error_message(self, tb_str, error_str):
        QMessageBox.warning(self, "Error", f'{tb_str} {str(error_str)}')

    def measurement_finished(self):
        try:
            self.keithley_6221.write(":OUTP OFF")
            self.keithley_6221.write("SOUR:WAVE:ABOR \n")
            # self.keithley_6221.write("*RST")
            self.keithley_6221.write("*CLS")
            # self.keithley_2182nv.write("*RST")
            self.keithley_2182nv.write("*CLS")
        except Exception:
            pass

        self.running = False
        self.measurement_active = False
        self.set_all_inputs_enabled(True)

        self.ppms_field_One_zone_radio_enabled = False
        self.ppms_field_Two_zone_radio_enabled = False
        self.ppms_field_Three_zone_radio_enabled = False
        self.nv_channel_1_enabled = None
        self.nv_channel_2_enabled = None
        # Update buttons
        if hasattr(self, 'start_measurement_btn'):
            self.start_measurement_btn.setEnabled(True)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(False)

        try:
            if self.worker is not None:
                self.worker.stop()
                self.worker = None
        except Exception:
            QMessageBox.warning(self, 'Fail', "Fail to stop the experiment")
        # self.stop_measurement()
        QMessageBox.information(self, "Measurement Finished", "The measurement has completed successfully!")

    def append_text(self, text, color):
        try:
            self.log_box.append(f'<span style="color:{color}">{str(text)}</span>')
            self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

        except Exception as e:
            QMessageBox.warning(self, "Error", f'{str(e)}')

    def update_ppms_temp_reading_label(self,  temp, temp_unit, status):
        self.ppms_reading_temp_label.setText(f'{str(temp)} {str(temp_unit)} ({status})')

    def update_ppms_chamber_reading_label(self,  cT):
        self.ppms_reading_chamber_label.setText(f'{str(cT)}')

    def update_ppms_field_reading_label(self,  field, field_unit, status):
        self.ppms_reading_field_label.setText(f'{str(field)} {str(field_unit)} ({status})')

    def update_lockin_label(self, x, y, mag, phase):
        self.dsp7265_x_reading_value_label.setText(f'{str(x)}')
        self.dsp7265_y_reading_value_label.setText(f'{str(y)}')
        self.dsp7265_mag_reading_value_label.setText(f'{str(mag)} volts')
        self.dsp7265_phase_reading_value_label.setText(f'{str(phase)} degs')

    def update_measurement_progress(self, day, hour, min, progress):
        self.eto_measurement_status_time_remaining_in_days_reading_label.setText(f'{str(day)} days')
        self.eto_measurement_status_time_remaining_in_hours_reading_label.setText(f'{str(hour)} hours')
        self.eto_measurement_status_time_remaining_in_mins_reading_label.setText(f'{str(min)} mins')
        self.eto_measurement_status_cur_percent_reading_label.setText(f'{str(progress)} %')

    def update_eto_average_label(self):
        avg = self.eto_setting_average_line_edit.text()
        self.eto_measurement_status_average_reading_label.setText(f'{str(avg)}')
        return int(avg)

    def update_dsp7265_freq_label(self, cur_freq):
        self.dsp7265_freq_reading_value_label.setText(str(cur_freq) + ' Hz')

    def update_keithley_6221_update_label(self, current, state):
        self.keithley_reading_current_reading_label.setText(str(current))
        self.keithley_reading_state_reading_label.setText(str(state))

    def run_ETO(self, append_text, progress_update, stop_measurement, update_ppms_temp_reading_label,
                update_ppms_field_reading_label, update_ppms_chamber_reading_label,
                update_nv_channel_1_label, update_nv_channel_2_label, update_lockin_label, clear_plot, update_plot,
                save_plot, measurement_finished, error_message, update_measurement_progress, update_dsp7265_freq_label,
                update_keithley_6221_update_label,
                keithley_6221, keithley_2182nv, DSP7265, current, TempList,
                topField, botField, folder_path, client, tempRate, current_mag, current_unit,
                file_name, run, number_of_field, field_mode_fixed, nv_channel_1_enabled,
                nv_channel_2_enabled, nv_NPLC, ppms_field_One_zone_radio_enabled,
                ppms_field_Two_zone_radio_enabled, ppms_field_Three_zone_radio_enabled,zone1_step_field,
                zone2_step_field, zone3_step_field, zone1_top_field, zone2_top_field, zone3_top_field, zone1_field_rate,
                zone2_field_rate, zone3_field_rate, Keithley_2182_Connected,
                Ketihley_6221_Connected, dsp7265_current_time_constant, DSP7265_Connected, running, demo, keithley_6221_dc_config,
                keithley_6221_ac_config, ac_current_waveform, ac_current_freq, ac_current_offset,
                eto_number_of_avg, init_temp_rate, demag_field, record_zero_field
                ):
        try:
            ppms = ThreadSafePPMSCommands(client, NotificationManager())

            def convert_to_seconds(time_str):
                import re
                # Allow optional space between number and unit
                match = re.match(r"(\d+(?:\.\d+)?)\s*(us|µs|ms|s|ks)", time_str.strip())
                if not match:
                    raise ValueError(f"Invalid time format: {time_str}")

                value, unit = match.groups()
                value = float(value)

                # Convert based on unit
                if unit == "ms" or unit == 'us' or unit == "µs":
                    return 1
                elif unit == "s":
                    return value * 2
                elif unit == "ks":
                    return (value+value/2) * 1000
                else:
                    raise ValueError(f"Unknown unit: {unit}")

            def deltaH_chk(currentField):
                if ppms_field_One_zone_radio_enabled:
                    deltaH = zone1_step_field
                    user_field_rate = zone1_field_rate
                elif ppms_field_Two_zone_radio_enabled:
                    if (currentField <= zone1_top_field + 1 or currentField >= -1 * zone1_top_field-1):
                        deltaH = zone1_step_field
                        user_field_rate = zone1_field_rate
                    elif (currentField > -1 * zone2_top_field and currentField <= zone2_top_field):
                        deltaH = zone2_step_field
                        user_field_rate = zone2_field_rate
                elif ppms_field_Three_zone_radio_enabled:
                    if (currentField <= zone1_top_field+1 or currentField >= -1 * zone1_top_field-1):
                        deltaH = zone1_step_field
                        user_field_rate = zone1_field_rate
                    elif (currentField < zone2_top_field and currentField >= -1 * zone2_top_field):
                        deltaH = zone2_step_field
                        user_field_rate = zone2_field_rate
                    elif (currentField > -1 * zone3_top_field and currentField < zone3_top_field):
                        deltaH = zone3_step_field
                        user_field_rate = zone3_field_rate
                return deltaH, user_field_rate

            def get_chamber_status():
                try:
                    success, cT = ppms.get_chamber_status(timeout=10)
                    # cT = client.get_chamber()
                    if not success:
                        stop_measurement()
                    return cT
                except SystemExit as e:
                    tb_str = traceback.format_exc()
                    NotificationManager().send_message(
                        f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

            def set_temperature(set_point, temp_rate):
                try:
                    success = ppms.set_temperature(
                        set_point=set_point,
                        temp_rate=temp_rate,
                        timeout=10  # 30 second timeout
                    )
                    if not success:
                        stop_measurement()
                    # client.set_temperature(set_point,
                    #                        temp_rate,
                    #                        client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
                except SystemExit as e:
                    tb_str = traceback.format_exc()
                    NotificationManager().send_message(
                        f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

            def set_field(set_point, field_rate):
                try:
                    success = ppms.set_field(
                        set_point=set_point,
                        field_rate=field_rate,
                        timeout=10
                    )
                    if not success:
                        stop_measurement()
                    # client.set_field(set_point,
                    #                  field_rate,
                    #                  client.field.approach_mode.linear,  # linear/oscillate
                    #                  client.field.driven_mode.driven)
                    append_text(f'Setting Field to {str(set_point)} Oe... \n', 'orange')
                except SystemExit as e:
                    tb_str = traceback.format_exc()
                    NotificationManager().send_message(
                        f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

            def read_temperature():
                try:
                    success, temp, status, unit = ppms.read_temperature(timeout=10)
                    if not success:
                        stop_measurement()
                    # temperature, status = client.get_temperature()
                    # temp_unit = client.temperature.units
                    return temp, status, unit
                except SystemExit as e:
                    tb_str = traceback.format_exc()
                    NotificationManager().send_message(
                        f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

            def read_field():
                try:
                    success, field, status, unit = ppms.read_field(timeout=10)
                    if not success:
                        stop_measurement()
                    # field, status = client.get_field()
                    # field_unit = client.field.units
                    return field, status, unit
                except SystemExit as e:
                    tb_str = traceback.format_exc()
                    NotificationManager().send_message(
                        f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

            NotificationManager().send_message(message="The measurement has been started successfully.")

            number_of_current = len(current)
            number_of_temp = len(TempList)
            fast_field_rate = 220
            zero_field = 0
            start_time = time.time()
            append_text('Measurement Start....\n', 'red')
            user_field_rate = zone1_field_rate
            time.sleep(5)
            if demo:
                append_text(f'Temperature = 300 K\n', 'purple')
                update_ppms_temp_reading_label('300', 'K', 'Ramping')
                # ------------Field Status----------------------
                append_text(f'Field = 0 Oe\n', 'purple')
                update_ppms_field_reading_label('0', 'Oe', 'stable')
            else:
                # -------------Temp Status---------------------
                temperature, status, temp_unit = read_temperature()
                append_text(f'Current temperature is {temperature} {temp_unit}\n', 'purple')
                update_ppms_temp_reading_label(str(temperature), str(temp_unit), status)
                # ------------Field Status----------------------
                field, status, field_unit = read_field()
                append_text(f'Current field is {field} {field_unit}\n', 'purple')
                update_ppms_field_reading_label(str(field), field_unit, status)

            # ----------------- Loop Down ----------------------#
            Curlen = len(current)
            templen = len(TempList)
            totoal_progress = Curlen*templen

            if not demo:
                cT = get_chamber_status()
                update_ppms_chamber_reading_label(str(cT))
                if not running():
                    stop_measurement()
                    return
                for i in range(templen):
                    set_field(zero_field, fast_field_rate)

                    time.sleep(10)
                    while True:
                        if not running():
                            stop_measurement()
                            return
                        time.sleep(15)
                        F, sF, field_unit = read_field()
                        update_ppms_field_reading_label(str(F), field_unit, sF)
                        append_text(f'Status: {sF}\n', 'red')
                        if sF == 'Holding (driven)':
                            break
                    append_text(f'Loop is at {str(TempList[i])} K Temperature\n', 'blue')
                    temp_set_point = TempList[i]
                    if i == 0:
                        set_temperature(temp_set_point, init_temp_rate)
                    else:
                        set_temperature(temp_set_point, tempRate)
                    append_text(f'Waiting for {temp_set_point} K Temperature\n', 'red')
                    time.sleep(4)

                    MyTemp, sT, temp_unit = read_temperature()
                    update_ppms_temp_reading_label(str(MyTemp), str(temp_unit), sT)
                    while True:
                        if not running():
                            stop_measurement()
                            return
                        time.sleep(1.5)
                        MyTemp, sT, temp_unit = read_temperature()
                        update_ppms_temp_reading_label(str(MyTemp), str(temp_unit), sT)
                        append_text(f'Temperature Status: {sT}\n', 'blue')
                        if sT == 'Stable':
                            break
                    if i == 0:
                        append_text(f'Stabilizing the Temperature....', 'orange')
                        time.sleep(60)

                    else:
                        append_text(f'Stabilizing the Temperature.....', 'orange')
                        time.sleep(300)

                    for j in range(Curlen):
                        NotificationManager().send_message(f"Starting measurement at temperature {str(TempList[i])} K, {current_mag[j]} {current_unit}")
                        clear_plot()
                        csv_filename = f"{folder_path}{file_name}_{TempList[i]}_K_{current_mag[j]}_{current_unit}_Run_{run}.csv"
                        csv_filename_avg = f"{folder_path}{file_name}_{TempList[i]}_K_{current_mag[j]}_{current_unit}_Run_{run}_avg.csv"
                        csv_filename_zero_field = f"{folder_path}{file_name}_{TempList[i]}_K_{current_mag[j]}_{current_unit}_Run_{run}_zero_field.csv"

                        # number_of_current = number_of_current - 1
                        time.sleep(5)
                        set_field(demag_field, fast_field_rate)
                        append_text(f'Waiting for {demag_field} Oe Field used for demagnetization... \n', 'blue')
                        time.sleep(10)
                        while True:
                            if not running():
                                stop_measurement()
                                return
                            time.sleep(15)
                            F, sF, field_unit = read_field()
                            update_ppms_field_reading_label(str(F), field_unit, sF)
                            append_text(f'Status: {sF}\n', 'red')
                            if sF == 'Holding (driven)':
                                break
                        client.set_field(zero_field,
                                         fast_field_rate,
                                         client.field.approach_mode.oscillate,  # linear/oscillate
                                         client.field.driven_mode.driven)
                        append_text(f'Waiting for {zero_field} Oe Field for Demagnetization... \n', 'blue')
                        time.sleep(10)
                        while True:
                            if not running():
                                stop_measurement()
                                return
                            time.sleep(15)
                            F, sF, field_unit = read_field()
                            update_ppms_field_reading_label(str(F), field_unit, sF)
                            append_text(f'Status: {sF}\n', 'red')
                            if sF == 'Holding (driven)':
                                break

                        if Keithley_2182_Connected:
                            keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                            keithley_2182nv.write(f"SENS:VOLT:DC:NPLC {nv_NPLC}")
                            keithley_2182nv.write(f"SENS:VOLT:DC:LPAS OFF")
                        time.sleep(2)  # Wait for the configuration to complete
                        Chan_1_voltage = 0
                        Chan_2_voltage = 0
                        k = 0
                        MyField, sF, field_unit = read_field()
                        update_ppms_field_reading_label(str(MyField), field_unit, sF)

                        if Ketihley_6221_Connected:
                            # keithley_6221.write('CLE')
                            if keithley_6221_dc_config:
                                keithley_6221.write(":OUTP OFF")  # Set source function to current
                                keithley_6221.write("CURRent:RANGe:AUTO ON \n")
                                keithley_6221.write(f'CURR {current[j]} \n')
                                keithley_6221.write(":OUTP ON")  # Turn on the output
                                append_text(f'DC current is set to: {str(current_mag[j])} {str(current_unit)}', 'blue')
                                update_keithley_6221_update_label(current[j], "ON")

                            if keithley_6221_ac_config:
                                keithley_6221.write("SOUR:WAVE:ABOR \n")
                                keithley_6221.write('CURR:RANG:AUTO ON \n')
                                keithley_6221.write(f'SOUR:WAVE:FUNC {ac_current_waveform} \n')
                                keithley_6221.write(f'SOUR:WAVE:AMPL {current[j]} \n')
                                keithley_6221.write(f'SOUR:WAVE:FREQ {ac_current_freq} \n')
                                keithley_6221.write(f'SOUR:WAVE:OFFset {ac_current_offset} \n')
                                keithley_6221.write('SOUR:WAVE:RANG BEST \n')
                                keithley_6221.write('SOUR:WAVE:ARM \n')
                                keithley_6221.write('SOUR:WAVE:INIT \n')
                                update_keithley_6221_update_label(current[j], "ON")


                        if DSP7265_Connected:
                            time.sleep(10)
                            delay = convert_to_seconds(dsp7265_current_time_constant)
                            cur_freq = str(float(DSP7265.query('FRQ[.]')) / 1000)
                            update_dsp7265_freq_label(cur_freq)
                            DSP7265.write('AQN')


                        if record_zero_field:
                            while k < eto_number_of_avg:
                                if Keithley_2182_Connected:
                                    try:
                                        if nv_channel_1_enabled:
                                            keithley_2182nv.write("SENS:CHAN 1")
                                            volt = keithley_2182nv.query("READ?")
                                            Chan_1_voltage = float(volt)
                                            append_text(f"Channel 1 Zero Field Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                    except Exception as e:
                                        QMessageBox.warning(self, 'Warning', str(e))

                                    if nv_channel_2_enabled:
                                        keithley_2182nv.write("SENS:CHAN 2")
                                        volt2 = keithley_2182nv.query("READ?")
                                        Chan_2_voltage = float(volt2)
                                        update_nv_channel_2_label(str(Chan_2_voltage))
                                        append_text(f"Channel 2 Zero Field Voltage: {str(Chan_2_voltage)} V\n", 'green')

                                    # Calculate the average voltage
                                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                                    resistance_chan_2 = Chan_2_voltage / float(current[j])

                                    # Append the data to the CSV file
                                    with open(csv_filename_zero_field, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)",
                                                 "Channel 2 "
                                                 "Resistance ("
                                                 "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow([MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                             Chan_2_voltage, MyTemp, current[j]])
                                        append_text(f'Data Saved for {MyField} Oe at {MyTemp} K', 'green')
                                elif DSP7265_Connected:
                                    try:
                                        time.sleep(delay)
                                        X = float(DSP7265.query("X."))  # Read the measurement result
                                        Y = float(DSP7265.query("Y."))  # Read the measurement result
                                        Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                        Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                        update_lockin_label(str(X), str(Y), str(Mag), str(Phase))

                                    except Exception as e:
                                        QMessageBox.warning(self, "Reading Error", f'{e}')

                                    resistance_chan_1 = X / float(current[j])
                                    # Append the data to the CSV file
                                    with open(csv_filename_zero_field, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                                 "Voltage X (V)", "Voltage Y (V)", "Phase (deg)",
                                                 "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [MyField, resistance_chan_1, Mag, X, Y,
                                             Phase, MyTemp, current[j]])
                                        self.log_box.append(f'Data Saved for {MyField} Oe at {MyTemp} K\n')
                                k+=1
                                time.sleep(0.2)

                        self.pts = 0
                        currentField = topField
                        deltaH, user_field_rate = deltaH_chk(currentField)
                        number_of_field_update = number_of_field
                        self.field_array = []
                        self.channel1_field_array = []
                        self.channel2_field_array = []
                        self.channel1_field_avg_array = []
                        self.channel2_field_avg_array = []
                        self.field_avg_array = []
                        self.channel1_array = []
                        self.channel2_array = []
                        self.channel1_avg_array = []
                        self.channel2_avg_array = []
                        self.lockin_x = []
                        self.lockin_y = []
                        self.lockin_mag = []
                        self.lockin_pahse = []

                        if DSP7265_Connected:
                            cur_freq = str(float(DSP7265.query('FRQ[.]')) / 1000)
                            update_dsp7265_freq_label(cur_freq)
                            DSP7265.write('AQN')
                            time.sleep(5)

                        if field_mode_fixed:
                            while currentField >= botField:
                                if not running():
                                    stop_measurement()
                                    return
                                single_measurement_start = time.time()
                                append_text(f'Loop is at {currentField} Oe Field Up \n', 'blue')
                                field_set_point = currentField
                                append_text(f'Set the field to {field_set_point} Oe and then collect data \n', 'blue')
                                set_field(field_set_point, user_field_rate)

                                time.sleep(4)
                                while True:
                                    time.sleep(1)
                                    MyField, sF, field_unit = read_field()
                                    update_ppms_field_reading_label(str(MyField), field_unit, sF)
                                    append_text(f'Status: {sF}\n', 'blue')
                                    if sF == 'Holding (driven)':
                                        break

                                # ----------------------------- Measure NV voltage -------------------
                                append_text(f'Saving data for {MyField} Oe \n', 'green')
                                if Keithley_2182_Connected:
                                    keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                                    keithley_2182nv.write(f"VOLT:DC:NPLC {nv_NPLC}")
                                time.sleep(2)  # Wait for the configuration to complete
                                Chan_1_voltage = 0
                                Chan_2_voltage = 0
                                k = 0
                                MyField, sF, field_unit = read_field()
                                update_ppms_field_reading_label(str(MyField), field_unit, sF)
                                self.channel1_avg_array_temp = []
                                self.channel2_avg_array_temp = []
                                self.channel1_field_avg_array_temp = []
                                self.channel2_field_avg_array_temp = []
                                if Keithley_2182_Connected:
                                    while k < eto_number_of_avg:
                                        try:
                                            if nv_channel_1_enabled:
                                                keithley_2182nv.write("SENS:CHAN 1")
                                                volt = keithley_2182nv.query("READ?")
                                                Chan_1_voltage = float(volt)
                                                update_nv_channel_1_label(str(Chan_1_voltage))
                                                append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                                self.channel1_array.append(Chan_1_voltage)
                                                self.channel1_field_array.append(MyField)
                                                self.channel1_avg_array_temp.append(Chan_1_voltage)
                                                self.channel1_field_avg_array_temp.append(MyField)
                                                # update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                        except Exception as e:
                                            QMessageBox.warning(self, 'Warning', str(e))

                                        if nv_channel_2_enabled:
                                            keithley_2182nv.write("SENS:CHAN 2")
                                            volt2 = keithley_2182nv.query("READ?")
                                            Chan_2_voltage = float(volt2)
                                            update_nv_channel_2_label(str(Chan_2_voltage))
                                            append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                            self.channel2_array.append(Chan_2_voltage)
                                            self.channel2_field_array.append(MyField)
                                            self.channel2_avg_array_temp.append(Chan_2_voltage)
                                            self.channel2_field_avg_array_temp.append(MyField)
                                            # update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                        # Calculate the average voltage
                                        resistance_chan_1 = Chan_1_voltage / float(current[j])
                                        resistance_chan_2 = Chan_2_voltage / float(current[j])

                                        # Append the data to the CSV file
                                        with open(csv_filename, "a", newline="") as csvfile:
                                            csv_writer = csv.writer(csvfile)

                                            if csvfile.tell() == 0:  # Check if file is empty
                                                csv_writer.writerow(
                                                    ["Field (Oe)", "Channel 1 Resistance (Ohm)",
                                                     "Channel 1 Voltage (V)", "Channel 2 "
                                                                              "Resistance ("
                                                                              "Ohm)",
                                                     "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                            csv_writer.writerow(
                                                [MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                 Chan_2_voltage, MyTemp, current[j]])
                                            append_text(f'Data Saved for {MyField} Oe at {MyTemp} K', 'green')
                                        k += 1
                                        time.sleep(0.2)
                                    if self.channel1_avg_array_temp:
                                        channel1_avg_sig = sum(self.channel1_avg_array_temp) / len(self.channel1_avg_array_temp)
                                        channel1_field_avg_sig = sum(self.channel1_field_avg_array_temp) / len(
                                            self.channel1_field_avg_array_temp)
                                        self.channel1_avg_array.append(channel1_avg_sig)
                                        self.channel1_field_avg_array.append(channel1_field_avg_sig)
                                        resistance_chan_1_avg = channel1_avg_sig / float(current[j])
                                        update_plot(self.channel1_field_avg_array, self.channel1_avg_array, 'black', True, False)
                                    else:
                                        resistance_chan_1_avg = 0
                                        channel1_avg_sig = 0
                                    if self.channel2_avg_array_temp:
                                        channel2_avg_sig = sum(self.channel2_avg_array_temp) / len(self.channel2_avg_array_temp)
                                        channel2_field_avg_sig = sum(self.channel2_field_avg_array_temp) / len(
                                            self.channel2_field_avg_array_temp)
                                        self.channel2_avg_array.append(channel2_avg_sig)
                                        self.channel2_field_avg_array.append(channel2_field_avg_sig)
                                        resistance_chan_2_avg = channel2_avg_sig / float(current[j])
                                        update_plot(self.channel2_field_avg_array, self.channel2_avg_array, 'red', True, False)
                                        # Append the data to the CSV file
                                    else:
                                        resistance_chan_2_avg = 0
                                        channel2_avg_sig = 0
                                    with open(csv_filename_avg, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)",
                                                 "Channel 1 Voltage (V)", "Channel 2 "
                                                                          "Resistance ("
                                                                          "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [MyField, resistance_chan_1_avg, channel1_avg_sig, resistance_chan_2_avg,
                                             channel2_avg_sig, MyTemp, current[j]])
                                        append_text(f'Data Saved for {MyField} Oe at {MyTemp} K', 'green')
                                elif DSP7265_Connected:
                                    try:
                                        time.sleep(delay)
                                        X = float(DSP7265.query("X."))  # Read the measurement result
                                        Y = float(DSP7265.query("Y."))  # Read the measurement result
                                        Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                        Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                        update_lockin_label(str(X), str(Y), str(Mag), str(Phase))
                                        self.lockin_x.append(X)
                                        # self.lockin_y.append(Y)
                                        self.lockin_mag.append(Mag)
                                        # self.lockin_pahse.append(Phase)
                                        self.field_array.append(MyField)
                                        # # Drop off the first y element, append a new one.
                                        update_plot(self.field_array, self.lockin_x, 'black', True, False)
                                            # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                    except Exception as e:
                                        QMessageBox.warning(self, "Reading Error", f'{e}')

                                    resistance_chan_1 = Mag / float(current[j])
                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                                 "Voltage X (V)", "Voltage Y (V)", "Phase (deg)",
                                                                                   "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [currentField, resistance_chan_1, Mag, X, Y,
                                             Phase, MyTemp, current[j]])
                                        self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')

                                MyField, sF, field_unit = read_field()
                                update_ppms_field_reading_label(str(MyField), field_unit, sF)
                                MyTemp, sT, temp_unit = read_temperature()
                                update_ppms_temp_reading_label(str(MyTemp), str(temp_unit), sT)
                                # ----------------------------- Measure NV voltage -------------------
                                deltaH, user_field_rate = deltaH_chk(currentField)

                                append_text(f'deltaH = {deltaH}\n', 'orange')
                                # Update currentField for the next iteration
                                currentField -= deltaH
                                self.pts += 1  # Number of self.pts count
                                single_measurement_end = time.time()
                                Single_loop = single_measurement_end - single_measurement_start
                                number_of_field_update = number_of_field_update - 1
                                append_text('Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop), 'purple')
                                append_text('Estimated Single measurement (in hrs):  {} hrs \n'.format(
                                    Single_loop * number_of_field / 60 / 60), 'purple')
                                total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                            number_of_temp - i)
                                totoal_time_in_minutes = total_time_in_seconds / 60
                                total_time_in_hours = totoal_time_in_minutes / 60
                                total_time_in_days = total_time_in_hours / 24
                                append_text('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                    total_time_in_seconds), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                        totoal_time_in_minutes), 'purple')
                                append_text('Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                    total_time_in_hours), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                        total_time_in_days), 'purple')
                                total_estimated_experiment_time_in_seconds = Single_loop * (number_of_field) * (
                                    number_of_current) * (number_of_temp)
                                current_progress = (total_estimated_experiment_time_in_seconds - total_time_in_seconds) / total_estimated_experiment_time_in_seconds
                                progress_update(int(current_progress * 100))
                                update_measurement_progress(total_time_in_days, total_time_in_hours,
                                                            totoal_time_in_minutes, current_progress * 100)

                            # ----------------- Loop Up ----------------------#
                            currentField = botField
                            deltaH, user_field_rate = deltaH_chk(currentField)
                            NotificationManager().send_message(f"Starting the second half of measurement - ramping field up")
                            current_progress = int((i + 1) * (j + 1) / totoal_progress * 100) / 2
                            progress_update(int(current_progress))
                            while currentField <= topField:
                                if not running():
                                    stop_measurement()
                                    return
                                single_measurement_start = time.time()
                                append_text(f'\n Loop is at {currentField} Oe Field Up \n', 'blue')
                                field_set_point = currentField

                                append_text(f'Set the field to {field_set_point} Oe and then collect data \n', 'greem')
                                set_field(field_set_point, user_field_rate)

                                time.sleep(4)
                                while True:
                                    time.sleep(1)

                                    MyField, sF, field_unit = read_field()
                                    update_ppms_field_reading_label(str(MyField), field_unit, sF)
                                    append_text(f'Status: {sF}\n', 'blue')
                                    if sF == 'Holding (driven)':
                                        break

                                # ----------------------------- Measure NV voltage -------------------
                                append_text(f'Saving data for {MyField} Oe \n', 'green')
                                Chan_1_voltage = 0
                                Chan_2_voltage = 0
                                if Keithley_2182_Connected:
                                    keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                                    keithley_2182nv.write(f"VOLT:DC:NPLC {nv_NPLC}")
                                time.sleep(2)  # Wait for the configuration to complete
                                MyField, sF, field_unit = read_field()
                                update_ppms_field_reading_label(str(MyField), field_unit, sF)
                                k = 0
                                self.channel1_avg_array_temp = []
                                self.channel2_avg_array_temp = []
                                self.channel1_field_avg_array_temp = []
                                self.channel2_field_avg_array_temp = []
                                if Keithley_2182_Connected:
                                    while k < eto_number_of_avg:
                                        try:
                                            if nv_channel_1_enabled:
                                                keithley_2182nv.write("SENS:CHAN 1")
                                                volt = keithley_2182nv.query("READ?")
                                                Chan_1_voltage = float(volt)
                                                update_nv_channel_1_label(str(Chan_1_voltage))
                                                append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                                self.channel1_array.append(Chan_1_voltage)
                                                self.channel1_field_array.append(MyField)
                                                self.channel1_avg_array_temp.append(Chan_1_voltage)
                                                self.channel1_field_avg_array_temp.append(MyField)
                                                # update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                        except Exception as e:
                                            QMessageBox.warning(self, 'Warning', str(e))

                                        if nv_channel_2_enabled:
                                            keithley_2182nv.write("SENS:CHAN 2")
                                            volt2 = keithley_2182nv.query("READ?")
                                            Chan_2_voltage = float(volt2)
                                            update_nv_channel_2_label(str(Chan_2_voltage))
                                            append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                            self.channel2_array.append(Chan_2_voltage)
                                            self.channel2_field_array.append(MyField)
                                            self.channel2_avg_array_temp.append(Chan_2_voltage)
                                            self.channel2_field_avg_array_temp.append(MyField)
                                            # update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                        # Calculate the average voltage
                                        resistance_chan_1 = Chan_1_voltage / float(current[j])
                                        resistance_chan_2 = Chan_2_voltage / float(current[j])

                                        # Append the data to the CSV file
                                        with open(csv_filename, "a", newline="") as csvfile:
                                            csv_writer = csv.writer(csvfile)

                                            if csvfile.tell() == 0:  # Check if file is empty
                                                csv_writer.writerow(
                                                    ["Field (Oe)", "Channel 1 Resistance (Ohm)",
                                                     "Channel 1 Voltage (V)", "Channel 2 "
                                                                              "Resistance ("
                                                                              "Ohm)",
                                                     "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                            csv_writer.writerow(
                                                [MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                 Chan_2_voltage, MyTemp, current[j]])
                                            append_text(f'Data Saved for {MyField} Oe at {MyTemp} K', 'green')
                                        k += 1
                                        time.sleep(0.2)
                                    if self.channel1_avg_array_temp:
                                        channel1_avg_sig = sum(self.channel1_avg_array_temp) / len(
                                            self.channel1_avg_array_temp)
                                        channel1_field_avg_sig = sum(self.channel1_field_avg_array_temp) / len(
                                            self.channel1_field_avg_array_temp)
                                        self.channel1_avg_array.append(channel1_avg_sig)
                                        self.channel1_field_avg_array.append(channel1_field_avg_sig)
                                        resistance_chan_1_avg = channel1_avg_sig / float(current[j])
                                        update_plot(self.channel1_field_avg_array, self.channel1_avg_array, 'black',
                                                    True, False)

                                    else:
                                        resistance_chan_1_avg = 0
                                        channel1_avg_sig = 0
                                    if self.channel2_avg_array_temp:
                                        channel2_avg_sig = sum(self.channel2_avg_array_temp) / len(
                                            self.channel2_avg_array_temp)
                                        channel2_field_avg_sig = sum(self.channel2_field_avg_array_temp) / len(
                                            self.channel2_field_avg_array_temp)
                                        self.channel2_avg_array.append(channel2_avg_sig)
                                        self.channel2_field_avg_array.append(channel2_field_avg_sig)
                                        resistance_chan_2_avg = channel2_avg_sig / float(current[j])
                                        update_plot(self.channel2_field_avg_array, self.channel2_avg_array, 'red', True,
                                                    False)
                                        # Append the data to the CSV file
                                    else:
                                        resistance_chan_2_avg = 0
                                        channel2_avg_sig = 0
                                    with open(csv_filename_avg, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)",
                                                 "Channel 1 Voltage (V)", "Channel 2 "
                                                                          "Resistance ("
                                                                          "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [MyField, resistance_chan_1_avg, channel1_avg_sig, resistance_chan_2_avg,
                                             channel2_avg_sig, MyTemp, current[j]])
                                        append_text(f'Data Saved for {MyField} Oe at {MyTemp} K', 'green')
                                elif DSP7265_Connected:
                                    try:
                                        time.sleep(delay)
                                        X = float(DSP7265.query("X."))  # Read the measurement result
                                        Y = float(DSP7265.query("Y."))  # Read the measurement result
                                        Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                        Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                        update_lockin_label(str(X), str(Y), str(Mag), str(Phase))
                                        self.lockin_x.append(X)
                                        # self.lockin_y.append(Y)
                                        self.lockin_mag.append(Mag)
                                        # self.lockin_pahse.append(Phase)
                                        self.field_array.append(MyField)

                                            # # Drop off the first y element, append a new one.
                                        update_plot(self.field_array, self.lockin_x, 'black', True, False)
                                            # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                    except Exception as e:
                                        QMessageBox.warning(self, "Reading Error", f'{e}')

                                    resistance_chan_1 = Mag / float(current[j])
                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                                 "Voltage X (V)", "Voltage Y (V)", "Phase (deg)",
                                                                                   "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [currentField, resistance_chan_1, Mag, X, Y,
                                             Phase, MyTemp, current[j]])
                                        self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')
                                # ----------------------------- Measure NV voltage -------------------
                                deltaH, user_field_rate = deltaH_chk(currentField)

                                append_text(f'deltaH = {deltaH}\n', 'orange')
                                # Update currentField for the next iteration
                                currentField += deltaH
                                self.pts += 1  # Number of self.pts count
                                single_measurement_end = time.time()
                                Single_loop = single_measurement_end - single_measurement_start
                                number_of_field_update = number_of_field_update - 1
                                total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                            number_of_temp - i)
                                totoal_time_in_minutes = total_time_in_seconds / 60
                                total_time_in_hours = totoal_time_in_minutes / 60
                                total_time_in_days = total_time_in_hours / 24
                                append_text('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                    total_time_in_seconds), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                        totoal_time_in_minutes), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                        total_time_in_hours), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                        total_time_in_days), 'purple')
                                total_estimated_experiment_time_in_seconds = Single_loop * (number_of_field) * (
                                    number_of_current) * (number_of_temp)
                                current_progress = (total_estimated_experiment_time_in_seconds - total_time_in_seconds) / total_estimated_experiment_time_in_seconds
                                try:
                                    progress_update(int(current_progress * 100))
                                except Exception:
                                    None
                                update_measurement_progress(total_time_in_days, total_time_in_hours,
                                                            totoal_time_in_minutes, current_progress * 100)
                        else:
                            set_field(topField, fast_field_rate)

                            time.sleep(4)
                            MyField, sF, field_unit = read_field()
                            update_ppms_field_reading_label(str(MyField), field_unit, sF)
                            while True:
                                try:
                                    time.sleep(1.5)
                                    MyField, sF, field_unit = read_field()
                                    update_ppms_field_reading_label(str(MyField), field_unit, sF)
                                    append_text(f'Status: {sF}\n', 'red')
                                    if sF == 'Holding (driven)':
                                        break
                                except SystemExit as e:
                                    error_message(e, e)
                                    NotificationManager().send_message(
                                            "Your measurement went wrong, possible PPMS client lost connection", 'critical')
                            time.sleep(20)
                            deltaH, user_field_rate = deltaH_chk(MyField)
                            currentField = MyField
                            set_field(botField, user_field_rate)
                            append_text(f'Start collecting data \n', 'purple')
                            counter = 0
                            while currentField >= botField + 1:
                                if not running():
                                    stop_measurement()
                                    return
                                counter += 1
                                single_measurement_start = time.time()
                                if Keithley_2182_Connected:
                                    NPLC = nv_NPLC
                                    keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                                    keithley_2182nv.write(f"VOLT:DC:NPLC {NPLC}")
                                time.sleep(1)
                                currentField, sF, field_unit = read_field()

                                update_ppms_field_reading_label(str(currentField), field_unit, sF)
                                append_text(f'Saving data for {currentField} Oe \n', 'green')

                                Chan_1_voltage = 0
                                Chan_2_voltage = 0
                                self.field_array.append(currentField)
                                if Keithley_2182_Connected:
                                    if nv_channel_1_enabled:
                                        keithley_2182nv.write("SENS:CHAN 1")
                                        volt = keithley_2182nv.query("READ?")
                                        Chan_1_voltage = float(volt)
                                        update_nv_channel_1_label(str(Chan_1_voltage))
                                        append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                        self.channel1_array.append(Chan_1_voltage)
                                        if counter % 20 == 0:
                                            counter = 0
                                            update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                    if nv_channel_2_enabled:
                                        keithley_2182nv.write("SENS:CHAN 2")
                                        volt2 = keithley_2182nv.query("READ?")
                                        Chan_2_voltage = float(volt2)
                                        update_nv_channel_2_label(str(Chan_2_voltage))
                                        append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                        self.channel2_array.append(Chan_2_voltage)
                                        # # Drop off the first y element, append a new one.
                                        if counter % 20 == 0:
                                            counter = 0
                                            update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                    # Calculate the average voltage
                                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                                    resistance_chan_2 = Chan_2_voltage / float(current[j])

                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                                      "Resistance ("
                                                                                                                      "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow([currentField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                             Chan_2_voltage, MyTemp, current[j]])
                                        append_text(f'Data Saved for {currentField} Oe at {MyTemp} K', 'green')
                                elif DSP7265_Connected:
                                    try:
                                        time.sleep(delay)
                                        X = float(DSP7265.query("X."))  # Read the measurement result
                                        Y = float(DSP7265.query("Y."))  # Read the measurement result
                                        Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                        Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                        update_lockin_label(str(X), str(Y), str(Mag), str(Phase))
                                        self.lockin_x.append(X)
                                        # self.lockin_y.append(Y)
                                        self.lockin_mag.append(Mag)
                                        # self.lockin_pahse.append(Phase)
                                        if counter % 20 == 0:
                                            counter = 0
                                            # # Drop off the first y element, append a new one.
                                            update_plot(self.field_array, self.lockin_x, 'black', True, False)
                                            # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                    except Exception as e:
                                        QMessageBox.warning(self, "Reading Error", f'{e}')

                                    resistance_chan_1 = Mag / float(current[j])
                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                                 "Voltage X (V)", "Voltage Y (V)", "Phase (deg)",
                                                                                   "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [currentField, resistance_chan_1, Mag, X, Y,
                                             Phase, MyTemp, current[j]])
                                        self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')
                                # ----------------------------- Measure NV voltage -------------------
                                deltaH, user_field_rate = deltaH_chk(currentField)

                                append_text(f'Field Rate = {user_field_rate}\n', 'orange')
                                # Update currentField for the next iteration
                                # currentField -= deltaH
                                self.pts += 1  # Number of self.pts count
                                single_measurement_end = time.time()
                                Single_loop = single_measurement_end - single_measurement_start
                                number_of_field_update = number_of_field_update - 1
                                append_text('Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop),
                                            'purple')
                                append_text('Estimated Single measurement (in hrs):  {} hrs \n'.format(
                                    Single_loop * number_of_field / 60 / 60), 'purple')
                                total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                        number_of_temp - i)
                                totoal_time_in_minutes = total_time_in_seconds / 60
                                total_time_in_hours = totoal_time_in_minutes / 60
                                total_time_in_days = total_time_in_hours / 24
                                append_text('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                    total_time_in_seconds), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                        totoal_time_in_minutes), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                        total_time_in_hours), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                        total_time_in_days), 'purple')
                                total_estimated_experiment_time_in_seconds = Single_loop * (number_of_field) * (
                                    number_of_current) * (number_of_temp)
                                current_progress = (total_estimated_experiment_time_in_seconds - total_time_in_seconds) / total_estimated_experiment_time_in_seconds
                                progress_update(int(current_progress * 100))
                                update_measurement_progress(total_time_in_days, total_time_in_hours,
                                                            totoal_time_in_minutes, current_progress * 100)

                            # ----------------- Loop Up ----------------------#
                            NotificationManager().send_message(f"Starting the second half of measurement - ramping field up")
                            currentField = botField
                            set_field(currentField, user_field_rate)
                            append_text(f'Start collecting data \n', 'Purple')
                            time.sleep(4)
                            currentField, sF, field_unit = read_field()
                            update_ppms_field_reading_label(str(currentField), field_unit, sF)

                            while True:
                                time.sleep(1)
                                currentField, sF, field_unit = read_field()
                                update_ppms_field_reading_label(str(currentField), field_unit, sF)
                                append_text(f'Status: {sF}\n', 'blue')
                                if sF == 'Holding (driven)':
                                    break

                            deltaH, user_field_rate = deltaH_chk(currentField)
                            time.sleep(20)
                            set_field(topField, user_field_rate)
                            append_text(f'Start collecting data \n', 'purple')
                            counter = 0
                            current_progress = int((i + 1) * (j + 1) / totoal_progress * 100)/2
                            progress_update(int(current_progress))
                            while currentField <= topField - 1:
                                if not running():
                                    print('Not Running')
                                    stop_measurement()
                                    return
                                counter += 1
                                single_measurement_start = time.time()
                                if Keithley_2182_Connected:
                                    keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                                    keithley_2182nv.write(f"VOLT:DC:NPLC {nv_NPLC}")
                                time.sleep(1)
                                currentField, sF, field_unit = read_field()
                                update_ppms_field_reading_label(str(currentField), field_unit, sF)
                                append_text(f'Saving data for {currentField} {field_unit} \n', 'green')

                                Chan_1_voltage = 0
                                Chan_2_voltage = 0
                                self.field_array.append(currentField)
                                if Keithley_2182_Connected:
                                    if nv_channel_1_enabled:
                                        keithley_2182nv.write("SENS:CHAN 1")
                                        volt = keithley_2182nv.query("READ?")
                                        Chan_1_voltage = float(volt)
                                        update_nv_channel_1_label(str(Chan_1_voltage))
                                        append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                        self.channel1_array.append(Chan_1_voltage)
                                        if counter % 20 == 0:
                                            counter = 0
                                            update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                    if nv_channel_2_enabled:
                                        keithley_2182nv.write("SENS:CHAN 2")
                                        volt2 = keithley_2182nv.query("READ?")
                                        Chan_2_voltage = float(volt2)
                                        update_nv_channel_2_label(str(Chan_2_voltage))
                                        append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                        self.channel2_array.append(Chan_2_voltage)
                                        if counter % 20 == 0:
                                            counter = 0
                                        # # Drop off the first y element, append a new one.
                                            update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                                    resistance_chan_2 = Chan_2_voltage / float(current[j])
                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                                      "Resistance ("
                                                                                                                      "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow([currentField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                                             Chan_2_voltage, MyTemp, current[j]])
                                        self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')
                                elif DSP7265_Connected:
                                    try:
                                        time.sleep(delay)
                                        X = float(DSP7265.query("X."))  # Read the measurement result
                                        Y = float(DSP7265.query("Y."))  # Read the measurement result
                                        Mag = float(DSP7265.query("MAG."))  # Read the measurement result
                                        Phase = float(DSP7265.query("PHA."))  # Read the measurement result
                                        update_lockin_label(str(X), str(Y), str(Mag), str(Phase))
                                        self.lockin_x.append(X)
                                        # self.lockin_y.append(Y)
                                        self.lockin_mag.append(Mag)
                                        # self.lockin_pahse.append(Phase)
                                        if counter % 20 == 0:
                                            counter = 0
                                        # # Drop off the first y element, append a new one.
                                            update_plot(self.field_array, self.lockin_x, 'black', True, False)
                                            # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                    except Exception as e:
                                        QMessageBox.warning(self, "Reading Error", f'{e}')

                                    resistance_chan_1 = Mag / float(current[j])
                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Resistance (Ohm)", "Voltage Mag (V)",
                                                 "Voltage X (V)","Voltage Y (V)", "Phase (deg)",
                                                 "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [currentField, resistance_chan_1, Mag, X, Y,
                                             Phase, MyTemp, current[j]])
                                        self.log_box.append(f'Data Saved for {currentField} Oe at {MyTemp} K\n')

                                # ----------------------------- Measure NV voltage -------------------
                                deltaH, user_field_rate = deltaH_chk(currentField)

                                append_text(f'Field Rate = {user_field_rate}\n', 'orange')
                                # Update currentField for the next iteration
                                # Update currentField for the next iteration
                                self.pts += 1  # Number of self.pts count
                                single_measurement_end = time.time()
                                Single_loop = single_measurement_end - single_measurement_start
                                number_of_field_update = number_of_field_update - 1

                                total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                                        number_of_temp - i)
                                totoal_time_in_minutes = total_time_in_seconds / 60
                                total_time_in_hours = totoal_time_in_minutes / 60
                                total_time_in_days = total_time_in_hours / 24
                                append_text('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                    total_time_in_seconds), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                        totoal_time_in_minutes), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                        total_time_in_hours), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                        total_time_in_days), 'purple')
                                total_estimated_experiment_time_in_seconds = Single_loop * (number_of_field) * (
                                    number_of_current) * (number_of_temp)
                                current_progress = (total_estimated_experiment_time_in_seconds - total_time_in_seconds) / total_estimated_experiment_time_in_seconds
                                progress_update(int(current_progress * 100))
                                update_measurement_progress(total_time_in_days, total_time_in_hours,
                                                            totoal_time_in_minutes, current_progress * 100)
                        if Keithley_2182_Connected:
                            if field_mode_fixed:
                                if nv_channel_1_enabled:
                                    save_plot(self.channel1_field_avg_array, self.channel1_avg_array, 'black', True, False, True,
                                              str(TempList[i]), str(current[j]))
                                if nv_channel_2_enabled:
                                    save_plot(self.channel2_field_avg_array, self.channel2_avg_array, 'red', False, True, True,
                                              str(TempList[i]), str(current[j]))
                            else:
                                if nv_channel_1_enabled:
                                   save_plot(self.field_array, self.channel1_array, 'black', True, False, True, str(TempList[i]), str(current[j]))
                                if nv_channel_2_enabled:
                                   save_plot(self.field_array, self.channel2_array, 'red', False, True, True, str(TempList[i]), str(current[j]))
                        elif DSP7265_Connected:
                            save_plot(self.field_array, self.lockin_x, 'black', True, False, True, str(TempList[i]), str(current[j]))
                            # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)

                        # NotificationManager().send_message()
                        current_progress = int((i+1) * (j+1) / totoal_progress * 100)
                        progress_update(int(current_progress))
                time.sleep(2)
                client.set_field(zero_field,
                                 fast_field_rate,
                                 client.field.approach_mode.oscillate,  # linear/oscillate
                                 client.field.driven_mode.driven)
                append_text('Waiting for Zero Field', 'red')
                time.sleep(2)
                temperature, status, temp_unit = read_temperature()
                append_text(f'Finished Temperature = {temperature} {temp_unit}', 'green')
                update_ppms_temp_reading_label(str(temperature), str(temp_unit), status)
                time.sleep(2)
                field, status, field_unit = read_field()
                append_text(f'Finisehd Field = {field} {field_unit}\n', 'red')
                update_ppms_field_reading_label(str(field), field_unit, status)
                if Ketihley_6221_Connected:
                    if keithley_6221_dc_config:
                        keithley_6221.write(":SOR:CURR:LEV 0")  # Set current level to zero
                        keithley_6221.write(":OUTP OFF")  # Turn off the output
                        update_keithley_6221_update_label('N/A', "OFF")
                    if keithley_6221_ac_config:
                        keithley_6221.write("SOUR:WAVE:ABOR \n")
                        keithley_6221.write(f'SOUR:WAVE:AMPL 0 \n')
                        keithley_6221.write(f'SOUR:WAVE:FREQ 0 \n')
                        keithley_6221.write(f'SOUR:WAVE:OFFset 0 \n')
                        update_keithley_6221_update_label('N/A', "OFF")
                append_text("AC and DC current is set to: 0.00 A\n", 'red')
                # keithley_6221_Curr_Src.close()

                # Calculate the total runtime
                end_time = time.time()
                total_runtime = (end_time - start_time) / 3600
                self.log_box.append(f"Total runtime: {total_runtime} hours\n")
                self.log_box.append(f'Total data points: {str(self.pts)} pts\n')
                NotificationManager().send_message("The measurement has been completed successfully.")
                progress_update(int(100))
                append_text("You measurement is finished!", 'green')
                # stop_measurement()
                measurement_finished()
                return
            else:
                update_ppms_chamber_reading_label('Stable')
                for i in range(templen):
                    append_text(f'Waiting for 0 Oe Field for Temperature... \n', 'orange')
                    time.sleep(10)
                    append_text(f'Loop is at {str(TempList[i])} K Temperature\n', 'blue')
                    temp_set_point = TempList[i]
                    set_temperature(temp_set_point, 20)
                    append_text(f'Waiting for {temp_set_point} K Temperature\n', 'red')
                    time.sleep(4)
                    update_ppms_temp_reading_label(str(temp_set_point), 'K', 'chasing')
                    append_text(f'Temperature Status: Stable\n', 'blue')

                    if i == 0:
                        append_text(f'Stabilizing the Temperature....', 'orange')
                        time.sleep(60)

                    else:
                        append_text(f'Stabilizing the Temperature.....', 'orange')
                        time.sleep(300)

                    for j in range(Curlen):
                        NotificationManager().send_message(
                                f"Starting measurement at temperature {str(TempList[i])} K, {current_mag[j]} {current_unit}")
                        clear_plot()

                        append_text(f'Waiting for {topField} Oe Field... \n', 'blue')
                        time.sleep(10)
                        update_ppms_field_reading_label(str(topField), 'Oe', 'Chasing')
                        append_text(f'Status: Holding (driven)\n', 'red')
                        time.sleep(5)
                        append_text(f'Waiting for 0 Oe Field for Demagnetization... \n', 'blue')
                        time.sleep(10)

                        update_ppms_field_reading_label('0', 'Oe', 'Chasing')
                        append_text(f'Status: Holding (driven)\n', 'red')
                        time.sleep(5)
                        append_text(f'DC current is set to: {str(current_mag[j])} {str(current_unit)}', 'blue')

                        csv_filename = f"{folder_path}{file_name}_{TempList[i]}_K_{current_mag[j]}_{current_unit}_Run_{run}.csv"
                        self.pts = 0
                        currentField = topField
                        deltaH, user_field_rate = deltaH_chk(currentField)
                        number_of_field_update = number_of_field
                        self.field_array = []
                        self.channel1_array = []
                        self.channel2_array = []
                        self.lockin_x = []
                        self.lockin_y = []
                        self.lockin_mag = []
                        self.lockin_pahse = []

                        if field_mode_fixed:
                            while currentField >= botField:
                                if not running():
                                    stop_measurement()
                                    return
                                single_measurement_start = time.time()
                                append_text(f'Loop is at {currentField} Oe Field Up \n', 'blue')
                                field_set_point = currentField
                                append_text(f'Set the field to {field_set_point} Oe and then collect data \n', 'blue')
                                time.sleep(1)
                                append_text(f'Waiting for {field_set_point} Oe Field \n', 'red')
                                time.sleep(4)
                                sF = 'Holding (driven)'
                                append_text(f'Status: {sF}\n', 'blue')

                                # ----------------------------- Measure NV voltage -------------------
                                append_text(f'Saving data for {currentField} Oe \n', 'green')

                                time.sleep(2)  # Wait for the configuration to complete
                                Chan_1_voltage = 0
                                Chan_2_voltage = 0
                                update_ppms_field_reading_label(str(currentField), 'Oe', sF)
                                self.field_array.append(currentField)
                                if Keithley_2182_Connected:
                                    try:
                                        if nv_channel_1_enabled:
                                            volt = random.randint(0, 1000) / 1000
                                            Chan_1_voltage = float(volt)
                                            update_nv_channel_1_label(str(Chan_1_voltage))
                                            append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')

                                            self.channel1_array.append(Chan_1_voltage)
                                            # # Drop off the first y element, append a new one.
                                            update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                    except Exception as e:
                                        QMessageBox.warning(self, 'Warning', str(e))

                                    if nv_channel_2_enabled:
                                        volt2 = random.randint(0, 1000) / 1000
                                        Chan_2_voltage = float(volt2)
                                        update_nv_channel_2_label(str(Chan_2_voltage))
                                        append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                        self.channel2_array.append(Chan_2_voltage)
                                        # # Drop off the first y element, append a new one.
                                        update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                    # Calculate the average voltage
                                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                                    resistance_chan_2 = Chan_2_voltage / float(current[j])

                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)",
                                                 "Channel 2 "
                                                 "Resistance ("
                                                 "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [currentField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                             Chan_2_voltage, temp_set_point, current[j]])
                                        append_text(f'Data Saved for {currentField} Oe at {temp_set_point} K', 'green')



                                # ----------------------------- Measure NV voltage -------------------
                                deltaH, user_field_rate = deltaH_chk(currentField)

                                append_text(f'deltaH = {deltaH}\n', 'orange')
                                # Update currentField for the next iteration
                                currentField -= deltaH
                                self.pts += 1  # Number of self.pts count
                                single_measurement_end = time.time()
                                Single_loop = single_measurement_end - single_measurement_start
                                number_of_field_update = number_of_field_update - 1
                                append_text(
                                    'Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop),
                                    'purple')
                                append_text('Estimated Single measurement (in hrs):  {} hrs \n'.format(
                                    Single_loop * number_of_field / 60 / 60), 'purple')
                                total_time_in_seconds = Single_loop * (number_of_field_update) * (
                                            number_of_current - j) * (
                                                                number_of_temp - i)
                                totoal_time_in_minutes = total_time_in_seconds / 60
                                total_time_in_hours = totoal_time_in_minutes / 60
                                total_time_in_days = total_time_in_hours / 24
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                        total_time_in_seconds), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                        totoal_time_in_minutes), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                        total_time_in_hours), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                        total_time_in_days), 'purple')
                                total_estimated_experiment_time_in_hours = Single_loop * (number_of_field_update) * (
                                    number_of_current) * (number_of_temp) / 3600
                                current_progress = total_time_in_hours / total_estimated_experiment_time_in_hours
                                progress_update(int(current_progress * 100))
                                update_measurement_progress(total_time_in_days, total_time_in_hours,
                                                            totoal_time_in_minutes, current_progress * 100)

                            # ----------------- Loop Up ----------------------#
                            currentField = botField
                            deltaH, user_field_rate = deltaH_chk(currentField)
                            NotificationManager().send_message(
                                    f"Starting the second half of measurement - ramping field up")
                            current_progress = int((i + 1) * (j + 1) / totoal_progress * 100) / 2
                            progress_update(int(current_progress))
                            while currentField <= topField:

                                single_measurement_start = time.time()
                                append_text(f'\n Loop is at {currentField} Oe Field Up \n', 'blue')
                                field_set_point = currentField

                                append_text(f'Set the field to {field_set_point} Oe and then collect data \n', 'greem')
                                time.sleep(1)

                                append_text(f'Waiting for {field_set_point} Oe Field \n', 'red')
                                time.sleep(4)

                                append_text(f'Status: {sF}\n', 'blue')


                                # ----------------------------- Measure NV voltage -------------------
                                append_text(f'Saving data for {currentField} Oe \n', 'green')
                                Chan_1_voltage = 0
                                Chan_2_voltage = 0

                                time.sleep(2)  # Wait for the configuration to complete

                                update_ppms_field_reading_label(str(currentField), 'Oe', 'Holding')
                                self.field_array.append(currentField)
                                if Keithley_2182_Connected:
                                    if nv_channel_1_enabled:
                                        volt = random.randint(0, 1000) / 1000
                                        Chan_1_voltage = float(volt)
                                        update_nv_channel_1_label(str(Chan_1_voltage))
                                        append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                        self.channel1_array.append(Chan_1_voltage)
                                        update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                    if nv_channel_2_enabled:
                                        volt2 = random.randint(0, 1000) / 1000
                                        Chan_2_voltage = float(volt2)
                                        update_nv_channel_2_label(str(Chan_2_voltage))
                                        append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                        self.channel2_array.append(Chan_2_voltage)
                                        # # Drop off the first y element, append a new one.
                                        update_plot(self.field_array, self.channel2_array, 'red', False, True)
                                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                                    resistance_chan_2 = Chan_2_voltage / float(current[j])

                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)",
                                                 "Channel 2 "
                                                 "Resistance ("
                                                 "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [currentField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                             Chan_2_voltage, temp_set_point, current[j]])
                                        self.log_box.append(f'Data Saved for {currentField} Oe at {temp_set_point} K\n')

                                # ----------------------------- Measure NV voltage -------------------
                                deltaH, user_field_rate = deltaH_chk(currentField)

                                append_text(f'deltaH = {deltaH}\n', 'orange')
                                # Update currentField for the next iteration
                                currentField += deltaH
                                self.pts += 1  # Number of self.pts count
                                single_measurement_end = time.time()
                                Single_loop = single_measurement_end - single_measurement_start
                                number_of_field_update = number_of_field_update - 1
                                total_time_in_seconds = Single_loop * (number_of_field_update) * (
                                            number_of_current - j) * (
                                                                number_of_temp - i)
                                totoal_time_in_minutes = total_time_in_seconds / 60
                                total_time_in_hours = totoal_time_in_minutes / 60
                                total_time_in_days = total_time_in_hours / 24
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                        total_time_in_seconds), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                        totoal_time_in_minutes), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                        total_time_in_hours), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                        total_time_in_days), 'purple')
                                total_estimated_experiment_time_in_hours = Single_loop * (number_of_field_update) * (
                                    number_of_current) * (number_of_temp) / 3600
                                current_progress =  total_time_in_hours / total_estimated_experiment_time_in_hours
                                progress_update(int(current_progress * 100))
                                update_measurement_progress(total_time_in_days, total_time_in_hours,
                                                            totoal_time_in_minutes, current_progress * 100)
                        else:

                            append_text(f'Waiting for {topField} Oe Field... \n', 'blue')
                            time.sleep(4)


                            time.sleep(20)
                            deltaH, user_field_rate = deltaH_chk(currentField)
                            currentField = currentField
                            append_text(f'Set the field to {str(botField)} Oe and then collect data \n', 'purple')
                            counter = 0
                            while currentField >= botField:

                                counter += 1
                                single_measurement_start = time.time()
                                if Keithley_2182_Connected:
                                    NPLC = nv_NPLC

                                time.sleep(1)
                                currentField, sF, field_unit = read_field()
                                update_ppms_field_reading_label(str(currentField), 'Oe', sF)
                                append_text(f'Saving data for {currentField} Oe \n', 'green')

                                Chan_1_voltage = 0
                                Chan_2_voltage = 0
                                self.field_array.append(currentField)
                                if Keithley_2182_Connected:
                                    if nv_channel_1_enabled:
                                        volt = random.randint(0, 1000) / 1000
                                        Chan_1_voltage = float(volt)
                                        update_nv_channel_1_label(str(Chan_1_voltage))
                                        append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                        self.channel1_array.append(Chan_1_voltage)
                                        if counter % 20 == 0:
                                            counter = 0
                                            update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                    if nv_channel_2_enabled:
                                        volt2 = random.randint(0, 1000) / 1000
                                        Chan_2_voltage = float(volt2)
                                        update_nv_channel_2_label(str(Chan_2_voltage))
                                        append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                        self.channel2_array.append(Chan_2_voltage)
                                        # # Drop off the first y element, append a new one.
                                        if counter % 20 == 0:
                                            counter = 0
                                            update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                    # Calculate the average voltage
                                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                                    resistance_chan_2 = Chan_2_voltage / float(current[j])

                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)",
                                                 "Channel 2 "
                                                 "Resistance ("
                                                 "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [currentField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                             Chan_2_voltage, temp_set_point, current[j]])
                                        append_text(f'Data Saved for {currentField} Oe at {temp_set_point} K', 'green')

                                # ----------------------------- Measure NV voltage -------------------
                                deltaH, user_field_rate = deltaH_chk(currentField)

                                append_text(f'Field Rate = {user_field_rate}\n', 'orange')
                                # Update currentField for the next iteration
                                # currentField -= deltaH
                                self.pts += 1  # Number of self.pts count
                                single_measurement_end = time.time()
                                Single_loop = single_measurement_end - single_measurement_start
                                number_of_field_update = number_of_field_update - 1
                                append_text(
                                    'Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop),
                                    'purple')
                                append_text('Estimated Single measurement (in hrs):  {} hrs \n'.format(
                                    Single_loop * number_of_field / 60 / 60), 'purple')
                                total_time_in_seconds = Single_loop * (number_of_field_update) * (
                                            number_of_current - j) * (
                                                                number_of_temp - i)
                                totoal_time_in_minutes = total_time_in_seconds / 60
                                total_time_in_hours = totoal_time_in_minutes / 60
                                total_time_in_days = total_time_in_hours / 24
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                        total_time_in_seconds), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                        totoal_time_in_minutes), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                        total_time_in_hours), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                        total_time_in_days), 'purple')
                                total_estimated_experiment_time_in_hours = Single_loop * (number_of_field_update) * (
                                    number_of_current) * (number_of_temp) / 3600
                                current_progress =  total_time_in_hours / total_estimated_experiment_time_in_hours
                                progress_update(int(current_progress * 100))
                                update_measurement_progress(total_time_in_days, total_time_in_hours,
                                                            totoal_time_in_minutes, current_progress * 100)

                            # ----------------- Loop Up ----------------------#

                            currentField = botField

                            append_text(f'Set the field to {currentField} Oe and then collect data \n', 'greem')
                            time.sleep(4)


                            deltaH, user_field_rate = deltaH_chk(currentField)
                            time.sleep(20)

                            append_text(f'Set the field to {str(botField)} Oe and then collect data \n', 'purple')
                            counter = 0
                            current_progress = int((i + 1) * (j + 1) / totoal_progress * 100) / 2
                            progress_update(int(current_progress))
                            while currentField <= topField:

                                counter += 1
                                single_measurement_start = time.time()

                                time.sleep(1)

                                update_ppms_field_reading_label(str(currentField), 'Oe', 'Holding')
                                append_text(f'Saving data for {currentField} Oe \n', 'green')

                                Chan_1_voltage = 0
                                Chan_2_voltage = 0
                                self.field_array.append(currentField)
                                if Keithley_2182_Connected:
                                    if nv_channel_1_enabled:
                                        volt = random.randint(0, 1000) / 1000
                                        Chan_1_voltage = float(volt)
                                        update_nv_channel_1_label(str(Chan_1_voltage))
                                        append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                                        self.channel1_array.append(Chan_1_voltage)
                                        if counter % 20 == 0:
                                            counter = 0
                                            update_plot(self.field_array, self.channel1_array, 'black', True, False)
                                    if nv_channel_2_enabled:
                                        volt2 = random.randint(0, 1000) / 1000
                                        Chan_2_voltage = float(volt2)
                                        update_nv_channel_2_label(str(Chan_2_voltage))
                                        append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                                        self.channel2_array.append(Chan_2_voltage)
                                        if counter % 20 == 0:
                                            counter = 0
                                            # # Drop off the first y element, append a new one.
                                            update_plot(self.field_array, self.channel2_array, 'red', False, True)

                                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                                    resistance_chan_2 = Chan_2_voltage / float(current[j])
                                    # Append the data to the CSV file
                                    with open(csv_filename, "a", newline="") as csvfile:
                                        csv_writer = csv.writer(csvfile)

                                        if csvfile.tell() == 0:  # Check if file is empty
                                            csv_writer.writerow(
                                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)",
                                                 "Channel 2 "
                                                 "Resistance ("
                                                 "Ohm)",
                                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                                        csv_writer.writerow(
                                            [currentField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                             Chan_2_voltage, temp_set_point, current[j]])
                                        self.log_box.append(f'Data Saved for {currentField} Oe at {temp_set_point} K\n')


                                # ----------------------------- Measure NV voltage -------------------
                                deltaH, user_field_rate = deltaH_chk(currentField)

                                append_text(f'Field Rate = {user_field_rate}\n', 'orange')
                                # Update currentField for the next iteration
                                # Update currentField for the next iteration
                                self.pts += 1  # Number of self.pts count
                                single_measurement_end = time.time()
                                Single_loop = single_measurement_end - single_measurement_start
                                number_of_field_update = number_of_field_update - 1
                                total_time_in_seconds = Single_loop * (number_of_field_update) * (
                                            number_of_current - j) * (
                                                                number_of_temp - i)
                                totoal_time_in_minutes = total_time_in_seconds / 60
                                total_time_in_hours = totoal_time_in_minutes / 60
                                total_time_in_days = total_time_in_hours / 24
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                        total_time_in_seconds), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                        totoal_time_in_minutes), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                        total_time_in_hours), 'purple')
                                append_text(
                                    'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                        total_time_in_days), 'purple')
                                total_estimated_experiment_time_in_hours = Single_loop * (number_of_field_update) * (
                                    number_of_current) * (number_of_temp) / 3600
                                current_progress =  total_time_in_hours / total_estimated_experiment_time_in_hours
                                progress_update(int(current_progress * 100))
                                update_measurement_progress(total_time_in_days, total_time_in_hours,
                                                            totoal_time_in_minutes, current_progress * 100)
                        if Keithley_2182_Connected:
                            if nv_channel_1_enabled:
                                save_plot(self.field_array, self.channel1_array, 'black', True, False, True,
                                          str(TempList[i]), str(current[j]))
                            if nv_channel_2_enabled:
                                save_plot(self.field_array, self.channel2_array, 'red', False, True, True,
                                          str(TempList[i]), str(current[j]))

                        current_progress = int((i + 1) * (j + 1) / totoal_progress * 100)
                        progress_update(int(current_progress))

        except SystemExit as e:
            NotificationManager().send_message(
                "Your measurement went wrong, possible PPMS client lost connection", 'critical')
            error_message(e,e)
            stop_measurement()






# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     main_window = Measurement()
#     main_window.show()
#     sys.exit(app.exec())
