from PyQt6.QtWidgets import QMessageBox
from typing import Tuple, List, Optional


class Keithley6221ConfigHandler:
    """Helper class to handle Keithley 6221 configuration parsing and validation"""

    # Unit conversion mapping
    UNIT_MAP = {
        0: None,  # "Select Units"
        1: ('e-3', 'mA'),  # milliamps
        2: ('e-6', 'µA'),  # microamps
        3: ('e-9', 'nA'),  # nanoamps
        4: ('e-12', 'pA')  # picoamps
    }

    # Waveform mapping
    WAVEFORM_MAP = {
        0: None,  # "Select Funcs"
        1: ('SIN', 'SIN'),
        2: ('SQU', 'SQUARE'),
        3: ('RAMP', 'RAMP'),
        4: ('ARB0', 'ARB(x)')
    }

    @staticmethod
    def parse_unit(unit_index: int, parent_widget=None, error_context: str = "") -> Tuple[Optional[str], Optional[str]]:
        """
        Parse unit index and return (scpi_unit, display_unit)

        Args:
            unit_index: Index from combo box (0-4)
            parent_widget: Parent widget for error dialogs
            error_context: Context string for error messages

        Returns:
            Tuple of (scpi_unit, display_unit) or (None, None) if invalid
        """
        if unit_index == 0:
            if parent_widget:
                QMessageBox.warning(
                    parent_widget,
                    "Missing Items",
                    f"Please select current unit{' - ' + error_context if error_context else ''}"
                )
            return None, None

        return Keithley6221ConfigHandler.UNIT_MAP.get(unit_index, (None, None))

    @staticmethod
    def parse_waveform(waveform_index: int, parent_widget=None) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse waveform index and return (scpi_waveform, display_name)

        Args:
            waveform_index: Index from combo box (0-4)
            parent_widget: Parent widget for error dialogs

        Returns:
            Tuple of (scpi_waveform, display_name) or (None, None) if invalid
        """
        if waveform_index == 0:
            if parent_widget:
                QMessageBox.warning(
                    parent_widget,
                    "Missing Items",
                    "Please select waveform function"
                )
            return None, None

        return Keithley6221ConfigHandler.WAVEFORM_MAP.get(waveform_index, (None, None))

    @staticmethod
    def parse_current_list(text_input: str) -> List[float]:
        """
        Parse comma-separated current values

        Args:
            text_input: String with comma-separated values

        Returns:
            List of float values
        """
        cleaned = text_input.replace(" ", "")
        return [float(item) for item in cleaned.split(',') if item]

    @staticmethod
    def generate_current_range(start: float, stop: float, step: float) -> List[float]:
        """
        Generate current range with proper floating point handling

        Args:
            start: Starting current
            stop: Stopping current (inclusive)
            step: Step size

        Returns:
            List of current values
        """
        # Use proper floating point range generation
        import numpy as np
        # Add small epsilon to ensure stop is included
        return np.arange(start, stop + step / 2, step).tolist()

    @staticmethod
    def format_current_scpi(value: float, scpi_unit: str) -> str:
        """
        Format current value for SCPI command

        Args:
            value: Current magnitude
            scpi_unit: SCPI unit suffix (e.g., 'e-3')

        Returns:
            Formatted string for SCPI (e.g., "1.5e-3")
        """
        return f"{value}{scpi_unit}"

    @staticmethod
    def format_currents_scpi(values: List[float], scpi_unit: str) -> List[str]:
        """
        Format list of current values for SCPI commands

        Args:
            values: List of current magnitudes
            scpi_unit: SCPI unit suffix

        Returns:
            List of formatted SCPI strings
        """
        return [f"{val}{scpi_unit}" for val in values]


class Keithley6221DCConfig:
    """Data class for DC current configuration"""

    def __init__(self):
        self.enabled = False
        self.is_range_mode = False
        self.currents_scpi = []  # SCPI formatted currents (e.g., ["1.5e-3", "2.0e-3"])
        self.currents_mag = []  # Magnitude only (e.g., ["1.5", "2.0"])
        self.unit_display = ""  # Display unit (e.g., "mA")
        self.unit_scpi = ""  # SCPI unit (e.g., "e-3")

    def __repr__(self):
        return (f"Keithley6221DCConfig(enabled={self.enabled}, "
                f"is_range={self.is_range_mode}, "
                f"unit={self.unit_display}, "
                f"points={len(self.currents_scpi)})")


class Keithley6221ACConfig:
    """Data class for AC current configuration"""

    def __init__(self):
        self.enabled = False
        self.is_range_mode = False
        self.currents_scpi = []  # SCPI formatted currents
        self.currents_mag = []  # Magnitude only
        self.unit_display = ""  # Display unit
        self.unit_scpi = ""  # SCPI unit
        self.waveform_scpi = ""  # SCPI waveform (e.g., "SIN")
        self.waveform_display = ""  # Display waveform name
        self.frequency = ""  # Frequency in Hz
        self.offset_scpi = ""  # SCPI formatted offset with unit
        self.offset_value = ""  # Offset magnitude
        self.offset_unit_display = ""  # Offset display unit
        self.phase_marker_enabled = False
        self.phase_marker_trigger_line = 0

    def __repr__(self):
        return (f"Keithley6221ACConfig(enabled={self.enabled}, "
                f"waveform={self.waveform_display}, "
                f"freq={self.frequency}Hz, "
                f"points={len(self.currents_scpi)})")