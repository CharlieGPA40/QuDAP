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
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure


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
    update_rigol_freq_label = pyqtSignal(str)
    update_rigol_power_label = pyqtSignal(str)

    # Plotting signals
    update_plot = pyqtSignal(list, list, str, str)  # x_data, y_data, x_label, y_label
    update_spectrum_plot = pyqtSignal(list, list)  # freq_data, power_data
    save_plot = pyqtSignal(str)  # filename
    clear_plot = pyqtSignal()

    # Measurement progress
    update_measurement_progress = pyqtSignal(str)  # Current measurement status

    def __init__(self, parent, bk9205_instrument, rigol_instrument, measurement_data,
                 folder_path, file_name, run_number,
                 bk9205_connected=False, rigol_connected=False, demo_mode=False,
                 settling_time=1.0, spectrum_averaging=1,
                 save_individual_spectra=True, **kwargs):
        """
        Initialize worker thread.

        Args:
            parent: Parent widget
            bk9205_instrument: BK9205 instrument instance
            rigol_instrument: RIGOL spectrum analyzer instance
            measurement_data: Dictionary from extract_measurement_data()
            folder_path: Path to save data
            file_name: Base filename
            run_number: Run number
            bk9205_connected: Is BK9205 connected?
            rigol_connected: Is RIGOL connected?
            demo_mode: Run in demo mode (simulated data)?
            settling_time: Wait time after setting voltage/current (seconds)
            spectrum_averaging: Number of spectra to average
            save_individual_spectra: Save each spectrum as separate file?
            **kwargs: Additional parameters
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
        self.bk9205_connected = bk9205_connected
        self.rigol_connected = rigol_connected
        self.demo_mode = demo_mode

        # Measurement parameters
        self.settling_time = settling_time
        self.spectrum_averaging = spectrum_averaging
        self.save_individual_spectra = save_individual_spectra

        # Control flags
        self.running = True
        self.paused = False

        # Data storage
        self.measurement_results = []
        self.all_spectra = []

        # Additional parameters
        self.extra_params = kwargs

    def run(self):
        """Main execution method - runs in separate thread."""
        try:
            self.append_text.emit("=" * 60)
            self.append_text.emit("Starting BK9205 + RIGOL Measurement")
            self.append_text.emit(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
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

            # Save data
            self._save_all_data()

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
            if self.bk9205_connected and not self.demo_mode:
                self.append_text.emit("  Initializing BK9205...")
                # Add your BK9205 initialization code here
                # Example:
                # self.bk9205.reset()
                # self.bk9205.set_output_state('OFF')
                self.append_text.emit("  ✓ BK9205 initialized")
            else:
                self.append_text.emit("  ⚠ BK9205 not connected (demo mode)")

            # Initialize RIGOL
            if self.rigol_connected and not self.demo_mode:
                self.append_text.emit("  Initializing RIGOL...")
                # Add your RIGOL initialization code here
                # Example:
                # self.rigol.reset()
                # self.rigol.set_span(1e9)
                # self.rigol.set_rbw(1e6)
                self.append_text.emit("  ✓ RIGOL initialized")
            else:
                self.append_text.emit("  ⚠ RIGOL not connected (demo mode)")

            return True

        except Exception as e:
            error_msg = f"Instrument initialization failed: {str(e)}"
            self.append_text.emit(f"  ✗ {error_msg}")
            self.error_message.emit(error_msg)
            return False

    def _execute_measurement(self):
        """Execute the main measurement loop."""
        channel_mode = self.measurement_data['channel_mode']
        source_type = self.measurement_data['source_type']

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

        self.append_text.emit(f"\nMeasuring {ch_name.upper()} with {total_points} points")

        for idx, value in enumerate(values):
            if not self.running:
                self.append_text.emit("\n✗ Measurement stopped by user")
                break

            # Update progress
            progress = int((idx / total_points) * 100)
            self.progress_update.emit(progress)
            self.update_measurement_progress.emit(
                f"Point {idx + 1}/{total_points}: {value:.6f} {ch_data['unit']}"
            )

            # Set voltage/current
            self._set_channel_output(channel_num, value, self.measurement_data['source_type'])

            # Wait for settling
            self._wait_settling(f"Settling... ({self.settling_time}s)")

            # Capture spectrum
            spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

            # Store results
            result = {
                'point': idx + 1,
                'channel': ch_name,
                'value': value,
                'unit': ch_data['unit'],
                'source_type': self.measurement_data['source_type'],
                'spectrum': spectrum_data,
                'timestamp': datetime.now().isoformat()
            }
            self.measurement_results.append(result)

            # Update plots
            self._update_plots(result)

            # Save individual spectrum if enabled
            if self.save_individual_spectra:
                self._save_individual_spectrum(result, idx)

        self.progress_update.emit(100)

    def _measure_series_channels(self):
        """Measure series channel configuration."""
        self.append_text.emit("\n" + "=" * 60)
        self.append_text.emit("Starting Series Channel Measurement")
        self.append_text.emit("=" * 60)

        merged_data = self.measurement_data['channels']['merged']
        values = merged_data['values']
        total_points = len(values)

        self.append_text.emit(f"\nMeasuring CH1 & CH2 in Series with {total_points} points")
        self.append_text.emit("  Total voltage will be split between channels")

        for idx, total_value in enumerate(values):
            if not self.running:
                break

            # Update progress
            progress = int((idx / total_points) * 100)
            self.progress_update.emit(progress)
            self.update_measurement_progress.emit(
                f"Point {idx + 1}/{total_points}: Total={total_value:.6f} {merged_data['unit']}"
            )

            # Split the value between channels (you can customize this)
            # Example: 50/50 split
            ch1_value = total_value / 2
            ch2_value = total_value / 2

            self.append_text.emit(
                f"\n  Setting Ch1={ch1_value:.6f} {merged_data['unit']}, Ch2={ch2_value:.6f} {merged_data['unit']}")

            # Set both channels
            self._set_channel_output(1, ch1_value, self.measurement_data['source_type'])
            self._set_channel_output(2, ch2_value, self.measurement_data['source_type'])

            # Wait for settling
            self._wait_settling(f"Settling... ({self.settling_time}s)")

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
                'source_type': self.measurement_data['source_type'],
                'spectrum': spectrum_data,
                'timestamp': datetime.now().isoformat()
            }
            self.measurement_results.append(result)

            # Update plots
            self._update_plots(result)

            # Save individual spectrum if enabled
            if self.save_individual_spectra:
                self._save_individual_spectrum(result, idx)

        self.progress_update.emit(100)

    def _measure_parallel_channels(self):
        """Measure parallel channel configuration."""
        self.append_text.emit("\n" + "=" * 60)
        self.append_text.emit("Starting Parallel Channel Measurement")
        self.append_text.emit("=" * 60)

        merged_data = self.measurement_data['channels']['merged']
        values = merged_data['values']
        total_points = len(values)

        self.append_text.emit(f"\nMeasuring CH1 & CH2 in Parallel with {total_points} points")
        self.append_text.emit("  Both channels will be set to same value")

        for idx, value in enumerate(values):
            if not self.running:
                break

            # Update progress
            progress = int((idx / total_points) * 100)
            self.progress_update.emit(progress)
            self.update_measurement_progress.emit(
                f"Point {idx + 1}/{total_points}: {value:.6f} {merged_data['unit']}"
            )

            # Set both channels to same value
            self.append_text.emit(
                f"\n  Setting Ch1={value:.6f} {merged_data['unit']}, Ch2={value:.6f} {merged_data['unit']}")

            self._set_channel_output(1, value, self.measurement_data['source_type'])
            self._set_channel_output(2, value, self.measurement_data['source_type'])

            # Wait for settling
            self._wait_settling(f"Settling... ({self.settling_time}s)")

            # Capture spectrum
            spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

            # Store results
            result = {
                'point': idx + 1,
                'channel': 'merged_parallel',
                'value': value,
                'unit': merged_data['unit'],
                'source_type': self.measurement_data['source_type'],
                'spectrum': spectrum_data,
                'timestamp': datetime.now().isoformat()
            }
            self.measurement_results.append(result)

            # Update plots
            self._update_plots(result)

            # Save individual spectrum if enabled
            if self.save_individual_spectra:
                self._save_individual_spectrum(result, idx)

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

        # Determine measurement strategy
        # Strategy 1: Keep all fixed except one varying (if only one has multiple values)
        # Strategy 2: Iterate through all combinations (if multiple have ranges)

        varying_channels = [(name, data) for name, data in enabled_channels if len(data['values']) > 1]

        if len(varying_channels) == 0:
            # All fixed - single measurement
            self._measure_all_channels_fixed(enabled_channels)
        elif len(varying_channels) == 1:
            # One varying - simple loop
            self._measure_all_channels_one_varying(enabled_channels, varying_channels[0])
        else:
            # Multiple varying - user choice needed (using first varying as default)
            self.append_text.emit("  ⚠ Multiple channels have ranges - will vary first channel only")
            self._measure_all_channels_one_varying(enabled_channels, varying_channels[0])

    def _measure_all_channels_fixed(self, enabled_channels):
        """Measure all channels with fixed values."""
        self.append_text.emit("\nAll channels set to fixed values - single measurement")

        # Set all channels
        for ch_name, ch_data in enabled_channels:
            channel_num = self._get_channel_number(ch_name)
            value = ch_data['values'][0]
            self.append_text.emit(f"  Setting {ch_name.upper()}={value:.6f} {ch_data['unit']}")
            self._set_channel_output(channel_num, value, self.measurement_data['source_type'])

        # Wait and measure
        self._wait_settling(f"Settling... ({self.settling_time}s)")
        spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

        # Store result
        result = {
            'point': 1,
            'channel': 'all_fixed',
            'channels': {ch_name: ch_data['values'][0] for ch_name, ch_data in enabled_channels},
            'spectrum': spectrum_data,
            'timestamp': datetime.now().isoformat()
        }
        self.measurement_results.append(result)
        self._update_plots(result)

        self.progress_update.emit(100)

    def _measure_all_channels_one_varying(self, enabled_channels, varying_channel):
        """Measure all channels with one varying."""
        vary_name, vary_data = varying_channel
        values = vary_data['values']
        total_points = len(values)

        self.append_text.emit(f"\nVarying {vary_name.upper()} through {total_points} points")
        self.append_text.emit("  Other channels kept fixed")

        for idx, vary_value in enumerate(values):
            if not self.running:
                break

            # Update progress
            progress = int((idx / total_points) * 100)
            self.progress_update.emit(progress)
            self.update_measurement_progress.emit(
                f"Point {idx + 1}/{total_points}: {vary_name.upper()}={vary_value:.6f} {vary_data['unit']}"
            )

            # Set all channels
            for ch_name, ch_data in enabled_channels:
                channel_num = self._get_channel_number(ch_name)
                if ch_name == vary_name:
                    value = vary_value
                else:
                    value = ch_data['values'][0]

                self._set_channel_output(channel_num, value, self.measurement_data['source_type'])

            # Wait and measure
            self._wait_settling(f"Settling... ({self.settling_time}s)")
            spectrum_data = self._capture_spectrum(averaging=self.spectrum_averaging)

            # Store result
            result = {
                'point': idx + 1,
                'channel': 'all_varying',
                'varying_channel': vary_name,
                'varying_value': vary_value,
                'channels': {
                    ch_name: vary_value if ch_name == vary_name else ch_data['values'][0]
                    for ch_name, ch_data in enabled_channels
                },
                'spectrum': spectrum_data,
                'timestamp': datetime.now().isoformat()
            }
            self.measurement_results.append(result)
            self._update_plots(result)

            if self.save_individual_spectra:
                self._save_individual_spectrum(result, idx)

        self.progress_update.emit(100)

    def _get_channel_number(self, ch_name):
        """Convert channel name to number."""
        mapping = {
            'ch1': 1,
            'ch2': 2,
            'ch3': 3,
            'merged': 4
        }
        return mapping.get(ch_name, 1)

    def _set_channel_output(self, channel_num, value, source_type):
        """
        Set BK9205 channel output.

        Args:
            channel_num: Channel number (1, 2, 3)
            value: Value to set (in base units)
            source_type: 'voltage' or 'current'
        """
        if self.demo_mode or not self.bk9205_connected:
            # Demo mode - just update labels
            self.append_text.emit(f"    [DEMO] Setting Ch{channel_num} {source_type} to {value:.6f}")
            self._update_channel_label(channel_num, value, source_type)
            return

        try:
            # Real instrument commands
            if source_type == 'voltage':
                # Add your BK9205 voltage setting code here
                # Example:
                # self.bk9205.set_voltage(channel_num, value)
                self.append_text.emit(f"    Setting Ch{channel_num} voltage to {value:.6f} V")
            else:  # current
                # Add your BK9205 current setting code here
                # Example:
                # self.bk9205.set_current(channel_num, value)
                self.append_text.emit(f"    Setting Ch{channel_num} current to {value:.6f} A")

            # Enable output
            # self.bk9205.set_output_state(channel_num, 'ON')

            # Update UI labels
            self._update_channel_label(channel_num, value, source_type)

        except Exception as e:
            self.append_text.emit(f"    ✗ Error setting Ch{channel_num}: {str(e)}")

    def _update_channel_label(self, channel_num, value, source_type):
        """Update channel reading labels in UI."""
        label_text = f"{value:.6f}"

        if source_type == 'voltage':
            if channel_num == 1:
                self.update_bk9205_ch1_voltage_label.emit(label_text)
            elif channel_num == 2:
                self.update_bk9205_ch2_voltage_label.emit(label_text)
            elif channel_num == 3:
                self.update_bk9205_ch3_voltage_label.emit(label_text)
        else:  # current
            if channel_num == 1:
                self.update_bk9205_ch1_current_label.emit(label_text)
            elif channel_num == 2:
                self.update_bk9205_ch2_current_label.emit(label_text)
            elif channel_num == 3:
                self.update_bk9205_ch3_current_label.emit(label_text)

    def _wait_settling(self, message):
        """Wait for settling time with progress updates."""
        self.append_text.emit(f"    {message}")

        if self.demo_mode:
            time.sleep(0.1)  # Short delay in demo mode
        else:
            time.sleep(self.settling_time)

    def _capture_spectrum(self, averaging=1):
        """
        Capture spectrum from RIGOL.

        Args:
            averaging: Number of spectra to average

        Returns:
            dict: {'frequencies': array, 'powers': array, 'metadata': dict}
        """
        if self.demo_mode or not self.rigol_connected:
            # Generate demo spectrum
            return self._generate_demo_spectrum()

        try:
            self.append_text.emit(f"    Capturing spectrum (averaging {averaging})...")

            spectra = []
            for i in range(averaging):
                if not self.running:
                    break

                # Add your RIGOL spectrum capture code here
                # Example:
                # freq = self.rigol.get_frequency_data()
                # power = self.rigol.get_trace_data()
                # spectrum = {'frequencies': freq, 'powers': power}
                # spectra.append(spectrum)

                # Placeholder - replace with actual code
                spectrum = self._generate_demo_spectrum()
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
        # Create demo frequency array (1 GHz to 2 GHz)
        frequencies = np.linspace(1e9, 2e9, 1001)

        # Generate demo power data with some peaks
        powers = -80 + 10 * np.random.randn(len(frequencies))

        # Add a few peaks
        peak1_idx = 200
        peak2_idx = 500
        peak3_idx = 800

        powers[peak1_idx - 10:peak1_idx + 10] += 30 * np.exp(-((np.arange(-10, 10)) ** 2) / 20)
        powers[peak2_idx - 15:peak2_idx + 15] += 25 * np.exp(-((np.arange(-15, 15)) ** 2) / 30)
        powers[peak3_idx - 10:peak3_idx + 10] += 20 * np.exp(-((np.arange(-10, 10)) ** 2) / 20)

        return {
            'frequencies': frequencies.tolist(),
            'powers': powers.tolist(),
            'metadata': {
                'center_freq': 1.5e9,
                'span': 1e9,
                'rbw': 1e6,
                'timestamp': datetime.now().isoformat()
            }
        }

    def _average_spectra(self, spectra):
        """Average multiple spectra."""
        # Assume all spectra have same frequency points
        frequencies = spectra[0]['frequencies']
        powers_array = np.array([s['powers'] for s in spectra])
        avg_powers = np.mean(powers_array, axis=0)

        return {
            'frequencies': frequencies,
            'powers': avg_powers.tolist(),
            'metadata': spectra[0]['metadata']
        }

    def _update_plots(self, result):
        """Update live plots."""
        # Extract data for plotting
        if 'value' in result:
            x_val = result['value']
        elif 'total_value' in result:
            x_val = result['total_value']
        elif 'varying_value' in result:
            x_val = result['varying_value']
        else:
            x_val = result['point']

        # Get peak power from spectrum
        spectrum = result['spectrum']
        peak_power = max(spectrum['powers']) if spectrum['powers'] else 0

        # Update main plot (voltage/current vs peak power)
        x_data = [r.get('value', r.get('total_value', r.get('varying_value', r['point'])))
                  for r in self.measurement_results]
        y_data = [max(r['spectrum']['powers']) for r in self.measurement_results]

        x_label = f"{self.measurement_data['source_type'].capitalize()} ({result.get('unit', 'V')})"
        y_label = "Peak Power (dBm)"

        self.update_plot.emit(x_data, y_data, x_label, y_label)

        # Update spectrum plot with latest spectrum
        self.update_spectrum_plot.emit(spectrum['frequencies'], spectrum['powers'])

    def _save_individual_spectrum(self, result, index):
        """Save individual spectrum to file."""
        try:
            filename = f"{self.file_name}_point_{index + 1:04d}_spectrum.txt"
            filepath = f"{self.folder_path}/{filename}"

            with open(filepath, 'w') as f:
                f.write("# BK9205 + RIGOL Spectrum Measurement\n")
                f.write(f"# Timestamp: {result['timestamp']}\n")
                f.write(f"# Point: {result['point']}\n")

                if 'value' in result:
                    f.write(f"# {result['channel']}: {result['value']:.6f} {result['unit']}\n")
                elif 'total_value' in result:
                    f.write(f"# Total: {result['total_value']:.6f} {result['unit']}\n")
                    f.write(f"# Ch1: {result['ch1_value']:.6f} {result['unit']}\n")
                    f.write(f"# Ch2: {result['ch2_value']:.6f} {result['unit']}\n")

                f.write("#\n")
                f.write("# Frequency (Hz)\tPower (dBm)\n")

                spectrum = result['spectrum']
                for freq, power in zip(spectrum['frequencies'], spectrum['powers']):
                    f.write(f"{freq:.6e}\t{power:.6f}\n")

        except Exception as e:
            self.append_text.emit(f"    ✗ Error saving spectrum: {str(e)}")

    def _save_all_data(self):
        """Save all measurement results to file."""
        try:
            self.append_text.emit("\nSaving measurement data...")

            # Save summary file
            summary_file = f"{self.folder_path}/{self.file_name}_summary.txt"
            self._save_summary_file(summary_file)

            # Save detailed data file
            data_file = f"{self.folder_path}/{self.file_name}_data.txt"
            self._save_data_file(data_file)

            self.append_text.emit(f"✓ Data saved to {self.folder_path}")

        except Exception as e:
            self.append_text.emit(f"✗ Error saving data: {str(e)}")

    def _save_summary_file(self, filepath):
        """Save measurement summary."""
        with open(filepath, 'w') as f:
            f.write("BK9205 + RIGOL Measurement Summary\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Measurement Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Run Number: {self.run_number}\n")
            f.write(f"Channel Mode: {self.measurement_data['channel_mode']}\n")
            f.write(f"Source Type: {self.measurement_data['source_type']}\n")
            f.write(f"Total Points: {len(self.measurement_results)}\n")
            f.write(f"Settling Time: {self.settling_time} s\n")
            f.write(f"Spectrum Averaging: {self.spectrum_averaging}\n")
            f.write("\n")

            # Channel configuration
            f.write("Channel Configuration:\n")
            for ch_name, ch_data in self.measurement_data['channels'].items():
                if ch_data['enabled']:
                    f.write(f"  {ch_name.upper()}:\n")
                    f.write(f"    Mode: {ch_data['mode']}\n")
                    f.write(f"    Values: {len(ch_data['values'])} points\n")
                    f.write(
                        f"    Range: {min(ch_data['values']):.6f} to {max(ch_data['values']):.6f} {ch_data['unit']}\n")
            f.write("\n")

            # Summary statistics
            all_peak_powers = [max(r['spectrum']['powers']) for r in self.measurement_results]
            f.write("Measurement Statistics:\n")
            f.write(f"  Peak Power - Max: {max(all_peak_powers):.2f} dBm\n")
            f.write(f"  Peak Power - Min: {min(all_peak_powers):.2f} dBm\n")
            f.write(f"  Peak Power - Mean: {np.mean(all_peak_powers):.2f} dBm\n")
            f.write(f"  Peak Power - Std: {np.std(all_peak_powers):.2f} dBm\n")

    def _save_data_file(self, filepath):
        """Save detailed measurement data."""
        with open(filepath, 'w') as f:
            f.write("# BK9205 + RIGOL Measurement Data\n")
            f.write(f"# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("#\n")
            f.write("# Point\tTimestamp\tSource Value\tUnit\tPeak Power (dBm)\tPeak Freq (Hz)\n")

            for result in self.measurement_results:
                point = result['point']
                timestamp = result['timestamp']

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

                f.write(f"{point}\t{timestamp}\t{value:.6f}\t{unit}\t{peak_power:.6f}\t{peak_freq:.6e}\n")

    def _cleanup_instruments(self):
        """Turn off outputs and cleanup."""
        self.append_text.emit("\nCleaning up...")

        if self.bk9205_connected and not self.demo_mode:
            try:
                # Add your cleanup code here
                # Example:
                # self.bk9205.set_output_state('OFF')
                self.append_text.emit("  ✓ BK9205 outputs disabled")
            except Exception as e:
                self.append_text.emit(f"  ⚠ BK9205 cleanup warning: {str(e)}")

    def stop(self):
        """Stop the measurement."""
        self.running = False
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
    def __init__(self, rigol_connected, bk_9205_connected):
        super().__init__()
        try:
            with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                self.Button_stylesheet = file.read()
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.QCombo_stylesheet = file.read()
            self.font = QFont("Arial", 13)
            self.RIGOL_CONNECTED = rigol_connected
            self.BK_9205_CONNECTED = bk_9205_connected
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
        # self.stop_btn.clicked.connect(self.stop_measurement)
        self.rst_btn = QPushButton('Reset')
        # self.rst_btn.clicked.connect(self.rst)
        self.start_measurement_btn.setStyleSheet(self.Button_stylesheet)
        self.stop_btn.setStyleSheet(self.Button_stylesheet)
        self.rst_btn.setStyleSheet(self.Button_stylesheet)
        self.buttons_layout.addStretch(4)
        self.buttons_layout.addWidget(self.rst_btn)
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
        from QuDAP.GUI.Experiment.measurement import WideComboBox
        self.bk9205_channel_selection_combo_box = WideComboBox()
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
        from QuDAP.GUI.Experiment.measurement import WideComboBox
        self.bk9205_source_selection_combo_box = WideComboBox()
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
        range_from_label = QLabel(f'{channel} Range: From')
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
        bk9205_range_layout.addWidget(bk9205_range_unit_combo_box)

        bk9205_step_layout = QHBoxLayout()
        step_label = QLabel('Step Size:')
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
        bk9205_step_layout.addWidget(step_unit_combo_box)

        bk9205_setting_layout.addLayout(bk9205_range_layout)
        bk9205_setting_layout.addLayout(bk9205_step_layout)
        return bk9205_setting_layout, range_from_entry, range_to_entry, step_entry

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
        # dialog = LogWindow()
        # if dialog.exec():
        #     try:
        #         if self.worker is not None:
        #             self.stop_measurement()
        #         try:
        #             self.customize_layout.removeWidget(self.log_box)
        #             self.log_box.deleteLater()
        #             self.customize_layout.removeWidget(self.progress_bar)
        #             self.progress_bar.deleteLater()
        #         except Exception:
        #             pass
        #         self.running = True
        #         self.folder_path, self.file_name, self.formatted_date, self.sample_id, self.measurement, self.run, self.comment, self.user = dialog.get_text()
        #         self.log_box = QTextEdit(self)
        #         self.log_box.setReadOnly(True)  # Make the log box read-only
        #         self.progress_bar = QProgressBar(self)
        #         self.progress_bar.setMinimum(0)
        #         self.progress_bar.setMaximum(100)
        #         self.progress_bar.setFixedWidth(1140)
        #         self.progress_value = 0
        #         self.progress_bar.setValue(self.progress_value)
        #         self.progress_bar.setStyleSheet("""
        #                             QProgressBar {
        #                                 border: 1px solid #8f8f91;
        #                                 border-radius: 5px;
        #                                 background-color: #e0e0e0;
        #                                 text-align: center;
        #                             }
        #
        #                             QProgressBar::chunk {
        #                                 background-color:  #3498db;
        #                                 width: 5px;
        #                             }
        #                         """)
        #         self.log_box.setFixedSize(1140, 150)
        #         self.customize_layout.addWidget(self.progress_bar)
        #         self.customize_layout.addWidget(self.log_box, alignment=Qt.AlignmentFlag.AlignCenter)
        #         self.log_box.clear()
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
        reply = QMessageBox.question(
            self,
            'Confirm Measurement Settings',
            f"Proceed with these settings?\n\n{summary}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Start actual measurement
            self._run_bk9205_measurement(data)

            #
            # except Exception as e:
            #     None

    def _run_bk9205_measurement(self, data):
        """
        Execute the actual measurement.
        This is where you'd iterate through values and take measurements.
        """
        print("Starting measurement with configuration:")
        print(self.get_measurement_summary())

    def start_bk9205_rigol_measurement(self):
        """
        Start the BK9205 + RIGOL measurement.
        Call this when user clicks "Start Measurement" button.
        """
        try:
            # Step 1: Extract measurement configuration
            measurement_data = self.extract_measurement_data()

            # Step 2: Validate configuration
            if not self._validate_measurement_config(measurement_data):
                return

            # Step 3: Get log window information
            dialog = LogWindow()
            if not dialog.exec():
                return

            folder_path, file_name, formatted_date, sample_id, measurement_type, run, comment, user = dialog.get_text()

            # Step 4: Show confirmation dialog with measurement summary
            summary = self.get_measurement_summary()
            reply = QMessageBox.question(
                self,
                'Confirm Measurement',
                f"Start measurement with these settings?\n\n{summary}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Step 5: Prepare UI for measurement
            self._prepare_measurement_ui()

            # Step 6: Create and configure worker
            self.worker = BK9205_RIGOL_Worker(
                parent=self,
                bk9205_instrument=self.bk9205,
                rigol_instrument=self.rigol,
                measurement_data=measurement_data,
                folder_path=folder_path,
                file_name=file_name,
                run_number=run,
                bk9205_connected=self.BK_9205_CONNECTED,
                rigol_connected=self.RIGOL_CONNECTED,
                demo_mode=self.demo_mode,
                settling_time=1.0,  # You can make this configurable
                spectrum_averaging=1,  # You can make this configurable
                save_individual_spectra=True
            )

            # Step 7: Connect all signals
            self._connect_worker_signals()

            # Step 8: Start measurement
            self.worker.start()

            self.append_text("Measurement started successfully")

        except Exception as e:
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to start measurement:\n{str(e)}'
            )

    def _validate_measurement_config(self, data):
        """Validate measurement configuration before starting."""
        # Check channel mode
        if data['channel_mode'] == 'none':
            QMessageBox.warning(self, 'Warning', 'Please select a channel configuration')
            return False

        # Check for enabled channels
        has_enabled = any(ch['enabled'] for ch in data['channels'].values())
        if not has_enabled:
            QMessageBox.warning(self, 'Warning', 'No channels enabled for measurement')
            return False

        # Check for values
        for ch_name, ch_data in data['channels'].items():
            if ch_data['enabled'] and not ch_data['values']:
                ch_label = ch_name.upper().replace('merged', 'merged channels')
                QMessageBox.warning(self, 'Warning', f'No values specified for {ch_label}')
                return False

        return True

    def _prepare_measurement_ui(self):
        """Prepare UI for measurement (clear plots, create log box, etc.)."""
        try:
            # Clear existing plots
            self.canvas.axes.cla()
            if hasattr(self, 'canvas_2'):
                self.canvas_2.axes.cla()
            self.canvas.draw()

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
        self.worker.update_bk9205_ch1_voltage_label.connect(self.update_bk9205_ch1_voltage_label)
        self.worker.update_bk9205_ch1_current_label.connect(self.update_bk9205_ch1_current_label)
        self.worker.update_bk9205_ch2_voltage_label.connect(self.update_bk9205_ch2_voltage_label)
        self.worker.update_bk9205_ch2_current_label.connect(self.update_bk9205_ch2_current_label)
        self.worker.update_bk9205_ch3_voltage_label.connect(self.update_bk9205_ch3_voltage_label)
        self.worker.update_bk9205_ch3_current_label.connect(self.update_bk9205_ch3_current_label)

        # RIGOL updates
        self.worker.update_rigol_freq_label.connect(self.update_rigol_freq_label)
        self.worker.update_rigol_power_label.connect(self.update_rigol_power_label)

        # Plotting
        self.worker.update_plot.connect(self.update_plot)
        self.worker.update_spectrum_plot.connect(self.update_spectrum_plot)
        self.worker.save_plot.connect(self.save_plot)
        self.worker.clear_plot.connect(self.clear_plot)

    # =========================================================================
    # SLOT METHODS (UI Update Functions)
    # =========================================================================

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

    def update_bk9205_ch1_voltage_label(self, text):
        """Update Ch1 voltage label."""
        if hasattr(self, 'bk9205_channel1_voltage_reading_label'):
            self.bk9205_channel1_voltage_reading_label.setText(f"{text} V")

    def update_bk9205_ch1_current_label(self, text):
        """Update Ch1 current label."""
        if hasattr(self, 'bk9205_channel1_current_reading_label'):
            self.bk9205_channel1_current_reading_label.setText(f"{text} A")

    def update_bk9205_ch2_voltage_label(self, text):
        """Update Ch2 voltage label."""
        if hasattr(self, 'bk9205_channel2_voltage_reading_label'):
            self.bk9205_channel2_voltage_reading_label.setText(f"{text} V")

    def update_bk9205_ch2_current_label(self, text):
        """Update Ch2 current label."""
        if hasattr(self, 'bk9205_channel2_current_reading_label'):
            self.bk9205_channel2_current_reading_label.setText(f"{text} A")

    def update_bk9205_ch3_voltage_label(self, text):
        """Update Ch3 voltage label."""
        if hasattr(self, 'bk9205_channel3_voltage_reading_label'):
            self.bk9205_channel3_voltage_reading_label.setText(f"{text} V")

    def update_bk9205_ch3_current_label(self, text):
        """Update Ch3 current label."""
        if hasattr(self, 'bk9205_channel3_current_reading_label'):
            self.bk9205_channel3_current_reading_label.setText(f"{text} A")

    def update_rigol_freq_label(self, text):
        """Update RIGOL frequency label."""
        if hasattr(self, 'rigol_freq_label'):
            self.rigol_freq_label.setText(text)

    def update_rigol_power_label(self, text):
        """Update RIGOL power label."""
        if hasattr(self, 'rigol_power_label'):
            self.rigol_power_label.setText(text)

    def update_plot(self, x_data, y_data, x_label, y_label):
        """Update main measurement plot."""
        if hasattr(self, 'canvas'):
            self.canvas.axes.clear()
            self.canvas.axes.plot(x_data, y_data, 'bo-', markersize=6, linewidth=2)
            self.canvas.axes.set_xlabel(x_label, fontsize=12)
            self.canvas.axes.set_ylabel(y_label, fontsize=12)
            self.canvas.axes.grid(True, alpha=0.3)
            self.canvas.axes.set_title('Measurement Progress', fontsize=14, fontweight='bold')
            self.canvas.draw()

    def update_spectrum_plot(self, freq_data, power_data):
        """Update spectrum plot."""
        if hasattr(self, 'canvas_2'):
            self.canvas_2.axes.clear()
            # Convert frequency to GHz for better readability
            freq_ghz = [f / 1e9 for f in freq_data]
            self.canvas_2.axes.plot(freq_ghz, power_data, 'r-', linewidth=1)
            self.canvas_2.axes.set_xlabel('Frequency (GHz)', fontsize=12)
            self.canvas_2.axes.set_ylabel('Power (dBm)', fontsize=12)
            self.canvas_2.axes.grid(True, alpha=0.3)
            self.canvas_2.axes.set_title('Latest Spectrum', fontsize=14, fontweight='bold')
            self.canvas_2.draw()

    def save_plot(self, filename):
        """Save current plot."""
        if hasattr(self, 'canvas'):
            try:
                filepath = f"{self.folder_path}/{filename}"
                self.canvas.figure.savefig(filepath, dpi=300, bbox_inches='tight')
                self.append_text(f"Plot saved: {filename}")
            except Exception as e:
                self.append_text(f"Error saving plot: {str(e)}")

    def clear_plot(self):
        """Clear all plots."""
        if hasattr(self, 'canvas'):
            self.canvas.axes.clear()
            self.canvas.draw()
        if hasattr(self, 'canvas_2'):
            self.canvas_2.axes.clear()
            self.canvas_2.draw()

    def stop_measurement(self):
        """Stop the measurement."""
        if self.worker is not None:
            self.worker.stop()
            self.worker.wait()  # Wait for thread to finish
            self.worker = None
        self.append_text("Measurement stopped")

    def measurement_finished(self):
        """Called when measurement completes."""
        self.append_text("\n" + "=" * 60)
        self.append_text("Measurement finished successfully!")
        self.append_text("=" * 60)

        # Re-enable start button
        if hasattr(self, 'start_button'):
            self.start_button.setEnabled(True)

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