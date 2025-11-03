from PyQt6.QtWidgets import (
    QSizePolicy, QWidget, QMessageBox, QGroupBox, QFileDialog, QVBoxLayout, QLabel, QHBoxLayout,
    QCheckBox, QTextEdit, QPushButton, QComboBox, QLineEdit, QScrollArea, QDialog, QRadioButton, QMainWindow,
    QDialogButtonBox, QProgressBar, QButtonGroup, QApplication, QCompleter, QToolButton
)
from PyQt6.QtGui import QIcon, QFont, QDoubleValidator, QIcon
from PyQt6.QtCore import pyqtSignal, Qt, QTimer, QThread, QSettings, QSize
from PyQt6.QtGui import QKeyEvent
import traceback
import random
import matplotlib
import datetime
import time
import numpy as np
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

try:
    # from GUI.Experiment.BNC845RF import COMMAND
    from QuDAP.instrument.BK_precision_9129B import BK_9129_COMMAND
    from QuDAP.instrument.rigol_spectrum_analyzer import RIGOL_COMMAND

except ImportError:
    # from QuDAP.GUI.Experiment.BNC845RF import COMMAND
    from instrument.rigol_spectrum_analyzer import RIGOL_COMMAND
    from instrument.BK_precision_9129B import BK_9129_COMMAND
    # from GUI.Experiment.rigol_experiment import RIGOL_Measurement

