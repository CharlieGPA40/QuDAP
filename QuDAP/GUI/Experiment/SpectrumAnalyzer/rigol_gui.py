from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox,
                             QPushButton, QComboBox, QCheckBox, QLineEdit, QMessageBox, QScrollArea, QSizePolicy,
                             QDoubleSpinBox, QRadioButton, QButtonGroup, QTabWidget, QSpinBox)
from PyQt6.QtGui import QFont, QDoubleValidator, QIntValidator
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
import sys
import pyvisa as visa
import time
import numpy as np
import pyqtgraph as pg
import struct

# Import the standalone connection class and RIGOL commands
try:
    from instrument.instrument_connection import InstrumentConnection
    from instrument.rigol_spectrum_analyzer import RIGOL_COMMAND
except ImportError:
    from QuDAP.instrument.instrument_connection import InstrumentConnection
    from QuDAP.instrument.rigol_spectrum_analyzer import RIGOL_COMMAND


class ReadingThread(QThread):
    """Thread for continuous reading updates when connected"""

    reading_signal = pyqtSignal(dict)  # {center_freq, span, ref_level, rbw, vbw, sweep_time}
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, rigol_cmd, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.rigol_cmd = rigol_cmd
        self.should_stop = False

    def run(self):
        """Continuously read instrument parameters"""
        try:
            while not self.should_stop:
                try:
                    readings = {'center_freq': float(self.rigol_cmd.get_center_frequency(self.instrument).strip()),
                        'span': float(self.rigol_cmd.get_frequency_span(self.instrument).strip()),
                        'ref_level': float(self.rigol_cmd.get_reference_level(self.instrument).strip()),
                        'rbw': float(self.rigol_cmd.get_resolution_bandwidth(self.instrument).strip()),
                        'vbw': float(self.rigol_cmd.get_video_bandwidth(self.instrument).strip()),
                        'sweep_time': float(self.rigol_cmd.get_sweep_time(self.instrument).strip()),
                        'attenuation': float(self.rigol_cmd.get_attenuation(self.instrument).strip())}

                    self.reading_signal.emit(readings)
                    time.sleep(2)

                except Exception as e:
                    if not self.should_stop:
                        self.error_signal.emit(f"Reading error: {str(e)}")
                    break

        except Exception as e:
            self.error_signal.emit(f"Thread error: {str(e)}")

    def stop(self):
        """Stop reading"""
        self.should_stop = True


class EmulationThread(QThread):
    """Thread for emulation mode readings"""

    reading_signal = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.should_stop = False

    def run(self):
        """Generate emulated readings"""
        while not self.should_stop:
            readings = {'center_freq': 2.4e9 + np.random.randn() * 1e6, 'span': 100e6, 'ref_level': 0.0, 'rbw': 100e3,
                'vbw': 100e3, 'sweep_time': 0.1, 'attenuation': 10.0}
            self.reading_signal.emit(readings)
            time.sleep(2)

    def stop(self):
        """Stop emulation"""
        self.should_stop = True


class TraceMonitorThread(QThread):
    """Thread for monitoring and plotting trace data"""

    trace_signal = pyqtSignal(np.ndarray, np.ndarray)  # (frequencies, amplitudes)
    error_signal = pyqtSignal(str)

    def __init__(self, instrument, rigol_cmd, is_emulation=False, parent=None):
        super().__init__(parent)
        self.instrument = instrument
        self.rigol_cmd = rigol_cmd
        self.is_emulation = is_emulation
        self.should_stop = False

    def run(self):
        """Monitor trace data for plotting"""
        try:
            while not self.should_stop:
                try:
                    if self.is_emulation:
                        # Generate simulated trace
                        num_points = 601
                        frequencies = np.linspace(2.35e9, 2.45e9, num_points)
                        # Generate realistic spectrum with peaks
                        amplitudes = -80 + np.random.randn(num_points) * 5
                        # Add some peaks
                        peak_freqs = [2.38e9, 2.41e9, 2.44e9]
                        for pf in peak_freqs:
                            idx = np.argmin(np.abs(frequencies - pf))
                            amplitudes[idx - 10:idx + 10] += 40 * np.exp(-0.1 * np.arange(-10, 10) ** 2)
                    else:
                        # Read actual trace data
                        trace_data = self.rigol_cmd.get_trace_data(self.instrument, 'TRACE1')

                        # Get frequency parameters
                        center = float(self.rigol_cmd.get_center_frequency(self.instrument).strip())
                        span = float(self.rigol_cmd.get_frequency_span(self.instrument).strip())
                        start_freq = center - span / 2
                        stop_freq = center + span / 2

                        num_points = len(trace_data)
                        frequencies = np.linspace(start_freq, stop_freq, num_points)
                        amplitudes = np.array(trace_data)

                    self.trace_signal.emit(frequencies, amplitudes)
                    time.sleep(0.5)  # Update every 500ms

                except Exception as e:
                    if not self.should_stop:
                        self.error_signal.emit(f"Trace monitor error: {str(e)}")
                    break

        except Exception as e:
            self.error_signal.emit(f"Monitor thread error: {str(e)}")

    def stop(self):
        """Stop monitoring"""
        self.should_stop = True


