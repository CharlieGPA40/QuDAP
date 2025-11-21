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
import csv
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

try:
    # from GUI.Experiment.BNC845RF import COMMAND
    from QuDAP.instrument.BNC845 import BNC_845M_COMMAND
    from QuDAP.instrument.rigol_spectrum_analyzer import RIGOL_COMMAND

except ImportError:
    # from QuDAP.GUI.Experiment.BNC845RF import COMMAND
    from instrument.BNC845 import BNC_845M_COMMAND
    from instrument.BK_precision_9129B import BK_9129_COMMAND
    # from GUI.Experiment.rigol_experiment import RIGOL_Measurement


class ST_FMR_Worker(QThread):
    """
    Worker thread for automated BK9205 + RIGOL measurements.
    Loops through voltage/current values and captures spectrum at each point.
    """

    # PyQt Signals for UI updates
    progress_update = pyqtSignal(int)  # Progress percentage (0-100)
    append_text = pyqtSignal(str, str)  # Log messages
    stop_measurement = pyqtSignal()  # Signal to stop
    measurement_finished = pyqtSignal()  # Measurement complete
    update_fmr_ui = pyqtSignal()
    error_message = pyqtSignal(str)  # Error popup
    show_warning = pyqtSignal(str, str)
    show_error = pyqtSignal(str, str)
    show_info = pyqtSignal(str, str)

    # Instrument reading updates
    update_ppms_temp_reading_label = pyqtSignal(str, str, str)
    update_ppms_field_reading_label = pyqtSignal(str, str, str)
    update_ppms_chamber_reading_label = pyqtSignal(str)

    update_dsp7265_freq_label = pyqtSignal(str)
    update_lockin_label = pyqtSignal(str, str, str, str)

    save_individual_plot = pyqtSignal(str)
    send_notification = pyqtSignal(str)

    # Plotting signals
    update_2d_plot = pyqtSignal(list, list, list)  # x_data (indices), y_data (voltages), z_data (peak powers)
    update_fmr_spectrum_plot = pyqtSignal(list, list)  # freq_data, power_data
    save_plot = pyqtSignal(str)  # filename
    clear_plot = pyqtSignal()
    clear_fmr_plot = pyqtSignal()

    # Measurement progress
    update_measurement_progress = pyqtSignal(float, float, float, float)

    def __init__(self, parent, ppms_instrument, dsp7265_instrument, bnc845_instrument, ppms_setting, bnc845_setting,
                 measurment_setting, folder_path, file_name, run_number, settling_time, notification_manager, demo_mode=False, spectrum_averaging=1,
                 save_individual_spectra=True, **kwargs):
        """
        Initialize worker thread.
        """
        super().__init__(parent)

        self.parent = parent
        self.client = ppms_instrument
        self.dsp7265 = dsp7265_instrument
        self.bnc845 = bnc845_instrument
        self.ppms_setting = ppms_setting
        self.bnc845_setting = bnc845_setting
        self.measurment_setting = measurment_setting
        self.folder_path = folder_path
        self.file_name = file_name
        self.run_number = run_number
        self.settling_time = settling_time
        self.notification_manager = notification_manager

        # Connection flags
        self.demo_mode = demo_mode

        # Measurement parameters
        self.spectrum_averaging = spectrum_averaging
        self.save_individual_spectra = save_individual_spectra

        # Control flags
        self.running = True
        self.paused = False
        self.stopped_by_user = False

        # Data storage
        self.measurement_results = []
        self.all_spectra = []

        # initialize ppms safe command
        try:
            from QuDAP.GUI.Experiment.measurement import ThreadSafePPMSCommands
        except ImportError:
            from GUI.Experiment.measurement import ThreadSafePPMSCommands

        self.ppms = ThreadSafePPMSCommands(self.client, self.notification_manager)

        # Additional parameters
        self.extra_params = kwargs

    def run(self):
        """Main execution method - runs in separate thread."""
        try:
            self.append_text.emit("=" * 60, 'green')
            self.append_text.emit("Starting ST_FMR Measurement", 'green')
            self.append_text.emit(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 'green')
            self.append_text.emit("=" * 60, 'green')

            # Clear plots
            self.clear_plot.emit()

            if self.bnc845:
                self._turn_off_output_bnc845()

            try:
                self.send_notification.emit("The measurement has been started successfully.")
            except Exception as e:
                tb_str = traceback.format_exc()
                self.show_error.emit("Error", f'{tb_str}')
            if self.stopped_by_user:
                self.append_text.emit("\n" + "=" * 60, 'red')
                self.append_text.emit("Measurement stopped by user", 'red')
                self.append_text.emit("=" * 60, 'red')
                return  # Exit without emitting measurement_finished

            # Execute measurement
            try:
                self._execute_measurement()
            except Exception as e:
                tb_str = traceback.format_exc()
                self.show_error.emit("Error", f'{tb_str}')

            if self.stopped_by_user:
                self.append_text.emit("\n" + "=" * 60, 'red')
                self.append_text.emit("Measurement stopped by user", 'red')
                self.append_text.emit("=" * 60, 'red')
                return  # Exit without emitting measurement_finished

            # # Save consolidated data
            # self._save_consolidated_data()
            #
            # # Cleanup
            self._cleanup_instruments()

            self.append_text.emit("=" * 60, 'red')
            self.append_text.emit("Measurement Complete!", 'red')
            self.append_text.emit("=" * 60, 'red')
            self.measurement_finished.emit()

        except Exception as e:
            tb_str = traceback.format_exc()
            self.show_error.emit("Error", f'{tb_str}', 'black')
            error_msg = f"Error in measurement: {str(e)}\n{traceback.format_exc()}"
            self.append_text.emit(error_msg, 'red')
            self.stop_measurement.emit()


    def _execute_measurement(self):
        """Execute the main measurement loop."""
        # Read Experiment Settings
        try:
            number_of_repetition = self.measurment_setting['number_repetition']
            temperature_ramping_rate = self.measurment_setting['init_temp_rate']
            number_of_repetition = list(range(1, number_of_repetition + 1))
            # Read RF Settings
            frequency_list = self.bnc845_setting['frequency_settings']['Final_list']
            power_list = self.bnc845_setting['power_settings']['Final_list']
            # Read PPMS Setting
            temperature_list = self.ppms_setting['temperature_setting']['temperature_list']
            temperature_rate = self.ppms_setting['temperature_setting']['temperature_rate']
            field_direction = self.ppms_setting['field_setting']['field_direction']
            field_mode = self.ppms_setting['field_setting']['field_mode']

            number_of_power = len(power_list)
            number_of_frequency = len(frequency_list)
            number_of_temperature = len(temperature_list)

            fast_field_rate = 220
            zero_field = 0

            start_time = time.time()
            self.append_text.emit('Measurement Start....\n', 'red')
            time.sleep(5)

            # -------------Temperature Status---------------------
            self._update_temperature_reading_label()
            # ------------Field Status----------------------
            self._update_field_reading_label()
            # ------------Chamber Status----------------------
            # self._update_chamber_reading_label()

            if self.stopped_by_user:
                self.append_text.emit("\n" + "=" * 60, 'red')
                self.append_text.emit("Measurement stopped by user", 'red')
                self.append_text.emit("=" * 60, 'red')
                return  # Exit without emitting measurement_finished

            self.pts = 0


            for i in range(number_of_temperature):
                if self.stopped_by_user:
                    self.append_text.emit("\n" + "=" * 60, 'red')
                    self.append_text.emit("Measurement stopped by user", 'red')
                    self.append_text.emit("=" * 60, 'red')
                    return  # Exit without emitting measurement_finished
                self.temperature_array = []
                self._set_field(zero_field, fast_field_rate)
                time.sleep(10)
                # Waiting for field ready
                while True:
                    if self.stopped_by_user:
                        self.append_text.emit("\n" + "=" * 60, 'red')
                        self.append_text.emit("Measurement stopped by user", 'red')
                        self.append_text.emit("=" * 60, 'red')
                        return  # Exit without emitting measurement_finished
                    time.sleep(15)
                    _, field_status = self._update_field_reading_label()
                    if field_status == 'Holding (driven)':
                        break

                self.append_text.emit(f'Current loop sets at {str(temperature_list[i])} K\n', 'blue')
                temperature_set_point = temperature_list[i]
                # This part separates the initial temperature chasing rate and really measurement temperate rate
                if i == 0:
                    self._set_temperature(temperature_set_point, temperature_ramping_rate)
                else:
                    self._set_temperature(temperature_set_point, temperature_rate)
                self.append_text.emit(f'Waiting for {temperature_set_point} K Temperature\n', 'red')
                time.sleep(4)

                self._update_temperature_reading_label()
                while True:
                    if self.stopped_by_user:
                        self.append_text.emit("\n" + "=" * 60, 'red')
                        self.append_text.emit("Measurement stopped by user", 'red')
                        self.append_text.emit("=" * 60, 'red')
                        return  # Exit without emitting measurement_finished
                    time.sleep(1.5)
                    curTemp, temperature_status = self._update_temperature_reading_label()
                    if temperature_status == 'Stable':
                        break

                self.append_text.emit(f'Stabilizing the Temperature for 5 minutes.....', 'orange')
                # time.sleep(300)
                time.sleep(30)
                self.temperature_array.append(curTemp)
                if self.stopped_by_user:
                    self.append_text.emit("\n" + "=" * 60, 'red')
                    self.append_text.emit("Measurement stopped by user", 'red')
                    self.append_text.emit("=" * 60, 'red')
                    return  # Exit without emitting measurement_finished

                for j in range(number_of_frequency):
                    if self.stopped_by_user:
                        self.append_text.emit("\n" + "=" * 60, 'red')
                        self.append_text.emit("Measurement stopped by user", 'red')
                        self.append_text.emit("=" * 60, 'red')
                        return  # Exit without emitting measurement_finished
                    self.frequency_array = []
                    for k in range(number_of_power):
                        current_frequency = frequency_list[j]
                        current_power = power_list[k]
                        self.power_array = []
                        if self.bnc845:
                            try:
                                self._set_enable_bnc845(frequency=current_frequency, power=current_power)
                                self._turn_on_output_bnc845()
                                time.sleep(1)
                                self.update_fmr_ui.emit()
                                curFreq = self._get_current_frequency_bnc845()
                                self.frequency_array.append(curFreq)
                                curPower = self._get_current_power_bnc845()
                                self.power_array.append(curPower)
                            except Exception as e:
                                self.show_error.emit("BNC Setting Error", f'{e}')
                                self.stop_measurement().emit()
                        for l in range(len(number_of_repetition)):
                            if self.stopped_by_user:
                                self.append_text.emit("\n" + "=" * 60, 'red')
                                self.append_text.emit("Measurement stopped by user", 'red')
                                self.append_text.emit("=" * 60, 'red')
                                return  # Exit without emitting measurement_finished
                            total_progress = len(
                                number_of_repetition) * number_of_power * number_of_frequency * number_of_temperature
                            if i == 0 and j == 0 and k == 0 and l == 0:
                                remaining_progress = total_progress
                            else:
                                remaining_progress = remaining_progress - 1
                            self.repetition_array = []
                            self.repetition_array.append(number_of_repetition[l])
                            self.send_notification.emit(
                                f"Starting measurement at temperature: {str(temperature_list[i])} K, frequency: {frequency_list[j]} Hz,"
                                f"power: {power_list[k]} dBm, repetition: {number_of_repetition[l]}")

                            self.clear_plot.emit()

                            csv_filename = f"{self.folder_path}{self.file_name}_{temperature_list[i]}_K_{frequency_list[j]}_Hz_{power_list[k]}_dBm_Run_{self.run}_repeat_{number_of_repetition[l]}.csv"

                            time.sleep(5)

                            if self.stopped_by_user:
                                self.append_text.emit("\n" + "=" * 60, 'red')
                                self.append_text.emit("Measurement stopped by user", 'red')
                                self.append_text.emit("=" * 60, 'red')
                                return  # Exit without emitting measurement_finished

                            if self.dsp7265:
                                try:
                                    time.sleep(5)
                                    cur_freq = str(float(self.dsp7265.query('FRQ[.]')) / 1000)
                                    self.update_dsp7265_freq_label.emit(cur_freq)
                                    self.dsp7265.write('AQN')
                                    time.sleep(5)
                                except Exception as e:
                                    self.show_error.emit("DSP Setting Error", f'{e}')
                                    self.stop_measurement().emit()


                            self.field_array = []
                            self.lockin_x = []
                            self.lockin_y = []
                            self.lockin_mag = []
                            self.lockin_pahse = []
                            self.clear_fmr_plot.emit()

                            # ----------------- Loop Down ----------------------#
                            if field_mode == 'continuous':
                                field_zone_count = self.ppms_setting['field_setting']['final_continuous_list']['zone_count']
                                field_direction = self.ppms_setting['field_setting']['field_direction']
                                if field_direction == 'unidirectional':
                                    start_field = self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                                        'from']
                                    if field_zone_count == 1:
                                        end_field = self.ppms_setting['field_setting']['final_continuous_list']['region1']['to']
                                    elif field_zone_count == 2:
                                        end_field = self.ppms_setting['field_setting']['final_continuous_list']['region2']['to']
                                    elif field_zone_count == 3:
                                        end_field = self.ppms_setting['field_setting']['final_continuous_list']['region2']['to']
                                else:
                                    if field_zone_count == 1:
                                        start_field = self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                                            'from']
                                        end_field = self.ppms_setting['field_setting']['final_continuous_list']['region1']['to']
                                    elif field_zone_count == 2 or field_zone_count == 3:
                                        start_field = self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                                            'from_start']
                                        end_field = self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                                            'to_end']

                                self._set_field(start_field, fast_field_rate)
                                time.sleep(4)

                                MyField, field_status = self._update_field_reading_label()
                                self.update_ppms_field_reading_label.emit(str(MyField), 'Oe', field_status)
                                while True:
                                    try:
                                        if self.stopped_by_user:
                                            self.append_text.emit("\n" + "=" * 60, 'red')
                                            self.append_text.emit("Measurement stopped by user", 'red')
                                            self.append_text.emit("=" * 60, 'red')
                                            return  # Exit without emitting measurement_finished
                                        time.sleep(1)
                                        MyField, field_status = self._update_field_reading_label()
                                        if field_status == 'Holding (driven)':
                                            break
                                    except SystemExit as e:
                                        self.error_message.emit(e, e)
                                        self.send_notification.emit(
                                            "Your measurement went wrong, possible PPMS client lost connection", 'critical')
                                time.sleep(20)

                                currentField = MyField
                                user_field_rate = \
                                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                                        'rate']
                                self._set_field(end_field, user_field_rate)

                                self.append_text.emit(f'Start collecting data \n', 'purple')
                                counter = 0

                                while currentField >= end_field + 1:
                                    user_field_rate = self._continous_field_setting(field_direction, currentField, field_zone_count)
                                    self._set_field(end_field, user_field_rate)


                                    if self.stopped_by_user:
                                        self.append_text.emit("\n" + "=" * 60, 'red')
                                        self.append_text.emit("Measurement stopped by user", 'red')
                                        self.append_text.emit("=" * 60, 'red')
                                        return  # Exit without emitting measurement_finished
                                    counter += 1

                                    single_measurement_start = time.time()

                                    time.sleep(1)
                                    currentField, field_status = self._update_field_reading_label()

                                    self.append_text.emit(f'Saving data for {currentField} Oe \n', 'green')

                                    if self.dsp7265:
                                        try:
                                            if self.stopped_by_user:
                                                self.append_text.emit("\n" + "=" * 60, 'red')
                                                self.append_text.emit("Measurement stopped by user", 'red')
                                                self.append_text.emit("=" * 60, 'red')
                                                return  # Exit without emitting measurement_finished
                                            self._wait_settling("Wait for settling time.")
                                            currentField, field_status = self._update_field_reading_label()
                                            self.field_array.append(currentField)
                                            X = float(self.dsp7265.query("X."))  # Read the measurement result
                                            Y = float(self.dsp7265.query("Y."))  # Read the measurement result
                                            Mag = float(self.dsp7265.query("MAG."))  # Read the measurement result
                                            Phase = float(self.dsp7265.query("PHA."))  # Read the measurement result
                                            self.update_lockin_label.emit(str(X), str(Y), str(Mag), str(Phase))
                                            self.lockin_x.append(X)
                                            self.lockin_y.append(Y)
                                            self.lockin_mag.append(Mag)
                                            self.lockin_pahse.append(Phase)
                                            self.field_array.append(MyField)
                                            # Update current spectrum plot (right)
                                            if counter % 20 == 0:
                                                counter = 0
                                                # # Drop off the first y element, append a new one.
                                                self.update_fmr_spectrum_plot.emit(self.field_array, self.lockin_x)
                                                # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                        except Exception as e:
                                            self.show_error.emit("Reading Error", f'{e}')
                                            self.stop_measurement().emit()
                                            return


                                        # Append the data to the CSV file
                                        with open(csv_filename, "a", newline="") as csvfile:
                                            csv_writer = csv.writer(csvfile)

                                            if csvfile.tell() == 0:  # Check if file is empty
                                                csv_writer.writerow(
                                                    ["Temperature (K)", "Field (Oe)", "Voltage X (V)", "Voltage Y (V)",
                                                     "Voltage Mag (V)", "Phase (deg)"])

                                            csv_writer.writerow(
                                                [curTemp, currentField, X, Y, Mag, Phase])
                                            self.append_text.emit(f'Data Saved for {currentField} Oe at {curTemp} K\n', 'green')
                                    # ----------------------------- Measure NV voltage -------------------
                                    user_field_rate = self._continous_field_setting(field_direction, currentField,
                                                                                    field_zone_count)
                                    self._set_field(end_field, user_field_rate)
                                    if self.stopped_by_user:
                                        self.append_text.emit("\n" + "=" * 60, 'red')
                                        self.append_text.emit("Measurement stopped by user", 'red')
                                        self.append_text.emit("=" * 60, 'red')
                                        return  # Exit without emitting measurement_finished
                                    self.append_text.emit(f'Field Rate = {user_field_rate}\n', 'orange')
                                    # Update currentField for the next iteration
                                    total_estimate_field_step = (start_field - end_field) / user_field_rate
                                    estimate_field_step = (currentField - end_field) / user_field_rate
                                    if field_direction == 'bidirectional':
                                        total_estimate_field_step = total_estimate_field_step * 2
                                        estimate_field_step = total_estimate_field_step + estimate_field_step

                                    self.pts += 1  # Number of self.pts count
                                    single_measurement_end = time.time()
                                    Single_loop = single_measurement_end - single_measurement_start
                                    self.append_text.emit(
                                        'Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop),
                                        'purple')


                                    total_time_in_seconds = Single_loop * total_progress * total_estimate_field_step
                                    totoal_time_in_minutes = total_time_in_seconds / 60
                                    total_time_in_hours = totoal_time_in_minutes / 60
                                    total_time_in_days = total_time_in_hours / 24

                                    estimate_time_in_seconds = Single_loop * remaining_progress * estimate_field_step
                                    estimate_time_in_minutes = total_time_in_seconds / 60
                                    estimate_time_in_hours = totoal_time_in_minutes / 60
                                    estimate_time_in_days = total_time_in_hours / 24

                                    self.append_text.emit(
                                        'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                            estimate_time_in_seconds), 'purple')
                                    self.append_text.emit(
                                        'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                            estimate_time_in_minutes), 'purple')
                                    self.append_text.emit(
                                        'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                            estimate_time_in_hours), 'purple')
                                    self.append_text.emit(
                                        'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                            estimate_time_in_days), 'purple')
                                    if self.stopped_by_user:
                                        self.append_text.emit("\n" + "=" * 60, 'red')
                                        self.append_text.emit("Measurement stopped by user", 'red')
                                        self.append_text.emit("=" * 60, 'red')
                                        return  # Exit without emitting measurement_finished
                                    current_progress = (total_time_in_seconds - estimate_time_in_seconds) / total_time_in_seconds
                                    self.progress_update.emit(int(current_progress * 100))
                                    self.update_measurement_progress.emit(total_time_in_days, total_time_in_hours,
                                                                totoal_time_in_minutes, current_progress * 100)

                                # ----------------- Loop Up ----------------------#
                                if field_direction == 'bidirectional':
                                    self.send_notification.emit(
                                        f"Starting the second half of measurement - ramping field up")
                                    currentField = end_field
                                    self._set_field(end_field, user_field_rate)
                                    self.append_text.emit(f'Start collecting data \n', 'Purple')
                                    time.sleep(4)
                                    MyField, field_status = self._update_field_reading_label()
                                    self.update_ppms_field_reading_label.emit(str(MyField), 'Oe', field_status)
                                    while True:
                                        try:
                                            if self.stopped_by_user:
                                                self.append_text.emit("\n" + "=" * 60, 'red')
                                                self.append_text.emit("Measurement stopped by user", 'red')
                                                self.append_text.emit("=" * 60, 'red')
                                                return  # Exit without emitting measurement_finished
                                            time.sleep(1)
                                            MyField, field_status = self._update_field_reading_label()
                                            if field_status == 'Holding (driven)':
                                                break
                                        except SystemExit as e:
                                            self.error_message.emit(e, e)
                                            self.send_notification.emit(
                                                "Your measurement went wrong, possible PPMS client error",
                                                'critical')
                                    time.sleep(20)

                                    self._set_field(start_field, user_field_rate)

                                    counter = 0

                                    self.progress_update.emit(int(50))
                                    while currentField <= start_field - 1:
                                        if self.stopped_by_user:
                                            self.append_text.emit("\n" + "=" * 60, 'red')
                                            self.append_text.emit("Measurement stopped by user", 'red')
                                            self.append_text.emit("=" * 60, 'red')
                                            return  # Exit without emitting measurement_finished
                                        user_field_rate = self._continous_field_setting(field_direction, currentField,
                                                                                        field_zone_count)
                                        self._set_field(start_field, user_field_rate)

                                        if self.stopped_by_user:
                                            self.append_text.emit("\n" + "=" * 60, 'red')
                                            self.append_text.emit("Measurement stopped by user", 'red')
                                            self.append_text.emit("=" * 60, 'red')
                                            return  # Exit without emitting measurement_finished
                                        counter += 1

                                        single_measurement_start = time.time()

                                        time.sleep(1)
                                        currentField, field_status = self._update_field_reading_label()
                                        self.append_text.emit(f'Saving data for {currentField} Oe \n', 'green')

                                        if self.dsp7265:
                                            try:
                                                if self.stopped_by_user:
                                                    self.append_text.emit("\n" + "=" * 60, 'red')
                                                    self.append_text.emit("Measurement stopped by user", 'red')
                                                    self.append_text.emit("=" * 60, 'red')
                                                    return  # Exit without emitting measurement_finished
                                                self._wait_settling("Wait for settling time.")
                                                currentField, field_status = self._update_field_reading_label()
                                                self.field_array.append(currentField)
                                                X = float(self.dsp7265.query("X."))  # Read the measurement result
                                                Y = float(self.dsp7265.query("Y."))  # Read the measurement result
                                                Mag = float(self.dsp7265.query("MAG."))  # Read the measurement result
                                                Phase = float(self.dsp7265.query("PHA."))  # Read the measurement result
                                                self.update_lockin_label.emit(str(X), str(Y), str(Mag), str(Phase))
                                                self.lockin_x.append(X)
                                                self.lockin_y.append(Y)
                                                self.lockin_mag.append(Mag)
                                                self.lockin_pahse.append(Phase)
                                                self.field_array.append(MyField)
                                                # Update current spectrum plot (right)
                                                if counter % 20 == 0:
                                                    counter = 0
                                                    # # Drop off the first y element, append a new one.
                                                    self.update_fmr_spectrum_plot.emit(self.field_array, self.lockin_x)
                                                    # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                            except Exception as e:
                                                self.show_error.emit("Reading Error", f'{e}')
                                                self.stop_measurement().emit()
                                                return

                                            # Append the data to the CSV file
                                            with open(csv_filename, "a", newline="") as csvfile:
                                                csv_writer = csv.writer(csvfile)

                                                if csvfile.tell() == 0:  # Check if file is empty
                                                    csv_writer.writerow(
                                                        ["Temperature (K)", "Field (Oe)", "Voltage X (V)",
                                                         "Voltage Y (V)",
                                                         "Voltage Mag (V)", "Phase (deg)"])

                                                csv_writer.writerow(
                                                    [curTemp, currentField, X, Y, Mag, Phase])
                                                self.append_text.emit(
                                                    f'Data Saved for {currentField} Oe at {curTemp} K\n', 'green')

                                        # ----------------------------- Measure NV voltage -------------------
                                        user_field_rate = self._continous_field_setting(field_direction, currentField,
                                                                                        field_zone_count)

                                        self._set_field(end_field, user_field_rate)

                                        self.append_text.emit(f'Field Rate = {user_field_rate}\n', 'orange')

                                        # Update currentField for the next iteration
                                        if self.stopped_by_user:
                                            self.append_text.emit("\n" + "=" * 60, 'red')
                                            self.append_text.emit("Measurement stopped by user", 'red')
                                            self.append_text.emit("=" * 60, 'red')
                                            return  # Exit without emitting measurement_finished
                                        total_estimate_field_step = (start_field - end_field) / user_field_rate
                                        estimate_field_step = (currentField - end_field) / user_field_rate
                                        if field_direction == 'bidirectional':
                                            total_estimate_field_step = total_estimate_field_step * 2
                                            estimate_field_step = estimate_field_step

                                        self.pts += 1  # Number of self.pts count
                                        single_measurement_end = time.time()
                                        Single_loop = single_measurement_end - single_measurement_start
                                        self.append_text.emit(
                                            'Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop),
                                            'purple')

                                        total_time_in_seconds = Single_loop * total_progress * total_estimate_field_step
                                        totoal_time_in_minutes = total_time_in_seconds / 60
                                        total_time_in_hours = totoal_time_in_minutes / 60
                                        total_time_in_days = total_time_in_hours / 24

                                        estimate_time_in_seconds = Single_loop * remaining_progress * estimate_field_step
                                        estimate_time_in_minutes = total_time_in_seconds / 60
                                        estimate_time_in_hours = totoal_time_in_minutes / 60
                                        estimate_time_in_days = total_time_in_hours / 24

                                        self.append_text.emit(
                                            'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                                estimate_time_in_seconds), 'purple')
                                        self.append_text.emit(
                                            'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                                estimate_time_in_minutes), 'purple')
                                        self.append_text.emit(
                                            'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                                estimate_time_in_hours), 'purple')
                                        self.append_text.emit(
                                            'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                                estimate_time_in_days), 'purple')
                                        if self.stopped_by_user:
                                            self.append_text.emit("\n" + "=" * 60, 'red')
                                            self.append_text.emit("Measurement stopped by user", 'red')
                                            self.append_text.emit("=" * 60, 'red')
                                            return  # Exit without emitting measurement_finished
                                        current_progress = (
                                                                       total_time_in_seconds - estimate_time_in_seconds) / total_time_in_seconds
                                        self.progress_update.emit(int(current_progress * 100))
                                        self.update_measurement_progress.emit(total_time_in_days, total_time_in_hours,
                                                                              totoal_time_in_minutes,
                                                                              current_progress * 100)

                            else:
                                field_list = self.ppms_setting['field_setting']['final_step_list']
                                user_field_rate = self.ppms_setting['field_setting']['final_rate']
                                number_of_field = len(field_list)
                                number_of_field_update = number_of_field
                                total_progress_stepped =  total_progress * number_of_field

                                for m in range(number_of_field):
                                    if m == int(number_of_field /2) and field_direction == 'bidirectional':
                                        self.send_notification.emit(
                                            f"Starting the second half of measurement - ramping field up")
                                    if self.stopped_by_user:
                                        self.append_text.emit("\n" + "=" * 60, 'red')
                                        self.append_text.emit("Measurement stopped by user", 'red')
                                        self.append_text.emit("=" * 60, 'red')
                                        return  # Exit without emitting measurement_finished
                                    currentField = field_list[m]

                                    single_measurement_start = time.time()
                                    self.append_text.emit(f'Loop is at {currentField} Oe \n', 'blue')
                                    self.append_text.emit(f'Set the field to {currentField} Oe and then collect data \n', 'blue')
                                    self._set_field(currentField, user_field_rate)
                                    time.sleep(4)

                                    while True:
                                        try:
                                            if self.stopped_by_user:
                                                self.append_text.emit("\n" + "=" * 60, 'red')
                                                self.append_text.emit("Measurement stopped by user", 'red')
                                                self.append_text.emit("=" * 60, 'red')
                                                return  # Exit without emitting measurement_finished
                                            time.sleep(1)
                                            MyField, field_status = self._update_field_reading_label()
                                            if field_status == 'Holding (driven)':
                                                break
                                        except SystemExit as e:
                                            self.error_message.emit(e, e)
                                            self.send_notification.emit(
                                                "Your measurement went wrong, possible PPMS client lost connection",
                                                'critical')

                                    # ----------------------------- Measure NV voltage -------------------

                                    self.append_text.emit(f'Saving data for {MyField} Oe \n', 'green')

                                    MyField, field_status = self._update_field_reading_label()
                                    self.update_ppms_field_reading_label.emit(str(MyField), 'Oe', field_status)

                                    curTemp, temperature_status = self._update_temperature_reading_label()

                                    if self.dsp7265:
                                        try:
                                            if self.stopped_by_user:
                                                self.append_text.emit("\n" + "=" * 60, 'red')
                                                self.append_text.emit("Measurement stopped by user", 'red')
                                                self.append_text.emit("=" * 60, 'red')
                                                return  # Exit without emitting measurement_finished
                                            self._wait_settling("Wait for settling time.")
                                            X = float(self.dsp7265.query("X."))  # Read the measurement result
                                            Y = float(self.dsp7265.query("Y."))  # Read the measurement result
                                            Mag = float(self.dsp7265.query("MAG."))  # Read the measurement result
                                            Phase = float(self.dsp7265.query("PHA."))  # Read the measurement result
                                            self.update_lockin_label.emit(str(X), str(Y), str(Mag), str(Phase))
                                            self.lockin_x.append(X)
                                            self.lockin_y.append(Y)
                                            self.lockin_mag.append(Mag)
                                            self.lockin_pahse.append(Phase)
                                            self.field_array.append(MyField)
                                            # Update current spectrum plot (right)
                                            self.update_fmr_spectrum_plot.emit(self.field_array, self.lockin_x)

                                            # update_plot(self.field_array, self.lockin_pahse, 'red', False, True)
                                        except Exception as e:
                                            self.show_error.emit("Reading Error", f'{e}')
                                            self.stop_measurement().emit()
                                            return

                                        # Append the data to the CSV file
                                        with open(csv_filename, "a", newline="") as csvfile:
                                            csv_writer = csv.writer(csvfile)

                                            if csvfile.tell() == 0:  # Check if file is empty
                                                csv_writer.writerow(
                                                    ["Temperature (K)", "Field (Oe)", "Voltage X (V)", "Voltage Y (V)", "Voltage Mag (V)", "Phase (deg)"])

                                            csv_writer.writerow(
                                                [curTemp, currentField, X, Y, Mag, Phase])
                                            self.append_text.emit(f'Data Saved for {currentField} Oe at {curTemp} K\n', 'green')

                                    self._update_field_reading_label()
                                    self._update_temperature_reading_label()
                                    # ----------------------------- Measure NV voltage -------------------
                                    self.pts += 1  # Number of self.pts count
                                    single_measurement_end = time.time()
                                    Single_loop = single_measurement_end - single_measurement_start
                                    remaining_progress_stepped = remaining_progress * number_of_field - m

                                    self.append_text.emit('Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop),
                                                'purple')
                                    self.append_text.emit('Estimated Single measurement (in hrs):  {} hrs \n'.format(
                                        Single_loop * number_of_field / 60 / 60), 'purple')
                                    total_time_in_seconds = Single_loop * total_progress_stepped
                                    total_time_in_minutes = total_time_in_seconds / 60
                                    total_time_in_hours = total_time_in_minutes / 60
                                    total_time_in_days = total_time_in_hours / 24

                                    # remaining_time_in_seconds = Single_loop * (len(number_of_repetition)-l) * (number_of_power-k) * (number_of_frequency-j) * (number_of_temperature-i) * (number_of_field-m)
                                    remaining_time_in_seconds = Single_loop * remaining_progress_stepped
                                    remaining_time_in_minutes = remaining_time_in_seconds / 60
                                    remaining_time_in_hours = remaining_time_in_minutes / 60
                                    remaining_time_in_days = remaining_time_in_hours / 24
                                    self.append_text.emit(
                                        'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                                            remaining_time_in_seconds), 'purple')
                                    self.append_text.emit(
                                        'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                                            remaining_time_in_minutes), 'purple')
                                    self.append_text.emit(
                                        'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                                            remaining_time_in_hours), 'purple')
                                    self.append_text.emit(
                                        'Estimated Remaining Time for this round of measurement (in days):  {} days \n'.format(
                                            remaining_time_in_days), 'purple')
                                    if self.stopped_by_user:
                                        self.append_text.emit("\n" + "=" * 60, 'red')
                                        self.append_text.emit("Measurement stopped by user", 'red')
                                        self.append_text.emit("=" * 60, 'red')
                                        return  # Exit without emitting measurement_finished
                                    current_progress = (total_time_in_seconds - remaining_time_in_seconds) / total_time_in_seconds
                                    self.progress_update.emit(int(current_progress * 100))
                                    self.update_measurement_progress.emit(remaining_time_in_days, remaining_time_in_hours,
                                                                remaining_time_in_minutes, current_progress * 100)

                                    if self.stopped_by_user:
                                        self.append_text.emit("\n" + "=" * 60, 'red')
                                        self.append_text.emit("Measurement stopped by user", 'red')
                                        self.append_text.emit("=" * 60, 'red')
                                        return  # Exit without emitting measurement_finished
                                    time.sleep(2)


                            time.sleep(2)
                            self.client.set_field(zero_field,
                                             fast_field_rate,
                                             self.client.field.approach_mode.oscillate,  # linear/oscillate
                                             self.client.field.driven_mode.driven)
                            self.append_text.emit('Waiting for Zero Field', 'red')
                            time.sleep(2)
                            while True:
                                time.sleep(1)
                                MyField, field_status = self._update_field_reading_label()
                                if field_status == 'Holding (driven)':
                                    break

                        if self.bnc845:
                            self._turn_off_output_bnc845()
                            time.sleep(5)
                            self.update_fmr_ui.emit()
                #         if len(self.repetition_array) > 1:
                #             self.update_2d_plot.emit(self.field_array, self.repetition_array, self.lockin_x)
                #     if len(self.power_array) > 1:
                #         self.update_2d_plot.emit(self.field_array, self.power_array, self.lockin_x)
                # if len(self.frequency_array) > 1:
                #     self.update_2d_plot.emit(self.field_array, self.frequency_array, self.lockin_x)

            time.sleep(2)
            self.client.set_field(zero_field,
                                  fast_field_rate,
                                  self.client.field.approach_mode.oscillate,  # linear/oscillate
                                  self.client.field.driven_mode.driven)
            self.append_text.emit('Waiting for Zero Field', 'red')
            time.sleep(2)
            while True:
                time.sleep(1)
                MyField, field_status = self._update_field_reading_label()
                if field_status == 'Holding (driven)':
                    break
            self._update_field_reading_label()
            time.sleep(2)
            self._update_temperature_reading_label()
            self.progress_update.emit(100)
            self.save_plot.emit(self.file_name)
            self.update_measurement_progress.emit(0, 0, 0, 100)
            end_time = time.time()
            total_runtime = (end_time - start_time) / 3600
            self.append_text.emit(f"Total runtime: {total_runtime} hours\n", 'black')
            self.append_text.emit(f'Total data points: {str(self.pts)} pts\n', 'black')
            self.send_notification.emit("The measurement has been completed successfully.")
            self.append_text.emit("You measurement is finished!", 'green')
            # stop_measurement()
            self.measurement_finished.emit()
            return
        except Exception as e:
            tb_str = traceback.format_exc()
            self.show_error.emit("Error", f'{tb_str}')
        except SystemExit as e:
            tb_str = traceback.format_exc()
            self.show_error.emit("Error", f'{tb_str}')

    def _continous_field_setting(self, field_direction, currentField, field_zone_count):
        if field_direction == 'unidirectional':
            if field_zone_count == 1:
                user_field_rate = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'rate']
            elif field_zone_count == 2:
                zone1_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'from']
                zone1_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'to']

                zone2_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                        'from']
                zone2_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                        'to']

                if zone1_end_field <= currentField <= zone1_start_field:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                            'rate']

                elif zone2_end_field + 1 <= currentField <= zone2_start_field:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                            'rate']
            elif field_zone_count == 3:
                zone1_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'from']
                zone1_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'to']

                zone2_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                        'from']
                zone2_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                        'to']

                zone3_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region3'][
                        'from']
                zone3_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region3'][
                        'to']

                if zone1_end_field <= currentField <= zone1_start_field:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                            'rate']

                elif zone2_end_field + 1 <= currentField <= zone2_start_field:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                            'rate']

                elif zone3_end_field + 1 <= currentField <= zone3_start_field:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region3'][
                            'rate']
        else:
            if field_zone_count == 1:
                user_field_rate = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'rate']
            elif field_zone_count == 2:
                zone1_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'from_start']
                zone1_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'to_end']

                zone2_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                        'from']
                zone2_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                        'to']

                if zone2_start_field <= currentField <= zone1_start_field or zone2_end_field <= currentField <= zone1_end_field + 1:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                            'rate']

                elif zone2_start_field <= currentField <= zone2_end_field:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                            'rate']
            elif field_zone_count == 3:
                zone1_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'from_start']
                zone1_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                        'to_end']

                zone2_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                        'from_start']
                zone2_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                        'to_end']

                zone3_start_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region3'][
                        'from']
                zone3_end_field = \
                    self.ppms_setting['field_setting']['final_continuous_list']['region3'][
                        'to']

                if zone2_start_field <= currentField <= zone1_start_field or zone2_end_field <= currentField <= zone1_end_field + 1:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region1'][
                            'rate']
                elif zone3_start_field <= currentField <= zone2_start_field or zone3_end_field <= currentField <= zone2_end_field + 1:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region2'][
                            'rate']
                elif zone3_start_field <= currentField <= zone3_end_field + 1:
                    user_field_rate = \
                        self.ppms_setting['field_setting']['final_continuous_list']['region3'][
                            'rate']
        return user_field_rate


    # ==================================================================================
    # LABEL UPDATE METHODS
    # ==================================================================================
    def _update_temperature_reading_label(self):
        temperature, status, temp_unit = self._read_temperature()
        self.append_text.emit(f'Current temperature is {temperature} {temp_unit}; Status: {status}\n', 'purple')
        self.update_ppms_temp_reading_label.emit(str(temperature), str(temp_unit), status)
        return temperature, status

    def _update_field_reading_label(self):
        field, status, field_unit = self._read_field()
        self.append_text.emit(f'Current field is {field} {field_unit}; Status: {status}\n', 'purple')
        self.update_ppms_field_reading_label.emit(str(field), field_unit, status)
        return field, status

    def _update_chamber_reading_label(self):
        cT = self._get_chamber_status()
        self.append_text.emit(f'Current chamber status is {cT}\n', 'purple')
        self.update_ppms_chamber_reading_label(str(cT))
    # ==================================================================================
    # PPMS CONTROL METHODS
    # ==================================================================================
    def _get_chamber_status(self):
        try:
            success, cT = self.ppms.get_chamber_status(timeout=10)
            # cT = client.get_chamber()
            if not success:
                self.stop_measurement.emit()
            return cT
        except SystemExit as e:
            tb_str = traceback.format_exc()
            self.send_notification.emit(
                f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

    def _set_temperature(self, set_point, temp_rate):
        try:
            success = self.ppms.set_temperature(
                set_point=set_point,
                temp_rate=temp_rate,
                timeout=10  # 30 second timeout
            )
            if not success:
                self.stop_measurement.emit()
        except SystemExit as e:
            tb_str = traceback.format_exc()
            self.send_notification.emit(
                f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

    def _set_field(self, set_point, field_rate):
        try:
            success = self.ppms.set_field(
                set_point=set_point,
                field_rate=field_rate,
                timeout=10
            )
            if not success:
                self.stop_measurement.emit()
            self.append_text.emit(f'Setting Field to {str(set_point)} Oe... \n', 'orange')
        except SystemExit as e:
            tb_str = traceback.format_exc()
            self.send_notification.emit(
                f"Your measurement went wrong, possible PPMS command error {e} {tb_str}", 'critical')

    def _read_temperature(self):
        try:
            success, temp, status, unit = self.ppms.read_temperature(timeout=10)
            if not success:
                self.stop_measurement.emit()
            return temp, status, unit
        except SystemExit as e:
            tb_str = traceback.format_exc()
            self.send_notification.emit(
                f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

    def _read_field(self):
        try:
            success, field, status, unit = self.ppms.read_field(timeout=10)
            if not success:
                self.stop_measurement.emit()
            return field, status, unit
        except SystemExit as e:
            tb_str = traceback.format_exc()
            self.send_notification.emit(
                f"Your measurement went wrong, possible PPMS command error {e}", 'critical')

    # ==================================================================================
    # BNC CONTROL METHODS
    # ==================================================================================
    def _set_enable_bnc845(self, frequency, power):
        """Set voltage for single channel using APP:VOLT command."""
        BNC_845M_COMMAND().set_frequency(self.bnc845, frequency)
        BNC_845M_COMMAND().set_power(self.bnc845,power)

    def _turn_on_output_bnc845(self):
        """Turn on a bncl."""
        BNC_845M_COMMAND().set_output(self.bnc845,'ON')

    def _turn_off_output_bnc845(self):
        BNC_845M_COMMAND().set_output(self.bnc845,'OFF')

    def _get_current_frequency_bnc845(self):
        freq = BNC_845M_COMMAND().get_frequency(self.bnc845).strip()
        return freq

    def _get_current_power_bnc845(self):
        power = BNC_845M_COMMAND().get_power(self.bnc845).strip()
        return power

    # ==================================================================================
    # FMR Method Testing
    # ==================================================================================
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

    # ==================================================================================
    # DATA SAVING METHODS
    # ==================================================================================
    def _save_consolidated_data(self):
        """Save consolidated data file with all measurements and complete spectra."""
        try:
            self.append_text.emit("\nSaving consolidated measurement data...")

            data_file = f"{self.folder_path}/{self.file_name}_all_data.txt"

            with open(data_file, 'w') as f:
                # Write header information
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

                # # Write summary table
                # f.write("# SUMMARY TABLE\n")
                # f.write("# Point\tTimestamp\tSource_Value\tUnit\tPeak_Power(dBm)\tPeak_Freq(Hz)\tCenter_Freq(Hz)\n")
                #
                # for result in self.measurement_results:
                #     point = result['point']
                #     timestamp = result['timestamp']
                #
                #     # Determine source value
                #     if 'value' in result:
                #         value = result['value']
                #         unit = result['unit']
                #     elif 'total_value' in result:
                #         value = result['total_value']
                #         unit = result['unit']
                #     elif 'varying_value' in result:
                #         value = result['varying_value']
                #         unit = result.get('unit', 'V')
                #     else:
                #         value = 0
                #         unit = 'V'
                #
                #     spectrum = result['spectrum']
                #     peak_power = max(spectrum['powers'])
                #     peak_idx = spectrum['powers'].index(peak_power)
                #     peak_freq = spectrum['frequencies'][peak_idx]
                #     center_freq = (spectrum['frequencies'][0] + spectrum['frequencies'][-1]) / 2
                #
                #     f.write(
                #         f"{point}\t{timestamp}\t{value:.6f}\t{unit}\t{peak_power:.6f}\t{peak_freq:.6e}\t{center_freq:.6e}\n")

                # Write complete spectrum data with side-by-side power columns
                f.write("\n\n# COMPLETE SPECTRUM DATA\n")
                f.write("# All power values are in dBm\n")
                f.write("# Frequency data is the same for all measurements\n")
                f.write("=" * 80 + "\n")

                # Get frequency data (same for all measurements)
                freq_data = self.measurement_results[0]['spectrum']['frequencies']

                # Build header for spectrum data
                header = "Frequency(Hz)"
                for result in self.measurement_results:
                    point = result['point']

                    # Get source value for column label
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

                    header += f"\t{value:.3f}{unit}"

                f.write(header + "\n")

                # Write data rows
                num_freq_points = len(freq_data)
                for i in range(num_freq_points):
                    row = f"{freq_data[i]:.6e}"

                    # Append power value from each measurement
                    for result in self.measurement_results:
                        power = result['spectrum']['powers'][i]
                        row += f"\t{power:.6f}"

                    f.write(row + "\n")

            self.append_text.emit(f"✓ Saved consolidated data: {data_file}", 'green')

            # Also save summary statistics
            self._save_summary_statistics()

        except Exception as e:
            self.append_text(f"✗ Error saving consolidated data: {str(e)}")
            import traceback
            self.append_text(traceback.format_exc())

        except Exception as e:
            self.append_text.emit(f"✗ Error saving consolidated data: {str(e)}", 'red')

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

            self.append_text.emit(f"✓ Saved summary: {summary_file}", 'green')

        except Exception as e:
            self.append_text.emit(f"✗ Error saving summary: {str(e)}", 'red')

    # ==================================================================================
    # HELPER METHODS
    # ==================================================================================
    def _wait_settling(self, message):
        """Wait for settling time."""
        self.append_text.emit(f"    {message}", 'purple')
        if self.demo_mode:
            time.sleep(0.1)
        else:
            time.sleep(self.settling_time)

    def _cleanup_instruments(self):
        """Turn off outputs and cleanup."""
        self.append_text.emit("\nCleaning up...", 'green')

        if self.bnc845:
            try:
                self._turn_off_output_bnc845()
                time.sleep(5)
                self.update_fmr_ui.emit()
            except Exception as e:
                self.append_text.emit(f"  ⚠ BK9205 cleanup warning: {str(e)}")

    def stop(self):
        """Stop the measurement."""
        self.running = False
        self.stopped_by_user = True
        self.append_text.emit("\nStopping measurement...", 'red')

    def pause(self):
        """Pause the measurement."""
        self.paused = True
        self.append_text.emit("\nMeasurement paused", 'red')

    def resume(self):
        """Resume the measurement."""
        self.paused = False
        self.append_text.emit("\nMeasurement resumed", 'red')

class FMR_Measurement(QWidget):
    def __init__(self, ppms_client = None, bnc845 = None, dsp7265 = None):
        super().__init__()
        try:
            with open("GUI/QSS/QButtonWidget.qss", "r") as file:
                self.Button_stylesheet = file.read()
            with open("GUI/QSS/QComboWidget.qss", "r") as file:
                self.QCombo_stylesheet = file.read()
            self.font = QFont("Arial", 13)
            self.CLIENT = ppms_client
            self.BNC = bnc845
            self.DSP7265 = dsp7265
            self.worker = None
            self.init_ui()
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')
            return

    def init_ui(self):
        self.bnc845rf_main_layout = QHBoxLayout()

        self.bnc845rf_reading_groupbox = QGroupBox("BNC 845RF Reading")
        self.bnc845rf_reading_groupbox.setLayout(self.bnc845rf_window_reading_ui())
        self.bnc845rf_reading_groupbox.setFixedWidth(560)

        self.bnc845rf_setting_groupbox = QGroupBox("BNC 845RF Setting")
        self.bnc845rf_setting_groupbox.setLayout(self.bnc845rf_window_setting_ui())
        self.bnc845rf_setting_groupbox.setFixedWidth(560)

        self.bnc845rf_main_layout.addWidget(self.bnc845rf_reading_groupbox)
        self.bnc845rf_main_layout.addWidget(self.bnc845rf_setting_groupbox)
        self.setLayout(self.bnc845rf_main_layout)
        # return self.bnc845rf_main_layout
        # self.main_layout.addLayout(self.bnc845rf_main_layout)

    def bnc845rf_window_reading_ui(self):
        self.bnc845rf_window_reading_layout = QVBoxLayout()

        self.bnc845rf_current_frequency_layout = QHBoxLayout()
        bnc845rf_current_frequency_label = QLabel('Current Frequency:')
        bnc845rf_current_frequency_label.setFont(self.font)
        self.bnc845rf_current_frequency_reading_label = QLabel('N/A')
        self.bnc845rf_current_frequency_reading_label.setFont(self.font)
        self.bnc845rf_current_frequency_layout.addWidget(bnc845rf_current_frequency_label)
        self.bnc845rf_current_frequency_layout.addWidget(self.bnc845rf_current_frequency_reading_label)

        self.bnc845rf_current_power_layout = QHBoxLayout()
        bnc845rf_current_power_label = QLabel('Current Power:')
        bnc845rf_current_power_label.setFont(self.font)
        self.bnc845rf_current_power_reading_label = QLabel('N/A:')
        self.bnc845rf_current_power_reading_label.setFont(self.font)
        self.bnc845rf_current_power_layout.addWidget(bnc845rf_current_power_label)
        self.bnc845rf_current_power_layout.addWidget(self.bnc845rf_current_power_reading_label)

        self.bnc845rf_modulation_layout = QHBoxLayout()
        bnc845rf_modulation_label = QLabel('Modulation Type:')
        bnc845rf_modulation_label.setFont(self.font)
        self.bnc845rf_modulation_reading_label = QLabel('N/A')
        self.bnc845rf_modulation_reading_label.setFont(self.font)
        self.bnc845rf_modulation_layout.addWidget(bnc845rf_modulation_label)
        self.bnc845rf_modulation_layout.addWidget(self.bnc845rf_modulation_reading_label)

        self.bnc845rf_modulation_depth_reading_layout = QHBoxLayout()
        bnc845rf_modulation_depth_label = QLabel('Modulation Depth:')
        bnc845rf_modulation_depth_label.setFont(self.font)
        self.bnc845rf_modulation_depth_reading_label = QLabel('N/A')
        self.bnc845rf_modulation_depth_reading_label.setFont(self.font)
        self.bnc845rf_modulation_depth_reading_layout.addWidget(bnc845rf_modulation_depth_label)
        self.bnc845rf_modulation_depth_reading_layout.addWidget(self.bnc845rf_modulation_depth_reading_label)

        self.bnc845rf_modulation_frequency_reading_layout = QHBoxLayout()
        bnc845rf_modulation_frequency_label = QLabel('Modulation Frequency:')
        bnc845rf_modulation_frequency_label.setFont(self.font)
        self.bnc845rf_modulation_frequency_reading_label = QLabel('N/A')
        self.bnc845rf_modulation_frequency_reading_label.setFont(self.font)
        self.bnc845rf_modulation_frequency_reading_layout.addWidget(bnc845rf_modulation_frequency_label)
        self.bnc845rf_modulation_frequency_reading_layout.addWidget(self.bnc845rf_modulation_frequency_reading_label)

        self.bnc845rf_modulation_state_layout = QHBoxLayout()
        bnc845rf_modulation_state_label = QLabel('Modulation State:')
        bnc845rf_modulation_state_label.setFont(self.font)
        self.bnc845rf_modulation_state_reading_label = QLabel('N/A')
        self.bnc845rf_modulation_state_reading_label.setFont(self.font)
        self.bnc845rf_modulation_state_layout.addWidget(bnc845rf_modulation_state_label)
        self.bnc845rf_modulation_state_layout.addWidget(self.bnc845rf_modulation_state_reading_label)

        self.bnc845rf_state_layout = QHBoxLayout()
        bnc845rf_state_label = QLabel('RF State:')
        bnc845rf_state_label.setFont(self.font)
        self.bnc845rf_state_reading_label = QLabel('N/A')
        self.bnc845rf_state_reading_label.setFont(self.font)
        self.bnc845rf_state_layout.addWidget(bnc845rf_state_label)
        self.bnc845rf_state_layout.addWidget(self.bnc845rf_state_reading_label)

        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_current_frequency_layout)
        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_current_power_layout)
        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_modulation_layout)
        # self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_modulation_depth_reading_layout)
        # self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_modulation_frequency_reading_layout)
        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_modulation_state_layout)
        self.bnc845rf_window_reading_layout.addLayout(self.bnc845rf_state_layout)

        return self.bnc845rf_window_reading_layout

    def bnc845rf_window_setting_ui(self):
        self.bnc845rf_setting_layout = QVBoxLayout()

        self.bnc845rf_loop_setting_content_layout = QVBoxLayout()
        self.bnc845rf_loop_setting_layout = QHBoxLayout()
        bnc845rf_loop_setting_label = QLabel('Select the Experiment Loop:')
        bnc845rf_loop_setting_label.setFont(self.font)
        self.bnc845rf_loop_setting_combo = QComboBox()
        self.bnc845rf_loop_setting_combo.setFont(self.font)
        self.bnc845rf_loop_setting_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_loop_setting_combo.addItems(
            ["Select Loop", "Frequency Dependent", "Power Dependent", "Frequency and Power Dependent"])
        self.bnc845rf_loop_setting_combo.currentIndexChanged.connect(self.bnc845rf_loop_selection_ui)
        self.bnc845rf_loop_setting_layout.addWidget(bnc845rf_loop_setting_label)
        self.bnc845rf_loop_setting_layout.addWidget(self.bnc845rf_loop_setting_combo)

        self.bnc845rf_setting_layout.addLayout(self.bnc845rf_loop_setting_layout)
        self.bnc845rf_setting_layout.addLayout(self.bnc845rf_loop_setting_content_layout)
        self.bnc845rf_setting_layout.addLayout(self.bnc845rf_modulation_ui())

        return self.bnc845rf_setting_layout

    def bnc845rf_modulation_ui(self):
        self.bnc845rf_modulation_layout =QVBoxLayout()

        self.bnc845rf_modulation_select_layout = QHBoxLayout()
        self.bnc845rf_modulation_label = QLabel('Modulation: ')
        self.bnc845rf_modulation_label.setFont(self.font)
        self.bnc845rf_modulation_combo = QComboBox()
        self.bnc845rf_modulation_combo.setFont(self.font)
        self.bnc845rf_modulation_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_modulation_combo.addItems(
            ["Select Modulation", "Pulse Mod", "Amplitude Mod", "Frequency Mod", "Phase Mod"])
        self.bnc845rf_modulation_combo.currentIndexChanged.connect(self.bnc845rf_modulation_selection_ui)

        self.bnc845rf_modulation_select_layout.addWidget(self.bnc845rf_modulation_label)
        self.bnc845rf_modulation_select_layout.addWidget(self.bnc845rf_modulation_combo)

        self.bnc845rf_modulation_selected_layout = QVBoxLayout()

        self.bnc845rf_modulation_layout.addLayout(self.bnc845rf_modulation_select_layout)
        self.bnc845rf_modulation_layout.addLayout(self.bnc845rf_modulation_selected_layout)
        return self.bnc845rf_modulation_layout

    def bnc845rf_loop_selection_ui(self):
        self.clear_layout(self.bnc845rf_loop_setting_content_layout)
        if self.bnc845rf_loop_setting_combo.currentIndex() == 1:
            self.bnc845rf_frequency_radio_buttom_layout = QHBoxLayout()
            self.bnc845rf_frequency_zone_layout = QVBoxLayout()

            self.bnc845rf_frequency_zone_1 = False
            self.bnc845rf_frequency_zone_2 = False
            self.bnc845rf_frequency_zone_3 = False
            self.bnc845rf_frequency_zone_customized = False

            self.bnc845rf_frequency_zone_number_label = QLabel('Number of Independent Frequency Regions:')
            self.bnc845rf_frequency_zone_number_label.setFont(self.font)
            self.bnc845rf_frequency_zone_one_radio_button = QRadioButton("1")
            self.bnc845rf_frequency_zone_one_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_one_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_two_radio_button = QRadioButton("2")
            self.bnc845rf_frequency_zone_two_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_two_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_three_radio_button = QRadioButton("3")
            self.bnc845rf_frequency_zone_three_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_three_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_customized_radio_button = QRadioButton("Customize")
            self.bnc845rf_frequency_zone_customized_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_customized_radio_button.toggled.connect(self.select_frequency_zone)

            self.bnc845rf_frequency_zone_radio_button_group = QButtonGroup()
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_one_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_two_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_three_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(
                self.bnc845rf_frequency_zone_customized_radio_button)

            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_one_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_two_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_three_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_customized_radio_button)
            self.bnc845rf_power_setting_layout = QHBoxLayout()
            bnc845rf_power_setting_label = QLabel('Power:')
            bnc845rf_power_setting_label.setFont(self.font)
            self.bnc845rf_power_setting_entry = QLineEdit()
            self.bnc845rf_power_setting_entry.setFont(self.font)
            bnc845rf_power_setting_unit_label = QLabel('dbm')
            bnc845rf_power_setting_unit_label.setFont(self.font)
            self.bnc845rf_power_setting_layout.addWidget(bnc845rf_power_setting_label)
            self.bnc845rf_power_setting_layout.addWidget(self.bnc845rf_power_setting_entry)
            self.bnc845rf_power_setting_layout.addWidget(bnc845rf_power_setting_unit_label)

            self.bnc845rf_loop_setting_content_layout.addWidget(self.bnc845rf_frequency_zone_number_label)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_radio_buttom_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_zone_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_setting_layout)
        elif self.bnc845rf_loop_setting_combo.currentIndex() == 2:
            self.bnc845rf_power_radio_buttom_layout = QHBoxLayout()
            self.bnc845rf_power_zone_layout = QVBoxLayout()

            self.bnc845rf_power_zone_1 = False
            self.bnc845rf_power_zone_customized = False

            self.bnc845rf_power_zone_number_label = QLabel('Number of Independent Power Regions:')
            self.bnc845rf_power_zone_number_label.setFont(self.font)
            self.bnc845rf_power_zone_one_radio_button = QRadioButton("1")
            self.bnc845rf_power_zone_one_radio_button.setFont(self.font)
            self.bnc845rf_power_zone_one_radio_button.toggled.connect(self.select_power_zone)
            self.bnc845rf_power_zone_customized_radio_button = QRadioButton("Customize")
            self.bnc845rf_power_zone_customized_radio_button.setFont(self.font)
            self.bnc845rf_power_zone_customized_radio_button.toggled.connect(self.select_power_zone)

            self.bnc845rf_power_radio_buttom_layout.addWidget(self.bnc845rf_power_zone_one_radio_button)
            self.bnc845rf_power_radio_buttom_layout.addWidget(self.bnc845rf_power_zone_customized_radio_button)

            self.bnc845rf_power_zone_radio_button_group = QButtonGroup()
            self.bnc845rf_power_zone_radio_button_group.addButton(self.bnc845rf_power_zone_one_radio_button)
            self.bnc845rf_power_zone_radio_button_group.addButton(self.bnc845rf_power_zone_customized_radio_button)


            self.bnc845rf_frequency_setting_layout = QHBoxLayout()
            bnc845rf_frequency_setting_label = QLabel('Frequency:')
            bnc845rf_frequency_setting_label.setFont(self.font)
            self.bnc845rf_frequency_setting_entry = QLineEdit()
            self.bnc845rf_frequency_setting_entry.setFont(self.font)
            self.bnc845rf_frequency_setting_unit_combo = QComboBox()
            self.bnc845rf_frequency_setting_unit_combo.setFont(self.font)
            self.bnc845rf_frequency_setting_unit_combo.setStyleSheet(self.QCombo_stylesheet)
            self.bnc845rf_frequency_setting_unit_combo.addItems(
                ["Select Unit", "Hz", "kHz", "MHz", "GHz"])
            self.bnc845rf_frequency_setting_layout.addWidget(bnc845rf_frequency_setting_label)
            self.bnc845rf_frequency_setting_layout.addWidget(self.bnc845rf_frequency_setting_entry)
            self.bnc845rf_frequency_setting_layout.addWidget(self.bnc845rf_frequency_setting_unit_combo)

            self.bnc845rf_loop_setting_content_layout.addWidget(self.bnc845rf_frequency_zone_number_label)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_radio_buttom_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_zone_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_setting_layout)
        elif self.bnc845rf_loop_setting_combo.currentIndex() == 3:
            self.bnc845rf_frequency_radio_buttom_layout = QHBoxLayout()
            self.bnc845rf_frequency_zone_layout = QVBoxLayout()

            self.bnc845rf_frequency_zone_1 = False
            self.bnc845rf_frequency_zone_2 = False
            self.bnc845rf_frequency_zone_3 = False
            self.bnc845rf_frequency_zone_customized = False

            self.bnc845rf_frequency_zone_number_label = QLabel('Number of Independent Frequency Regions:')
            self.bnc845rf_frequency_zone_number_label.setFont(self.font)
            self.bnc845rf_frequency_zone_one_radio_button = QRadioButton("1")
            self.bnc845rf_frequency_zone_one_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_one_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_two_radio_button = QRadioButton("2")
            self.bnc845rf_frequency_zone_two_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_two_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_three_radio_button = QRadioButton("3")
            self.bnc845rf_frequency_zone_three_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_three_radio_button.toggled.connect(self.select_frequency_zone)
            self.bnc845rf_frequency_zone_customized_radio_button = QRadioButton("Customize")
            self.bnc845rf_frequency_zone_customized_radio_button.setFont(self.font)
            self.bnc845rf_frequency_zone_customized_radio_button.toggled.connect(self.select_frequency_zone)

            self.bnc845rf_frequency_zone_radio_button_group = QButtonGroup()
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_one_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_two_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_three_radio_button)
            self.bnc845rf_frequency_zone_radio_button_group.addButton(self.bnc845rf_frequency_zone_customized_radio_button)

            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_one_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_two_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_three_radio_button)
            self.bnc845rf_frequency_radio_buttom_layout.addWidget(self.bnc845rf_frequency_zone_customized_radio_button)

            self.bnc845rf_power_radio_buttom_layout = QHBoxLayout()
            self.bnc845rf_power_zone_layout = QVBoxLayout()

            self.bnc845rf_power_zone_1 = False
            self.bnc845rf_power_zone_customized = False

            self.bnc845rf_power_zone_number_label = QLabel('Number of Independent Power Regions:')
            self.bnc845rf_power_zone_number_label.setFont(self.font)
            self.bnc845rf_power_zone_one_radio_button = QRadioButton("1")
            self.bnc845rf_power_zone_one_radio_button.setFont(self.font)
            self.bnc845rf_power_zone_one_radio_button.toggled.connect(self.select_power_zone)
            self.bnc845rf_power_zone_customized_radio_button = QRadioButton("Customize")
            self.bnc845rf_power_zone_customized_radio_button.setFont(self.font)
            self.bnc845rf_power_zone_customized_radio_button.toggled.connect(self.select_power_zone)

            self.bnc845rf_power_radio_buttom_layout.addWidget(self.bnc845rf_power_zone_one_radio_button)
            self.bnc845rf_power_radio_buttom_layout.addWidget(self.bnc845rf_power_zone_customized_radio_button)

            self.bnc845rf_loop_setting_content_layout.addWidget(self.bnc845rf_frequency_zone_number_label)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_radio_buttom_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_frequency_zone_layout)
            self.bnc845rf_loop_setting_content_layout.addWidget(self.bnc845rf_power_zone_number_label)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_radio_buttom_layout)
            self.bnc845rf_loop_setting_content_layout.addLayout(self.bnc845rf_power_zone_layout)

    def bnc845rf_modulation_selection_ui(self):
        try:
            self.clear_layout(self.bnc845rf_modulation_selected_layout)
            if self.bnc845rf_modulation_combo.currentIndex() == 1:
                None
            elif self.bnc845rf_modulation_combo.currentIndex() == 2:
                self.bnc845rf_am_layout = QVBoxLayout()

                bnc845rf_am_freq_layout = QHBoxLayout()
                bnc845rf_am_freq_label = QLabel('Mod Frequency:')
                bnc845rf_am_freq_label.setFont(self.font)
                self.bnc845rf_am_freq_entry = QLineEdit()
                self.bnc845rf_am_freq_entry.setFont(self.font)
                bnc845rf_am_freq_unit_label = QLabel('Hz')
                bnc845rf_am_freq_unit_label.setFont(self.font)
                bnc845rf_am_freq_layout.addWidget(bnc845rf_am_freq_label)
                bnc845rf_am_freq_layout.addWidget(self.bnc845rf_am_freq_entry)
                bnc845rf_am_freq_layout.addWidget(bnc845rf_am_freq_unit_label)

                bnc845rf_am_depth_layout = QHBoxLayout()
                bnc845rf_am_depth_label = QLabel('Mod Depth:')
                bnc845rf_am_depth_label.setFont(self.font)
                self.bnc845rf_am_depth_entry = QLineEdit()
                self.bnc845rf_am_depth_entry.setFont(self.font)
                bnc845rf_am_depth_unit_label = QLabel('%')
                bnc845rf_am_depth_unit_label.setFont(self.font)
                bnc845rf_am_depth_layout.addWidget(bnc845rf_am_depth_label)
                bnc845rf_am_depth_layout.addWidget(self.bnc845rf_am_depth_entry)
                bnc845rf_am_depth_layout.addWidget(bnc845rf_am_depth_unit_label)

                bnc845rf_am_source_layout = QHBoxLayout()
                bnc845rf_am_source_label = QLabel('Source:')
                bnc845rf_am_source_label.setFont(self.font)
                self.bnc845rf_am_source_combo = QComboBox()
                self.bnc845rf_am_source_combo.setFont(self.font)
                self.bnc845rf_am_source_combo.setStyleSheet(self.QCombo_stylesheet)
                self.bnc845rf_am_source_combo.addItems(
                    ["INT", "EXT"])
                bnc845rf_am_source_layout.addWidget(bnc845rf_am_source_label)
                bnc845rf_am_source_layout.addWidget(self.bnc845rf_am_source_combo)

                # self.bnc845rf_am_modulation_on_off_button = QPushButton('On')
                # self.bnc845rf_am_modulation_on_off_button.setFont(self.font)
                # self.bnc845rf_am_modulation_on_off_button.setStyleSheet(self.Button_stylesheet)
                # self.bnc845rf_am_modulation_on_off_button.clicked.connect(self.bnc845_am_control)

                self.bnc845rf_am_layout.addLayout(bnc845rf_am_freq_layout)
                self.bnc845rf_am_layout.addLayout(bnc845rf_am_depth_layout)
                self.bnc845rf_am_layout.addLayout(bnc845rf_am_source_layout)
                # self.bnc845rf_am_layout.addWidget(self.bnc845rf_am_modulation_on_off_button)
                self.bnc845rf_modulation_selected_layout.addLayout(self.bnc845rf_am_layout)
            elif self.bnc845rf_modulation_combo.currentIndex() == 3:
                None
            else:
                None

        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def select_frequency_zone(self):
        try:
            if self.bnc845rf_frequency_zone_one_radio_button.isChecked() and self.bnc845rf_frequency_zone_1 == False:
                self.bnc845rf_frequency_zone_one_radio_button.setChecked(False)
                self.bnc845rf_frequency_zone_1 = True
                self.bnc845rf_frequency_zone_2 = False
                self.bnc845rf_frequency_zone_3 = False
                self.bnc845rf_frequency_zone_customized = False
                self.select_frequency_zone_one()
                self.bnc845rf_frequency_zone_one_radio_button.setChecked(False)
            elif self.bnc845rf_frequency_zone_two_radio_button.isChecked() and self.bnc845rf_frequency_zone_2 == False:
                self.bnc845rf_frequency_zone_two_radio_button.setChecked(False)
                self.bnc845rf_frequency_zone_1 = False
                self.bnc845rf_frequency_zone_2 = True
                self.bnc845rf_frequency_zone_3 = False
                self.bnc845rf_frequency_zone_customized = False
                self.select_frequency_zone_two()
                self.bnc845rf_frequency_zone_two_radio_button.setChecked(False)
            elif self.bnc845rf_frequency_zone_three_radio_button.isChecked() and self.bnc845rf_frequency_zone_3 == False:
                self.bnc845rf_frequency_zone_three_radio_button.setChecked(False)
                self.bnc845rf_frequency_zone_1 = False
                self.bnc845rf_frequency_zone_2 = False
                self.bnc845rf_frequency_zone_3 = True
                self.bnc845rf_frequency_zone_customized = False
                self.select_frequency_zone_three()
                self.bnc845rf_frequency_zone_three_radio_button.setChecked(False)
            elif self.bnc845rf_frequency_zone_customized_radio_button.isChecked() and self.bnc845rf_frequency_zone_customized == False:
                self.bnc845rf_frequency_zone_customized_radio_button.setChecked(False)
                self.bnc845rf_frequency_zone_1 = False
                self.bnc845rf_frequency_zone_2 = False
                self.bnc845rf_frequency_zone_3 = False
                self.bnc845rf_frequency_zone_customized = True
                self.select_frequency_zone_customize()
                self.bnc845rf_frequency_zone_customized_radio_button.setChecked(False)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def select_power_zone(self):
        try:
            if self.bnc845rf_power_zone_one_radio_button.isChecked() and self.bnc845rf_power_zone_1 == False:
                self.bnc845rf_power_zone_one_radio_button.setChecked(False)
                self.bnc845rf_power_zone_1 = True
                self.bnc845rf_power_zone_customized = False
                self.select_power_zone_one()
                self.bnc845rf_power_zone_one_radio_button.setChecked(False)
            elif self.bnc845rf_power_zone_customized_radio_button.isChecked() and self.bnc845rf_power_zone_customized == False:
                self.bnc845rf_power_zone_customized_radio_button.setChecked(False)
                self.bnc845rf_power_zone_1 = False
                self.bnc845rf_power_zone_customized = True
                self.select_power_zone_customize()
                self.bnc845rf_power_zone_customized_radio_button.setChecked(False)
        except Exception as e:
            tb_str = traceback.format_exc()
            QMessageBox.warning(self, "Error", f'{tb_str} {str(e)}')

    def select_frequency_zone_one(self):
        self.bnc845rf_frequency_zone_one_freq_layout = QVBoxLayout()

        self.bnc845rf_frequency_zone_range_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_one_freq_from_label = QLabel('Range: From')
        self.bnc845rf_frequency_zone_one_freq_from_label.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_from_entry = QLineEdit()
        self.bnc845rf_frequency_zone_one_freq_from_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_to_label = QLabel(' to ')
        self.bnc845rf_frequency_zone_one_freq_to_label.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_to_entry = QLineEdit()
        self.bnc845rf_frequency_zone_one_freq_to_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_one_freq_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_one_freq_unit_combo.addItems(
            ["Select Unit", "Hz", "kHz", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_from_label)
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_from_entry)
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_to_label)
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_to_entry)
        self.bnc845rf_frequency_zone_range_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_unit_combo)

        self.bnc845rf_frequency_zone_step_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_one_freq_step_label = QLabel('Step Size:')
        self.bnc845rf_frequency_zone_one_freq_step_label.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_step_entry = QLineEdit()
        self.bnc845rf_frequency_zone_one_freq_step_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_step_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_one_freq_step_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_one_freq_step_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_one_freq_step_unit_combo.addItems(
            ["Select Unit", "Hz", "kHz", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_step_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_step_label)
        self.bnc845rf_frequency_zone_step_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_step_entry)
        self.bnc845rf_frequency_zone_step_layout.addWidget(self.bnc845rf_frequency_zone_one_freq_step_unit_combo)

        self.bnc845rf_frequency_zone_one_freq_layout.addLayout(self.bnc845rf_frequency_zone_range_layout)
        self.bnc845rf_frequency_zone_one_freq_layout.addLayout(self.bnc845rf_frequency_zone_step_layout)

        self.clear_layout(self.bnc845rf_frequency_zone_layout)
        self.bnc845rf_frequency_zone_layout.addLayout(self.bnc845rf_frequency_zone_one_freq_layout)

    def select_power_zone_one(self):
        self.bnc845rf_power_zone_one_power_layout = QVBoxLayout()

        self.bnc845rf_power_zone_range_layout = QHBoxLayout()
        bnc845rf_power_zone_one_power_from_label = QLabel('Range: From')
        bnc845rf_power_zone_one_power_from_label.setFont(self.font)
        self.bnc845rf_power_zone_one_power_from_entry = QLineEdit()
        self.bnc845rf_power_zone_one_power_from_entry.setFont(self.font)
        bnc845rf_power_zone_one_power_to_label = QLabel(' to ')
        bnc845rf_power_zone_one_power_to_label.setFont(self.font)
        self.bnc845rf_power_zone_one_power_to_entry = QLineEdit()
        self.bnc845rf_power_zone_one_power_to_entry.setFont(self.font)
        bnc845rf_power_zone_one_power_unit_label = QLabel('dBm')
        bnc845rf_power_zone_one_power_unit_label.setFont(self.font)
        self.bnc845rf_power_zone_range_layout.addWidget(bnc845rf_power_zone_one_power_from_label)
        self.bnc845rf_power_zone_range_layout.addWidget(self.bnc845rf_power_zone_one_power_from_entry)
        self.bnc845rf_power_zone_range_layout.addWidget(bnc845rf_power_zone_one_power_to_label)
        self.bnc845rf_power_zone_range_layout.addWidget(self.bnc845rf_power_zone_one_power_to_entry)
        self.bnc845rf_power_zone_range_layout.addWidget(bnc845rf_power_zone_one_power_unit_label)

        self.bnc845rf_power_zone_step_layout = QHBoxLayout()
        bnc845rf_power_zone_one_power_step_label = QLabel('Step Size:')
        bnc845rf_power_zone_one_power_step_label.setFont(self.font)
        self.bnc845rf_power_zone_one_power_step_entry = QLineEdit()
        self.bnc845rf_power_zone_one_power_step_entry.setFont(self.font)
        bnc845rf_power_zone_one_power_step_unit_label = QLabel('dBm')
        bnc845rf_power_zone_one_power_step_unit_label.setFont(self.font)

        self.bnc845rf_power_zone_step_layout.addWidget(bnc845rf_power_zone_one_power_step_label)
        self.bnc845rf_power_zone_step_layout.addWidget(self.bnc845rf_power_zone_one_power_step_entry)
        self.bnc845rf_power_zone_step_layout.addWidget(bnc845rf_power_zone_one_power_step_unit_label)

        self.bnc845rf_power_zone_one_power_layout.addLayout(self.bnc845rf_power_zone_range_layout)
        self.bnc845rf_power_zone_one_power_layout.addLayout(self.bnc845rf_power_zone_step_layout)

        self.clear_layout(self.bnc845rf_power_zone_layout)
        self.bnc845rf_power_zone_layout.addLayout(self.bnc845rf_power_zone_one_power_layout)

    def select_frequency_zone_two(self):
        self.select_frequency_zone_one()
        self.bnc845rf_frequency_zone_two_freq_layout = QVBoxLayout()

        self.bnc845rf_frequency_zone_two_range_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_two_freq_from_label = QLabel('Range: From')
        self.bnc845rf_frequency_zone_two_freq_from_label.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_from_entry = QLineEdit()
        self.bnc845rf_frequency_zone_two_freq_from_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_to_label = QLabel(' to ')
        self.bnc845rf_frequency_zone_two_freq_to_label.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_to_entry = QLineEdit()
        self.bnc845rf_frequency_zone_two_freq_to_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_two_freq_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_two_freq_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_from_label)
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_from_entry)
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_to_label)
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_to_entry)
        self.bnc845rf_frequency_zone_two_range_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_unit_combo)

        self.bnc845rf_frequency_zone_two_step_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_two_freq_step_label = QLabel('Step Size:')
        self.bnc845rf_frequency_zone_two_freq_step_label.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_step_entry = QLineEdit()
        self.bnc845rf_frequency_zone_two_freq_step_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_step_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_two_freq_step_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_two_freq_step_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_two_freq_step_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_two_step_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_step_label)
        self.bnc845rf_frequency_zone_two_step_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_step_entry)
        self.bnc845rf_frequency_zone_two_step_layout.addWidget(self.bnc845rf_frequency_zone_two_freq_step_unit_combo)

        self.bnc845rf_frequency_zone_two_freq_layout.addLayout(self.bnc845rf_frequency_zone_two_range_layout)
        self.bnc845rf_frequency_zone_two_freq_layout.addLayout(self.bnc845rf_frequency_zone_two_step_layout)

        self.bnc845rf_frequency_zone_layout.addLayout(self.bnc845rf_frequency_zone_two_freq_layout)

    def select_frequency_zone_three(self):
        self.select_frequency_zone_two()
        self.bnc845rf_frequency_zone_three_freq_layout = QVBoxLayout()

        self.bnc845rf_frequency_zone_three_range_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_three_freq_from_label = QLabel('Range: From')
        self.bnc845rf_frequency_zone_three_freq_from_label.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_from_entry = QLineEdit()
        self.bnc845rf_frequency_zone_three_freq_from_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_to_label = QLabel(' to ')
        self.bnc845rf_frequency_zone_three_freq_to_label.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_to_entry = QLineEdit()
        self.bnc845rf_frequency_zone_three_freq_to_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_three_freq_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_three_freq_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_from_label)
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_from_entry)
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_to_label)
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_to_entry)
        self.bnc845rf_frequency_zone_three_range_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_unit_combo)

        self.bnc845rf_frequency_zone_three_step_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_three_freq_step_label = QLabel('Step Size:')
        self.bnc845rf_frequency_zone_three_freq_step_label.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_step_entry = QLineEdit()
        self.bnc845rf_frequency_zone_three_freq_step_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_step_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_three_freq_step_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_three_freq_step_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_three_freq_step_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_three_step_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_step_label)
        self.bnc845rf_frequency_zone_three_step_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_step_entry)
        self.bnc845rf_frequency_zone_three_step_layout.addWidget(self.bnc845rf_frequency_zone_three_freq_step_unit_combo)

        self.bnc845rf_frequency_zone_three_freq_layout.addLayout(self.bnc845rf_frequency_zone_three_range_layout)
        self.bnc845rf_frequency_zone_three_freq_layout.addLayout(self.bnc845rf_frequency_zone_three_step_layout)

        self.bnc845rf_frequency_zone_layout.addLayout(self.bnc845rf_frequency_zone_three_freq_layout)

    def select_frequency_zone_customize(self):
        self.bnc845rf_frequency_zone_customized_layout = QHBoxLayout()
        self.bnc845rf_frequency_zone_customized_label = QLabel('Frequency List: [')
        self.bnc845rf_frequency_zone_customized_label.setFont(self.font)
        self.bnc845rf_frequency_zone_customized_entry = QLineEdit()
        self.bnc845rf_frequency_zone_customized_entry.setFont(self.font)
        self.bnc845rf_frequency_zone_customized_end_label = QLabel(']')
        self.bnc845rf_frequency_zone_customized_end_label.setFont(self.font)
        self.bnc845rf_frequency_zone_customized_unit_combo = QComboBox()
        self.bnc845rf_frequency_zone_customized_unit_combo.setFont(self.font)
        self.bnc845rf_frequency_zone_customized_unit_combo.setStyleSheet(self.QCombo_stylesheet)
        self.bnc845rf_frequency_zone_customized_unit_combo.addItems(
            ["Select Unit", "Hz", "kHZ", "MHz", "GHz"])
        self.bnc845rf_frequency_zone_customized_layout.addWidget(self.bnc845rf_frequency_zone_customized_label)
        self.bnc845rf_frequency_zone_customized_layout.addWidget(self.bnc845rf_frequency_zone_customized_entry)
        self.bnc845rf_frequency_zone_customized_layout.addWidget(self.bnc845rf_frequency_zone_customized_end_label)
        self.bnc845rf_frequency_zone_customized_layout.addWidget(self.bnc845rf_frequency_zone_customized_unit_combo)

        self.clear_layout(self.bnc845rf_frequency_zone_layout)
        self.bnc845rf_frequency_zone_layout.addLayout(self.bnc845rf_frequency_zone_customized_layout)

    def select_power_zone_customize(self):
        self.bnc845rf_power_zone_customized_layout = QHBoxLayout()
        bnc845rf_power_zone_customized_label = QLabel('Power List: [')
        bnc845rf_power_zone_customized_label.setFont(self.font)
        self.bnc845rf_power_zone_customized_entry = QLineEdit()
        self.bnc845rf_power_zone_customized_entry.setFont(self.font)
        bnc845rf_power_zone_customized_end_label = QLabel(']')
        bnc845rf_power_zone_customized_end_label.setFont(self.font)
        bnc845rf_power_zone_customized_unit_label = QLabel('dBm')
        bnc845rf_power_zone_customized_unit_label.setFont(self.font)
        self.bnc845rf_power_zone_customized_layout.addWidget(bnc845rf_power_zone_customized_label)
        self.bnc845rf_power_zone_customized_layout.addWidget(self.bnc845rf_power_zone_customized_entry)
        self.bnc845rf_power_zone_customized_layout.addWidget(bnc845rf_power_zone_customized_end_label)
        self.bnc845rf_power_zone_customized_layout.addWidget(bnc845rf_power_zone_customized_unit_label)

        self.clear_layout(self.bnc845rf_power_zone_layout)
        self.bnc845rf_power_zone_layout.addLayout(self.bnc845rf_power_zone_customized_layout)

    def _get_frequency_zone_one(self):
        """Get frequency zone 1 settings and return as list"""
        zone_data = {
            'from': self.bnc845rf_frequency_zone_one_freq_from_entry.text(),
            'to': self.bnc845rf_frequency_zone_one_freq_to_entry.text(),
            'step': self.bnc845rf_frequency_zone_one_freq_step_entry.text(),
            'unit': self.bnc845rf_frequency_zone_one_freq_unit_combo.currentText(),
            'step_unit': self.bnc845rf_frequency_zone_one_freq_step_unit_combo.currentText()
        }

        # Generate frequency list
        zone_data['frequency_list'] = self._generate_frequency_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step'],
            zone_data['unit'],
            zone_data['step_unit']
        )

        return zone_data

    def _get_frequency_zone_two(self):
        """Get frequency zone 2 settings and return as list"""
        zone_data = {
            'from': self.bnc845rf_frequency_zone_two_freq_from_entry.text(),
            'to': self.bnc845rf_frequency_zone_two_freq_to_entry.text(),
            'step': self.bnc845rf_frequency_zone_two_freq_step_entry.text(),
            'unit': self.bnc845rf_frequency_zone_two_freq_unit_combo.currentText(),
            'step_unit': self.bnc845rf_frequency_zone_two_freq_step_unit_combo.currentText()
        }

        # Generate frequency list
        zone_data['frequency_list'] = self._generate_frequency_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step'],
            zone_data['unit'],
            zone_data['step_unit']
        )

        return zone_data

    def _get_frequency_zone_three(self):
        """Get frequency zone 3 settings and return as list"""
        zone_data = {
            'from': self.bnc845rf_frequency_zone_three_freq_from_entry.text(),
            'to': self.bnc845rf_frequency_zone_three_freq_to_entry.text(),
            'step': self.bnc845rf_frequency_zone_three_freq_step_entry.text(),
            'unit': self.bnc845rf_frequency_zone_three_freq_unit_combo.currentText(),
            'step_unit': self.bnc845rf_frequency_zone_three_freq_step_unit_combo.currentText()
        }

        # Generate frequency list
        zone_data['frequency_list'] = self._generate_frequency_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step'],
            zone_data['unit'],
            zone_data['step_unit']
        )

        return zone_data

    def _get_frequency_zone_customized(self):
        """Get customized frequency zone settings"""
        zone_data = {
            'raw_input': self.bnc845rf_frequency_zone_customized_entry.text(),
            'unit': self.bnc845rf_frequency_zone_customized_unit_combo.currentText()
        }

        # Parse the frequency list from the entry
        unit = self.bnc845rf_frequency_zone_customized_unit_combo.currentText()
        frequency_str = self.bnc845rf_frequency_zone_customized_entry.text()
        unit_multiplier = {
            'Hz': 1,
            'kHz': 1e3,
            'MHz': 1e6,
            'GHz': 1e9
        }

        multiplier = unit_multiplier.get(unit, 1)
        freq_list = self._parse_custom_list(frequency_str)
        frequency_list_hz = [freq * multiplier for freq in freq_list]
        zone_data['frequency_list'] = frequency_list_hz

        return zone_data

    def _get_power_zone_one(self):
        """Get power zone 1 settings and return as list in dBm"""
        zone_data = {
            'from': self.bnc845rf_power_zone_one_power_from_entry.text(),
            'to': self.bnc845rf_power_zone_one_power_to_entry.text(),
            'step': self.bnc845rf_power_zone_one_power_step_entry.text(),
            'unit': 'dBm'
        }

        # Generate power list
        zone_data['power_list'] = self._generate_power_list(
            zone_data['from'],
            zone_data['to'],
            zone_data['step']
        )

        return zone_data

    def _get_power_zone_customized(self):
        """Get customized power zone settings"""
        zone_data = {
            'raw_input': self.bnc845rf_power_zone_customized_entry.text(),
            'unit': 'dBm'
        }

        # Parse the power list from the entry
        power_str = self.bnc845rf_power_zone_customized_entry.text()
        zone_data['power_list'] = self._parse_custom_list(power_str)

        return zone_data

    def _get_modulation_settings(self):
        """Get modulation settings (user input settings)"""
        modulation_data = {
            'type': self.bnc845rf_modulation_combo.currentText()
        }

        # Get modulation-specific settings
        if self.bnc845rf_modulation_combo.currentIndex() == 2:  # Amplitude Modulation
            if hasattr(self, 'bnc845rf_am_freq_entry'):
                modulation_data['am_frequency'] = self.bnc845rf_am_freq_entry.text()
                modulation_data['am_frequency_unit'] = 'Hz'

            if hasattr(self, 'bnc845rf_am_depth_entry'):
                modulation_data['am_depth'] = self.bnc845rf_am_depth_entry.text()
                modulation_data['am_depth_unit'] = '%'

            if hasattr(self, 'bnc845rf_am_source_combo'):
                modulation_data['am_source'] = self.bnc845rf_am_source_combo.currentText()

        return modulation_data

    def _get_modulation_readings(self):
        """
        Get all modulation readings from the instrument display.
        These are the actual measured/read values from the BNC845RF.
        """
        readings = {}

        try:
            # Get modulation type reading from label
            if hasattr(self, 'bnc845rf_modulation_reading_label'):
                readings['modulation_type'] = self.bnc845rf_modulation_reading_label.text()

            # Get modulation depth reading from label
            if hasattr(self, 'bnc845rf_modulation_depth_reading_label'):
                readings['modulation_depth'] = self.bnc845rf_modulation_depth_reading_label.text()

            # Get modulation frequency reading from label
            if hasattr(self, 'bnc845rf_modulation_frequency_reading_label'):
                readings['modulation_frequency'] = self.bnc845rf_modulation_frequency_reading_label.text()

            # Get modulation state reading from label
            if hasattr(self, 'bnc845rf_modulation_state_reading_label'):
                readings['modulation_state'] = self.bnc845rf_modulation_state_reading_label.text()

        except Exception as e:
            print(f"Error getting modulation readings: {str(e)}")

        return readings

    def _get_modulation_readings_from_instrument(self, instrument, bnc_cmd):
        """
        Query all modulation settings directly from the BNC845RF instrument.
        This queries the actual instrument state, not just the UI labels.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance

        Returns:
            Dictionary with all modulation readings from instrument
        """
        readings = {}

        try:
            # Query AM (Amplitude Modulation) settings
            try:
                readings['am_state'] = bnc_cmd.get_am_state(instrument).strip()
                readings['am_depth'] = bnc_cmd.get_am_depth(instrument).strip()
                readings['am_source'] = bnc_cmd.get_am_source(instrument).strip()
                readings['am_internal_frequency'] = bnc_cmd.get_am_internal_frequency(instrument).strip()
            except Exception as e:
                readings['am_error'] = str(e)

            # Query FM (Frequency Modulation) settings
            try:
                readings['fm_state'] = bnc_cmd.get_fm_state(instrument).strip()
                readings['fm_deviation'] = bnc_cmd.get_fm_deviation(instrument).strip()
                readings['fm_source'] = bnc_cmd.get_fm_source(instrument).strip()
                readings['fm_internal_frequency'] = bnc_cmd.get_fm_internal_frequency(instrument).strip()
                readings['fm_sensitivity'] = bnc_cmd.get_fm_sensitivity(instrument).strip()
                readings['fm_coupling'] = bnc_cmd.get_fm_coupling(instrument).strip()
            except Exception as e:
                readings['fm_error'] = str(e)

            # Query PM (Phase Modulation) settings
            try:
                readings['pm_state'] = bnc_cmd.get_pm_state(instrument).strip()
                readings['pm_deviation'] = bnc_cmd.get_pm_deviation(instrument).strip()
                readings['pm_source'] = bnc_cmd.get_pm_source(instrument).strip()
                readings['pm_sensitivity'] = bnc_cmd.get_pm_sensitivity(instrument).strip()
            except Exception as e:
                readings['pm_error'] = str(e)

            # Query Pulse Modulation settings
            try:
                readings['pulse_state'] = bnc_cmd.get_pulse_state(instrument).strip()
                readings['pulse_source'] = bnc_cmd.get_pulse_source(instrument).strip()
                readings['pulse_polarity'] = bnc_cmd.get_pulse_polarity(instrument).strip()
                readings['pulse_internal_frequency'] = bnc_cmd.get_pulse_internal_frequency(instrument).strip()
                readings['pulse_internal_period'] = bnc_cmd.get_pulse_internal_period(instrument).strip()
                readings['pulse_internal_width'] = bnc_cmd.get_pulse_internal_width(instrument).strip()
                readings['pulse_mode'] = bnc_cmd.get_pulse_mode(instrument).strip()
            except Exception as e:
                readings['pulse_error'] = str(e)

        except Exception as e:
            readings['general_error'] = str(e)
            print(f"Error querying modulation from instrument: {str(e)}")

        return readings

    def apply_modulation_settings_to_instrument(self, settings, instrument, bnc_cmd):
        """
        Apply the current UI modulation settings to the BNC845RF instrument.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance

        Returns:
            Dictionary with success status and any errors
        """
        result = {
            'success': False,
            'applied_settings': {},
            'errors': []
        }

        try:
            # First, turn off all modulations
            try:
                bnc_cmd.set_am_state(instrument, 'OFF')
                bnc_cmd.set_fm_state(instrument, 'OFF')
                bnc_cmd.set_pm_state(instrument, 'OFF')
                bnc_cmd.set_pulse_state(instrument, 'OFF')
            except Exception as e:
                result['errors'].append(f"Error turning off modulations: {str(e)}")

            # Apply Pulse Modulation (index 1)
            if settings['modulation_settings']['type'] == 'None':
                print('No Modulation')
            elif settings['modulation_settings']['type'] == 'Pulse Mod':
                print('Pulse Mod')
                try:
                    bnc_cmd.set_pulse_state(instrument, 'ON')
                    result['applied_settings']['modulation_type'] = 'Pulse Modulation'
                    result['applied_settings']['pulse_state'] = 'ON'
                except Exception as e:
                    result['errors'].append(f"Pulse modulation error: {str(e)}")

            # Apply Amplitude Modulation (index 2)
            elif settings['modulation_settings']['type'] == 'Amplitude Mod':
                try:
                    am_freq = str(settings['modulation_settings']['am_frequency'])
                    bnc_cmd.set_am_internal_frequency(instrument, am_freq, 'Hz')
                    result['applied_settings']['am_frequency'] = f"{am_freq} Hz"

                    am_depth = settings['modulation_settings']['am_depth']  # Convert % to 0-0.99
                    bnc_cmd.set_am_depth(instrument, am_depth)
                    result['applied_settings']['am_depth'] = f"{am_depth}"

                    am_source = settings['modulation_settings']['am_source']
                    bnc_cmd.set_am_source(instrument, am_source)
                    result['applied_settings']['am_source'] = am_source

                    bnc_cmd.set_am_state(instrument, 'ON')
                    result['applied_settings']['modulation_type'] = 'Amplitude Modulation'
                    result['applied_settings']['am_state'] = 'ON'

                except Exception as e:
                    result['errors'].append(f"AM modulation error: {str(e)}")

            # Apply Frequency Modulation (index 3)
            elif settings['modulation_settings']['type'] == 'Frequency Mod':
                try:
                    # Add FM settings here when FM UI is implemented
                    bnc_cmd.set_fm_state(instrument, 'ON')
                    result['applied_settings']['modulation_type'] = 'Frequency Modulation'
                    result['applied_settings']['fm_state'] = 'ON'
                except Exception as e:
                    result['errors'].append(f"FM modulation error: {str(e)}")

            # Apply Phase Modulation (index 4)
            elif settings['modulation_settings']['type'] == 'Phase Mod':
                try:
                    # Add PM settings here when PM UI is implemented
                    bnc_cmd.set_pm_state(instrument, 'ON')
                    result['applied_settings']['modulation_type'] = 'Phase Modulation'
                    result['applied_settings']['pm_state'] = 'ON'
                except Exception as e:
                    result['errors'].append(f"PM modulation error: {str(e)}")

            # Check if there were any errors
            result['success'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"General error: {str(e)}")
            result['success'] = False

        return result

    def apply_frequency_settings_to_instrument(self, instrument, bnc_cmd):
        """
        Apply frequency settings from the UI to the BNC845RF instrument.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance

        Returns:
            Dictionary with success status and applied settings
        """
        result = {
            'success': False,
            'applied_settings': {},
            'errors': []
        }

        try:
            loop_type = self.bnc845rf_loop_setting_combo.currentIndex()

            # Frequency Dependent (index 1)
            if loop_type == 1:
                try:
                    bnc_cmd.set_frequency_mode(instrument, 'SWEep')

                    # Get frequency zone settings
                    settings = self.get_bnc845rf_settings()
                    if 'frequency_zones' in settings:
                        zones = settings['frequency_zones']

                        # For simplicity, use zone_1 settings
                        if 'zone_1' in zones:
                            zone = zones['zone_1']
                            freq_list = zone.get('frequency_list', [])

                            if freq_list:
                                bnc_cmd.set_frequency_start(instrument, freq_list[0], 'Hz')
                                bnc_cmd.set_frequency_stop(instrument, freq_list[-1], 'Hz')
                                bnc_cmd.set_sweep_points(instrument, len(freq_list))

                                result['applied_settings']['frequency_start'] = f"{freq_list[0]} Hz"
                                result['applied_settings']['frequency_stop'] = f"{freq_list[-1]} Hz"
                                result['applied_settings']['sweep_points'] = len(freq_list)

                    # Set fixed power
                    if hasattr(self, 'bnc845rf_power_setting_entry') and self.bnc845rf_power_setting_entry.text():
                        power = float(self.bnc845rf_power_setting_entry.text())
                        bnc_cmd.set_power_mode(instrument, 'FIXed')
                        bnc_cmd.set_power_level(instrument, power, 'dBm')
                        result['applied_settings']['power'] = f"{power} dBm"

                    result['applied_settings']['mode'] = 'Frequency Sweep'

                except Exception as e:
                    result['errors'].append(f"Frequency sweep error: {str(e)}")

            # Power Dependent (index 2)
            elif loop_type == 2:
                try:
                    bnc_cmd.set_power_mode(instrument, 'SWEep')

                    # Get power zone settings
                    settings = self.get_bnc845rf_settings()
                    if 'power_zones' in settings:
                        zones = settings['power_zones']

                        if 'zone_1' in zones:
                            zone = zones['zone_1']
                            power_list = zone.get('power_list', [])

                            if power_list:
                                bnc_cmd.set_power_start(instrument, power_list[0], 'dBm')
                                bnc_cmd.set_power_stop(instrument, power_list[-1], 'dBm')
                                bnc_cmd.set_sweep_points(instrument, len(power_list))

                                result['applied_settings']['power_start'] = f"{power_list[0]} dBm"
                                result['applied_settings']['power_stop'] = f"{power_list[-1]} dBm"
                                result['applied_settings']['sweep_points'] = len(power_list)

                    # Set fixed frequency
                    if hasattr(self,
                               'bnc845rf_frequency_setting_entry') and self.bnc845rf_frequency_setting_entry.text():
                        freq = float(self.bnc845rf_frequency_setting_entry.text())
                        bnc_cmd.set_frequency_mode(instrument, 'CW')
                        bnc_cmd.set_frequency_cw(instrument, freq, 'Hz')
                        result['applied_settings']['frequency'] = f"{freq} Hz"

                    result['applied_settings']['mode'] = 'Power Sweep'

                except Exception as e:
                    result['errors'].append(f"Power sweep error: {str(e)}")

            result['success'] = len(result['errors']) == 0

        except Exception as e:
            result['errors'].append(f"General error: {str(e)}")
            result['success'] = False

        return result

    def update_ui_from_instrument(self, instrument, bnc_cmd):
        """
        Update all UI labels with current readings from the BNC845RF instrument.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance
        """
        try:
            # Update current frequency reading
            def format_frequency_with_unit(freq_hz):
                """
                Convert frequency in Hz to the most appropriate unit and format for display.

                Args:
                    freq_hz: Frequency value in Hz (can be string or float)

                Returns:
                    Formatted string with value and unit (e.g., "2.5 GHz")
                """
                try:
                    # Convert to float if it's a string
                    freq_value = float(freq_hz)

                    # Determine the best unit based on magnitude
                    if freq_value >= 1e9:
                        converted = freq_value / 1e9
                        unit = 'GHz'
                    elif freq_value >= 1e6:
                        converted = freq_value / 1e6
                        unit = 'MHz'
                    elif freq_value >= 1e3:
                        converted = freq_value / 1e3
                        unit = 'kHz'
                    else:
                        converted = freq_value
                        unit = 'Hz'

                    # Format the number (remove unnecessary decimal places)
                    if converted >= 100:
                        formatted = f"{converted:.2f}"
                    elif converted >= 10:
                        formatted = f"{converted:.3f}"
                    else:
                        formatted = f"{converted:.4f}"

                    return f"{formatted} {unit}"

                except (ValueError, TypeError):
                    return "N/A"

            if hasattr(self, 'bnc845rf_current_frequency_reading_label'):
                try:
                    freq = bnc_cmd.get_frequency(instrument).strip()
                    freq = format_frequency_with_unit(freq)
                    self.bnc845rf_current_frequency_reading_label.setText(freq)
                except:
                    pass

            # Update current power reading
            if hasattr(self, 'bnc845rf_current_power_reading_label'):
                try:
                    power = bnc_cmd.get_power(instrument).strip()
                    self.bnc845rf_current_power_reading_label.setText(f"{float(power):.2f} dBm")
                except:
                    pass

            # Update RF state
            if hasattr(self, 'bnc845rf_state_reading_label'):
                try:
                    state = bnc_cmd.get_output(instrument).strip()
                    if str(state) == 0:
                        state = "OFF"
                    else:
                        state = 'ON'
                    self.bnc845rf_state_reading_label.setText(state)
                except:
                    pass

            # Update modulation type
            if hasattr(self, 'bnc845rf_modulation_reading_label'):
                try:
                    # Check which modulation is active
                    am_state = bnc_cmd.get_am_state(instrument).strip()
                    fm_state = bnc_cmd.get_fm_state(instrument).strip()
                    pm_state = bnc_cmd.get_pm_state(instrument).strip()
                    pulse_state = bnc_cmd.get_pulse_state(instrument).strip()

                    if am_state == '1' or am_state.upper() == 'ON':
                        self.bnc845rf_modulation_reading_label.setText('AM')
                    elif fm_state == '1' or fm_state.upper() == 'ON':
                        self.bnc845rf_modulation_reading_label.setText('FM')
                    elif pm_state == '1' or pm_state.upper() == 'ON':
                        self.bnc845rf_modulation_reading_label.setText('PM')
                    elif pulse_state == '1' or pulse_state.upper() == 'ON':
                        self.bnc845rf_modulation_reading_label.setText('PULSE')
                    else:
                        self.bnc845rf_modulation_reading_label.setText('OFF')
                except:
                    pass

            # Update modulation depth (for AM)
            # if hasattr(self, 'bnc845rf_modulation_depth_reading_label'):
            #     try:
            #         depth = bnc_cmd.get_am_depth(instrument).strip()
            #         # Convert to percentage
            #         depth_val = float(depth) * 100
            #         self.bnc845rf_modulation_depth_reading_label.setText(f"{depth_val:.1f}%")
            #     except:
            #         pass
            #
            # # Update modulation frequency (for AM)
            # if hasattr(self, 'bnc845rf_modulation_frequency_reading_label'):
            #     try:
            #         freq = bnc_cmd.get_am_internal_frequency(instrument).strip()
            #         self.bnc845rf_modulation_frequency_reading_label.setText(freq)
            #     except:
            #         pass

            # Update modulation state
            if hasattr(self, 'bnc845rf_modulation_state_reading_label'):
                try:
                    am_state = bnc_cmd.get_am_state(instrument).strip()
                    if am_state == '1' or am_state.upper() == 'ON':
                        self.bnc845rf_modulation_state_reading_label.setText('ON')
                    else:
                        self.bnc845rf_modulation_state_reading_label.setText('OFF')
                except:
                    pass

        except Exception as e:
            print(f"Error updating UI from instrument: {str(e)}")

    # Update current frequency reading
    def format_frequency_with_unit(self, freq_hz):
        """
        Convert frequency in Hz to the most appropriate unit and format for display.

        Args:
            freq_hz: Frequency value in Hz (can be string or float)

        Returns:
            Formatted string with value and unit (e.g., "2.5 GHz")
        """
        try:
            # Convert to float if it's a string
            freq_value = float(freq_hz)

            # Determine the best unit based on magnitude
            if freq_value >= 1e9:
                converted = freq_value / 1e9
                unit = 'GHz'
            elif freq_value >= 1e6:
                converted = freq_value / 1e6
                unit = 'MHz'
            elif freq_value >= 1e3:
                converted = freq_value / 1e3
                unit = 'kHz'
            else:
                converted = freq_value
                unit = 'Hz'

            # Format the number (remove unnecessary decimal places)
            if converted >= 100:
                formatted = f"{converted:.2f}"
            elif converted >= 10:
                formatted = f"{converted:.3f}"
            else:
                formatted = f"{converted:.4f}"

            return f"{formatted} {unit}"

        except (ValueError, TypeError):
            return "N/A"

    def _update_frequency_from_instrument(self, instrument, bnc_cmd):
        """
        Update all UI labels with current readings from the BNC845RF instrument.

        Args:
            instrument: VISA instrument object
            bnc_cmd: BNC_845M_COMMAND instance
        """
        try:


            if hasattr(self, 'bnc845rf_current_frequency_reading_label'):
                try:
                    freq = bnc_cmd.get_frequency_cw(instrument).strip()
                    freq = self.format_frequency_with_unit(freq)
                    self.bnc845rf_current_frequency_reading_label.setText(freq)
                except:
                    pass
        except Exception as e:
            print(f"Error updating UI from instrument: {str(e)}")

    def update_power_from_instrument(self, instrument, bnc_cmd):
        try:
            # Update current power reading
            if hasattr(self, 'bnc845rf_current_power_reading_label'):
                try:
                    power = bnc_cmd.get_power_level(instrument).strip()
                    self.bnc845rf_current_power_reading_label.setText(f"{float(power):.2f} dBm")
                except:
                    pass
        except Exception as e:
            print(f"Error updating UI from instrument: {str(e)}")

    def update_state_from_instrument(self, instrument, bnc_cmd):
        try:
            # Update RF state
            if hasattr(self, 'bnc845rf_state_reading_label'):
                try:
                    state = bnc_cmd.get_output_state(instrument).strip()
                    self.bnc845rf_state_reading_label.setText(state)
                except:
                    pass
        except Exception as e:
            print(f"Error updating UI from instrument: {str(e)}")

    def _generate_frequency_list(self, from_val, to_val, step_val, unit, step_unit):
        """
        Generate a list of frequencies from start to end with given step.
        Returns list in base unit (Hz).
        """
        try:
            start = float(from_val)
            end = float(to_val)
            step = float(step_val)

            # Convert to Hz based on unit
            unit_multiplier = {
                'Hz': 1,
                'kHz': 1e3,
                'MHz': 1e6,
                'GHz': 1e9
            }

            multiplier = unit_multiplier.get(unit, 1)
            step_multiplier = unit_multiplier.get(step_unit, 1)

            start_hz = start * multiplier
            end_hz = end * multiplier
            step_hz = step * step_multiplier

            # Generate list
            frequency_list = []
            current = start_hz
            while current <= end_hz:
                frequency_list.append(current)
                current += step_hz

            return frequency_list

        except (ValueError, TypeError):
            return []

    def _generate_power_list(self, from_val, to_val, step_val):
        """
        Generate a list of power values from start to end with given step.
        Returns list in dBm.
        """
        try:
            start = float(from_val)
            end = float(to_val)
            step = float(step_val)

            # Generate list
            power_list = []
            current = start
            while current <= end:
                power_list.append(current)
                current += step

            return power_list

        except (ValueError, TypeError):
            return []

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

    def fmr_measurement_status_ui(self):
        fmr_measurement_status_layout = QVBoxLayout()

        fmr_measurement_status_repetition_layout = QHBoxLayout()
        fmr_measurement_status_repetition_label = QLabel('Number of Repetition:')
        fmr_measurement_status_repetition_label.setFont(self.font)
        fmr_measurement_status_repetition_reading_label = QLabel('NA')
        fmr_measurement_status_repetition_reading_label.setFont(self.font)
        fmr_measurement_status_repetition_layout.addWidget(fmr_measurement_status_repetition_label)
        fmr_measurement_status_repetition_layout.addWidget(fmr_measurement_status_repetition_reading_label)

        fmr_measurement_status_time_remaining_layout = QHBoxLayout()
        fmr_measurement_status_time_remaining_label = QLabel('Estimated Time Remaining')
        fmr_measurement_status_time_remaining_label.setFont(self.font)
        fmr_measurement_status_time_remaining_layout.addWidget(fmr_measurement_status_time_remaining_label)

        fmr_measurement_status_time_remaining_in_days_layout = QHBoxLayout()
        fmr_measurement_status_time_remaining_in_days_label = QLabel('In Days:')
        fmr_measurement_status_time_remaining_in_days_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_days_reading_label = QLabel('NA')
        fmr_measurement_status_time_remaining_in_days_reading_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_days_layout.addWidget(fmr_measurement_status_time_remaining_in_days_label)
        fmr_measurement_status_time_remaining_in_days_layout.addWidget(fmr_measurement_status_time_remaining_in_days_reading_label)

        fmr_measurement_status_time_remaining_in_hours_layout = QHBoxLayout()
        fmr_measurement_status_time_remaining_in_hours_label = QLabel('In Hours:')
        fmr_measurement_status_time_remaining_in_hours_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_hours_reading_label = QLabel('NA')
        fmr_measurement_status_time_remaining_in_hours_reading_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_hours_layout.addWidget(
            fmr_measurement_status_time_remaining_in_hours_label)
        fmr_measurement_status_time_remaining_in_hours_layout.addWidget(
            fmr_measurement_status_time_remaining_in_hours_reading_label)

        fmr_measurement_status_time_remaining_in_mins_layout = QHBoxLayout()
        fmr_measurement_status_time_remaining_in_mins_label = QLabel('In Minutes:')
        fmr_measurement_status_time_remaining_in_mins_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_mins_reading_label = QLabel('NA')
        fmr_measurement_status_time_remaining_in_mins_reading_label.setFont(self.font)
        fmr_measurement_status_time_remaining_in_mins_layout.addWidget(
            fmr_measurement_status_time_remaining_in_mins_label)
        fmr_measurement_status_time_remaining_in_mins_layout.addWidget(
            fmr_measurement_status_time_remaining_in_mins_reading_label)

        fmr_measurement_status_cur_percent_layout = QHBoxLayout()
        fmr_measurement_status_cur_percent_label = QLabel('Current Percentage:')
        fmr_measurement_status_cur_percent_label.setFont(self.font)
        fmr_measurement_status_cur_percent_reading_label = QLabel('NA')
        fmr_measurement_status_cur_percent_reading_label.setFont(self.font)
        fmr_measurement_status_cur_percent_layout.addWidget(
            fmr_measurement_status_cur_percent_label)
        fmr_measurement_status_cur_percent_layout.addWidget(
            fmr_measurement_status_cur_percent_reading_label)

        fmr_measurement_status_layout.addLayout(fmr_measurement_status_repetition_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_time_remaining_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_time_remaining_in_days_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_time_remaining_in_hours_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_time_remaining_in_mins_layout)
        fmr_measurement_status_layout.addLayout(fmr_measurement_status_cur_percent_layout)
        return (fmr_measurement_status_layout,
                fmr_measurement_status_repetition_reading_label,
                fmr_measurement_status_time_remaining_in_days_reading_label,
                fmr_measurement_status_time_remaining_in_hours_reading_label,
                fmr_measurement_status_time_remaining_in_mins_reading_label,
                fmr_measurement_status_cur_percent_reading_label)

    def st_fmr_setting_ui(self):
        fmr_setting_layout = QVBoxLayout()

        fmr_setting_average_layout = QHBoxLayout()
        fmr_setting_repetition_label = QLabel('Number of Repetitions:')
        fmr_setting_repetition_label.setToolTip('This setting for how many repetitions should be.')
        fmr_setting_repetition_label.setFont(self.font)
        fmr_setting_average_line_edit = QLineEdit('1')
        fmr_setting_average_line_edit.setFont(self.font)
        fmr_setting_average_layout.addWidget(fmr_setting_repetition_label)
        fmr_setting_average_layout.addStretch(1)
        fmr_setting_average_layout.addWidget(fmr_setting_average_line_edit)
        fmr_setting_layout.addLayout(fmr_setting_average_layout)

        fmr_setting_init_temp_rate_layout = QHBoxLayout()
        fmr_setting_init_temp_rate_label = QLabel('Temperature Ramping Rate (K/min):')
        fmr_setting_init_temp_rate_label.setFont(self.font)
        fmr_setting_init_temp_rate_line_edit = QLineEdit('50')
        fmr_setting_init_temp_rate_line_edit.setFont(self.font)
        fmr_setting_init_temp_rate_layout.addWidget(fmr_setting_init_temp_rate_label)
        fmr_setting_init_temp_rate_layout.addStretch(1)
        fmr_setting_init_temp_rate_layout.addWidget(fmr_setting_init_temp_rate_line_edit)
        fmr_setting_layout.addLayout(fmr_setting_init_temp_rate_layout)

        return (fmr_setting_layout,
                fmr_setting_average_line_edit,
                fmr_setting_init_temp_rate_line_edit)

    def validate_and_get_all_settings(self):
        """
        Validate that all required fields are filled and return all settings.
        Returns a tuple: (is_valid, settings_dict, error_messages)
        """
        errors = []
        settings = {}

        try:
            # 1. Check Loop Type Selection
            loop_index = self.bnc845rf_loop_setting_combo.currentIndex()
            if loop_index == 0:  # "Select Loop"
                errors.append("Please select an experiment loop type")
                return False, {}, errors

            settings['loop_type'] = self.bnc845rf_loop_setting_combo.currentText()

            # 2. Validate Frequency Settings (for loop types 1 and 3)
            if loop_index in [1, 3]:  # Frequency Dependent or Both
                freq_valid, freq_data, freq_errors = self._validate_frequency_settings()
                if not freq_valid:
                    errors.extend(freq_errors)
                else:
                    settings['frequency_settings'] = freq_data

            # 3. Validate Power Settings (for loop types 2 and 3)
            if loop_index in [2, 3]:  # Power Dependent or Both
                power_valid, power_data, power_errors = self._validate_power_settings()
                if not power_valid:
                    errors.extend(power_errors)
                else:
                    settings['power_settings'] = power_data

            # 4. Validate Fixed Power (for loop type 1)
            if loop_index == 1:  # Frequency Dependent
                power_valid, power_value, power_error = self._validate_fixed_power()
                if not power_valid:
                    errors.append(power_error)
                else:
                    settings['power_settings'] = power_value

            # 5. Validate Fixed Frequency (for loop type 2)
            if loop_index == 2:  # Power Dependent
                freq_valid, freq_value, freq_error = self._validate_fixed_frequency()
                if not freq_valid:
                    errors.append(freq_error)
                else:
                    settings['frequency_settings'] = freq_value

            # 6. Validate Modulation Settings
            mod_valid, mod_data, mod_errors = self._validate_modulation_settings()
            if not mod_valid:
                errors.extend(mod_errors)
            else:
                settings['modulation_settings'] = mod_data

            # Determine if all validations passed
            is_valid = len(errors) == 0
            # settings = self.get_bnc845rf_settings()

            return is_valid, settings, errors

        except Exception as e:
            import traceback
            tb_str = traceback.format_exc()
            errors.append(f"Validation error: {str(e)}")
            print(f"Validation exception: {tb_str}")
            return False, {}, errors

    def _validate_frequency_settings(self):
        """Validate frequency zone settings"""
        errors = []
        freq_data = {}

        try:
            # Check if any frequency zone is selected
            if not any([
                getattr(self, 'bnc845rf_frequency_zone_1', False),
                getattr(self, 'bnc845rf_frequency_zone_2', False),
                getattr(self, 'bnc845rf_frequency_zone_3', False),
                getattr(self, 'bnc845rf_frequency_zone_customized', False)
            ]):
                errors.append("Please select a frequency zone configuration")
                return False, {}, errors

            # Validate Zone 1 (always present if any zone is selected)
            if self.bnc845rf_frequency_zone_1:
                zone1_valid, zone1_data, zone1_errors = self._validate_frequency_zone_one()
                if not zone1_valid:
                    errors.extend(zone1_errors)
                else:
                    freq_data['Final_list'] = zone1_data['frequency_list']
                    freq_data['zone_1'] = zone1_data


            # Validate Zone 2
            if self.bnc845rf_frequency_zone_2:
                zone1_valid, zone1_data, zone1_errors = self._validate_frequency_zone_one()
                zone2_valid, zone2_data, zone2_errors = self._validate_frequency_zone_two()
                if not zone1_valid or not zone2_valid:
                    errors.extend(zone1_errors)
                    errors.extend(zone2_errors)
                else:
                    frequency_list = zone1_data['frequency_list'] + zone2_data['frequency_list']
                    final_list = list(dict.fromkeys(frequency_list))
                    freq_data['Final_list'] = final_list
                    freq_data['zone_1'] = zone1_data
                    freq_data['zone_2'] = zone2_data

            # Validate Zone 3
            if self.bnc845rf_frequency_zone_3:
                zone1_valid, zone1_data, zone1_errors = self._validate_frequency_zone_one()
                zone2_valid, zone2_data, zone2_errors = self._validate_frequency_zone_two()
                zone3_valid, zone3_data, zone3_errors = self._validate_frequency_zone_three()
                if not zone1_valid or not zone2_valid or not zone3_valid:
                    errors.extend(zone1_errors)
                    errors.extend(zone2_errors)
                    errors.extend(zone3_errors)
                else:
                    frequency_list = zone1_data['frequency_list'] + zone2_data['frequency_list'] + zone3_data['frequency_list']
                    final_list = list(dict.fromkeys(frequency_list))
                    freq_data['Final_list'] = final_list
                    freq_data['zone_1'] = zone1_data
                    freq_data['zone_2'] = zone2_data
                    freq_data['zone_3'] = zone3_data

            # Validate Customized
            if self.bnc845rf_frequency_zone_customized:
                custom_valid, custom_data, custom_errors = self._validate_frequency_zone_customized()
                if not custom_valid:
                    errors.extend(custom_errors)
                else:
                    freq_data['Final_list'] = custom_data['frequency_list']
                    freq_data['customized'] = custom_data

            is_valid = len(errors) == 0
            return is_valid, freq_data, errors

        except Exception as e:
            errors.append(f"Frequency validation error: {str(e)}")
            return False, {}, errors

    def _validate_frequency_zone_one(self):
        """Validate frequency zone 1 fields"""
        errors = []
        zone_data = {}

        try:
            # Check if fields exist
            if not hasattr(self, 'bnc845rf_frequency_zone_one_freq_from_entry'):
                errors.append("Zone 1: Frequency fields not initialized")
                return False, {}, errors

            # Get values
            from_val = self.bnc845rf_frequency_zone_one_freq_from_entry.text().strip()
            to_val = self.bnc845rf_frequency_zone_one_freq_to_entry.text().strip()
            step_val = self.bnc845rf_frequency_zone_one_freq_step_entry.text().strip()
            unit = self.bnc845rf_frequency_zone_one_freq_unit_combo.currentText()
            step_unit = self.bnc845rf_frequency_zone_one_freq_step_unit_combo.currentText()

            # Check if empty
            if not from_val:
                errors.append("Zone 1: 'From' frequency is empty")
            if not to_val:
                errors.append("Zone 1: 'To' frequency is empty")
            if not step_val:
                errors.append("Zone 1: 'Step' size is empty")
            if unit == "Select Unit":
                errors.append("Zone 1: Please select frequency unit")
            if step_unit == "Select Unit":
                errors.append("Zone 1: Please select step frequency unit")



            # Validate numeric values
            try:
                from_num = float(from_val) if from_val else 0
                to_num = float(to_val) if to_val else 0
                step_num = float(step_val) if step_val else 0

                if from_num < 0:
                    errors.append("Zone 1: 'From' frequency must be positive")
                if to_num < 0:
                    errors.append("Zone 1: 'To' frequency must be positive")
                if step_num <= 0:
                    errors.append("Zone 1: 'Step' size must be greater than zero")
                if from_num >= to_num:
                    errors.append("Zone 1: 'From' frequency must be less than 'To' frequency")

                # Store validated data
                if len(errors) == 0:
                    zone_data = {
                        'from': from_num,
                        'to': to_num,
                        'step': step_num,
                        'unit': unit,
                        'frequency_list': self._generate_frequency_list(from_val, to_val, step_val, unit, step_unit)
                    }

            except ValueError:
                errors.append("Zone 1: Invalid numeric values")

            is_valid = len(errors) == 0
            return is_valid, zone_data, errors

        except Exception as e:
            errors.append(f"Zone 1 validation error: {str(e)}")
            return False, {}, errors

    def _validate_frequency_zone_two(self):
        """Validate frequency zone 2 fields"""
        errors = []
        zone_data = {}

        try:
            if not hasattr(self, 'bnc845rf_frequency_zone_two_freq_from_entry'):
                errors.append("Zone 2: Frequency fields not initialized")
                return False, {}, errors

            from_val = self.bnc845rf_frequency_zone_two_freq_from_entry.text().strip()
            to_val = self.bnc845rf_frequency_zone_two_freq_to_entry.text().strip()
            step_val = self.bnc845rf_frequency_zone_two_freq_step_entry.text().strip()
            unit = self.bnc845rf_frequency_zone_two_freq_unit_combo.currentText()
            step_unit = self.bnc845rf_frequency_zone_two_freq_step_unit_combo.currentText()

            if not from_val:
                errors.append("Zone 2: 'From' frequency is empty")
            if not to_val:
                errors.append("Zone 2: 'To' frequency is empty")
            if not step_val:
                errors.append("Zone 2: 'Step' size is empty")
            if unit == "Select Unit":
                errors.append("Zone 2: Please select frequency unit")
            if step_unit == "Select Unit":
                errors.append("Zone 2: Please select step frequency unit")

            try:
                from_num = float(from_val) if from_val else 0
                to_num = float(to_val) if to_val else 0
                step_num = float(step_val) if step_val else 0

                if from_num < 0:
                    errors.append("Zone 2: 'From' frequency must be positive")
                if to_num < 0:
                    errors.append("Zone 2: 'To' frequency must be positive")
                if step_num <= 0:
                    errors.append("Zone 2: 'Step' size must be greater than zero")
                if from_num >= to_num:
                    errors.append("Zone 2: 'From' frequency must be less than 'To' frequency")

                if len(errors) == 0:
                    zone_data = {
                        'from': from_num,
                        'to': to_num,
                        'step': step_num,
                        'unit': unit,
                        'frequency_list': self._generate_frequency_list(from_val, to_val, step_val, unit, step_unit)
                    }

            except ValueError:
                errors.append("Zone 2: Invalid numeric values")

            is_valid = len(errors) == 0
            return is_valid, zone_data, errors

        except Exception as e:
            errors.append(f"Zone 2 validation error: {str(e)}")
            return False, {}, errors

    def _validate_frequency_zone_three(self):
        """Validate frequency zone 3 fields"""
        errors = []
        zone_data = {}

        try:
            if not hasattr(self, 'bnc845rf_frequency_zone_three_freq_from_entry'):
                errors.append("Zone 3: Frequency fields not initialized")
                return False, {}, errors

            from_val = self.bnc845rf_frequency_zone_three_freq_from_entry.text().strip()
            to_val = self.bnc845rf_frequency_zone_three_freq_to_entry.text().strip()
            step_val = self.bnc845rf_frequency_zone_three_freq_step_entry.text().strip()
            unit = self.bnc845rf_frequency_zone_three_freq_unit_combo.currentText()
            step_unit = self.bnc845rf_frequency_zone_three_freq_step_unit_combo.currentText()

            if not from_val:
                errors.append("Zone 3: 'From' frequency is empty")
            if not to_val:
                errors.append("Zone 3: 'To' frequency is empty")
            if not step_val:
                errors.append("Zone 3: 'Step' size is empty")
            if unit == "Select Unit":
                errors.append("Zone 3: Please select frequency unit")
            if step_unit == "Select Unit":
                errors.append("Zone 3: Please select step frequency unit")

            try:
                from_num = float(from_val) if from_val else 0
                to_num = float(to_val) if to_val else 0
                step_num = float(step_val) if step_val else 0

                if from_num < 0:
                    errors.append("Zone 3: 'From' frequency must be positive")
                if to_num < 0:
                    errors.append("Zone 3: 'To' frequency must be positive")
                if step_num <= 0:
                    errors.append("Zone 3: 'Step' size must be greater than zero")
                if from_num >= to_num:
                    errors.append("Zone 3: 'From' frequency must be less than 'To' frequency")

                if len(errors) == 0:
                    zone_data = {
                        'from': from_num,
                        'to': to_num,
                        'step': step_num,
                        'unit': unit,
                        'frequency_list': self._generate_frequency_list(from_val, to_val, step_val, unit, step_unit)
                    }

            except ValueError:
                errors.append("Zone 3: Invalid numeric values")

            is_valid = len(errors) == 0
            return is_valid, zone_data, errors

        except Exception as e:
            errors.append(f"Zone 3 validation error: {str(e)}")
            return False, {}, errors

    def _validate_frequency_zone_customized(self):
        """Validate customized frequency zone"""
        errors = []
        zone_data = {}

        try:
            if not hasattr(self, 'bnc845rf_frequency_zone_customized_entry'):
                errors.append("Customized: Frequency field not initialized")
                return False, {}, errors

            freq_list_str = self.bnc845rf_frequency_zone_customized_entry.text().strip()
            unit = self.bnc845rf_frequency_zone_customized_unit_combo.currentText()

            if not freq_list_str:
                errors.append("Customized: Frequency list is empty")
            if unit == "Select Unit":
                errors.append("Customized: Please select frequency unit")

            freq_list = self._parse_custom_list(freq_list_str)
            unit_multiplier = {
                'Hz': 1,
                'kHz': 1e3,
                'MHz': 1e6,
                'GHz': 1e9
            }

            multiplier = unit_multiplier.get(unit, 1)
            freq_list = [freq * multiplier for freq in freq_list]

            if len(freq_list) == 0:
                errors.append("Customized: Invalid frequency list format (use comma-separated values)")
            else:
                # Check for negative values
                if any(f < 0 for f in freq_list):
                    errors.append("Customized: All frequencies must be positive")

            if len(errors) == 0:
                zone_data = {
                    'raw_input': freq_list_str,
                    'unit': unit,
                    'frequency_list': freq_list
                }

            is_valid = len(errors) == 0
            return is_valid, zone_data, errors

        except Exception as e:
            errors.append(f"Customized validation error: {str(e)}")
            return False, {}, errors

    def _validate_power_settings(self):
        """Validate power zone settings"""
        errors = []
        power_data = {}

        try:
            # Check if any power zone is selected
            if not any([
                getattr(self, 'bnc845rf_power_zone_1', False),
                getattr(self, 'bnc845rf_power_zone_customized', False)
            ]):
                errors.append("Please select a power zone configuration")
                return False, {}, errors

            # Validate Zone 1
            if self.bnc845rf_power_zone_1:
                zone1_valid, zone1_data, zone1_errors = self._validate_power_zone_one()
                if not zone1_valid:
                    errors.extend(zone1_errors)
                else:
                    power_data['Final_list'] = zone1_data['power_list']
                    power_data['zone_1'] = zone1_data

            # Validate Customized
            if self.bnc845rf_power_zone_customized:
                custom_valid, custom_data, custom_errors = self._validate_power_zone_customized()
                if not custom_valid:
                    errors.extend(custom_errors)
                else:
                    power_data['Final_list'] = custom_data['power_list']
                    power_data['customized'] = custom_data

            is_valid = len(errors) == 0
            return is_valid, power_data, errors

        except Exception as e:
            errors.append(f"Power validation error: {str(e)}")
            return False, {}, errors

    def _validate_power_zone_one(self):
        """Validate power zone 1 fields"""
        errors = []
        zone_data = {}

        try:
            if not hasattr(self, 'bnc845rf_power_zone_one_power_from_entry'):
                errors.append("Power Zone 1: Fields not initialized")
                return False, {}, errors

            from_val = self.bnc845rf_power_zone_one_power_from_entry.text().strip()
            to_val = self.bnc845rf_power_zone_one_power_to_entry.text().strip()
            step_val = self.bnc845rf_power_zone_one_power_step_entry.text().strip()

            if not from_val:
                errors.append("Power Zone 1: 'From' power is empty")
            if not to_val:
                errors.append("Power Zone 1: 'To' power is empty")
            if not step_val:
                errors.append("Power Zone 1: 'Step' size is empty")

            try:
                from_num = float(from_val) if from_val else 0
                to_num = float(to_val) if to_val else 0
                step_num = float(step_val) if step_val else 0

                if step_num <= 0:
                    errors.append("Power Zone 1: 'Step' size must be greater than zero")
                if from_num >= to_num:
                    errors.append("Power Zone 1: 'From' power must be less than 'To' power")

                if len(errors) == 0:
                    zone_data = {
                        'from': from_num,
                        'to': to_num,
                        'step': step_num,
                        'unit': 'dBm',
                        'power_list': self._generate_power_list(from_val, to_val, step_val)
                    }

            except ValueError:
                errors.append("Power Zone 1: Invalid numeric values")

            is_valid = len(errors) == 0
            return is_valid, zone_data, errors

        except Exception as e:
            errors.append(f"Power Zone 1 validation error: {str(e)}")
            return False, {}, errors

    def _validate_power_zone_customized(self):
        """Validate customized power zone"""
        errors = []
        zone_data = {}

        try:
            if not hasattr(self, 'bnc845rf_power_zone_customized_entry'):
                errors.append("Customized Power: Field not initialized")
                return False, {}, errors

            if not hasattr(self, 'bnc845rf_frequency_zone_customized_unit_combo'):
                errors.append("Customized Power: Field not initialized")
                return False, {}, errors

            power_list_str = self.bnc845rf_power_zone_customized_entry.text().strip()

            if not power_list_str:
                errors.append("Customized Power: Power list is empty")

            power_list = self._parse_custom_list(power_list_str)

            if len(power_list) == 0:
                errors.append("Customized Power: Invalid power list format (use comma-separated values)")

            if len(errors) == 0:
                zone_data = {
                    'raw_input': power_list_str,
                    'unit': 'dBm',
                    'power_list': power_list
                }

            is_valid = len(errors) == 0
            return is_valid, zone_data, errors

        except Exception as e:
            errors.append(f"Customized Power validation error: {str(e)}")
            return False, {}, errors

    def _validate_fixed_power(self):
        """Validate fixed power field"""
        try:
            if not hasattr(self, 'bnc845rf_power_setting_entry'):
                return False, None, "Fixed power field not initialized"

            power_str = self.bnc845rf_power_setting_entry.text().strip()

            if not power_str:
                return False, None, "Fixed power value is empty"

            try:
                power_val = float(power_str)
                return True, {'Final_list': [power_val], 'unit': 'dBm'}, ""
            except ValueError:
                return False, None, "Fixed power: Invalid numeric value"

        except Exception as e:
            return False, None, f"Fixed power validation error: {str(e)}"

    def _validate_fixed_frequency(self):
        """Validate fixed frequency field"""
        try:
            if not hasattr(self, 'bnc845rf_frequency_setting_entry'):
                return False, None, "Fixed frequency field not initialized"
            if not hasattr(self, 'bnc845rf_frequency_setting_unit_combo'):
                return False, None, "Fixed frequency unit not initialized"

            freq_str = self.bnc845rf_frequency_setting_entry.text().strip()
            unit = self.bnc845rf_frequency_setting_unit_combo.currentText()

            if unit == "Select Unit":
                return False, None, "Zone 3: Please select step frequency unit"

            if not freq_str:
                return False, None, "Fixed frequency value is empty"

            try:
                freq_val = float(freq_str)
                if freq_val < 0:
                    return False, None, "Fixed frequency must be positive"
                return True, {'Final_list': [freq_val], 'unit': 'Hz'}, ""
            except ValueError:
                return False, None, "Fixed frequency: Invalid numeric value"

        except Exception as e:
            return False, None, f"Fixed frequency validation error: {str(e)}"

    def _validate_modulation_settings(self):
        """Validate modulation settings"""
        errors = []
        mod_data = {}

        try:
            mod_index = self.bnc845rf_modulation_combo.currentIndex()

            if mod_index == 0:  # "Select Modulation"
                # Modulation is optional, so this is not an error
                mod_data['type'] = 'None'
                return True, mod_data, []

            mod_data['type'] = self.bnc845rf_modulation_combo.currentText()

            # Validate Pulse Modulation (index 1)
            if mod_index == 1:
                mod_data['pulse'] = {'enabled': True}

            # Validate Amplitude Modulation (index 2)
            elif mod_index == 2:
                if hasattr(self, 'bnc845rf_am_freq_entry'):
                    freq_str = self.bnc845rf_am_freq_entry.text().strip()
                    if not freq_str:
                        errors.append("AM: Modulation frequency is empty")
                    else:
                        try:
                            freq_val = float(freq_str)
                            if freq_val <= 0:
                                errors.append("AM: Modulation frequency must be positive")
                            else:
                                mod_data['am_frequency'] = freq_val
                                mod_data['am_frequency_unit'] = 'Hz'
                        except ValueError:
                            errors.append("AM: Invalid modulation frequency")

                if hasattr(self, 'bnc845rf_am_depth_entry'):
                    depth_str = self.bnc845rf_am_depth_entry.text().strip()
                    if not depth_str:
                        errors.append("AM: Modulation depth is empty")
                    else:
                        try:
                            depth_val = float(depth_str)
                            if depth_val < 0 or depth_val > 100:
                                errors.append("AM: Modulation depth must be between 0 and 100%")
                            else:
                                mod_data['am_depth'] = depth_val
                                mod_data['am_depth_unit'] = '%'
                        except ValueError:
                            errors.append("AM: Invalid modulation depth")

                if hasattr(self, 'bnc845rf_am_source_combo'):
                    source = self.bnc845rf_am_source_combo.currentText()
                    mod_data['am_source'] = source

            # Validate Frequency Modulation (index 3)
            elif mod_index == 3:
                mod_data['fm'] = {'enabled': True}
                # Add FM-specific validation when UI is implemented

            # Validate Phase Modulation (index 4)
            elif mod_index == 4:
                mod_data['pm'] = {'enabled': True}
                # Add PM-specific validation when UI is implemented

            is_valid = len(errors) == 0
            return is_valid, mod_data, errors

        except Exception as e:
            errors.append(f"Modulation validation error: {str(e)}")
            return False, {}, errors


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