class BK9205_RIGOL_Worker(QThread):
    """
    Worker thread for automated BK9205 + RIGOL measurements.
    Loops through voltage/current values and captures spectrum at each point.
    """

    # PyQt Signals for UI updates
    progress_update = pyqtSignal(int)  # Progress percentage (0-100)
    append_text = pyqtSignal(str)  # Log messages
    stop_measurement = pyqtSignal()  # Signal to stop
    measurement_finished = pyqtSignal()  # Measurement complete
    error_message = pyqtSignal(str)  # Error popup

    # Instrument reading updates
    update_bk9205_ch1_voltage_label = pyqtSignal(str)
    update_bk9205_ch1_current_label = pyqtSignal(str)
    update_bk9205_ch2_voltage_label = pyqtSignal(str)
    update_bk9205_ch2_current_label = pyqtSignal(str)
    update_bk9205_ch3_voltage_label = pyqtSignal(str)
    update_bk9205_ch3_current_label = pyqtSignal(str)

    update_bk9205_ch1_status_label = pyqtSignal(str)
    update_bk9205_ch2_status_label = pyqtSignal(str)
    update_bk9205_ch3_status_label = pyqtSignal(str)

    update_rigol_freq_label = pyqtSignal(str)
    update_rigol_power_label = pyqtSignal(str)
    save_individual_plot = pyqtSignal(str)

    # Plotting signals
    update_2d_plot = pyqtSignal(list, list, list)  # x_data (indices), y_data (voltages), z_data (peak powers)
    update_spectrum_plot = pyqtSignal(list, list)  # freq_data, power_data
    save_plot = pyqtSignal(str)  # filename
    clear_plot = pyqtSignal()

    # Measurement progress
    update_measurement_progress = pyqtSignal(str)  # Current measurement status

    def __init__(self, parent, bk9205_instrument, rigol_instrument, measurement_data,
                 folder_path, file_name, run_number, demo_mode=False,
                 settling_time=1.0, spectrum_averaging=1,
                 save_individual_spectra=True, **kwargs):
        """
        Initialize worker thread.
        """
        super().__init__(parent)

        self.parent = parent
        self.bk9205 = bk9205_instrument
        self.rigol = rigol_instrument
        self.measurement_data = measurement_data
        self.folder_path = folder_path
        self.file_name = file_name
        self.run_number = run_number

        # Connection flags
        self.demo_mode = demo_mode

        # Measurement parameters
        self.settling_time = settling_time
        self.spectrum_averaging = spectrum_averaging
        self.save_individual_spectra = save_individual_spectra

        # Control flags
        self.running = True
        self.paused = False
        self.stopped_by_user = False

        # Data storage
        self.measurement_results = []
        self.all_spectra = []

        # Additional parameters
        self.extra_params = kwargs

    def run(self):
        """Main execution method - runs in separate thread."""
        try:
            print('Here')
            self.append_text.emit("=" * 60)
            self.append_text.emit("Starting BK9205 + RIGOL Measurement")
            self.append_text.emit(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.append_text.emit("=" * 60)

            # Validate measurement data
            if not self._validate_measurement_data():
                return

            # Initialize instruments
            if not self._initialize_instruments():
                return

            # Clear plots
            self.clear_plot.emit()

            # Execute measurement
            self._execute_measurement()

            if self.stopped_by_user:
                self.append_text.emit("\n" + "=" * 60)
                self.append_text.emit("Measurement stopped by user")
                self.append_text.emit("=" * 60)
                return  # Exit without emitting measurement_finished

            # Save consolidated data
            self._save_consolidated_data()

            # Cleanup
            self._cleanup_instruments()

            self.append_text.emit("=" * 60)
            self.append_text.emit("Measurement Complete!")
            self.append_text.emit("=" * 60)
            self.measurement_finished.emit()

        except Exception as e:
            error_msg = f"Error in measurement: {str(e)}\n{traceback.format_exc()}"
            self.append_text.emit(error_msg)
            self.error_message.emit(error_msg)
            self.stop_measurement.emit()

    def _validate_measurement_data(self):
        """Validate measurement configuration."""
        self.append_text.emit("\nValidating measurement configuration...")

        if self.measurement_data['channel_mode'] == 'none':
            self.error_message.emit("No channels selected for measurement")
            return False

        # Check that at least one channel is enabled
        has_enabled = any(ch['enabled'] for ch in self.measurement_data['channels'].values())
        if not has_enabled:
            self.error_message.emit("No enabled channels found")
            return False

        # Check that enabled channels have values
        for ch_name, ch_data in self.measurement_data['channels'].items():
            if ch_data['enabled'] and not ch_data['values']:
                self.error_message.emit(f"No values specified for {ch_name}")
                return False

        self.append_text.emit("✓ Measurement configuration valid")
        self._log_measurement_summary()
        return True

    def _log_measurement_summary(self):
        """Log measurement configuration summary."""
        self.append_text.emit("\nMeasurement Configuration:")
        self.append_text.emit(f"  Channel Mode: {self.measurement_data['channel_mode']}")
        self.append_text.emit(f"  Source Type: {self.measurement_data['source_type']}")

        for ch_name, ch_data in self.measurement_data['channels'].items():
            if ch_data['enabled']:
                ch_label = ch_name.upper().replace('MERGED', 'CH1+CH2')
                self.append_text.emit(f"\n  {ch_label}:")
                self.append_text.emit(f"    Mode: {ch_data['mode']}")
                self.append_text.emit(f"    Number of points: {len(ch_data['values'])}")
                self.append_text.emit(
                    f"    Range: {min(ch_data['values']):.6f} to {max(ch_data['values']):.6f} {ch_data['unit']}")

    def _initialize_instruments(self):
        """Initialize BK9205 and RIGOL instruments."""
        self.append_text.emit("\nInitializing instruments...")

        try:
            # Initialize BK9205
            if self.bk9205 and not self.demo_mode:
                self.append_text.emit("  Initializing BK9205...")
                self.bk9205_cmd = BK_9129_COMMAND()

                # Turn off all outputs initially
                self.bk9205_cmd.set_output_state(self.bk9205, 'OFF')
                self.append_text.emit("  ✓ BK9205 initialized")
            else:
                self.append_text.emit("  ⚠ BK9205 not connected (demo mode)")
                self.bk9205_cmd = None

            # Initialize RIGOL
            if self.rigol and not self.demo_mode:
                self.append_text.emit("  Initializing RIGOL...")
                self.rigol_cmd = RIGOL_COMMAND()

                # Reset and configure RIGOL for measurement
                # Add your specific RIGOL configuration here
                self.append_text.emit("  ✓ RIGOL initialized")
            else:
                self.append_text.emit("  ⚠ RIGOL not connected (demo mode)")
                self.rigol_cmd = None

            return True

        except Exception as e:
            error_msg = f"Instrument initialization failed: {str(e)}"
            self.append_text.emit(f"  ✗ {error_msg}")
            self.error_message.emit(error_msg)
            return False

    def _execute_measurement(self):
        """Execute the main measurement loop."""
        channel_mode = self.measurement_data['channel_mode']

        if channel_mode == 'single':
            self._measure_single_channel()
        elif channel_mode == 'series':
            self._measure_series_channels()
        elif channel_mode == 'parallel':
            self._measure_parallel_channels()
        elif channel_mode == 'all':
            self._measure_all_channels()

    def _measure_single_channel(self):
        """Measure single channel configuration."""
        self.append_text.emit("\n" + "=" * 60)
        self.append_text.emit("Starting Single Channel Measurement")
        self.append_text.emit("=" * 60)

        # Find the enabled channel
        enabled_channel = None
        for ch_name, ch_data in self.measurement_data['channels'].items():
            if ch_data['enabled']:
                enabled_channel = (ch_name, ch_data)
                break

        if not enabled_channel:
            return

        ch_name, ch_data = enabled_channel
        channel_num = self._get_channel_number(ch_name)
        values = ch_data['values']
        total_points = len(values)
        source_type = self.measurement_data['source_type']

        self.append_text.emit(f"\nMeasuring {ch_name.upper()} with {total_points} points")

        for idx, value in enumerate(values):
            if not self.running:
                self.append_text.emit("\n✗ Measurement stopped by user")
                return

            # Update progress
            progress = int((idx / total_points) * 100)
            self.progress_update.emit(progress)
            self.update_measurement_progress.emit(
                f"Point {idx + 1}/{total_points}: {value:.6f} {ch_data['unit']}"
            )

            # Step 1: Set voltage/current using set_all_voltages/currents command
            self._set_channel_voltage_all_command(channel_num, value, source_type)

            # Step 2: Turn on the channel
            self._turn_on_channel(channel_num)

            # Step 3: Wait for settling
            self._wait_settling(f"Settling... ({self.settling_time}s)")

            # Step 4: Read back voltages/currents and update labels
            self._read_and_update_labels()

            # Step 5: Capture spectrum
            spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

            # Step 6: Store results
            result = {
                'point': idx + 1,
                'channel': ch_name,
                'channel_num': channel_num,
                'value': value,
                'unit': ch_data['unit'],
                'source_type': source_type,
                'spectrum': spectrum_data,
                'timestamp': datetime.datetime.now().isoformat()
            }
            self.measurement_results.append(result)

            # Step 7: Save individual spectrum file
            if self.save_individual_spectra:
                self._save_individual_spectrum(result, idx)


            # Step 8: Update plots
            self._update_plots()
            plot_filename = f"{self.file_name}_point_{idx + 1:04d}_spectrum.png"
            self.save_individual_plot.emit(plot_filename)
            time.sleep(1)

        self.save_plot.emit(self.file_name)
        self.progress_update.emit(100)

    def _measure_series_channels(self):
        """Measure series channel configuration (Ch1 + Ch2)."""
        self.append_text.emit("\n" + "=" * 60)
        self.append_text.emit("Starting Series Channel Measurement")
        self.append_text.emit("=" * 60)

        merged_data = self.measurement_data['channels']['merged']
        values = merged_data['values']
        total_points = len(values)
        source_type = self.measurement_data['source_type']

        self.append_text.emit(f"\nMeasuring CH1 & CH2 in Series with {total_points} points")

        for idx, total_value in enumerate(values):
            if not self.running:
                return

            progress = int((idx / total_points) * 100)
            self.progress_update.emit(progress)
            self.update_measurement_progress.emit(
                f"Point {idx + 1}/{total_points}: Total={total_value:.6f} {merged_data['unit']}"
            )

            # Split voltage between channels (50/50 split)
            ch1_value = total_value / 2
            ch2_value = total_value / 2

            # Set both channels using APP:VOLT command
            self._set_series_channels(ch1_value, ch2_value, source_type)

            # Enable series mode and turn on outputs
            self._enable_series_mode()

            # Wait for settling
            self._wait_settling(f"Settling... ({self.settling_time}s)")

            # Read back and update labels
            self._read_and_update_labels()

            # Capture spectrum
            spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

            # Store results
            result = {
                'point': idx + 1,
                'channel': 'merged_series',
                'total_value': total_value,
                'ch1_value': ch1_value,
                'ch2_value': ch2_value,
                'unit': merged_data['unit'],
                'source_type': source_type,
                'spectrum': spectrum_data,
                'timestamp': datetime.datetime.now().isoformat()
            }
            self.measurement_results.append(result)

            # Save individual spectrum
            if self.save_individual_spectra:
                self._save_individual_spectrum(result, idx)


            # Update plots
            self._update_plots()
            plot_filename = f"{self.file_name}_point_{idx + 1:04d}_spectrum.png"
            self.save_individual_plot.emit(plot_filename)
        self.save_plot.emit(self.file_name)
        self.progress_update.emit(100)

    def _measure_parallel_channels(self):
        """Measure parallel channel configuration (Ch1 || Ch2)."""
        self.append_text.emit("\n" + "=" * 60)
        self.append_text.emit("Starting Parallel Channel Measurement")
        self.append_text.emit("=" * 60)

        merged_data = self.measurement_data['channels']['merged']
        values = merged_data['values']
        total_points = len(values)
        source_type = self.measurement_data['source_type']

        self.append_text.emit(f"\nMeasuring CH1 & CH2 in Parallel with {total_points} points")

        for idx, value in enumerate(values):
            if not self.running:
                return

            progress = int((idx / total_points) * 100)
            self.progress_update.emit(progress)
            self.update_measurement_progress.emit(
                f"Point {idx + 1}/{total_points}: {value:.6f} {merged_data['unit']}"
            )

            # Set both channels to same value
            self._set_parallel_channels(value, value, source_type)

            # Enable parallel mode and turn on outputs
            self._enable_parallel_mode()

            # Wait for settling
            self._wait_settling(f"Settling... ({self.settling_time}s)")

            # Read back and update labels
            self._read_and_update_labels()

            # Capture spectrum
            spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

            # Store results
            result = {
                'point': idx + 1,
                'channel': 'merged_parallel',
                'value': value,
                'unit': merged_data['unit'],
                'source_type': source_type,
                'spectrum': spectrum_data,
                'timestamp': datetime.datetime.now().isoformat()
            }
            self.measurement_results.append(result)

            # Save individual spectrum
            if self.save_individual_spectra:
                self._save_individual_spectrum(result, idx)


            # Update plots
            self._update_plots()
            plot_filename = f"{self.file_name}_point_{idx + 1:04d}_spectrum.png"
            self.save_individual_plot.emit(plot_filename)
        self.save_plot.emit(self.file_name)
        self.progress_update.emit(100)

    def _measure_all_channels(self):
        """Measure all channels configuration."""
        self.append_text.emit("\n" + "=" * 60)
        self.append_text.emit("Starting All Channels Measurement")
        self.append_text.emit("=" * 60)

        # Get enabled channels
        enabled_channels = [
            (ch_name, ch_data)
            for ch_name, ch_data in self.measurement_data['channels'].items()
            if ch_data['enabled']
        ]

        # Find varying channel (one with multiple values)
        varying_channels = [(name, data) for name, data in enabled_channels if len(data['values']) > 1]

        if len(varying_channels) == 0:
            # All fixed values
            self._measure_all_channels_fixed(enabled_channels)
        else:
            # Use first varying channel
            self._measure_all_channels_one_varying(enabled_channels, varying_channels[0])

    def _measure_all_channels_fixed(self, enabled_channels):
        """All channels with fixed values - single measurement."""
        self.append_text.emit("\nAll channels set to fixed values - single measurement")

        # Prepare voltage list for all 3 channels
        ch_values = [0.0, 0.0, 0.0]  # Ch1, Ch2, Ch3
        source_type = self.measurement_data['source_type']

        for ch_name, ch_data in enabled_channels:
            ch_num = self._get_channel_number(ch_name)
            ch_values[ch_num - 1] = ch_data['values'][0]

        # Set all channels at once
        self._set_all_channels(ch_values[0], ch_values[1], ch_values[2], source_type)

        # Turn on all channels
        self._turn_on_all_channels()

        # Wait for settling
        self._wait_settling(f"Settling... ({self.settling_time}s)")

        # Read and update
        self._read_and_update_labels()

        # Capture spectrum
        spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

        # Store result
        result = {
            'point': 1,
            'channel': 'all_fixed',
            'ch1_value': ch_values[0],
            'ch2_value': ch_values[1],
            'ch3_value': ch_values[2],
            'spectrum': spectrum_data,
            'timestamp': datetime.datetime.now().isoformat()
        }
        self.measurement_results.append(result)

        if self.save_individual_spectra:
            self._save_individual_spectrum(result, 0)


        self._update_plots()
        plot_filename = f"{self.file_name}_point_spectrum.png"
        self.save_individual_plot.emit(plot_filename)
        self.save_plot.emit(self.file_name)
        self.progress_update.emit(100)

    def _measure_all_channels_one_varying(self, enabled_channels, varying_channel):
        """All channels with one varying."""
        vary_name, vary_data = varying_channel
        values = vary_data['values']
        total_points = len(values)
        source_type = self.measurement_data['source_type']

        self.append_text.emit(f"\nVarying {vary_name.upper()} through {total_points} points")

        for idx, vary_value in enumerate(values):
            if not self.running:
                return

            progress = int((idx / total_points) * 100)
            self.progress_update.emit(progress)
            self.update_measurement_progress.emit(
                f"Point {idx + 1}/{total_points}: {vary_name.upper()}={vary_value:.6f}"
            )

            # Prepare voltage list
            ch_values = [0.0, 0.0, 0.0]
            for ch_name, ch_data in enabled_channels:
                ch_num = self._get_channel_number(ch_name)
                if ch_name == vary_name:
                    ch_values[ch_num - 1] = vary_value
                else:
                    ch_values[ch_num - 1] = ch_data['values'][0]

            # Set all channels
            self._set_all_channels(ch_values[0], ch_values[1], ch_values[2], source_type)

            # Turn on all channels
            self._turn_on_all_channels()

            # Wait for settling
            self._wait_settling(f"Settling... ({self.settling_time}s)")

            # Read and update
            self._read_and_update_labels()

            # Capture spectrum
            spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

            # Store result
            result = {
                'point': idx + 1,
                'channel': 'all_varying',
                'varying_channel': vary_name,
                'varying_value': vary_value,
                'ch1_value': ch_values[0],
                'ch2_value': ch_values[1],
                'ch3_value': ch_values[2],
                'spectrum': spectrum_data,
                'timestamp': datetime.datetime.now().isoformat()
            }
            self.measurement_results.append(result)

            if self.save_individual_spectra:
                self._save_individual_spectrum(result, idx)


            self._update_plots()
            plot_filename = f"{self.file_name}_point_{idx + 1:04d}_spectrum.png"
            self.save_individual_plot.emit(plot_filename)
        self.save_plot.emit(self.file_name)
        self.progress_update.emit(100)

    # ==================================================================================
    # BK9205 CONTROL METHODS
    # ==================================================================================

    def _set_channel_voltage_all_command(self, channel_num, value, source_type):
        """Set voltage for single channel using APP:VOLT command."""
        if self.demo_mode or not self.bk9205:
            self.append_text.emit(f"    [DEMO] Setting Ch{channel_num} {source_type} to {value:.6f}")
            return

        try:
            # Use APP:VOLT command to set only the specified channel
            if source_type == 'voltage':
                if channel_num == 1:
                    print(value)
                    self.bk9205_cmd.set_all_voltages(self.bk9205, value, 0, 0, 'V')
                elif channel_num == 2:
                    self.bk9205_cmd.set_all_voltages(self.bk9205, 0, value, 0, 'V')
                elif channel_num == 3:
                    self.bk9205_cmd.set_all_voltages(self.bk9205, 0, 0, value, 'V')
                self.append_text.emit(f"    Set Ch{channel_num} voltage to {value:.6f} V")
            else:  # current
                if channel_num == 1:
                    self.bk9205_cmd.set_all_currents(self.bk9205, value, 0, 0, 'A')
                elif channel_num == 2:
                    self.bk9205_cmd.set_all_currents(self.bk9205, 0, value, 0, 'A')
                elif channel_num == 3:
                    self.bk9205_cmd.set_all_currents(self.bk9205, 0, 0, value, 'A')
                self.append_text.emit(f"    Set Ch{channel_num} current to {value:.6f} A")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error setting Ch{channel_num}: {str(e)}")

    def _set_all_channels(self, ch1_value, ch2_value, ch3_value, source_type):
        """Set all three channels at once using APP:VOLT or APP:CURR command."""
        if self.demo_mode or not self.bk9205:
            self.append_text.emit(f"    [DEMO] Setting Ch1={ch1_value:.6f}, Ch2={ch2_value:.6f}, Ch3={ch3_value:.6f}")
            return

        try:
            if source_type == 'voltage':
                self.bk9205_cmd.set_all_voltages(self.bk9205, ch1_value, ch2_value, ch3_value, 'V')
                self.append_text.emit(
                    f"    Set voltages: Ch1={ch1_value:.6f}V, Ch2={ch2_value:.6f}V, Ch3={ch3_value:.6f}V")
            else:
                self.bk9205_cmd.set_all_currents(self.bk9205, ch1_value, ch2_value, ch3_value, 'A')
                self.append_text.emit(
                    f"    Set currents: Ch1={ch1_value:.6f}A, Ch2={ch2_value:.6f}A, Ch3={ch3_value:.6f}A")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error setting all channels: {str(e)}")

    def _set_series_channels(self, ch1_value, ch2_value, source_type):
        """Set Ch1 and Ch2 for series mode."""
        if self.demo_mode or not self.bk9205:
            self.append_text.emit(f"    [DEMO] Setting series: Ch1={ch1_value:.6f}, Ch2={ch2_value:.6f}")
            return

        try:
            if source_type == 'voltage':
                self.bk9205_cmd.set_all_voltages(self.bk9205, ch1_value, ch2_value, 0, 'V')
            else:
                self.bk9205_cmd.set_all_currents(self.bk9205, ch1_value, ch2_value, 0, 'A')

            self.append_text.emit(f"    Set series mode: Ch1={ch1_value:.6f}, Ch2={ch2_value:.6f}")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error setting series channels: {str(e)}")

    def _set_parallel_channels(self, ch1_value, ch2_value, source_type):
        """Set Ch1 and Ch2 for parallel mode."""
        if self.demo_mode or not self.bk9205:
            self.append_text.emit(f"    [DEMO] Setting parallel: Ch1={ch1_value:.6f}, Ch2={ch2_value:.6f}")
            return

        try:
            if source_type == 'voltage':
                self.bk9205_cmd.set_all_voltages(self.bk9205, ch1_value, ch2_value, 0, 'V')
            else:
                self.bk9205_cmd.set_all_currents(self.bk9205, ch1_value, ch2_value, 0, 'A')

            self.append_text.emit(f"    Set parallel mode: Ch1={ch1_value:.6f}, Ch2={ch2_value:.6f}")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error setting parallel channels: {str(e)}")

    def _turn_on_channel(self, channel_num):
        """Turn on a specific channel."""
        if self.demo_mode or not self.bk9205:
            return

        try:
            # Select and turn on the channel
            ch_name = f'CH{channel_num}'
            self.bk9205_cmd.select_channel(self.bk9205, ch_name)
            self.bk9205_cmd.set_channel_output_state(self.bk9205, 'ON')
            self.append_text.emit(f"    Turned ON Ch{channel_num}")
            if channel_num == 1:
                self.update_bk9205_ch1_status_label.emit(f"On")
            if channel_num == 2:
                self.update_bk9205_ch2_status_label.emit(f"On")
            if channel_num == 3:
                self.update_bk9205_ch3_status_label.emit(f"On")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error turning on Ch{channel_num}: {str(e)}")

    def _turn_on_all_channels(self):
        """Turn on all three channels."""
        if self.demo_mode or not self.bk9205:
            return

        try:
            self.bk9205_cmd.set_output_state(self.bk9205, 'ON')
            self.append_text.emit("    Turned ON all channels")
            self.update_bk9205_ch1_status_label.emit(f"On")
            self.update_bk9205_ch2_status_label.emit(f"On")
            self.update_bk9205_ch3_status_label.emit(f"On")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error turning on all channels: {str(e)}")

    def _enable_series_mode(self):
        """Enable series mode for Ch1+Ch2."""
        if self.demo_mode or not self.bk9205:
            return

        try:
            self.bk9205_cmd.set_series_mode(self.bk9205)
            self.bk9205_cmd.set_output_series_state(self.bk9205, 'ON')
            self.append_text.emit("    Enabled series mode")
            self.update_bk9205_ch1_status_label.emit(f"On")
            self.update_bk9205_ch2_status_label.emit(f"On")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error enabling series mode: {str(e)}")

    def _enable_parallel_mode(self):
        """Enable parallel mode for Ch1||Ch2."""
        if self.demo_mode or not self.bk9205:
            return

        try:
            self.bk9205_cmd.set_parallel_mode(self.bk9205)
            self.bk9205_cmd.set_output_parallel_state(self.bk9205, 'ON')
            self.append_text.emit("    Enabled parallel mode")
            self.update_bk9205_ch1_status_label.emit(f"On")
            self.update_bk9205_ch2_status_label.emit(f"On")
        except Exception as e:
            self.append_text.emit(f"    ✗ Error enabling parallel mode: {str(e)}")

    def _read_and_update_labels(self):
        """Read actual voltages/currents from BK9205 and update UI labels."""
        if self.demo_mode or not self.bk9205:
            return

        try:
            # Read all voltages
            voltages_str = self.bk9205_cmd.measure_all_voltages(self.bk9205)
            voltages = voltages_str.split(',')

            if len(voltages) >= 2:
                self.update_bk9205_ch1_voltage_label.emit(f"{float(voltages[0]):.6f}")
                self.update_bk9205_ch2_voltage_label.emit(f"{float(voltages[1]):.6f}")
                self.update_bk9205_ch3_voltage_label.emit(f"{float(voltages[2]):.6f}")

            # Read all currents
            currents_str = self.bk9205_cmd.measure_all_currents(self.bk9205)
            currents = currents_str.split(',')

            if len(currents) >= 2:
                self.update_bk9205_ch1_current_label.emit(f"{float(currents[0]):.6f}")
                self.update_bk9205_ch2_current_label.emit(f"{float(currents[1]):.6f}")
                self.update_bk9205_ch3_current_label.emit(f"{float(currents[2]):.6f}")

        except Exception as e:
            self.append_text.emit(f"    ⚠ Warning reading measurements: {str(e)}")

    # ==================================================================================
    # RIGOL SPECTRUM ANALYZER METHODS
    # ==================================================================================

    def _capture_spectrum(self, averaging=1):
        """Capture spectrum from RIGOL with averaging."""
        if self.demo_mode or not self.rigol:
            return self._generate_demo_spectrum()

        try:
            self.append_text.emit(f"    Capturing spectrum (averaging {averaging})...")

            spectra = []
            for i in range(averaging):
                if not self.running:
                    return

                # Trigger single sweep
                self.rigol_cmd.single_sweep(self.rigol)

                # Wait for sweep to complete
                time.sleep(0.5)  # Adjust based on sweep time

                # Get trace data
                self.rigol_cmd.set_data_format(self.rigol, 'REAL')
                trace_data_str = self.rigol_cmd.get_trace_data(self.rigol, 'TRACE1')
                print*(trace_data_str)
                trace_data = [float(x) for x in trace_data_str.split(',')]
                print(trace_data_str)

                # Get frequency data
                start_freq = float(self.rigol_cmd.get_start_frequency(self.rigol))
                stop_freq = float(self.rigol_cmd.get_stop_frequency(self.rigol))
                num_points = len(trace_data)
                frequencies = np.linspace(start_freq, stop_freq, num_points).tolist()

                spectrum = {
                    'frequencies': frequencies,
                    'powers': trace_data
                }
                spectra.append(spectrum)

                if averaging > 1:
                    self.append_text.emit(f"      Trace {i + 1}/{averaging}")

            # Average spectra
            if len(spectra) > 1:
                avg_spectrum = self._average_spectra(spectra)
            else:
                avg_spectrum = spectra[0]

            # Update RIGOL labels
            if avg_spectrum['frequencies']:
                center_freq = (avg_spectrum['frequencies'][0] + avg_spectrum['frequencies'][-1]) / 2
                peak_power = max(avg_spectrum['powers'])
                self.update_rigol_freq_label.emit(f"{center_freq / 1e9:.3f} GHz")
                self.update_rigol_power_label.emit(f"{peak_power:.2f} dBm")

            self.append_text.emit("    ✓ Spectrum captured")
            return avg_spectrum

        except Exception as e:
            self.append_text.emit(f"    ✗ Error capturing spectrum: {str(e)}")
            return self._generate_demo_spectrum()

    def _generate_demo_spectrum(self):
        """Generate demo spectrum data."""
        time.sleep(3)
        frequencies = np.linspace(1e9, 2e9, 1001)
        powers = -80 + 10 * np.random.randn(len(frequencies))

        # Add peaks
        for peak_idx in [200, 500, 800]:
            powers[peak_idx - 10:peak_idx + 10] += 30 * np.exp(-((np.arange(-10, 10)) ** 2) / 20)

        return {
            'frequencies': frequencies.tolist(),
            'powers': powers.tolist(),
            'metadata': {
                'center_freq': 1.5e9,
                'span': 1e9,
                'rbw': 1e6,
                'timestamp': datetime.datetime.now().isoformat()
            }
        }

    def _average_spectra(self, spectra):
        """Average multiple spectra."""
        frequencies = spectra[0]['frequencies']
        powers_array = np.array([s['powers'] for s in spectra])
        avg_powers = np.mean(powers_array, axis=0)

        return {
            'frequencies': frequencies,
            'powers': avg_powers.tolist(),
            'metadata': spectra[0].get('metadata', {})
        }

    # ==================================================================================
    # DATA SAVING METHODS
    # ==================================================================================

    def _save_individual_spectrum(self, result, index):
        """Save individual spectrum to text file."""
        try:
            filename = f"{self.file_name}_point_{index + 1:04d}_spectrum.txt"
            filepath = f"{self.folder_path}/{filename}"

            with open(filepath, 'w') as f:
                f.write("# BK9205 + RIGOL Spectrum Measurement\n")
                f.write(f"# Timestamp: {result['timestamp']}\n")
                f.write(f"# Point: {result['point']}\n")

                # Write channel-specific info
                if 'value' in result:
                    f.write(f"# Channel: {result['channel']}\n")
                    f.write(f"# {result['source_type'].capitalize()}: {result['value']:.6f} {result['unit']}\n")
                elif 'total_value' in result:
                    f.write(
                        f"# Total {result['source_type'].capitalize()}: {result['total_value']:.6f} {result['unit']}\n")
                    f.write(f"# Ch1 {result['source_type'].capitalize()}: {result['ch1_value']:.6f} {result['unit']}\n")
                    f.write(f"# Ch2 {result['source_type'].capitalize()}: {result['ch2_value']:.6f} {result['unit']}\n")
                elif 'ch1_value' in result:
                    f.write(f"# Ch1: {result['ch1_value']:.6f}\n")
                    f.write(f"# Ch2: {result['ch2_value']:.6f}\n")
                    f.write(f"# Ch3: {result['ch3_value']:.6f}\n")

                f.write("#\n")
                f.write("# Frequency (Hz)\tPower (dBm)\n")

                spectrum = result['spectrum']
                for freq, power in zip(spectrum['frequencies'], spectrum['powers']):
                    f.write(f"{freq:.6e}\t{power:.6f}\n")

            self.append_text.emit(f"    Saved: {filename}")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error saving spectrum: {str(e)}")

    def _save_consolidated_data(self):
        """Save consolidated data file with all measurements."""
        try:
            self.append_text.emit("\nSaving consolidated measurement data...")

            data_file = f"{self.folder_path}/{self.file_name}_all_data.txt"

            with open(data_file, 'w') as f:
                f.write("# BK9205 + RIGOL Consolidated Measurement Data\n")
                f.write("=" * 80 + "\n")
                f.write(f"# Measurement Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Run Number: {self.run_number}\n")
                f.write(f"# Channel Mode: {self.measurement_data['channel_mode']}\n")
                f.write(f"# Source Type: {self.measurement_data['source_type']}\n")
                f.write(f"# Total Points: {len(self.measurement_results)}\n")
                f.write(f"# Settling Time: {self.settling_time} s\n")
                f.write(f"# Spectrum Averaging: {self.spectrum_averaging}\n")
                f.write("=" * 80 + "\n\n")

                # Write column headers
                f.write("# Point\tTimestamp\tSource_Value\tUnit\tPeak_Power(dBm)\tPeak_Freq(Hz)\tCenter_Freq(Hz)\n")

                # Write data
                for result in self.measurement_results:
                    point = result['point']
                    timestamp = result['timestamp']

                    # Determine source value
                    if 'value' in result:
                        value = result['value']
                        unit = result['unit']
                    elif 'total_value' in result:
                        value = result['total_value']
                        unit = result['unit']
                    elif 'varying_value' in result:
                        value = result['varying_value']
                        unit = result.get('unit', 'V')
                    else:
                        value = 0
                        unit = 'V'

                    spectrum = result['spectrum']
                    peak_power = max(spectrum['powers'])
                    peak_idx = spectrum['powers'].index(peak_power)
                    peak_freq = spectrum['frequencies'][peak_idx]
                    center_freq = (spectrum['frequencies'][0] + spectrum['frequencies'][-1]) / 2

                    f.write(
                        f"{point}\t{timestamp}\t{value:.6f}\t{unit}\t{peak_power:.6f}\t{peak_freq:.6e}\t{center_freq:.6e}\n")

            self.append_text.emit(f"✓ Saved consolidated data: {data_file}")

            # Also save summary statistics
            self._save_summary_statistics()

        except Exception as e:
            self.append_text.emit(f"✗ Error saving consolidated data: {str(e)}")

    def _save_summary_statistics(self):
        """Save summary statistics file."""
        try:
            summary_file = f"{self.folder_path}/{self.file_name}_summary.txt"

            with open(summary_file, 'w') as f:
                f.write("BK9205 + RIGOL Measurement Summary\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"Measurement Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Run Number: {self.run_number}\n")
                f.write(f"Total Points: {len(self.measurement_results)}\n\n")

                # Calculate statistics
                all_peak_powers = [max(r['spectrum']['powers']) for r in self.measurement_results]

                f.write("Peak Power Statistics:\n")
                f.write(f"  Maximum: {max(all_peak_powers):.2f} dBm\n")
                f.write(f"  Minimum: {min(all_peak_powers):.2f} dBm\n")
                f.write(f"  Mean: {np.mean(all_peak_powers):.2f} dBm\n")
                f.write(f"  Std Dev: {np.std(all_peak_powers):.2f} dBm\n\n")

                # Measurement configuration
                f.write("Configuration:\n")
                f.write(f"  Channel Mode: {self.measurement_data['channel_mode']}\n")
                f.write(f"  Source Type: {self.measurement_data['source_type']}\n")
                f.write(f"  Settling Time: {self.settling_time} s\n")
                f.write(f"  Spectrum Averaging: {self.spectrum_averaging}\n")

            self.append_text.emit(f"✓ Saved summary: {summary_file}")

        except Exception as e:
            self.append_text.emit(f"✗ Error saving summary: {str(e)}")

    # ==================================================================================
    # PLOTTING METHODS
    # ==================================================================================

    def _update_plots(self):
        """Update both the 2D cumulative plot and the current spectrum plot."""

        # Extract frequency data (use first spectrum's frequencies)
        if len(self.measurement_results) > 0:
            freq_data = self.measurement_results[0]['spectrum']['frequencies']
        else:
            return

        # Extract voltage/current values and spectra
        y_data = []  # Voltages/currents
        z_data = []  # All spectra (2D array)

        for result in self.measurement_results:
            # Get source value
            if 'value' in result:
                y_data.append(result['value'])
            elif 'total_value' in result:
                y_data.append(result['total_value'])
            elif 'varying_value' in result:
                y_data.append(result['varying_value'])
            else:
                y_data.append(0)

            # Get spectrum power data
            spectrum = result['spectrum']
            z_data.append(spectrum['powers'])

        # Update 2D cumulative plot (left) - now showing freq vs voltage
        self.update_2d_plot.emit(freq_data, y_data, z_data)

        # Update current spectrum plot (right)
        latest_result = self.measurement_results[-1]
        spectrum = latest_result['spectrum']
        self.update_spectrum_plot.emit(spectrum['frequencies'], spectrum['powers'])

    # ==================================================================================
    # HELPER METHODS
    # ==================================================================================

    def _get_channel_number(self, ch_name):
        """Convert channel name to number."""
        mapping = {
            'ch1': 1,
            'ch2': 2,
            'ch3': 3,
            'merged': 4
        }
        return mapping.get(ch_name, 1)

    def _wait_settling(self, message):
        """Wait for settling time."""
        self.append_text.emit(f"    {message}")
        if self.demo_mode:
            time.sleep(0.1)
        else:
            time.sleep(self.settling_time)

    def _cleanup_instruments(self):
        """Turn off outputs and cleanup."""
        self.append_text.emit("\nCleaning up...")

        if self.bk9205 and not self.demo_mode:
            try:
                self.bk9205_cmd.set_output_state(self.bk9205, 'OFF')
                self.append_text.emit("  ✓ BK9205 outputs disabled")
                self.update_bk9205_ch1_status_label.emit(f"OFF")
                self.update_bk9205_ch2_status_label.emit(f"OFF")
                self.update_bk9205_ch2_status_label.emit(f"OFF")
            except Exception as e:
                self.append_text.emit(f"  ⚠ BK9205 cleanup warning: {str(e)}")

    def stop(self):
        """Stop the measurement."""
        self.running = False
        self.stopped_by_user = True
        self.append_text.emit("\nStopping measurement...")

    def pause(self):
        """Pause the measurement."""
        self.paused = True
        self.append_text.emit("\nMeasurement paused")

    def resume(self):
        """Resume the measurement."""
        self.paused = False
        self.append_text.emit("\nMeasurement resumed")

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

        measurement_hints = [""]
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
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.sample_id}_{self.measurement}_2V_Run_{self.run}.txt"
        self.example_file_name.setText(self.file_name)

    def update_measurement(self, text):
        # Replace spaces with underscores in the text
        self.measurement = self.measurement_type_entry_box.text()
        self.measurement = text.replace(" ", "_")
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.sample_id}_{self.measurement}_2V_Run_{self.run}.txt"
        self.example_file_name.setText(self.file_name)

    def update_run_number(self, text):
        # Replace spaces with underscores in the text
        self.run = self.run_number_entry_box.text()
        self.run = text.replace(" ", "_")
        self.file_name = f"{self.random_number}_{self.formatted_date}_{self.sample_id}_{self.measurement}_2V_Run_{self.run}.csv"
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
    def __init__(self, parent=None, width=100, height=100, dpi=300):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)

