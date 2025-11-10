"""
Stanford Research Systems Model SR7265 DSP Lock-In Amplifier
Command Interface Class

This class provides a comprehensive interface for controlling the SR7265
DSP Lock-In Amplifier via RS-232 or GPIB commands.

Based on Model SR7265 Instruction Manual

Author: Command Interface Generator
Date: 2025
"""


class SR7265_COMMAND:
    """
    Command class for Stanford Research Systems SR7265 Lock-In Amplifier

    Supports remote control via:
    - RS-232 (9600, 19200, 38400 baud)
    - GPIB (IEEE-488)

    All commands follow SR7265 command syntax
    """

    def __init__(self):
        """Initialize the SR7265 command class with lookup tables"""
        self.name = "SRS Model SR7265 DSP Lock-In Amplifier"
        self.version = "1.0"

        # Time Constant Lookup Table
        self.time_constants = {
            0: "10 µs",
            1: "20 µs",
            2: "40 µs",
            3: "80 µs",
            4: "160 µs",
            5: "320 µs",
            6: "640 µs",
            7: "5 ms",
            8: "10 ms",
            9: "20 ms",
            10: "50 ms",
            11: "100 ms",
            12: "200 ms",
            13: "500 ms",
            14: "1 s",
            15: "2 s",
            16: "5 s",
            17: "10 s",
            18: "20 s",
            19: "50 s",
            20: "100 s",
            21: "200 s",
            22: "500 s",
            23: "1 ks",
            24: "2 ks",
            25: "5 ks",
            26: "10 ks",
            27: "20 ks",
            28: "50 ks",
            29: "100 ks"
        }

        # Sensitivity Lookup Table
        self.sensitivities_imode_0 = {
            1: "2 nV",
            2: "5 nV",
            3: "10 nV",
            4: "20 nV",
            5: "50 nV",
            6: "100 nV",
            7: "200 nV",
            8: "500 nV",
            9: "1 µV",
            10: "2 µV",
            11: "5 µV",
            12: "10 µV",
            13: "20 µV",
            14: "50 µV",
            15: "100 µV",
            16: "200 µV",
            17: "500 µV",
            18: "1 mV",
            19: "2 mV",
            20: "5 mV",
            21: "10 mV",
            22: "20 mV",
            23: "50 mV",
            24: "100 mV",
            25: "200 mV",
            26: "500 mV",
            27: "1 V"
        }

        self.sensitivities_imode_1 = {
            1: "2 fA",
            2: "5 fA",
            3: "10 fA",
            4: "20 fA",
            5: "50 fA",
            6: "100 fA",
            7: "200 fA",
            8: "500 fA",
            9: "1 pA",
            10: "2 pA",
            11: "5 pA",
            12: "10 pA",
            13: "20 pA",
            14: "50 pA",
            15: "100 pA",
            16: "200 pA",
            17: "500 pA",
            18: "1 nA",
            19: "2 nA",
            20: "5 nA",
            21: "10 nA",
            22: "20 nA",
            23: "50 nA",
            24: "100 nA",
            25: "200 nA",
            26: "500 nA",
            27: "1 µA"
        }

        self.sensitivities_imode_2 = {
            1: "n/a",
            2: "n/a",
            3: "n/a",
            4: "n/a",
            5: "n/a",
            6: "n/a",
            7: "2 fA",
            8: "5 fA",
            9: "10 fA",
            10: "20 fA",
            11: "50 fA",
            12: "100 fA",
            13: "200 fA",
            14: "500 fA",
            15: "1 pA",
            16: "2 pA",
            17: "5 pA",
            18: "10 pA",
            19: "20 pA",
            20: "50 pA",
            21: "100 pA",
            22: "200 pA",
            23: "500 pA",
            24: "1 nA",
            25: "2 nA",
            26: "5 nA",
            27: "10 nA"
        }

        # AC Gain Settings
        self.ac_gains = {
            0: "0 dB (x1)",
            1: "10 dB (x3.162)",
            2: "20 dB (x10)",
            3: "30 dB (x31.62)",
            4: "40 dB (x100)",
            5: "50 dB (x316.2)",
            6: "60 dB (x1000)",
            7: "70 dB (x3162)",
            8: "80 dB (x10000)",
            9: "90 dB (x31623)"
        }

        # Dynamic Reserve Settings
        self.dynamic_reserves = {
            0: "Low Noise (High Reserve)",
            1: "Normal",
            2: "Low Distortion (Low Reserve)"
        }

        # Input Configuration
        self.input_configs = {
            0: "A",
            1: "A-B",
            2: "I (1 MΩ)",
            3: "I (100 MΩ)"
        }

        # Input Coupling
        self.input_couplings = {
            0: "AC",
            1: "DC"
        }

        # Input Ground/Float
        self.input_grounds = {
            0: "Float",
            1: "Ground"
        }

        # Line Filter Settings
        self.line_filters = {
            0: "Off",
            1: "Line",
            2: "2 x Line",
            3: "Both"
        }

        # Reference Source
        self.reference_sources = {
            0: "Internal",
            1: "External"
        }

        # Reference Trigger Mode
        self.reference_triggers = {
            0: "Zero Crossing",
            1: "TTL Rising Edge",
            2: "TTL Falling Edge"
        }

        # Harmonic
        self.harmonics = {
            1: "1st Harmonic",
            2: "2nd Harmonic"
        }

        # Output Channel Assignments
        self.output_channels = {
            0: "Display",
            1: "X",
            2: "Y",
            3: "R",
            4: "Theta",
            5: "In 1",
            6: "In 2",
            7: "In 3",
            8: "In 4",
            9: "Xnoise",
            10: "Ynoise",
            11: "Out 1",
            12: "Out 2",
            13: "Theta (zero at DC)",
            14: "Output Offset 1",
            15: "Output Offset 2",
            16: "X"
        }

        # Slope Settings (Filter Slope)
        self.slopes = {
            0: "6 dB/oct",
            1: "12 dB/oct",
            2: "18 dB/oct",
            3: "24 dB/oct"
        }

        # Curve Buffer Status
        self.curve_status = {
            0: "No activity",
            1: "Starting measurement",
            2: "Running",
            3: "Complete",
            4: "Aborted"
        }

    # ========================================================================================
    # Signal Channel Commands
    # ========================================================================================

    def set_sensitivity(self, instrument, index: int):
        """
        Set AC gain (sensitivity)

        Args:
            instrument: VISA instrument object
            index: Sensitivity index (0-26)
                   Returns with description, e.g., index 0 is "2 nV"
        """
        if 0 <= index <= 26:
            description = self.sensitivities.get(index, f"Index {index}")
            instrument.write(f'SEN {index}')
            return f"Set sensitivity to index {index}: {description}"
        else:
            raise ValueError(f"Invalid sensitivity index. Must be 0-26. Index {index} is out of range.")

    def get_sensitivity(self, instrument) -> str:
        """Query AC gain (sensitivity) - Returns index and description"""
        response = instrument.query('SEN')
        try:
            index = int(response.strip())
            description = self.sensitivities.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_ac_gain(self, instrument, index: int):
        """
        Set AC gain

        Args:
            instrument: VISA instrument object
            index: AC gain index (0-9)
                   Returns with description, e.g., index 0 is "0 dB (x1)"
        """
        if 0 <= index <= 9:
            description = self.ac_gains.get(index, f"Index {index}")
            instrument.write(f'ACGAIN {index}')
            return f"Set AC gain to index {index}: {description}"
        else:
            raise ValueError(f"Invalid AC gain index. Must be 0-9. Index {index} is out of range.")

    def get_ac_gain(self, instrument) -> str:
        """Query AC gain - Returns index and description"""
        response = instrument.query('ACGAIN')
        try:
            index = int(response.strip())
            description = self.ac_gains.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_auto_sensitivity(self, instrument):
        """Automatically adjust sensitivity"""
        instrument.write('AS')

    def set_auto_measure(self, instrument):
        """Automatically set measurement parameters"""
        instrument.write('ASM')

    def set_auto_phase(self, instrument):
        """Automatically adjust reference phase"""
        instrument.write('AQN')

    def set_input_config(self, instrument, config: int):
        """
        Set input configuration

        Args:
            instrument: VISA instrument object
            config: Input configuration (0-3)
                    0: A
                    1: A-B
                    2: I (1 MΩ)
                    3: I (100 MΩ)
        """
        if 0 <= config <= 3:
            description = self.input_configs.get(config, f"Index {config}")
            instrument.write(f'VMODE {config}')
            return f"Set input config to index {config}: {description}"
        else:
            raise ValueError(f"Invalid input config. Must be 0-3.")

    def get_input_config(self, instrument) -> str:
        """Query input configuration - Returns index and description"""
        response = instrument.query('VMODE')
        try:
            index = int(response.strip())
            description = self.input_configs.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_input_coupling(self, instrument, coupling: int):
        """
        Set input coupling (AC/DC)

        Args:
            instrument: VISA instrument object
            coupling: 0 = AC, 1 = DC
        """
        if coupling in [0, 1]:
            description = self.input_couplings.get(coupling, f"Index {coupling}")
            instrument.write(f'CP {coupling}')
            return f"Set input coupling to index {coupling}: {description}"
        else:
            raise ValueError("Invalid coupling. Must be 0 (AC) or 1 (DC).")

    def get_input_coupling(self, instrument) -> str:
        """Query input coupling - Returns index and description"""
        response = instrument.query('CP')
        try:
            index = int(response.strip())
            description = self.input_couplings.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_input_ground(self, instrument, ground: int):
        """
        Set input shield ground/float

        Args:
            instrument: VISA instrument object
            ground: 0 = Float, 1 = Ground
        """
        if ground in [0, 1]:
            description = self.input_grounds.get(ground, f"Index {ground}")
            instrument.write(f'FLOAT {ground}')
            return f"Set input ground to index {ground}: {description}"
        else:
            raise ValueError("Invalid ground setting. Must be 0 (Float) or 1 (Ground).")

    def get_input_ground(self, instrument) -> str:
        """Query input shield ground/float - Returns index and description"""
        response = instrument.query('FLOAT')
        try:
            index = int(response.strip())
            description = self.input_grounds.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_line_filter(self, instrument, filter_index: int):
        """
        Set line frequency rejection filter

        Args:
            instrument: VISA instrument object
            filter_index: Line filter setting (0-3)
                          0: Off
                          1: Line
                          2: 2 x Line
                          3: Both
        """
        if 0 <= filter_index <= 3:
            description = self.line_filters.get(filter_index, f"Index {filter_index}")
            instrument.write(f'LF {filter_index}')
            return f"Set line filter to index {filter_index}: {description}"
        else:
            raise ValueError("Invalid line filter. Must be 0-3.")

    def get_line_filter(self, instrument) -> str:
        """Query line filter setting - Returns index and description"""
        response = instrument.query('LF')
        try:
            index = int(response.strip())
            description = self.line_filters.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_dynamic_reserve(self, instrument, reserve: int):
        """
        Set dynamic reserve

        Args:
            instrument: VISA instrument object
            reserve: Dynamic reserve (0-2)
                     0: Low Noise (High Reserve)
                     1: Normal
                     2: Low Distortion (Low Reserve)
        """
        if 0 <= reserve <= 2:
            description = self.dynamic_reserves.get(reserve, f"Index {reserve}")
            instrument.write(f'RESERVE {reserve}')
            return f"Set dynamic reserve to index {reserve}: {description}"
        else:
            raise ValueError("Invalid dynamic reserve. Must be 0-2.")

    def get_dynamic_reserve(self, instrument) -> str:
        """Query dynamic reserve - Returns index and description"""
        response = instrument.query('RESERVE')
        try:
            index = int(response.strip())
            description = self.dynamic_reserves.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    # ========================================================================================
    # Reference Channel Commands
    # ========================================================================================

    def set_reference_frequency(self, instrument, frequency: float):
        """
        Set internal oscillator frequency

        Args:
            instrument: VISA instrument object
            frequency: Frequency in Hz (0.001 Hz to 120 kHz)
        """
        if 0.001 <= frequency <= 120000:
            instrument.write(f'OF {frequency}')
            return f"Set reference frequency to {frequency} Hz"
        else:
            raise ValueError("Frequency must be between 0.001 Hz and 120 kHz")

    def get_reference_frequency(self, instrument) -> str:
        """Query internal oscillator frequency"""
        return instrument.query('OF.')

    def set_reference_phase(self, instrument, phase: float):
        """
        Set reference phase

        Args:
            instrument: VISA instrument object
            phase: Phase in degrees (0-360 or -180 to +180)
        """
        instrument.write(f'REFP {phase}')
        return f"Set reference phase to {phase}°"

    def get_reference_phase(self, instrument) -> str:
        """Query reference phase"""
        return instrument.query('REFP.')

    def set_reference_source(self, instrument, source: int):
        """
        Set reference source

        Args:
            instrument: VISA instrument object
            source: 0 = Internal, 1 = External
        """
        if source in [0, 1]:
            description = self.reference_sources.get(source, f"Index {source}")
            instrument.write(f'IE {source}')
            return f"Set reference source to index {source}: {description}"
        else:
            raise ValueError("Invalid reference source. Must be 0 (Internal) or 1 (External).")

    def get_reference_source(self, instrument) -> str:
        """Query reference source - Returns index and description"""
        response = instrument.query('IE')
        try:
            index = int(response.strip())
            description = self.reference_sources.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_reference_trigger(self, instrument, trigger: int):
        """
        Set reference trigger mode

        Args:
            instrument: VISA instrument object
            trigger: Trigger mode (0-2)
                     0: Zero Crossing
                     1: TTL Rising Edge
                     2: TTL Falling Edge
        """
        if 0 <= trigger <= 2:
            description = self.reference_triggers.get(trigger, f"Index {trigger}")
            instrument.write(f'REFMODE {trigger}')
            return f"Set reference trigger to index {trigger}: {description}"
        else:
            raise ValueError("Invalid trigger mode. Must be 0-2.")

    def get_reference_trigger(self, instrument) -> str:
        """Query reference trigger mode - Returns index and description"""
        response = instrument.query('REFMODE')
        try:
            index = int(response.strip())
            description = self.reference_triggers.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_harmonic(self, instrument, harmonic: int):
        """
        Set detection harmonic

        Args:
            instrument: VISA instrument object
            harmonic: 1 or 2 for 1st or 2nd harmonic
        """
        if harmonic in [1, 2]:
            description = self.harmonics.get(harmonic, f"{harmonic}")
            instrument.write(f'REFN {harmonic}')
            return f"Set harmonic to {harmonic}: {description}"
        else:
            raise ValueError("Invalid harmonic. Must be 1 or 2.")

    def get_harmonic(self, instrument) -> str:
        """Query detection harmonic - Returns index and description"""
        response = instrument.query('REFN')
        try:
            index = int(response.strip())
            description = self.harmonics.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_oscillator_amplitude(self, instrument, amplitude: float):
        """
        Set internal oscillator amplitude

        Args:
            instrument: VISA instrument object
            amplitude: Amplitude in Volts (0.0 to 5.0 V)
        """
        if 0.0 <= amplitude <= 5.0:
            instrument.write(f'OA {amplitude}')
            return f"Set oscillator amplitude to {amplitude} V"
        else:
            raise ValueError("Amplitude must be between 0.0 and 5.0 V")

    def get_oscillator_amplitude(self, instrument) -> str:
        """Query internal oscillator amplitude"""
        return instrument.query('OA.')

    # ========================================================================================
    # Signal Channel Output Filters Commands
    # ========================================================================================

    def set_time_constant(self, instrument, index: int):
        """
        Set time constant

        Args:
            instrument: VISA instrument object
            index: Time constant index (0-29)
                   Returns with description, e.g., index 0 is "10 µs"
        """
        if 0 <= index <= 29:
            description = self.time_constants.get(index, f"Index {index}")
            instrument.write(f'TC {index}')
            return f"Set time constant to index {index}: {description}"
        else:
            raise ValueError(f"Invalid time constant index. Must be 0-29. Index {index} is out of range.")

    def get_time_constant(self, instrument) -> str:
        """Query time constant - Returns index and description"""
        response = instrument.query('TC')
        try:
            index = int(response.strip())
            description = self.time_constants.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_filter_slope(self, instrument, slope: int):
        """
        Set output filter slope

        Args:
            instrument: VISA instrument object
            slope: Slope index (0-3)
                   0: 6 dB/oct
                   1: 12 dB/oct
                   2: 18 dB/oct
                   3: 24 dB/oct
        """
        if 0 <= slope <= 3:
            description = self.slopes.get(slope, f"Index {slope}")
            instrument.write(f'SLOPE {slope}')
            return f"Set filter slope to index {slope}: {description}"
        else:
            raise ValueError("Invalid slope. Must be 0-3.")

    def get_filter_slope(self, instrument) -> str:
        """Query output filter slope - Returns index and description"""
        response = instrument.query('SLOPE')
        try:
            index = int(response.strip())
            description = self.slopes.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def set_sync_filter(self, instrument, state: int):
        """
        Enable/disable synchronous filter

        Args:
            instrument: VISA instrument object
            state: 0 = Off, 1 = On
        """
        if state in [0, 1]:
            instrument.write(f'SYNC {state}')
            return f"Set sync filter to {'On' if state == 1 else 'Off'}"
        else:
            raise ValueError("Invalid state. Must be 0 (Off) or 1 (On).")

    def get_sync_filter(self, instrument) -> str:
        """Query synchronous filter state"""
        response = instrument.query('SYNC')
        try:
            state = int(response.strip())
            return f"{state} ({'On' if state == 1 else 'Off'})"
        except:
            return response

    # ========================================================================================
    # Instrument Outputs Commands
    # ========================================================================================

    def get_x_value(self, instrument) -> str:
        """Query X output value"""
        return instrument.query('X.')

    def get_y_value(self, instrument) -> str:
        """Query Y output value"""
        return instrument.query('Y.')

    def get_r_value(self, instrument) -> str:
        """Query R (magnitude) output value"""
        return instrument.query('MAG.')

    def get_theta_value(self, instrument) -> str:
        """Query Theta (phase) output value"""
        return instrument.query('PHA.')

    def get_xy_values(self, instrument) -> tuple:
        """Query both X and Y values"""
        response = instrument.query('XY.')
        values = response.split(',')
        if len(values) == 2:
            return (float(values[0]), float(values[1]))
        return response

    def get_r_theta_values(self, instrument) -> tuple:
        """Query both R and Theta values"""
        response = instrument.query('MP.')
        values = response.split(',')
        if len(values) == 2:
            return (float(values[0]), float(values[1]))
        return response

    def get_adc(self, instrument, channel: int) -> str:
        """
        Query ADC value

        Args:
            instrument: VISA instrument object
            channel: ADC channel (1-4)
        """
        if 1 <= channel <= 4:
            return instrument.query(f'ADC {channel}')
        else:
            raise ValueError("Invalid ADC channel. Must be 1-4.")

    def set_dac(self, instrument, channel: int, value: float):
        """
        Set DAC output value

        Args:
            instrument: VISA instrument object
            channel: DAC channel (1 or 2)
            value: Output value in Volts (-12.0 to +12.0 V)
        """
        if channel in [1, 2]:
            if -12.0 <= value <= 12.0:
                instrument.write(f'DAC {channel} {value}')
                return f"Set DAC {channel} to {value} V"
            else:
                raise ValueError("DAC value must be between -12.0 and +12.0 V")
        else:
            raise ValueError("Invalid DAC channel. Must be 1 or 2.")

    def get_dac(self, instrument, channel: int) -> str:
        """Query DAC output value"""
        if channel in [1, 2]:
            return instrument.query(f'DAC. {channel}')
        else:
            raise ValueError("Invalid DAC channel. Must be 1 or 2.")

    # ========================================================================================
    # Signal Channel Output Amplifiers Commands
    # ========================================================================================

    def set_output_offset(self, instrument, channel: int, offset_percent: float):
        """
        Set output offset

        Args:
            instrument: VISA instrument object
            channel: Output channel (1 or 2)
            offset_percent: Offset as percentage (-105% to +105%)
        """
        if channel in [1, 2]:
            if -105.0 <= offset_percent <= 105.0:
                instrument.write(f'XOF {channel} {offset_percent}')
                return f"Set output {channel} offset to {offset_percent}%"
            else:
                raise ValueError("Offset must be between -105% and +105%")
        else:
            raise ValueError("Invalid output channel. Must be 1 or 2.")

    def get_output_offset(self, instrument, channel: int) -> str:
        """Query output offset"""
        if channel in [1, 2]:
            return instrument.query(f'XOF. {channel}')
        else:
            raise ValueError("Invalid output channel. Must be 1 or 2.")

    def set_output_expand(self, instrument, channel: int, expand: int):
        """
        Set output expand (gain)

        Args:
            instrument: VISA instrument object
            channel: Output channel (1 or 2)
            expand: Expand factor (0=x1, 1=x10, 2=x100)
        """
        if channel in [1, 2]:
            if 0 <= expand <= 2:
                expand_values = {0: "x1", 1: "x10", 2: "x100"}
                description = expand_values.get(expand, f"Index {expand}")
                instrument.write(f'EXP {channel} {expand}')
                return f"Set output {channel} expand to index {expand}: {description}"
            else:
                raise ValueError("Expand must be 0 (x1), 1 (x10), or 2 (x100)")
        else:
            raise ValueError("Invalid output channel. Must be 1 or 2.")

    def get_output_expand(self, instrument, channel: int) -> str:
        """Query output expand - Returns index and description"""
        if channel in [1, 2]:
            response = instrument.query(f'EXP. {channel}')
            try:
                expand_values = {0: "x1", 1: "x10", 2: "x100"}
                index = int(response.strip())
                description = expand_values.get(index, "Unknown")
                return f"{index} ({description})"
            except:
                return response
        else:
            raise ValueError("Invalid output channel. Must be 1 or 2.")

    def auto_offset_x(self, instrument):
        """Automatically adjust X output offset"""
        instrument.write('AXO')

    def auto_offset_y(self, instrument):
        """Automatically adjust Y output offset"""
        instrument.write('AYO')

    # ========================================================================================
    # Internal Oscillator Commands
    # ========================================================================================

    def set_oscillator_output(self, instrument, state: int):
        """
        Enable/disable oscillator output

        Args:
            instrument: VISA instrument object
            state: 0 = Off, 1 = On
        """
        if state in [0, 1]:
            instrument.write(f'OSCS {state}')
            return f"Set oscillator output to {'On' if state == 1 else 'Off'}"
        else:
            raise ValueError("Invalid state. Must be 0 (Off) or 1 (On).")

    def get_oscillator_output(self, instrument) -> str:
        """Query oscillator output state"""
        response = instrument.query('OSCS')
        try:
            state = int(response.strip())
            return f"{state} ({'On' if state == 1 else 'Off'})"
        except:
            return response

    def set_frequency_sweep(self, instrument, start_freq: float, stop_freq: float,
                            duration: float):
        """
        Configure frequency sweep

        Args:
            instrument: VISA instrument object
            start_freq: Start frequency in Hz
            stop_freq: Stop frequency in Hz
            duration: Sweep duration in seconds
        """
        instrument.write(f'SWEEP {start_freq} {stop_freq} {duration}')
        return f"Set frequency sweep: {start_freq} Hz to {stop_freq} Hz in {duration} s"

    def start_frequency_sweep(self, instrument):
        """Start frequency sweep"""
        instrument.write('STRT')

    # ========================================================================================
    # Output Data Curve Buffer Commands
    # ========================================================================================

    def set_curve_length(self, instrument, length: int):
        """
        Set curve buffer length

        Args:
            instrument: VISA instrument object
            length: Number of points (1-32768)
        """
        if 1 <= length <= 32768:
            instrument.write(f'LEN {length}')
            return f"Set curve length to {length} points"
        else:
            raise ValueError("Curve length must be between 1 and 32768")

    def get_curve_length(self, instrument) -> str:
        """Query curve buffer length"""
        return instrument.query('LEN')

    def set_curve_storage_interval(self, instrument, interval: float):
        """
        Set curve storage interval

        Args:
            instrument: VISA instrument object
            interval: Storage interval in seconds (10 µs to 1000 s)
        """
        instrument.write(f'STR {interval}')
        return f"Set storage interval to {interval} s"

    def get_curve_storage_interval(self, instrument) -> str:
        """Query curve storage interval"""
        return instrument.query('STR')

    def start_curve_storage(self, instrument):
        """Start curve buffer data storage"""
        instrument.write('TD')

    def halt_curve_storage(self, instrument):
        """Halt curve buffer data storage"""
        instrument.write('HC')

    def get_curve_status(self, instrument) -> str:
        """Query curve buffer status - Returns index and description"""
        response = instrument.query('M')
        try:
            index = int(response.strip())
            description = self.curve_status.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    def get_curve_data_point(self, instrument, bin_number: int) -> str:
        """
        Query single curve data point

        Args:
            instrument: VISA instrument object
            bin_number: Data point index (0 to length-1)
        """
        return instrument.query(f'DC. {bin_number}')

    def get_curve_data(self, instrument) -> str:
        """Query all curve data"""
        return instrument.query('DC')

    # ========================================================================================
    # Computer Interfaces (RS-232 and GPIB) Commands
    # ========================================================================================

    def set_baud_rate(self, instrument, rate: int):
        """
        Set RS-232 baud rate

        Args:
            instrument: VISA instrument object
            rate: Baud rate (0=9600, 1=19200, 2=38400)
        """
        if 0 <= rate <= 2:
            rates = {0: "9600", 1: "19200", 2: "38400"}
            description = rates.get(rate, f"Index {rate}")
            instrument.write(f'BAUD {rate}')
            return f"Set baud rate to index {rate}: {description} baud"
        else:
            raise ValueError("Invalid baud rate. Must be 0 (9600), 1 (19200), or 2 (38400).")

    def get_baud_rate(self, instrument) -> str:
        """Query RS-232 baud rate - Returns index and description"""
        response = instrument.query('BAUD')
        try:
            rates = {0: "9600", 1: "19200", 2: "38400"}
            index = int(response.strip())
            description = rates.get(index, "Unknown")
            return f"{index} ({description} baud)"
        except:
            return response

    def set_gpib_address(self, instrument, address: int):
        """
        Set GPIB address

        Args:
            instrument: VISA instrument object
            address: GPIB address (0-30)
        """
        if 0 <= address <= 30:
            instrument.write(f'ADDR {address}')
            return f"Set GPIB address to {address}"
        else:
            raise ValueError("GPIB address must be between 0 and 30")

    def get_gpib_address(self, instrument) -> str:
        """Query GPIB address"""
        return instrument.query('ADDR')

    def set_overload_byte(self, instrument, state: int):
        """
        Enable/disable overload byte

        Args:
            instrument: VISA instrument object
            state: 0 = Off, 1 = On
        """
        if state in [0, 1]:
            instrument.write(f'OVLS {state}')
            return f"Set overload byte to {'On' if state == 1 else 'Off'}"
        else:
            raise ValueError("Invalid state. Must be 0 (Off) or 1 (On).")

    def get_overload_byte(self, instrument) -> str:
        """Query overload byte state"""
        response = instrument.query('OVLS')
        try:
            state = int(response.strip())
            return f"{state} ({'On' if state == 1 else 'Off'})"
        except:
            return response

    # ========================================================================================
    # Instrument Identification Commands
    # ========================================================================================

    def get_id(self, instrument) -> str:
        """Query instrument identification string"""
        return instrument.query('ID')

    def get_version(self, instrument) -> str:
        """Query firmware version"""
        return instrument.query('VER')

    # ========================================================================================
    # Front Panel Commands
    # ========================================================================================

    def set_display_brightness(self, instrument, brightness: int):
        """
        Set display brightness

        Args:
            instrument: VISA instrument object
            brightness: Brightness level (0-3)
        """
        if 0 <= brightness <= 3:
            instrument.write(f'BRIGHT {brightness}')
            return f"Set display brightness to level {brightness}"
        else:
            raise ValueError("Brightness must be 0-3")

    def get_display_brightness(self, instrument) -> str:
        """Query display brightness"""
        return instrument.query('BRIGHT')

    def set_key_click(self, instrument, state: int):
        """
        Enable/disable key click sound

        Args:
            instrument: VISA instrument object
            state: 0 = Off, 1 = On
        """
        if state in [0, 1]:
            instrument.write(f'KEYCLICK {state}')
            return f"Set key click to {'On' if state == 1 else 'Off'}"
        else:
            raise ValueError("Invalid state. Must be 0 (Off) or 1 (On).")

    def get_key_click(self, instrument) -> str:
        """Query key click state"""
        response = instrument.query('KEYCLICK')
        try:
            state = int(response.strip())
            return f"{state} ({'On' if state == 1 else 'Off'})"
        except:
            return response

    def set_remote_mode(self, instrument, mode: int):
        """
        Set remote mode

        Args:
            instrument: VISA instrument object
            mode: 0 = Local, 1 = Remote, 2 = Local Lockout
        """
        if 0 <= mode <= 2:
            modes = {0: "Local", 1: "Remote", 2: "Local Lockout"}
            description = modes.get(mode, f"Index {mode}")
            instrument.write(f'REMOTE {mode}')
            return f"Set remote mode to index {mode}: {description}"
        else:
            raise ValueError("Invalid mode. Must be 0 (Local), 1 (Remote), or 2 (Local Lockout).")

    def get_remote_mode(self, instrument) -> str:
        """Query remote mode - Returns index and description"""
        response = instrument.query('REMOTE')
        try:
            modes = {0: "Local", 1: "Remote", 2: "Local Lockout"}
            index = int(response.strip())
            description = modes.get(index, "Unknown")
            return f"{index} ({description})"
        except:
            return response

    # ========================================================================================
    # Status and Auto Functions Commands
    # ========================================================================================

    def get_status(self, instrument) -> str:
        """Query instrument status byte"""
        return instrument.query('ST')

    def get_overload_status(self, instrument) -> str:
        """Query overload status"""
        return instrument.query('N')

    def get_signal_strength_indicator(self, instrument) -> str:
        """Query signal strength indicator (0-4)"""
        return instrument.query('Y3')

    def auto_gain(self, instrument):
        """Automatically adjust gain"""
        instrument.write('AUTOGAIN')

    def auto_reserve(self, instrument):
        """Automatically set dynamic reserve"""
        instrument.write('AUTORESERVE')

    # ========================================================================================
    # Dual Reference Mode Commands (if applicable)
    # ========================================================================================

    def set_dual_mode(self, instrument, state: int):
        """
        Enable/disable dual reference mode

        Args:
            instrument: VISA instrument object
            state: 0 = Single Reference, 1 = Dual Reference
        """
        if state in [0, 1]:
            instrument.write(f'DUALMODE {state}')
            return f"Set dual mode to {'Dual Reference' if state == 1 else 'Single Reference'}"
        else:
            raise ValueError("Invalid state. Must be 0 (Single) or 1 (Dual).")

    def get_dual_mode(self, instrument) -> str:
        """Query dual reference mode state"""
        response = instrument.query('DUALMODE')
        try:
            state = int(response.strip())
            return f"{state} ({'Dual Reference' if state == 1 else 'Single Reference'})"
        except:
            return response

    # ========================================================================================
    # Utility Commands
    # ========================================================================================

    def clear_status(self, instrument):
        """Clear status registers"""
        instrument.write('*CLS')

    def reset(self, instrument):
        """Reset instrument to default settings"""
        instrument.write('*RST')

    def self_test(self, instrument) -> str:
        """Perform self-test"""
        return instrument.query('*TST?')

    def set_auto_default(self, instrument):
        """Restore factory default settings"""
        instrument.write('ADF')

    # ========================================================================================
    # Convenience Methods
    # ========================================================================================

    def configure_basic_measurement(self, instrument, sensitivity_index: int,
                                    time_constant_index: int, reference_freq: float):
        """
        Convenience method to configure basic lock-in measurement

        Args:
            instrument: VISA instrument object
            sensitivity_index: Sensitivity index (0-26)
            time_constant_index: Time constant index (0-29)
            reference_freq: Reference frequency in Hz
        """
        self.set_sensitivity(instrument, sensitivity_index)
        self.set_time_constant(instrument, time_constant_index)
        self.set_reference_frequency(instrument, reference_freq)
        return "Basic measurement configured"

    def configure_internal_reference(self, instrument, frequency: float, amplitude: float):
        """
        Convenience method to configure internal reference

        Args:
            instrument: VISA instrument object
            frequency: Reference frequency in Hz
            amplitude: Oscillator amplitude in V
        """
        self.set_reference_source(instrument, 0)  # Internal
        self.set_reference_frequency(instrument, frequency)
        self.set_oscillator_amplitude(instrument, amplitude)
        self.set_oscillator_output(instrument, 1)  # Enable output
        return f"Internal reference configured: {frequency} Hz, {amplitude} V"

    def configure_external_reference(self, instrument, trigger_mode: int = 0):
        """
        Convenience method to configure external reference

        Args:
            instrument: VISA instrument object
            trigger_mode: 0=Zero Crossing, 1=TTL Rising, 2=TTL Falling
        """
        self.set_reference_source(instrument, 1)  # External
        self.set_reference_trigger(instrument, trigger_mode)
        return "External reference configured"

    def perform_auto_setup(self, instrument):
        """
        Convenience method to perform automatic setup
        """
        self.set_auto_measure(instrument)
        self.set_auto_phase(instrument)
        return "Automatic setup performed"

    def read_all_outputs(self, instrument) -> dict:
        """
        Convenience method to read all main outputs

        Returns:
            Dictionary with X, Y, R, Theta values
        """
        x = float(self.get_x_value(instrument))
        y = float(self.get_y_value(instrument))
        r = float(self.get_r_value(instrument))
        theta = float(self.get_theta_value(instrument))

        return {
            'X': x,
            'Y': y,
            'R': r,
            'Theta': theta
        }