class RigolDSA800(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RIGOL DSA800 Spectrum Analyzer")
        self.setGeometry(100, 100, 1600, 900)

        self.rigol = None
        self.rigol_cmd = RIGOL_COMMAND()
        self.reading_thread = None
        self.trace_monitor_thread = None
        self.emulation_thread = None
        self.isConnect = False

        self.font = QFont("Arial", 10)
        self.titlefont = QFont("Arial", 14)
        self.titlefont.setBold(True)

        # Load scrollbar stylesheet
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

        self.init_ui()

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
        self.scroll_area.setFixedWidth(700)

        left_content = QWidget()
        left_content.setMaximumWidth(680)

        self.left_layout = QVBoxLayout()
        self.left_layout.setContentsMargins(10, 10, 10, 10)
        self.left_layout.setSpacing(10)

        # Title
        title = QLabel("RIGOL DSA800 Spectrum Analyzer")
        title.setFont(self.titlefont)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.left_layout.addWidget(title)

        # Setup sections
        self.setup_connection_section(self.left_layout)
        self.setup_readings_section(self.left_layout)
        self.setup_frequency_control_section(self.left_layout)
        self.setup_amplitude_control_section(self.left_layout)
        self.setup_bandwidth_control_section(self.left_layout)
        self.setup_sweep_control_section(self.left_layout)
        self.setup_marker_control_section(self.left_layout)
        self.setup_trace_control_section(self.left_layout)
        self.setup_monitor_section(self.left_layout)

        self.left_layout.addStretch()

        left_content.setLayout(self.left_layout)
        self.scroll_area.setWidget(left_content)

        main_layout.addWidget(self.scroll_area)

        # Right panel with plot
        self.setup_plot_panel(main_layout)

        central_widget.setLayout(main_layout)

    def setup_connection_section(self, parent_layout):
        """Setup device connection section"""
        self.connection_widget = InstrumentConnection(instrument_list=["RIGOL DSA800"], allow_emulation=True,
            title="Instrument Connection")
        self.connection_widget.instrument_connected.connect(self.on_instrument_connected)
        self.connection_widget.instrument_disconnected.connect(self.on_instrument_disconnected)
        parent_layout.addWidget(self.connection_widget)

    def setup_readings_section(self, parent_layout):
        """Setup current readings section"""
        readings_group = QGroupBox("Current Settings")
        readings_layout = QVBoxLayout()

        # Center Frequency
        cf_layout = QHBoxLayout()
        cf_label = QLabel("Center Freq:")
        cf_label.setFont(self.font)
        cf_label.setFixedWidth(120)
        self.cf_reading = QLabel("N/A")
        self.cf_reading.setFont(self.font)
        cf_layout.addWidget(cf_label)
        cf_layout.addWidget(self.cf_reading, 1)
        readings_layout.addLayout(cf_layout)

        # Span
        span_layout = QHBoxLayout()
        span_label = QLabel("Span:")
        span_label.setFont(self.font)
        span_label.setFixedWidth(120)
        self.span_reading = QLabel("N/A")
        self.span_reading.setFont(self.font)
        span_layout.addWidget(span_label)
        span_layout.addWidget(self.span_reading, 1)
        readings_layout.addLayout(span_layout)

        # Reference Level
        ref_layout = QHBoxLayout()
        ref_label = QLabel("Ref Level:")
        ref_label.setFont(self.font)
        ref_label.setFixedWidth(120)
        self.ref_reading = QLabel("N/A")
        self.ref_reading.setFont(self.font)
        ref_layout.addWidget(ref_label)
        ref_layout.addWidget(self.ref_reading, 1)
        readings_layout.addLayout(ref_layout)

        # RBW
        rbw_layout = QHBoxLayout()
        rbw_label = QLabel("RBW:")
        rbw_label.setFont(self.font)
        rbw_label.setFixedWidth(120)
        self.rbw_reading = QLabel("N/A")
        self.rbw_reading.setFont(self.font)
        rbw_layout.addWidget(rbw_label)
        rbw_layout.addWidget(self.rbw_reading, 1)
        readings_layout.addLayout(rbw_layout)

        # VBW
        vbw_layout = QHBoxLayout()
        vbw_label = QLabel("VBW:")
        vbw_label.setFont(self.font)
        vbw_label.setFixedWidth(120)
        self.vbw_reading = QLabel("N/A")
        self.vbw_reading.setFont(self.font)
        vbw_layout.addWidget(vbw_label)
        vbw_layout.addWidget(self.vbw_reading, 1)
        readings_layout.addLayout(vbw_layout)

        # Sweep Time
        sweep_layout = QHBoxLayout()
        sweep_label = QLabel("Sweep Time:")
        sweep_label.setFont(self.font)
        sweep_label.setFixedWidth(120)
        self.sweep_reading = QLabel("N/A")
        self.sweep_reading.setFont(self.font)
        sweep_layout.addWidget(sweep_label)
        sweep_layout.addWidget(self.sweep_reading, 1)
        readings_layout.addLayout(sweep_layout)

        # Attenuation
        atten_layout = QHBoxLayout()
        atten_label = QLabel("Attenuation:")
        atten_label.setFont(self.font)
        atten_label.setFixedWidth(120)
        self.atten_reading = QLabel("N/A")
        self.atten_reading.setFont(self.font)
        atten_layout.addWidget(atten_label)
        atten_layout.addWidget(self.atten_reading, 1)
        readings_layout.addLayout(atten_layout)

        readings_group.setLayout(readings_layout)
        parent_layout.addWidget(readings_group)

    def setup_frequency_control_section(self, parent_layout):
        """Setup frequency control section"""
        freq_group = QGroupBox("Frequency Control")
        freq_layout = QVBoxLayout()

        # Center Frequency
        cf_layout = QHBoxLayout()
        cf_label = QLabel("Center Freq:")
        cf_label.setFont(self.font)
        cf_label.setFixedWidth(100)
        self.cf_entry = QDoubleSpinBox()
        self.cf_entry.setFont(self.font)
        self.cf_entry.setRange(0, 7500)
        self.cf_entry.setDecimals(3)
        self.cf_entry.setValue(2400)
        self.cf_entry.setSuffix(" MHz")
        cf_layout.addWidget(cf_label)
        cf_layout.addWidget(self.cf_entry, 1)
        freq_layout.addLayout(cf_layout)

        # Span
        span_layout = QHBoxLayout()
        span_label = QLabel("Span:")
        span_label.setFont(self.font)
        span_label.setFixedWidth(100)
        self.span_entry = QDoubleSpinBox()
        self.span_entry.setFont(self.font)
        self.span_entry.setRange(0, 7500)
        self.span_entry.setDecimals(3)
        self.span_entry.setValue(100)
        self.span_entry.setSuffix(" MHz")
        span_layout.addWidget(span_label)
        span_layout.addWidget(self.span_entry, 1)
        freq_layout.addLayout(span_layout)

        # Apply button
        apply_freq_btn = QPushButton("Apply Frequency Settings")
        apply_freq_btn.setFont(self.font)
        apply_freq_btn.clicked.connect(self.apply_frequency_settings)
        apply_freq_btn.setMinimumHeight(30)
        apply_freq_btn.setEnabled(False)
        self.apply_freq_btn = apply_freq_btn
        freq_layout.addWidget(apply_freq_btn)

        # Quick controls
        quick_layout = QHBoxLayout()

        full_span_btn = QPushButton("Full Span")
        full_span_btn.setFont(self.font)
        full_span_btn.clicked.connect(self.set_full_span)
        full_span_btn.setEnabled(False)
        self.full_span_btn = full_span_btn

        zoom_in_btn = QPushButton("Zoom In")
        zoom_in_btn.setFont(self.font)
        zoom_in_btn.clicked.connect(self.zoom_in)
        zoom_in_btn.setEnabled(False)
        self.zoom_in_btn = zoom_in_btn

        zoom_out_btn = QPushButton("Zoom Out")
        zoom_out_btn.setFont(self.font)
        zoom_out_btn.clicked.connect(self.zoom_out)
        zoom_out_btn.setEnabled(False)
        self.zoom_out_btn = zoom_out_btn

        quick_layout.addWidget(full_span_btn)
        quick_layout.addWidget(zoom_in_btn)
        quick_layout.addWidget(zoom_out_btn)
        freq_layout.addLayout(quick_layout)

        freq_group.setLayout(freq_layout)
        parent_layout.addWidget(freq_group)

    def setup_amplitude_control_section(self, parent_layout):
        """Setup amplitude control section"""
        amp_group = QGroupBox("Amplitude Control")
        amp_layout = QVBoxLayout()

        # Reference Level
        ref_layout = QHBoxLayout()
        ref_label = QLabel("Ref Level:")
        ref_label.setFont(self.font)
        ref_label.setFixedWidth(100)
        self.ref_entry = QDoubleSpinBox()
        self.ref_entry.setFont(self.font)
        self.ref_entry.setRange(-100, 20)
        self.ref_entry.setDecimals(1)
        self.ref_entry.setValue(0)
        self.ref_entry.setSuffix(" dBm")
        ref_layout.addWidget(ref_label)
        ref_layout.addWidget(self.ref_entry, 1)
        amp_layout.addLayout(ref_layout)

        # Attenuation
        atten_layout = QHBoxLayout()
        atten_label = QLabel("Attenuation:")
        atten_label.setFont(self.font)
        atten_label.setFixedWidth(100)
        self.atten_spin = QSpinBox()
        self.atten_spin.setFont(self.font)
        self.atten_spin.setRange(0, 30)
        self.atten_spin.setValue(10)
        self.atten_spin.setSuffix(" dB")
        atten_layout.addWidget(atten_label)
        atten_layout.addWidget(self.atten_spin, 1)
        amp_layout.addLayout(atten_layout)

        # Auto Attenuation
        self.auto_atten_checkbox = QCheckBox("Auto Attenuation")
        self.auto_atten_checkbox.setFont(self.font)
        self.auto_atten_checkbox.setChecked(True)
        amp_layout.addWidget(self.auto_atten_checkbox)

        # Apply button
        apply_amp_btn = QPushButton("Apply Amplitude Settings")
        apply_amp_btn.setFont(self.font)
        apply_amp_btn.clicked.connect(self.apply_amplitude_settings)
        apply_amp_btn.setMinimumHeight(30)
        apply_amp_btn.setEnabled(False)
        self.apply_amp_btn = apply_amp_btn
        amp_layout.addWidget(apply_amp_btn)

        # Auto functions
        auto_layout = QHBoxLayout()

        auto_scale_btn = QPushButton("Auto Scale")
        auto_scale_btn.setFont(self.font)
        auto_scale_btn.clicked.connect(self.auto_scale)
        auto_scale_btn.setEnabled(False)
        self.auto_scale_btn = auto_scale_btn

        auto_tune_btn = QPushButton("Auto Tune")
        auto_tune_btn.setFont(self.font)
        auto_tune_btn.clicked.connect(self.auto_tune)
        auto_tune_btn.setEnabled(False)
        self.auto_tune_btn = auto_tune_btn

        auto_layout.addWidget(auto_scale_btn)
        auto_layout.addWidget(auto_tune_btn)
        amp_layout.addLayout(auto_layout)

        amp_group.setLayout(amp_layout)
        parent_layout.addWidget(amp_group)

    def setup_bandwidth_control_section(self, parent_layout):
        """Setup bandwidth control section"""
        bw_group = QGroupBox("Bandwidth Control")
        bw_layout = QVBoxLayout()

        # RBW
        rbw_layout = QHBoxLayout()
        rbw_label = QLabel("RBW:")
        rbw_label.setFont(self.font)
        rbw_label.setFixedWidth(100)
        self.rbw_entry = QDoubleSpinBox()
        self.rbw_entry.setFont(self.font)
        self.rbw_entry.setRange(10, 1000)
        self.rbw_entry.setDecimals(1)
        self.rbw_entry.setValue(100)
        self.rbw_entry.setSuffix(" kHz")
        rbw_layout.addWidget(rbw_label)
        rbw_layout.addWidget(self.rbw_entry, 1)
        bw_layout.addLayout(rbw_layout)

        # Auto RBW
        self.auto_rbw_checkbox = QCheckBox("Auto RBW")
        self.auto_rbw_checkbox.setFont(self.font)
        self.auto_rbw_checkbox.setChecked(True)
        bw_layout.addWidget(self.auto_rbw_checkbox)

        # VBW
        vbw_layout = QHBoxLayout()
        vbw_label = QLabel("VBW:")
        vbw_label.setFont(self.font)
        vbw_label.setFixedWidth(100)
        self.vbw_entry = QDoubleSpinBox()
        self.vbw_entry.setFont(self.font)
        self.vbw_entry.setRange(1, 3000)
        self.vbw_entry.setDecimals(1)
        self.vbw_entry.setValue(100)
        self.vbw_entry.setSuffix(" kHz")
        vbw_layout.addWidget(vbw_label)
        vbw_layout.addWidget(self.vbw_entry, 1)
        bw_layout.addLayout(vbw_layout)

        # Auto VBW
        self.auto_vbw_checkbox = QCheckBox("Auto VBW")
        self.auto_vbw_checkbox.setFont(self.font)
        self.auto_vbw_checkbox.setChecked(True)
        bw_layout.addWidget(self.auto_vbw_checkbox)

        # Apply button
        apply_bw_btn = QPushButton("Apply Bandwidth Settings")
        apply_bw_btn.setFont(self.font)
        apply_bw_btn.clicked.connect(self.apply_bandwidth_settings)
        apply_bw_btn.setMinimumHeight(30)
        apply_bw_btn.setEnabled(False)
        self.apply_bw_btn = apply_bw_btn
        bw_layout.addWidget(apply_bw_btn)

        bw_group.setLayout(bw_layout)
        parent_layout.addWidget(bw_group)

    def setup_sweep_control_section(self, parent_layout):
        """Setup sweep control section"""
        sweep_group = QGroupBox("Sweep Control")
        sweep_layout = QVBoxLayout()

        # Continuous sweep
        self.continuous_sweep_checkbox = QCheckBox("Continuous Sweep")
        self.continuous_sweep_checkbox.setFont(self.font)
        self.continuous_sweep_checkbox.setChecked(True)
        self.continuous_sweep_checkbox.stateChanged.connect(self.set_continuous_sweep)
        sweep_layout.addWidget(self.continuous_sweep_checkbox)

        # Sweep buttons
        sweep_btn_layout = QHBoxLayout()

        single_sweep_btn = QPushButton("Single Sweep")
        single_sweep_btn.setFont(self.font)
        single_sweep_btn.clicked.connect(self.single_sweep)
        single_sweep_btn.setMinimumHeight(30)
        single_sweep_btn.setEnabled(False)
        self.single_sweep_btn = single_sweep_btn

        preset_btn = QPushButton("Preset")
        preset_btn.setFont(self.font)
        preset_btn.clicked.connect(self.preset_instrument)
        preset_btn.setMinimumHeight(30)
        preset_btn.setEnabled(False)
        self.preset_btn = preset_btn

        sweep_btn_layout.addWidget(single_sweep_btn)
        sweep_btn_layout.addWidget(preset_btn)
        sweep_layout.addLayout(sweep_btn_layout)

        sweep_group.setLayout(sweep_layout)
        parent_layout.addWidget(sweep_group)

    def setup_marker_control_section(self, parent_layout):
        """Setup marker control section"""
        marker_group = QGroupBox("Marker Control")
        marker_layout = QVBoxLayout()

        # Marker selection
        marker_sel_layout = QHBoxLayout()
        marker_label = QLabel("Marker:")
        marker_label.setFont(self.font)
        self.marker_combo = QComboBox()
        self.marker_combo.setFont(self.font)
        self.marker_combo.addItems(["Marker 1", "Marker 2", "Marker 3", "Marker 4"])
        marker_sel_layout.addWidget(marker_label)
        marker_sel_layout.addWidget(self.marker_combo, 1)
        marker_layout.addLayout(marker_sel_layout)

        # Marker enable
        self.marker_enable_checkbox = QCheckBox("Enable Selected Marker")
        self.marker_enable_checkbox.setFont(self.font)
        self.marker_enable_checkbox.stateChanged.connect(self.toggle_marker)
        marker_layout.addWidget(self.marker_enable_checkbox)

        # Marker functions
        marker_btn_layout1 = QHBoxLayout()

        peak_search_btn = QPushButton("Peak Search")
        peak_search_btn.setFont(self.font)
        peak_search_btn.clicked.connect(self.marker_peak_search)
        peak_search_btn.setEnabled(False)
        self.peak_search_btn = peak_search_btn

        next_peak_btn = QPushButton("Next Peak")
        next_peak_btn.setFont(self.font)
        next_peak_btn.clicked.connect(self.marker_next_peak)
        next_peak_btn.setEnabled(False)
        self.next_peak_btn = next_peak_btn

        marker_btn_layout1.addWidget(peak_search_btn)
        marker_btn_layout1.addWidget(next_peak_btn)
        marker_layout.addLayout(marker_btn_layout1)

        marker_btn_layout2 = QHBoxLayout()

        peak_to_center_btn = QPushButton("Peak → Center")
        peak_to_center_btn.setFont(self.font)
        peak_to_center_btn.clicked.connect(self.peak_to_center)
        peak_to_center_btn.setEnabled(False)
        self.peak_to_center_btn = peak_to_center_btn

        marker_off_btn = QPushButton("All Markers Off")
        marker_off_btn.setFont(self.font)
        marker_off_btn.clicked.connect(self.all_markers_off)
        marker_off_btn.setEnabled(False)
        self.marker_off_btn = marker_off_btn

        marker_btn_layout2.addWidget(peak_to_center_btn)
        marker_btn_layout2.addWidget(marker_off_btn)
        marker_layout.addLayout(marker_btn_layout2)

        marker_group.setLayout(marker_layout)
        parent_layout.addWidget(marker_group)

    def setup_trace_control_section(self, parent_layout):
        """Setup trace control section"""
        trace_group = QGroupBox("Trace Control")
        trace_layout = QVBoxLayout()

        # Trace mode
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Trace Mode:")
        mode_label.setFont(self.font)
        self.trace_mode_combo = QComboBox()
        self.trace_mode_combo.setFont(self.font)
        self.trace_mode_combo.addItems(["Write", "Max Hold", "Min Hold", "Average"])
        self.trace_mode_combo.currentTextChanged.connect(self.set_trace_mode)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.trace_mode_combo, 1)
        trace_layout.addLayout(mode_layout)

        # Average count (only visible when Average mode)
        self.avg_widget = QWidget()
        avg_layout = QHBoxLayout()
        avg_layout.setContentsMargins(0, 0, 0, 0)
        avg_label = QLabel("Avg Count:")
        avg_label.setFont(self.font)
        self.avg_count_spin = QSpinBox()
        self.avg_count_spin.setFont(self.font)
        self.avg_count_spin.setRange(1, 1000)
        self.avg_count_spin.setValue(10)
        avg_layout.addWidget(avg_label)
        avg_layout.addWidget(self.avg_count_spin, 1)
        self.avg_widget.setLayout(avg_layout)
        self.avg_widget.setVisible(False)
        trace_layout.addWidget(self.avg_widget)

        # Detector type
        det_layout = QHBoxLayout()
        det_label = QLabel("Detector:")
        det_label.setFont(self.font)
        self.detector_combo = QComboBox()
        self.detector_combo.setFont(self.font)
        self.detector_combo.addItems(["Positive", "Negative", "Normal", "Sample", "RMS", "Average", "QPeak"])
        self.detector_combo.currentTextChanged.connect(self.set_detector)
        det_layout.addWidget(det_label)
        det_layout.addWidget(self.detector_combo, 1)
        trace_layout.addLayout(det_layout)

        trace_group.setLayout(trace_layout)
        parent_layout.addWidget(trace_group)

    def setup_monitor_section(self, parent_layout):
        """Setup monitoring section"""
        monitor_group = QGroupBox("Real-time Monitoring")
        monitor_layout = QVBoxLayout()

        # Start/Stop monitoring
        monitor_btn_layout = QHBoxLayout()
        self.start_monitor_btn = QPushButton("Start Monitoring")
        self.start_monitor_btn.setFont(self.font)
        self.start_monitor_btn.clicked.connect(self.toggle_monitoring)
        self.start_monitor_btn.setMinimumHeight(35)
        self.start_monitor_btn.setEnabled(False)
        monitor_btn_layout.addWidget(self.start_monitor_btn)
        monitor_layout.addLayout(monitor_btn_layout)

        # Status label
        self.monitor_status_label = QLabel("Status: Not monitoring")
        self.monitor_status_label.setFont(self.font)
        monitor_layout.addWidget(self.monitor_status_label)

        monitor_group.setLayout(monitor_layout)
        parent_layout.addWidget(monitor_group)

    def setup_plot_panel(self, parent_layout):
        """Setup right panel with spectrum plot"""
        plot_widget = QWidget()
        plot_layout = QVBoxLayout()
        plot_layout.setContentsMargins(10, 10, 10, 10)

        # Plot title
        plot_title = QLabel("Spectrum Display")
        plot_title.setFont(self.titlefont)
        plot_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        plot_layout.addWidget(plot_title)

        # Create PyQtGraph plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        self.plot_widget.setLabel('left', 'Amplitude (dBm)')
        self.plot_widget.setLabel('bottom', 'Frequency (GHz)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()

        # Create plot curve
        self.spectrum_curve = self.plot_widget.plot(pen=pg.mkPen(color='b', width=2), name='Spectrum')

        plot_layout.addWidget(self.plot_widget)
        plot_widget.setLayout(plot_layout)
        parent_layout.addWidget(plot_widget)

    def on_instrument_connected(self, instrument, instrument_name):
        """Handle instrument connection"""
        self.rigol = instrument
        self.isConnect = True
        print(f"Connected to {instrument_name}")

        if self.rigol and self.rigol != 'Emulation':
            # Initialize instrument
            self.rigol_cmd.clear(self.rigol)

            # Start reading thread
            self.reading_thread = ReadingThread(self.rigol, self.rigol_cmd)
            self.reading_thread.reading_signal.connect(self.update_readings)
            self.reading_thread.error_signal.connect(self.on_reading_error)
            self.reading_thread.start()
        else:
            # Emulation mode
            self.emulation_thread = EmulationThread()
            self.emulation_thread.reading_signal.connect(self.update_readings)
            self.emulation_thread.start()

        # Enable controls
        self.apply_freq_btn.setEnabled(True)
        self.full_span_btn.setEnabled(True)
        self.zoom_in_btn.setEnabled(True)
        self.zoom_out_btn.setEnabled(True)
        self.apply_amp_btn.setEnabled(True)
        self.auto_scale_btn.setEnabled(True)
        self.auto_tune_btn.setEnabled(True)
        self.apply_bw_btn.setEnabled(True)
        self.single_sweep_btn.setEnabled(True)
        self.preset_btn.setEnabled(True)
        self.peak_search_btn.setEnabled(True)
        self.next_peak_btn.setEnabled(True)
        self.peak_to_center_btn.setEnabled(True)
        self.marker_off_btn.setEnabled(True)
        self.start_monitor_btn.setEnabled(True)

    def on_instrument_disconnected(self, instrument_name):
        """Handle instrument disconnection"""
        # Stop monitoring
        self.stop_monitoring()

        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()
            self.reading_thread = None

        if self.emulation_thread and self.emulation_thread.isRunning():
            self.emulation_thread.stop()
            self.emulation_thread.wait()
            self.emulation_thread = None

        self.rigol = None
        self.isConnect = False
        print(f"Disconnected from {instrument_name}")

        # Disable controls
        self.apply_freq_btn.setEnabled(False)
        self.full_span_btn.setEnabled(False)
        self.zoom_in_btn.setEnabled(False)
        self.zoom_out_btn.setEnabled(False)
        self.apply_amp_btn.setEnabled(False)
        self.auto_scale_btn.setEnabled(False)
        self.auto_tune_btn.setEnabled(False)
        self.apply_bw_btn.setEnabled(False)
        self.single_sweep_btn.setEnabled(False)
        self.preset_btn.setEnabled(False)
        self.peak_search_btn.setEnabled(False)
        self.next_peak_btn.setEnabled(False)
        self.peak_to_center_btn.setEnabled(False)
        self.marker_off_btn.setEnabled(False)
        self.start_monitor_btn.setEnabled(False)

        # Reset readings
        self.cf_reading.setText("N/A")
        self.span_reading.setText("N/A")
        self.ref_reading.setText("N/A")
        self.rbw_reading.setText("N/A")
        self.vbw_reading.setText("N/A")
        self.sweep_reading.setText("N/A")
        self.atten_reading.setText("N/A")

    def update_readings(self, readings):
        """Update reading labels"""
        self.cf_reading.setText(f"{readings['center_freq'] / 1e9:.3f} GHz")
        self.span_reading.setText(f"{readings['span'] / 1e6:.3f} MHz")
        self.ref_reading.setText(f"{readings['ref_level']:.1f} dBm")
        self.rbw_reading.setText(f"{readings['rbw'] / 1e3:.1f} kHz")
        self.vbw_reading.setText(f"{readings['vbw'] / 1e3:.1f} kHz")
        self.sweep_reading.setText(f"{readings['sweep_time']:.3f} s")
        self.atten_reading.setText(f"{readings['attenuation']:.0f} dB")

    def on_reading_error(self, error_msg):
        """Handle reading thread error"""
        print(f"Reading error: {error_msg}")

    def apply_frequency_settings(self):
        """Apply frequency settings"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        cf_mhz = self.cf_entry.value()
        span_mhz = self.span_entry.value()

        if self.rigol == 'Emulation':
            QMessageBox.information(self, "Emulation Mode",
                                    f"Frequency settings applied:\nCenter: {cf_mhz} MHz\nSpan: {span_mhz} MHz")
            return

        try:
            self.rigol_cmd.set_center_frequency(self.rigol, cf_mhz, 'MHz')
            time.sleep(0.05)
            self.rigol_cmd.set_frequency_span(self.rigol, span_mhz, 'MHz')

            QMessageBox.information(self, "Success",
                                    f"Frequency settings applied:\nCenter: {cf_mhz} MHz\nSpan: {span_mhz} MHz")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting frequency:\n{str(e)}")

    def set_full_span(self):
        """Set full span"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            self.span_entry.setValue(7500)
            return

        try:
            self.rigol_cmd.set_full_span(self.rigol)
            time.sleep(0.1)
            # Update reading
            if self.reading_thread:
                pass  # Thread will update automatically

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting full span:\n{str(e)}")

    def zoom_in(self):
        """Zoom in (span / 2)"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            current_span = self.span_entry.value()
            self.span_entry.setValue(current_span / 2)
            return

        try:
            self.rigol_cmd.zoom_in(self.rigol)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error zooming in:\n{str(e)}")

    def zoom_out(self):
        """Zoom out (span * 2)"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            current_span = self.span_entry.value()
            self.span_entry.setValue(min(current_span * 2, 7500))
            return

        try:
            self.rigol_cmd.zoom_out(self.rigol)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error zooming out:\n{str(e)}")

    def apply_amplitude_settings(self):
        """Apply amplitude settings"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        ref_level = self.ref_entry.value()
        attenuation = self.atten_spin.value()
        auto_atten = self.auto_atten_checkbox.isChecked()

        if self.rigol == 'Emulation':
            QMessageBox.information(self, "Emulation Mode",
                                    f"Amplitude settings applied:\nRef Level: {ref_level} dBm\nAttenuation: {attenuation} dB")
            return

        try:
            self.rigol_cmd.set_reference_level(self.rigol, ref_level, 'dBm')
            time.sleep(0.05)

            if auto_atten:
                self.rigol_cmd.set_attenuation_auto(self.rigol, 'ON')
            else:
                self.rigol_cmd.set_attenuation_auto(self.rigol, 'OFF')
                self.rigol_cmd.set_attenuation(self.rigol, attenuation)

            QMessageBox.information(self, "Success",
                                    f"Amplitude settings applied:\nRef Level: {ref_level} dBm\nAttenuation: {'Auto' if auto_atten else f'{attenuation} dB'}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting amplitude:\n{str(e)}")

    def auto_scale(self):
        """Auto scale amplitude"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Auto scale executed")
            return

        try:
            self.rigol_cmd.auto_scale(self.rigol)
            time.sleep(1)
            QMessageBox.information(self, "Success", "Auto scale completed")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in auto scale:\n{str(e)}")

    def auto_tune(self):
        """Auto tune to find signal"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Auto tune executed")
            return

        try:
            self.rigol_cmd.auto_tune(self.rigol)
            time.sleep(2)
            QMessageBox.information(self, "Success", "Auto tune completed")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in auto tune:\n{str(e)}")

    def apply_bandwidth_settings(self):
        """Apply bandwidth settings"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        rbw_khz = self.rbw_entry.value()
        vbw_khz = self.vbw_entry.value()
        auto_rbw = self.auto_rbw_checkbox.isChecked()
        auto_vbw = self.auto_vbw_checkbox.isChecked()

        if self.rigol == 'Emulation':
            QMessageBox.information(self, "Emulation Mode",
                                    f"Bandwidth settings applied:\nRBW: {rbw_khz} kHz\nVBW: {vbw_khz} kHz")
            return

        try:
            if auto_rbw:
                self.rigol_cmd.set_rbw_auto(self.rigol, 'ON')
            else:
                self.rigol_cmd.set_rbw_auto(self.rigol, 'OFF')
                self.rigol_cmd.set_resolution_bandwidth(self.rigol, rbw_khz, 'kHz')

            time.sleep(0.05)

            if auto_vbw:
                self.rigol_cmd.set_vbw_auto(self.rigol, 'ON')
            else:
                self.rigol_cmd.set_vbw_auto(self.rigol, 'OFF')
                self.rigol_cmd.set_video_bandwidth(self.rigol, vbw_khz, 'kHz')

            QMessageBox.information(self, "Success",
                                    f"Bandwidth settings applied:\nRBW: {'Auto' if auto_rbw else f'{rbw_khz} kHz'}\nVBW: {'Auto' if auto_vbw else f'{vbw_khz} kHz'}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting bandwidth:\n{str(e)}")

    def set_continuous_sweep(self):
        """Set continuous sweep mode"""
        if not self.isConnect or self.rigol == 'Emulation':
            return

        try:
            state = 'ON' if self.continuous_sweep_checkbox.isChecked() else 'OFF'
            self.rigol_cmd.set_continuous_sweep(self.rigol, state)

        except Exception as e:
            print(f"Error setting continuous sweep: {e}")

    def single_sweep(self):
        """Trigger single sweep"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Single sweep triggered")
            return

        try:
            self.rigol_cmd.single_sweep(self.rigol)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error triggering single sweep:\n{str(e)}")

    def preset_instrument(self):
        """Preset instrument to default settings"""
        if not self.isConnect:
            return

        reply = QMessageBox.question(self, "Confirm Preset",
                                     "Are you sure you want to preset the instrument to default settings?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if self.rigol == 'Emulation':
                QMessageBox.information(self, "Emulation Mode", "Instrument preset")
                return

            try:
                self.rigol_cmd.preset(self.rigol)
                time.sleep(1)
                QMessageBox.information(self, "Success", "Instrument preset successfully")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error presetting instrument:\n{str(e)}")

    def toggle_marker(self):
        """Toggle marker on/off"""
        if not self.isConnect or self.rigol == 'Emulation':
            return

        try:
            marker_num = self.marker_combo.currentIndex() + 1
            state = 'ON' if self.marker_enable_checkbox.isChecked() else 'OFF'
            self.rigol_cmd.set_marker_state(self.rigol, marker_num, state)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error toggling marker:\n{str(e)}")

    def marker_peak_search(self):
        """Perform marker peak search"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            QMessageBox.information(self, "Emulation Mode", "Peak search executed")
            return

        try:
            marker_num = self.marker_combo.currentIndex() + 1
            self.rigol_cmd.marker_peak_search(self.rigol, marker_num)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error in peak search:\n{str(e)}")

    def marker_next_peak(self):
        """Move marker to next peak"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            return

        try:
            marker_num = self.marker_combo.currentIndex() + 1
            self.rigol_cmd.marker_next_peak(self.rigol, marker_num)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error finding next peak:\n{str(e)}")

    def peak_to_center(self):
        """Move peak to center frequency"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            return

        try:
            marker_num = self.marker_combo.currentIndex() + 1
            self.rigol_cmd.peak_to_center(self.rigol, marker_num)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error moving peak to center:\n{str(e)}")

    def all_markers_off(self):
        """Turn off all markers"""
        if not self.isConnect:
            return

        if self.rigol == 'Emulation':
            self.marker_enable_checkbox.setChecked(False)
            return

        try:
            self.rigol_cmd.marker_all_off(self.rigol)
            self.marker_enable_checkbox.setChecked(False)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error turning off markers:\n{str(e)}")

    def set_trace_mode(self, mode_text):
        """Set trace mode"""
        if not self.isConnect or self.rigol == 'Emulation':
            # Show/hide average count widget
            self.avg_widget.setVisible(mode_text == "Average")
            return

        try:
            mode_map = {"Write": "WRITe", "Max Hold": "MAXHold", "Min Hold": "MINHold", "Average": "VIDeoavg"}

            mode = mode_map.get(mode_text, "WRITe")
            self.rigol_cmd.set_trace_mode(self.rigol, 1, mode)

            # Show/hide average count widget
            self.avg_widget.setVisible(mode_text == "Average")

            if mode_text == "Average":
                count = self.avg_count_spin.value()
                self.rigol_cmd.set_trace_average_count(self.rigol, count)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting trace mode:\n{str(e)}")

    def set_detector(self, detector_text):
        """Set detector type"""
        if not self.isConnect or self.rigol == 'Emulation':
            return

        try:
            detector_map = {"Positive": "POSitive", "Negative": "NEGative", "Normal": "NORMal", "Sample": "SAMPle",
                "RMS": "RMS", "Average": "VAVerage", "QPeak": "QPEak"}

            detector = detector_map.get(detector_text, "POSitive")
            self.rigol_cmd.set_detector_type(self.rigol, detector)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error setting detector:\n{str(e)}")

    def toggle_monitoring(self):
        """Start or stop monitoring"""
        if self.trace_monitor_thread and self.trace_monitor_thread.isRunning():
            self.stop_monitoring()
        else:
            self.start_monitoring()

    def start_monitoring(self):
        """Start trace monitoring for plotting"""
        if not self.isConnect:
            QMessageBox.warning(self, "Not Connected", "Please connect to instrument first")
            return

        if self.trace_monitor_thread and self.trace_monitor_thread.isRunning():
            return

        is_emulation = (self.rigol == 'Emulation')

        self.trace_monitor_thread = TraceMonitorThread(self.rigol, self.rigol_cmd, is_emulation)
        self.trace_monitor_thread.trace_signal.connect(self.update_plot)
        self.trace_monitor_thread.error_signal.connect(self.on_reading_error)
        self.trace_monitor_thread.start()

        self.monitor_status_label.setText("Status: Monitoring active")
        self.start_monitor_btn.setText("Stop Monitoring")
        print("Monitoring started")

    def stop_monitoring(self):
        """Stop monitoring"""
        if self.trace_monitor_thread and self.trace_monitor_thread.isRunning():
            self.trace_monitor_thread.stop()
            self.trace_monitor_thread.wait()
            self.trace_monitor_thread = None

        self.monitor_status_label.setText("Status: Not monitoring")
        self.start_monitor_btn.setText("Start Monitoring")
        print("Monitoring stopped")

    def update_plot(self, frequencies, amplitudes):
        """Update spectrum plot"""
        # Convert frequencies to GHz for display
        freq_ghz = frequencies / 1e9
        self.spectrum_curve.setData(freq_ghz, amplitudes)

    def closeEvent(self, event):
        """Handle window close"""
        self.stop_monitoring()

        if self.reading_thread and self.reading_thread.isRunning():
            self.reading_thread.stop()
            self.reading_thread.wait()

        if self.emulation_thread and self.emulation_thread.isRunning():
            self.emulation_thread.stop()
            self.emulation_thread.wait()

        if self.rigol and self.rigol != 'Emulation':
            try:
                self.rigol.close()
            except:
                pass

        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = RigolDSA800()
    window.show()
    sys.exit(app.exec())