class RIGOL_Measurement(QWidget):
    def __init__(self, rigol_connected = None, bk_9205_connected = None):
        super().__init__()
        try:
            with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                self.Button_stylesheet = file.read()
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.QCombo_stylesheet = file.read()
            self.font = QFont("Arial", 13)
            self.RIGOL_CONNECTED = rigol_connected
            self.BK_9205_CONNECTED = bk_9205_connected
            self.worker = None
            self.init_ui()
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
            return

    def reset_preset(self):
        def safe_clear_layout(layout_attr_name):
            """Safely clear a layout if it exists"""
            if hasattr(self, layout_attr_name):
                layout = getattr(self, layout_attr_name)
                if layout is not None:
                    try:
                        self.clear_layout(layout)
                        return True
                    except Exception as e:
                        print(f"Error clearing {layout_attr_name}: {e}")
            return False

        safe_clear_layout('customize_layout')

    def init_ui(self):
        self.instrument_layout = QVBoxLayout()
        self.customize_layout = QVBoxLayout()
        self.customize_layout.addLayout(self.instrument_layout)
        self.customize_layout.addWidget(self.figure_layout_ui())
        self.customize_layout.addWidget(self.button_layout_ui())
        self.bk9205_layout_ui()
        return self.customize_layout

    def figure_layout_ui(self):
        try:
            from instrument.rigol_spectrum_analyzer import RIGOL_COMMAND
            from instrument.BK_precision_9129B import BK_9129_COMMAND
            from GUI.Experiment.measurement import WideComboBox
        except ImportError:
            from QuDAP.instrument.rigol_spectrum_analyzer import RIGOL_COMMAND
            from QuDAP.instrument.BK_precision_9129B import BK_9129_COMMAND
            from QuDAP.GUI.Experiment.measurement import WideComboBox

        figure_group_box = QGroupBox("Graph")
        figure_content_layout = QHBoxLayout()
        cumulative_figure_Layout = QVBoxLayout()
        self.cumulative_canvas = MplCanvas(self, width=100, height=4, dpi=100)
        cumulative_toolbar = NavigationToolbar(self.cumulative_canvas, self)
        cumulative_toolbar.setStyleSheet("""
                                                                                QWidget {
                                                                                    border: None;
                                                                                }
                                                                            """)
        cumulative_figure_Layout.addWidget(cumulative_toolbar, alignment=Qt.AlignmentFlag.AlignCenter)
        cumulative_figure_Layout.addWidget(self.cumulative_canvas, alignment=Qt.AlignmentFlag.AlignCenter)
        figure_content_layout.addLayout(cumulative_figure_Layout)

        single_figure_Layout = QVBoxLayout()
        self.single_canvas = MplCanvas(self, width=100, height=4, dpi=100)
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
        figure_group_box.setFixedSize(1150, 400)
        return figure_group_box

    def button_layout_ui(self):
        self.buttons_layout = QHBoxLayout()
        self.start_measurement_btn = QPushButton('Start')
        self.start_measurement_btn.clicked.connect(self.start_measurement)
        self.stop_btn = QPushButton('Stop')
        self.stop_btn.clicked.connect(self.stop_measurement)
        self.rst_btn = QPushButton('Reset')
        # self.rst_btn.clicked.connect(self.rst)
        self.start_measurement_btn.setStyleSheet(self.Button_stylesheet)
        self.stop_btn.setStyleSheet(self.Button_stylesheet)
        self.rst_btn.setStyleSheet(self.Button_stylesheet)
        self.buttons_layout.addStretch(4)
        # self.buttons_layout.addWidget(self.rst_btn)
        self.buttons_layout.addWidget(self.stop_btn)
        self.buttons_layout.addWidget(self.start_measurement_btn)
        self.button_container = QWidget()
        self.button_container.setLayout(self.buttons_layout)
        self.button_container.setFixedSize(1150, 80)
        return self.button_container

    def bk9205_layout_ui(self):
        self.bk9205_main_layout = QHBoxLayout()

        bk9205_reading_groupbox = QGroupBox("BK9205 Reading")
        bk9205_reading_groupbox.setLayout(self.bk9205_window_reading_ui())
        bk9205_reading_groupbox.setFixedWidth(560)

        bk9205_setting_groupbox = QGroupBox("BK9205 Setting")
        bk9205_setting_groupbox.setLayout(self.bk9205_window_setting_ui())
        bk9205_setting_groupbox.setFixedWidth(560)

        self.bk9205_main_layout.addWidget(bk9205_reading_groupbox)
        self.bk9205_main_layout.addWidget(bk9205_setting_groupbox)
        self.instrument_layout.addLayout(self.bk9205_main_layout)

    def bk9205_window_reading_ui(self):
        self.bk9205_window_reading_layout = QVBoxLayout()
        bk9205_channel_1_layout, self.bk9205_channel_1_state_reading_label, self.bk9205_channel_1_voltage_reading_label, self.bk9205_channel_1_current_reading_label = self.bk9205_reading_channel_layout('1')
        self.bk9205_window_reading_layout.addLayout(bk9205_channel_1_layout)

        bk9205_channel_2_layout, self.bk9205_channel_2_state_reading_label, self.bk9205_channel_2_voltage_reading_label, self.bk9205_channel_2_current_reading_label = self.bk9205_reading_channel_layout('2')
        self.bk9205_window_reading_layout.addLayout(bk9205_channel_2_layout)

        bk9205_channel_3_layout, self.bk9205_channel_3_state_reading_label, self.bk9205_channel_3_voltage_reading_label, self.bk9205_channel_3_current_reading_label = self.bk9205_reading_channel_layout('3')
        self.bk9205_window_reading_layout.addLayout(bk9205_channel_3_layout)
        return self.bk9205_window_reading_layout

    def bk9205_reading_channel_layout(self, current_channel):
        bk9205_channel_layout = QVBoxLayout()
        bk9205_channel_state_layout = QHBoxLayout()
        bk9205_channel_state_label = QLabel(f'Channel {current_channel} State:')
        bk9205_channel_state_label.setFont(self.font)
        bk9205_channel_state_reading_label = QLabel('Unknown')
        bk9205_channel_state_reading_label.setFont(self.font)
        bk9205_channel_state_layout.addWidget(bk9205_channel_state_label)
        bk9205_channel_state_layout.addWidget(bk9205_channel_state_reading_label)
        bk9205_channel_state_layout.addStretch(1)

        bk9205_channel_current_voltage_layout = QHBoxLayout()
        bk9205_channel_voltage_label = QLabel('Voltage:')
        bk9205_channel_voltage_label.setFont(self.font)
        bk9205_channel_voltage_reading_label = QLabel('N/A')
        bk9205_channel_voltage_reading_label.setFont(self.font)
        bk9205_channel_current_label = QLabel('Current:')
        bk9205_channel_current_label.setFont(self.font)
        bk9205_channel_current_reading_label = QLabel('N/A')
        bk9205_channel_current_reading_label.setFont(self.font)
        bk9205_channel_current_voltage_layout.addStretch(1)
        bk9205_channel_current_voltage_layout.addWidget(bk9205_channel_voltage_label)
        bk9205_channel_current_voltage_layout.addWidget(bk9205_channel_voltage_reading_label)
        bk9205_channel_current_voltage_layout.addStretch(1)
        bk9205_channel_current_voltage_layout.addWidget(bk9205_channel_current_label)
        bk9205_channel_current_voltage_layout.addWidget(bk9205_channel_current_reading_label)
        bk9205_channel_current_voltage_layout.addStretch(1)

        bk9205_channel_layout.addLayout(bk9205_channel_state_layout)
        bk9205_channel_layout.addLayout(bk9205_channel_current_voltage_layout)
        return bk9205_channel_layout, bk9205_channel_state_reading_label, bk9205_channel_voltage_reading_label, bk9205_channel_current_reading_label

    def bk9205_window_setting_ui(self):
        self.bk9205_setting_layout = QVBoxLayout()

        bk9205_channel_selection_layout = QHBoxLayout()
        bk9205_channel_selection_label = QLabel('Select Output Channel:')
        bk9205_channel_selection_label.setFont(self.font)
        # from QuDAP.GUI.Experiment.measurement import WideComboBox
        self.bk9205_channel_selection_combo_box = QComboBox()
        self.bk9205_channel_selection_combo_box.setFont(self.font)
        self.bk9205_channel_selection_combo_box.setStyleSheet(self.QCombo_stylesheet)
        self.bk9205_channel_selection_combo_box.addItems(
            ["Select Input Mode", "Channel 1", "Channel 2", "Channel 3", "Ch1 and Ch2 in series", "Ch1 and Ch2 in parallel", 'All Channels'])
        self.bk9205_channel_selection_combo_box.currentIndexChanged.connect(self.bk9205_window_setting_source_ui)

        bk9205_channel_selection_layout.addWidget(bk9205_channel_selection_label)
        bk9205_channel_selection_layout.addWidget(self.bk9205_channel_selection_combo_box)
        self.bk9205_source_layout = QVBoxLayout()
        self.bk9205_range_layout = QVBoxLayout()
        self.bk9205_setting_layout.addLayout(bk9205_channel_selection_layout)
        self.bk9205_setting_layout.addLayout(self.bk9205_source_layout)
        self.bk9205_setting_layout.addLayout(self.bk9205_range_layout)
        return self.bk9205_setting_layout

    def bk9205_window_setting_source_ui(self):
        self.bk9205_source_label_layout = QHBoxLayout()
        bk9205_source_selection_layout = QLabel('Select Output Source:')
        bk9205_source_selection_layout.setFont(self.font)
        # from QuDAP.GUI.Experiment.measurement import WideComboBox
        self.bk9205_source_selection_combo_box = QComboBox()
        self.bk9205_source_selection_combo_box.setFont(self.font)
        self.bk9205_source_selection_combo_box.setStyleSheet(self.QCombo_stylesheet)
        self.bk9205_source_selection_combo_box.addItems(
            ["Select Source", "Voltage", "Current"])
        self.bk9205_source_selection_combo_box.currentIndexChanged.connect(self.bk9205_window_setting_channel_ui)
        self.safe_clear_layout("bk9205_source_layout")
        self.safe_clear_layout("bk9205_range_layout")
        self.bk9205_source_label_layout.addWidget(bk9205_source_selection_layout)
        self.bk9205_source_label_layout.addWidget(self.bk9205_source_selection_combo_box)
        self.bk9205_source_layout.addLayout(self.bk9205_source_label_layout)

    def bk9205_window_setting_channel_ui(self):
        """
        Modified version using merged channel approach for series and parallel configurations.
        Replace your existing bk9205_window_setting_channel_ui with this version.
        """
        bk9205_source_selection_index = self.bk9205_source_selection_combo_box.currentIndex()
        bk9205_channel_selection_index = self.bk9205_channel_selection_combo_box.currentIndex()
        self.safe_clear_layout("bk9205_range_layout")

        if bk9205_channel_selection_index == 0:
            self.safe_clear_layout("bk9205_range_layout")

        # Single Channels
        elif bk9205_channel_selection_index == 1 and bk9205_source_selection_index == 1:
            self._create_channel_ui(1, 'Channel 1', 'voltage')
        elif bk9205_channel_selection_index == 1 and bk9205_source_selection_index == 2:
            self._create_channel_ui(1, 'Channel 1', 'current')
        elif bk9205_channel_selection_index == 2 and bk9205_source_selection_index == 1:
            self._create_channel_ui(2, 'Channel 2', 'voltage')
        elif bk9205_channel_selection_index == 2 and bk9205_source_selection_index == 2:
            self._create_channel_ui(2, 'Channel 2', 'current')
        elif bk9205_channel_selection_index == 3 and bk9205_source_selection_index == 1:
            self._create_channel_ui(3, 'Channel 3', 'voltage')
        elif bk9205_channel_selection_index == 3 and bk9205_source_selection_index == 2:
            self._create_channel_ui(3, 'Channel 3', 'current')

        # Series Configuration (MERGED as channel 4)
        elif bk9205_channel_selection_index == 4 and bk9205_source_selection_index == 1:
            self._create_channel_ui(4, 'Ch1 & Ch2 (Series)', 'voltage')
        elif bk9205_channel_selection_index == 4 and bk9205_source_selection_index == 2:
            self._create_channel_ui(4, 'Ch1 & Ch2 (Series)', 'current')

        # Parallel Configuration (MERGED as channel 4)
        elif bk9205_channel_selection_index == 5 and bk9205_source_selection_index == 1:
            self._create_channel_ui(4, 'Ch1 & Ch2 (Parallel)', 'voltage')
        elif bk9205_channel_selection_index == 5 and bk9205_source_selection_index == 2:
            self._create_channel_ui(4, 'Ch1 & Ch2 (Parallel)', 'current')

        # All Channels
        elif bk9205_channel_selection_index == 6 and bk9205_source_selection_index == 1:
            self._create_channel_ui(1, 'Channel 1', 'voltage')
            self._create_channel_ui(2, 'Channel 2', 'voltage')
            self._create_channel_ui(3, 'Channel 3', 'voltage')
        elif bk9205_channel_selection_index == 6 and bk9205_source_selection_index == 2:
            self._create_channel_ui(1, 'Channel 1', 'current')
            self._create_channel_ui(2, 'Channel 2', 'current')
            self._create_channel_ui(3, 'Channel 3', 'current')

        self.bk9205_range_layout.update()
        if self.bk9205_setting_layout.parentWidget():
            self.bk9205_setting_layout.parentWidget().updateGeometry()

    def _create_channel_ui(self, channel_num, channel_name, source_type):
        """Helper to create UI for a single channel."""
        from PyQt6.QtWidgets import QVBoxLayout

        ch_prefix = f'bk9205_ch{channel_num}'
        source_prefix = source_type

        # Create mode selection UI
        mode_layout, mode_group, fixed_radio, range_radio = self.bk9205_window_setting_voltage_fix_range_mode(
            channel=channel_name, type=source_type)
        self.bk9205_range_layout.addLayout(mode_layout)

        # Store references
        setattr(self, f'{ch_prefix}_{source_prefix}_mode_layout', mode_layout)
        setattr(self, f'{ch_prefix}_{source_prefix}_mode_group', mode_group)
        setattr(self, f'{ch_prefix}_{source_prefix}_fixed_radio', fixed_radio)
        setattr(self, f'{ch_prefix}_{source_prefix}_range_radio', range_radio)

        # Create dynamic layout container
        dynamic_layout = QVBoxLayout()
        self.bk9205_range_layout.addLayout(dynamic_layout)
        setattr(self, f'{ch_prefix}_{source_prefix}_dynamic_layout', dynamic_layout)

        # Create update function
        def update_mode():
            self.safe_clear_layout(f'{ch_prefix}_{source_prefix}_dynamic_layout')
            if fixed_radio.isChecked():
                fixed_layout, fixed_entry, fixed_unit = self.bk9205_window_setting_voltage_current_fixed_ui(
                    channel=channel_name, type=source_type)
                dynamic_layout.addLayout(fixed_layout)
                setattr(self, f'bk9205_channel{channel_num}_{source_type}_fixed_layout', fixed_layout)
                setattr(self, f'bk9205_channel{channel_num}_{source_type}_fixed_entry', fixed_entry)
                setattr(self, f'bk9205_channel{channel_num}_{source_type}_fixed_unit', fixed_unit)
            else:
                range_layout, range_from, range_to, range_step = self.bk9205_window_setting_voltage_current_range_ui(
                    channel=channel_name, type=source_type)
                dynamic_layout.addLayout(range_layout)
                setattr(self, f'bk9205_channel{channel_num}_{source_type}_range_setting_layout', range_layout)
                setattr(self, f'bk9205_channel{channel_num}_{source_type}_range_setting_from', range_from)
                setattr(self, f'bk9205_channel{channel_num}_{source_type}_range_setting_to', range_to)
                setattr(self, f'bk9205_channel{channel_num}_{source_type}_range_setting_step', range_step)

        mode_group.buttonClicked.connect(update_mode)
        update_mode()

    # -------------------------------------------------------------------------
    # MEASUREMENT EXTRACTION METHODS (add these to your class)
    # -------------------------------------------------------------------------

    def extract_measurement_data(self):
        """
        Extracts all measurement settings from the UI.

        Returns a dictionary with structure:
        {
            'channel_mode': 'single'/'series'/'parallel'/'all',
            'source_type': 'voltage'/'current',
            'channels': {
                'ch1': {'enabled': bool, 'mode': 'fixed'/'range', 'values': [list], 'unit': str},
                'ch2': {...},
                'ch3': {...},
                'merged': {...}  # For series/parallel
            }
        }
        """
        bk9205_source_selection_index = self.bk9205_source_selection_combo_box.currentIndex()
        bk9205_channel_selection_index = self.bk9205_channel_selection_combo_box.currentIndex()

        result = {
            'channel_mode': None,
            'source_type': 'voltage' if bk9205_source_selection_index == 1 else 'current',
            'channels': {
                'ch1': {'enabled': False, 'mode': None, 'values': [], 'unit': None},
                'ch2': {'enabled': False, 'mode': None, 'values': [], 'unit': None},
                'ch3': {'enabled': False, 'mode': None, 'values': [], 'unit': None},
                'merged': {'enabled': False, 'mode': None, 'values': [], 'unit': None}
            }
        }

        if bk9205_channel_selection_index == 0:
            result['channel_mode'] = 'none'
        elif bk9205_channel_selection_index == 1:
            result['channel_mode'] = 'single'
            result['channels']['ch1'] = self._extract_channel_data(1, result['source_type'])
        elif bk9205_channel_selection_index == 2:
            result['channel_mode'] = 'single'
            result['channels']['ch2'] = self._extract_channel_data(2, result['source_type'])
        elif bk9205_channel_selection_index == 3:
            result['channel_mode'] = 'single'
            result['channels']['ch3'] = self._extract_channel_data(3, result['source_type'])
        elif bk9205_channel_selection_index == 4:
            result['channel_mode'] = 'series'
            result['channels']['merged'] = self._extract_channel_data(4, result['source_type'])
        elif bk9205_channel_selection_index == 5:
            result['channel_mode'] = 'parallel'
            result['channels']['merged'] = self._extract_channel_data(4, result['source_type'])
        elif bk9205_channel_selection_index == 6:
            result['channel_mode'] = 'all'
            result['channels']['ch1'] = self._extract_channel_data(1, result['source_type'])
            result['channels']['ch2'] = self._extract_channel_data(2, result['source_type'])
            result['channels']['ch3'] = self._extract_channel_data(3, result['source_type'])

        return result

    def _extract_channel_data(self, channel_num, source_type):
        """Extract data for a specific channel."""
        channel_data = {'enabled': False, 'mode': None, 'values': [], 'unit': None}

        ch_prefix = f'bk9205_ch{channel_num}'
        source_prefix = 'voltage' if source_type == 'voltage' else 'current'

        fixed_radio_name = f'{ch_prefix}_{source_prefix}_fixed_radio'

        if not hasattr(self, fixed_radio_name):
            return channel_data

        fixed_radio = getattr(self, f'{ch_prefix}_{source_prefix}_fixed_radio')
        range_radio = getattr(self, f'{ch_prefix}_{source_prefix}_range_radio')

        channel_data['enabled'] = True

        if fixed_radio.isChecked():
            channel_data['mode'] = 'fixed'
            channel_data.update(self._extract_fixed_mode_data(channel_num, source_type))
        elif range_radio.isChecked():
            channel_data['mode'] = 'range'
            channel_data.update(self._extract_range_mode_data(channel_num, source_type))

        return channel_data

    def _extract_fixed_mode_data(self, channel_num, source_type):
        """Extract data from fixed mode UI."""
        ch_name = f'channel{channel_num}'
        source = 'voltage' if source_type == 'voltage' else 'current'

        entry_name = f'bk9205_{ch_name}_{source}_fixed_entry'
        unit_name = f'bk9205_{ch_name}_{source}_fixed_unit'

        if not hasattr(self, entry_name):
            return {'values': [], 'unit': None}

        entry = getattr(self, entry_name)
        unit_combo = getattr(self, unit_name)

        try:
            value = float(entry.text())
            unit = unit_combo.currentText()
            converted_value = self._convert_to_base_unit(value, unit)
            return {
                'values': [converted_value],
                'unit': 'V' if source_type == 'voltage' else 'A'
            }
        except (ValueError, AttributeError):
            return {'values': [], 'unit': None}

    def _extract_range_mode_data(self, channel_num, source_type):
        """Extract data from range mode UI and generate value list."""
        ch_name = f'channel{channel_num}'
        source = 'voltage' if source_type == 'voltage' else 'current'

        from_name = f'bk9205_{ch_name}_{source}_range_setting_from'
        to_name = f'bk9205_{ch_name}_{source}_range_setting_to'
        step_name = f'bk9205_{ch_name}_{source}_range_setting_step'

        if not hasattr(self, from_name):
            return {'values': [], 'unit': None}

        from_entry = getattr(self, from_name)
        to_entry = getattr(self, to_name)
        step_entry = getattr(self, step_name)

        try:
            from_value = float(from_entry.text())
            to_value = float(to_entry.text())
            step_value = float(step_entry.text())

            values = self._generate_range_values(from_value, to_value, step_value)

            return {
                'values': values,
                'unit': 'V' if source_type == 'voltage' else 'A'
            }
        except (ValueError, AttributeError):
            return {'values': [], 'unit': None}

    def _generate_range_values(self, from_val, to_val, step):
        """
        Generates list of values from range.
        Example: _generate_range_values(1, 5, 1) returns [1, 2, 3, 4, 5]
        """
        if step <= 0:
            return []

        values = []
        current = from_val

        if from_val <= to_val:
            while current <= to_val:
                values.append(round(current, 10))
                current += step
        else:
            while current >= to_val:
                values.append(round(current, 10))
                current -= step

        return values

    def _convert_to_base_unit(self, value, unit):
        """Convert value to base unit (V or A)."""
        conversion_factors = {
            'V': 1, 'kV': 1000, 'mV': 0.001, 'µV': 0.000001,
            'A': 1, 'mA': 0.001, 'µA': 0.000001
        }
        return value * conversion_factors.get(unit, 1)

    def get_measurement_summary(self):
        """Get human-readable summary of measurement configuration."""
        data = self.extract_measurement_data()

        summary = []
        summary.append(f"Channel Mode: {data['channel_mode']}")
        summary.append(f"Source Type: {data['source_type']}")
        summary.append("")

        for ch_name, ch_data in data['channels'].items():
            if ch_data['enabled']:
                ch_label = ch_name.upper().replace('MERGED', 'CH1+CH2')
                summary.append(f"{ch_label}:")
                summary.append(f"  Mode: {ch_data['mode']}")
                summary.append(f"  Values: {ch_data['values']}")
                summary.append(f"  Unit: {ch_data['unit']}")
                summary.append("")

        return "\n".join(summary)

    def bk9205_window_setting_voltage_fix_range_mode(self, channel='', type='voltage'):
        """
        Creates a UI with button group showing Fixed and Range options for voltage/current selection.

        Args:
            channel: Channel name (e.g., 'Channel 1', 'Channel 2', etc.)
            type: 'voltage' or 'current'

        Returns:
            layout: The layout containing the Fixed/Range selection
            button_group: QButtonGroup for the radio buttons
            fixed_radio: Radio button for Fixed mode
            range_radio: Radio button for Range mode
        """
        bk9205_fix_range_layout = QVBoxLayout()

        # Create label for the selection
        mode_selection_label = QLabel(f'{channel} - Select {type.capitalize()} Mode:')
        mode_selection_label.setFont(self.font)

        # Create button group for Fixed/Range selection
        button_group = QButtonGroup()

        # Create radio buttons
        fixed_radio = QRadioButton('Fixed')
        fixed_radio.setFont(self.font)
        range_radio = QRadioButton('Range')
        range_radio.setFont(self.font)

        # Add radio buttons to button group
        button_group.addButton(fixed_radio, 0)  # ID 0 for Fixed
        button_group.addButton(range_radio, 1)  # ID 1 for Range

        # Set default selection
        fixed_radio.setChecked(True)

        # Create horizontal layout for radio buttons
        radio_buttons_layout = QHBoxLayout()
        radio_buttons_layout.addWidget(fixed_radio)
        radio_buttons_layout.addWidget(range_radio)
        radio_buttons_layout.addStretch(1)

        # Add to main layout
        bk9205_fix_range_layout.addWidget(mode_selection_label)
        bk9205_fix_range_layout.addLayout(radio_buttons_layout)

        return bk9205_fix_range_layout, button_group, fixed_radio, range_radio

    def bk9205_window_setting_voltage_current_fixed_ui(self, channel='', type='voltage'):
        bk9205_setting_layout = QVBoxLayout()

        bk9205_fixed_layout = QHBoxLayout()
        fixed_label = QLabel(f'{channel} Set Voltage:')
        fixed_label.setFont(self.font)
        fixed_entry = QLineEdit()
        fixed_entry.setFont(self.font)
        bk9205_fixed_unit_combo_box = QComboBox()
        bk9205_fixed_unit_combo_box.setFont(self.font)
        bk9205_fixed_unit_combo_box.setStyleSheet(self.QCombo_stylesheet)
        if type == 'voltage':
            bk9205_fixed_unit_combo_box.addItems(["Select Unit", "V", "kV", "mV", "µV"])
        else:
            bk9205_fixed_unit_combo_box.addItems(["Select Unit", "A", "mA", "µA"])
        bk9205_fixed_layout.addWidget(fixed_label)
        bk9205_fixed_layout.addWidget(fixed_entry)
        bk9205_fixed_layout.addWidget(bk9205_fixed_unit_combo_box)

        bk9205_setting_layout.addLayout(bk9205_fixed_layout)
        return bk9205_setting_layout, fixed_entry, bk9205_fixed_unit_combo_box

    def bk9205_window_setting_voltage_current_range_ui(self, channel='', type='voltage'):
        bk9205_setting_layout = QVBoxLayout()

        bk9205_range_layout = QHBoxLayout()
        if type == 'voltage':
            range_from_label = QLabel(f'{channel} Range (V): From')
        else:
            range_from_label = QLabel(f'{channel} Range (A): From')
        range_from_label.setFont(self.font)
        range_from_entry = QLineEdit()
        range_from_entry.setFont(self.font)
        range_to_label = QLabel(' to ')
        range_to_label.setFont(self.font)
        range_to_entry = QLineEdit()
        range_to_entry.setFont(self.font)
        bk9205_range_unit_combo_box = QComboBox()
        bk9205_range_unit_combo_box.setFont(self.font)
        bk9205_range_unit_combo_box.setStyleSheet(self.QCombo_stylesheet)
        if type == 'voltage':
            bk9205_range_unit_combo_box.addItems(["Select Unit", "V", "kV", "mV", "µV"])
        else:
            bk9205_range_unit_combo_box.addItems(["Select Unit", "A", "mA", "µA"])
        bk9205_range_layout.addWidget(range_from_label)
        bk9205_range_layout.addWidget(range_from_entry)
        bk9205_range_layout.addWidget(range_to_label)
        bk9205_range_layout.addWidget(range_to_entry)
        # bk9205_range_layout.addWidget(bk9205_range_unit_combo_box)

        bk9205_step_layout = QHBoxLayout()
        if type == 'voltage':
            step_label = QLabel('Step Size (V):')
        else:
            step_label = QLabel('Step Size (A):')
        step_label.setFont(self.font)
        step_entry = QLineEdit()
        step_entry.setFont(self.font)
        step_unit_combo_box = QComboBox()
        step_unit_combo_box.setFont(self.font)
        step_unit_combo_box.setStyleSheet(self.QCombo_stylesheet)
        if type == 'voltage':
            step_unit_combo_box.addItems(["Select Unit", "V", "kV", "mV", "µV"])
        else:
            step_unit_combo_box.addItems(["Select Unit", "A", "mA", "µA"])
        bk9205_step_layout.addWidget(step_label)
        bk9205_step_layout.addWidget(step_entry)
        # bk9205_step_layout.addWidget(step_unit_combo_box)

        bk9205_setting_layout.addLayout(bk9205_range_layout)
        bk9205_setting_layout.addLayout(bk9205_step_layout)
        return bk9205_setting_layout, range_from_entry, range_to_entry, step_entry,

    def safe_clear_layout(self, layout_attr_name):
        """Safely clear a layout if it exists"""
        if hasattr(self, layout_attr_name):
            layout = getattr(self, layout_attr_name)
            if layout is not None:
                try:
                    self.clear_layout(layout)
                    return True
                except Exception as e:
                    print(f"Error clearing {layout_attr_name}: {e}")
        return False

    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                if child.layout() is not None:
                    self.clear_layout(child.layout())

    def start_measurement(self):
        dialog = LogWindow()
        if dialog.exec():
            try:
                if self.worker is not None:
                    self.stop_measurement()
                try:
                    self.customize_layout.removeWidget(self.log_box)
                    self.log_box.deleteLater()
                    self.customize_layout.removeWidget(self.progress_bar)
                    self.progress_bar.deleteLater()
                except Exception:
                    pass
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
                self.customize_layout.addWidget(self.progress_bar)
                self.customize_layout.addWidget(self.log_box, alignment=Qt.AlignmentFlag.AlignCenter)
                self.log_box.clear()
                data = self.extract_measurement_data()
                # Validate
                has_enabled_channel = any(ch['enabled'] for ch in data['channels'].values())
                if not has_enabled_channel:
                    QMessageBox.warning(self, 'Warning', 'No channels enabled for measurement')
                    return

                # Check for empty values
                for ch_name, ch_data in data['channels'].items():
                    if ch_data['enabled'] and not ch_data['values']:
                        ch_label = ch_name.upper().replace('merged', 'merged channels')
                        QMessageBox.warning(self, 'Warning', f'No values specified for {ch_label}')
                        return

                # Show summary for confirmation
                summary = self.get_measurement_summary()

                self._prepare_measurement_ui()
                self.worker = BK9205_RIGOL_Worker(
                    parent=self,
                    bk9205_instrument=self.BK_9205_CONNECTED,
                    rigol_instrument=self.RIGOL_CONNECTED,
                    measurement_data=data,
                    folder_path=self.folder_path,
                    file_name=self.file_name,
                    run_number=self.run,
                    demo_mode=getattr(self, 'demo_mode', False),
                    settling_time=1.0,
                    spectrum_averaging=1,
                    save_individual_spectra=True
                )

                # Connect signals
                self._connect_worker_signals()

                # Start measurement
                self.worker.start()

                # Disable start button
                if hasattr(self, 'start_measurement_btn'):
                    self.start_measurement_btn.setEnabled(False)
            except SystemExit as e:
                QMessageBox.critical(
                    self,
                    'Error',
                    f'Failed to start measurement:\n{str(e)}'
                )

            except Exception as e:
                QMessageBox.critical(
                    self,
                    'Error',
                    f'Failed to start measurement:\n{str(e)}'
                )


            #
            # self._connect_worker_signals()
            #
            # # Step 8: Start measurement
            # self.worker.start()

    def _prepare_measurement_ui(self):
        """Prepare UI for measurement (clear plots, create log box, etc.)."""
        try:
            # Clear existing plots
            self.cumulative_canvas.axes.cla()
            self.single_canvas.axes.cla()
            self.cumulative_canvas.draw()
            self.single_canvas.draw()

            # Remove old log box and progress bar if they exist
            if hasattr(self, 'log_box'):
                try:
                    self.customize_layout.removeWidget(self.log_box)
                    self.log_box.deleteLater()
                except:
                    pass

            if hasattr(self, 'progress_bar'):
                try:
                    self.customize_layout.removeWidget(self.progress_bar)
                    self.progress_bar.deleteLater()
                except:
                    pass

            # Create new log box
            from PyQt6.QtWidgets import QTextEdit, QProgressBar
            from PyQt6.QtCore import Qt

            self.log_box = QTextEdit(self)
            self.log_box.setReadOnly(True)
            self.log_box.setFixedSize(1140, 150)

            # Create progress bar
            self.progress_bar = QProgressBar(self)
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setFixedWidth(1140)
            self.progress_bar.setValue(0)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #8f8f91;
                    border-radius: 5px;
                    background-color: #e0e0e0;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #3498db;
                    width: 5px;
                }
            """)

            # Add to layout
            self.customize_layout.addWidget(self.progress_bar)
            self.customize_layout.addWidget(self.log_box, alignment=Qt.AlignmentFlag.AlignCenter)

            self.log_box.clear()

        except Exception as e:
            print(f"Error preparing UI: {str(e)}")

    def _connect_worker_signals(self):
        """Connect all worker signals to GUI slots."""
        # Progress updates
        self.worker.progress_update.connect(self.update_progress)
        self.worker.update_measurement_progress.connect(self.update_measurement_progress)

        # Text logging
        self.worker.append_text.connect(self.append_text)

        # Measurement control
        self.worker.stop_measurement.connect(self.stop_measurement)
        self.worker.measurement_finished.connect(self.measurement_finished)
        self.worker.error_message.connect(self.error_popup)

        # BK9205 channel updates
        self.worker.update_bk9205_ch1_status_label.connect(self.update_bk9205_ch1_status_label)
        self.worker.update_bk9205_ch2_status_label.connect(self.update_bk9205_ch2_status_label)
        self.worker.update_bk9205_ch3_status_label.connect(self.update_bk9205_ch3_status_label)
        self.worker.update_bk9205_ch1_voltage_label.connect(self.update_bk9205_ch1_voltage_label)
        self.worker.update_bk9205_ch1_current_label.connect(self.update_bk9205_ch1_current_label)
        self.worker.update_bk9205_ch2_voltage_label.connect(self.update_bk9205_ch2_voltage_label)
        self.worker.update_bk9205_ch2_current_label.connect(self.update_bk9205_ch2_current_label)
        self.worker.update_bk9205_ch3_voltage_label.connect(self.update_bk9205_ch3_voltage_label)
        self.worker.update_bk9205_ch3_current_label.connect(self.update_bk9205_ch3_current_label)

        # RIGOL updates
        self.worker.update_rigol_freq_label.connect(self.update_rigol_freq_label)
        self.worker.update_rigol_power_label.connect(self.update_rigol_power_label)
        self.worker.save_individual_plot.connect(self.save_individual_spectrum_plot)

        # Plotting
        self.worker.update_2d_plot.connect(self.update_2d_plot)
        self.worker.update_spectrum_plot.connect(self.update_spectrum_plot)
        self.worker.save_plot.connect(self.save_plot)
        self.worker.clear_plot.connect(self.clear_plot)

    def update_progress(self, value):
        """Update progress bar."""
        if hasattr(self, 'progress_bar'):
            self.progress_bar.setValue(value)

    def update_measurement_progress(self, text):
        """Update measurement progress text."""
        # You can display this in a status label
        if hasattr(self, 'measurement_status_label'):
            self.measurement_status_label.setText(text)

    def append_text(self, text):
        """Append text to log box."""
        if hasattr(self, 'log_box'):
            self.log_box.append(text)
            # Auto-scroll to bottom
            scrollbar = self.log_box.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def update_bk9205_ch1_status_label(self, text):
        """Update Ch1 voltage label."""
        if hasattr(self, 'bk9205_channel_1_state_reading_label'):
            self.bk9205_channel_1_state_reading_label.setText(f"{text} V")

    def update_bk9205_ch2_status_label(self, text):
        """Update Ch1 voltage label."""
        if hasattr(self, 'bk9205_channel_2_state_reading_label'):
            self.bk9205_channel_2_state_reading_label.setText(f"{text} V")

    def update_bk9205_ch3_status_label(self, text):
        """Update Ch1 voltage label."""
        if hasattr(self, 'bk9205_channel_3_state_reading_label'):
            self.bk9205_channel_3_state_reading_label.setText(f"{text} V")

    def update_bk9205_ch1_voltage_label(self, text):
        """Update Ch1 voltage label."""
        if hasattr(self, 'bk9205_channel_1_voltage_reading_label'):
            self.bk9205_channel_1_voltage_reading_label.setText(f"{text} V")

    def update_bk9205_ch1_current_label(self, text):
        """Update Ch1 current label."""
        if hasattr(self, 'bk9205_channel_1_current_reading_label'):
            self.bk9205_channel_1_current_reading_label.setText(f"{text} A")

    def update_bk9205_ch2_voltage_label(self, text):
        """Update Ch2 voltage label."""
        if hasattr(self, 'bk9205_channel_2_voltage_reading_label'):
            self.bk9205_channel_2_voltage_reading_label.setText(f"{text} V")

    def update_bk9205_ch2_current_label(self, text):
        """Update Ch2 current label."""
        if hasattr(self, 'bk9205_channel_2_current_reading_label'):
            self.bk9205_channel_2_current_reading_label.setText(f"{text} A")

    def update_bk9205_ch3_voltage_label(self, text):
        """Update Ch3 voltage label."""
        if hasattr(self, 'bk9205_channel_3_voltage_reading_label'):
            self.bk9205_channel_3_voltage_reading_label.setText(f"{text} V")

    def update_bk9205_ch3_current_label(self, text):
        """Update Ch3 current label."""
        if hasattr(self, 'bk9205_channel_3_current_reading_label'):
            self.bk9205_channel_3_current_reading_label.setText(f"{text} A")

    def update_rigol_freq_label(self, text):
        """Update RIGOL frequency label."""
        if hasattr(self, 'rigol_freq_label'):
            self.rigol_freq_label.setText(text)

    def update_rigol_power_label(self, text):
        """Update RIGOL power label."""
        if hasattr(self, 'rigol_power_label'):
            self.rigol_power_label.setText(text)

    def update_2d_plot(self, x_data, y_data, z_data):
        """
        Update 2D cumulative plot (left plot).
        Creates a 2D colormap showing frequency vs voltage with spectrum power as color.

        Args:
            x_data: List of frequencies (Hz) - can be from first spectrum
            y_data: List of voltage/current values for each measurement
            z_data: List of spectra (each spectrum is a list of power values)
        """
        if not hasattr(self, 'cumulative_canvas'):
            return

        try:
            import numpy as np

            # Clear the figure completely to avoid colorbar issues
            self.cumulative_canvas.figure.clear()

            # Create new axes
            self.cumulative_canvas.axes = self.cumulative_canvas.figure.add_subplot(111)

            # Reset colorbar reference
            self.cumulative_colorbar = None

            # Convert frequencies to GHz for better readability
            freq_ghz = np.array(x_data) / 1e9

            # Create 2D array: rows = different voltages, columns = frequency points
            # z_data should be a 2D array where each row is a spectrum
            Z = np.array(z_data)  # Shape: (num_voltages, num_freq_points)

            # Create meshgrid for plotting
            Y, X = np.meshgrid(y_data, freq_ghz)

            # Create 2D heatmap
            im = self.cumulative_canvas.axes.pcolormesh(
                X, Y, Z.T,  # Transpose Z to match meshgrid dimensions
                cmap='viridis',
                shading='auto'
            )

            # Alternative: Use contourf for smoother appearance
            # levels = 20
            # im = self.cumulative_canvas.axes.contourf(
            #     X, Y, Z.T,
            #     levels=levels,
            #     cmap='viridis'
            # )

            # Add colorbar
            try:
                self.cumulative_colorbar = self.cumulative_canvas.figure.colorbar(
                    im,
                    ax=self.cumulative_canvas.axes,
                    label='Power (dBm)',
                    pad=0.02
                )
            except Exception as e:
                print(f"Warning: Could not create colorbar: {e}")

            # Labels and styling
            self.cumulative_canvas.axes.set_xlabel('Frequency (GHz)', fontsize=11, fontweight='bold')

            # Determine ylabel based on worker's measurement_data
            if hasattr(self, 'worker') and self.worker is not None and hasattr(self.worker, 'measurement_data'):
                source_type = self.worker.measurement_data.get('source_type', 'voltage').capitalize()
                unit = 'V' if source_type.lower() == 'voltage' else 'A'
            else:
                source_type = 'Value'
                unit = 'V/A'

            self.cumulative_canvas.axes.set_ylabel(f'{source_type} ({unit})', fontsize=11, fontweight='bold')
            self.cumulative_canvas.axes.set_title('Frequency vs Voltage Spectrum Map', fontsize=13, fontweight='bold')

            # Adjust layout
            try:
                self.cumulative_canvas.figure.tight_layout()
            except Exception as e:
                print(f"Warning: tight_layout failed: {e}")

            # Draw the canvas
            self.cumulative_canvas.draw()

        except Exception as e:
            print(f"Error updating 2D plot: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def update_spectrum_plot(self, freq_data, power_data):
        """
        Update spectrum plot (right plot).
        Shows the latest captured spectrum.

        Args:
            freq_data: List of frequencies in Hz
            power_data: List of power values in dBm
        """
        if not hasattr(self, 'single_canvas'):
            return

        try:
            import numpy as np

            # Clear the axes
            self.single_canvas.axes.clear()

            # Convert frequency to GHz for better readability
            freq_ghz = [f / 1e9 for f in freq_data]

            # Plot spectrum
            self.single_canvas.axes.plot(
                freq_ghz,
                power_data,
                'r-',
                linewidth=1.5,
                label='Spectrum'
            )

            # Find and mark peak
            peak_power = max(power_data)
            peak_idx = power_data.index(peak_power)
            peak_freq = freq_ghz[peak_idx]

            self.single_canvas.axes.plot(
                peak_freq,
                peak_power,
                'go',
                markersize=10,
                markeredgecolor='black',
                markeredgewidth=1.5,
                label=f'Peak: {peak_power:.2f} dBm @ {peak_freq:.3f} GHz',
                zorder=3
            )

            # Add vertical line at peak
            self.single_canvas.axes.axvline(
                peak_freq,
                color='green',
                linestyle='--',
                alpha=0.5,
                linewidth=1
            )

            # Labels and styling
            self.single_canvas.axes.set_xlabel('Frequency (GHz)', fontsize=11, fontweight='bold')
            self.single_canvas.axes.set_ylabel('Power (dBm)', fontsize=11, fontweight='bold')
            self.single_canvas.axes.set_title('Latest Spectrum', fontsize=13, fontweight='bold')
            self.single_canvas.axes.grid(True, alpha=0.3, linestyle='--', linewidth=0.8)
            self.single_canvas.axes.legend(loc='upper right', fontsize=9)

            # Set reasonable y-axis limits
            y_min = min(power_data)
            y_max = max(power_data)
            y_range = y_max - y_min
            self.single_canvas.axes.set_ylim(y_min - 0.1 * y_range, y_max + 0.1 * y_range)

            # Tight layout
            try:
                self.single_canvas.figure.tight_layout()
            except Exception as e:
                print(f"Warning: tight_layout failed: {e}")

            # Draw the canvas
            self.single_canvas.draw()

        except Exception as e:
            print(f"Error updating spectrum plot: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def clear_plot(self):
        """Clear all plots."""
        try:
            if hasattr(self, 'cumulative_canvas'):
                self.cumulative_canvas.figure.clear()
                self.cumulative_canvas.axes = self.cumulative_canvas.figure.add_subplot(111)
                self.cumulative_canvas.axes.set_title('Waiting for measurement...')
                self.cumulative_canvas.draw()
                self.cumulative_colorbar = None

            if hasattr(self, 'single_canvas'):
                self.single_canvas.axes.clear()
                self.single_canvas.axes.set_title('Waiting for spectrum...')
                self.single_canvas.draw()
        except Exception as e:
            print(f"Error clearing plots: {e}")

    def save_individual_spectrum_plot(self, filename):
        """Save current spectrum plot (right side) to file."""
        try:
            spectrum_file = f"{self.folder_path}/{filename}"
            self.single_canvas.figure.savefig(
                spectrum_file,
                dpi=300,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )
            self.append_text(f"    ✓ Spectrum plot saved: {filename}")
        except Exception as e:
            self.append_text(f"    ✗ Error saving spectrum plot: {str(e)}")

    def save_plot(self, filename):
        """Save current plots to files."""
        try:
            # Save cumulative plot
            cumulative_file = f"{self.folder_path}/{filename}_cumulative.png"
            self.cumulative_canvas.figure.savefig(
                cumulative_file,
                dpi=300,
                bbox_inches='tight',
                facecolor='white',
                edgecolor='none'
            )

            # # Save spectrum plot
            # spectrum_file = f"{self.folder_path}/{filename}_spectrum.png"
            # self.single_canvas.figure.savefig(
            #     spectrum_file,
            #     dpi=300,
            #     bbox_inches='tight',
            #     facecolor='white',
            #     edgecolor='none'
            # )

            self.append_text(f"✓ Plots saved: {filename}_cumulative.png, {filename}_spectrum.png")

        except Exception as e:
            self.append_text(f"✗ Error saving plots: {str(e)}")
            import traceback
            self.append_text(traceback.format_exc())

    def stop_measurement(self):
        """Stop the measurement."""
        if hasattr(self, 'worker') and self.worker is not None:
            self.worker.stop()
            self.worker.wait()
            self.worker = None
            self.append_text("Measurement stopped by user")

        # Re-enable start button
        if hasattr(self, 'start_measurement_btn'):
            self.start_measurement_btn.setEnabled(True)

    def measurement_finished(self):
        """Called when measurement completes."""
        self.append_text("\n" + "=" * 60)
        self.append_text("Measurement finished successfully!")
        self.append_text("=" * 60)

        # Re-enable start button
        if hasattr(self, 'start_measurement_btn'):
            self.start_measurement_btn.setEnabled(True)

        # Show completion message
        QMessageBox.information(
            self,
            'Measurement Complete',
            f'Measurement completed successfully!\n\nData saved to:\n{self.folder_path}'
        )

    def error_popup(self, message):
        """Show error popup."""
        QMessageBox.critical(self, 'Error', message)

    # =========================================================================
    # BUTTON HANDLERS
    # =========================================================================

    def pause_button_clicked(self):
        """Handle pause button click."""
        if self.worker is not None:
            self.worker.pause()

    def resume_button_clicked(self):
        """Handle resume button click."""
        if self.worker is not None:
            self.worker.resume()

    def stop_button_clicked(self):
        """Handle stop button click."""
        reply = QMessageBox.question(
            self,
            'Confirm Stop',
            'Are you sure you want to stop the measurement?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.stop_measurement()

if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = RIGOL_Measurement(None, None)
    window.show()
    sys.exit(app.exec())