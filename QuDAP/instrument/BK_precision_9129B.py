class BK_9129_COMMAND:
    # IEEE488.2 Common Commands
    def clear(self, instrument):
        """Clear all status registers"""
        instrument.write('*CLS')

    def get_id(self, instrument) -> str:
        """Get instrument identification"""
        id = instrument.query('*IDN?')
        return id

    def reset(self, instrument):
        """Reset to default settings"""
        instrument.write('*RST')

    def save_state(self, instrument, memory_location: int):
        """Save current settings to memory (1-9)"""
        if 1 <= memory_location <= 9:
            instrument.write(f'*SAV {memory_location}')

    def recall_state(self, instrument, memory_location: int):
        """Recall saved settings from memory (1-9)"""
        if 1 <= memory_location <= 9:
            instrument.write(f'*RCL {memory_location}')

    # System Commands
    def get_system_error(self, instrument):
        """Query error information"""
        return instrument.query('SYST:ERR?')

    def set_remote_mode(self, instrument):
        """Enable remote control mode"""
        instrument.write('SYST:REM')

    def set_local_mode(self, instrument):
        """Return to local control mode"""
        instrument.write('SYST:LOC')

    def beep(self, instrument):
        """Make the instrument beep"""
        instrument.write('SYST:BEEP')

    # Output Control Commands
    def set_output_state(self, instrument, state: str):
        """Set output state for all channels (1|0|ON|OFF)"""
        if state in ['1', '0', 'ON', 'OFF']:
            instrument.write(f'OUTP:STAT {state}')

    def get_output_state(self, instrument) -> str:
        """Query output state of all channels"""
        return instrument.query('OUTP:STAT:ALL?')

    def set_output_series_state(self, instrument, state: str):
        """Set CH1+CH2 series mode (1|0|ON|OFF)"""
        if state in ['1', '0', 'ON', 'OFF']:
            instrument.write(f'OUTP:SER {state}')

    def get_output_series_state(self, instrument) -> str:
        """Query series mode state"""
        return instrument.query('OUTP:SER?')

    def set_output_parallel_state(self, instrument, state: str):
        """Set CH1+CH2 parallel mode (1|0|ON|OFF)"""
        if state in ['1', '0', 'ON', 'OFF']:
            instrument.write(f'OUTP:PARA {state}')

    def get_output_parallel_state(self, instrument) -> str:
        """Query parallel mode state"""
        return instrument.query('OUTP:PARA?')

    # Channel Control Commands
    def select_channel(self, instrument, channel: str):
        """Select channel (CH1|CH2|CH3)"""
        if channel in ['CH1', 'CH2', 'CH3']:
            instrument.write(f'INST:SEL {channel}')

    def get_selected_channel(self, instrument) -> str:
        """Query currently selected channel"""
        return instrument.query('INST:SEL?')

    def set_channel_output_state(self, instrument, state: str):
        """Set output state for selected channel (1|0|ON|OFF)"""
        if state in ['1', '0', 'ON', 'OFF']:
            instrument.write(f'SOUR:CHAN:OUTP:STAT {state}')

    def get_channel_output_state(self, instrument) -> str:
        """Query selected channel output state"""
        return instrument.query('SOUR:CHAN:OUTP:STAT?')

    def clear_output_protection(self, instrument):
        """Clear protection (OVP, OTP)"""
        instrument.write('SOUR:OUTP:PROT:CLE')

    # Voltage Commands
    def set_voltage(self, instrument, voltage_channel: float = '', unit_channel: str = 'V'):
        """Set voltage for selected channel (unit: V, mV, kV, uV)"""
        instrument.write(f'VOLT {voltage_channel}{unit_channel}')

    def get_voltage(self, instrument) -> str:
        """Query voltage setting for selected channel"""
        return instrument.query('VOLT?')

    def set_voltage_limit(self, instrument, voltage: float, unit: str = 'V'):
        """Set voltage limit for selected channel"""
        instrument.write(f'SOUR:VOLT:LIMIT {voltage}{unit}')

    def get_voltage_limit(self, instrument) -> str:
        """Query voltage limit"""
        return instrument.query('SOUR:VOLT:LIMIT?')

    def voltage_up(self, instrument):
        """Increase voltage by one step"""
        instrument.write('VOLT:UP')

    def voltage_down(self, instrument):
        """Decrease voltage by one step"""
        instrument.write('VOLT:DOWN')

    def set_voltage_step(self, instrument, step: float, unit: str = 'V'):
        """Set voltage step size"""
        instrument.write(f'SOUR:VOLT:LEV:IMM:STEP:INCR {step}{unit}')

    def get_voltage_step(self, instrument) -> str:
        """Query voltage step size"""
        return instrument.query('SOUR:VOLT:LEV:IMM:STEP:INCR?')

    # Current Commands
    def set_current(self, instrument, current: float, unit: str = 'A'):
        """Set current for selected channel (unit: A, mA, uA)"""
        instrument.write(f'CURR {current}{unit}')

    def get_current(self, instrument) -> str:
        """Query current setting for selected channel"""
        return instrument.query('CURR?')

    def current_up(self, instrument):
        """Increase current by one step"""
        instrument.write('CURR:UP')

    def current_down(self, instrument):
        """Decrease current by one step"""
        instrument.write('CURR:DOWN')

    def set_current_step(self, instrument, step: float, unit: str = 'A'):
        """Set current step size"""
        instrument.write(f'SOUR:CURR:LEV:IMM:STEP:INCR {step}{unit}')

    def get_current_step(self, instrument) -> str:
        """Query current step size"""
        return instrument.query('SOUR:CURR:LEV:IMM:STEP:INCR?')

    # Multi-Channel Commands
    def set_all_voltages(self, instrument, ch1: float, ch2: float, ch3: float, unit: str = 'V'):
        """Set voltage for all channels simultaneously"""
        instrument.write(f'APP:VOLT {ch1}{unit},{ch2}{unit},{ch3}{unit}')

    def get_all_voltages(self, instrument) -> str:
        """Query voltage settings for all channels"""
        return instrument.query('APP:VOLT?')

    def set_all_currents(self, instrument, ch1: float, ch2: float, ch3: float, unit: str = 'A'):
        """Set current for all channels simultaneously"""
        instrument.write(f'APP:CURR {ch1}{unit},{ch2}{unit},{ch3}{unit}')

    def get_all_currents(self, instrument) -> str:
        """Query current settings for all channels"""
        return instrument.query('APP:CURR?')

    def set_all_outputs(self, instrument, ch1: str, ch2: str, ch3: str):
        """Set output state for all channels (1|0|ON|OFF for each)"""
        instrument.write(f'APP:OUT {ch1},{ch2},{ch3}')

    def get_all_outputs(self, instrument) -> str:
        """Query output states for all channels"""
        return instrument.query('APP:OUT?')

    # Measurement Commands
    def measure_voltage(self, instrument, channel: str = None) -> str:
        """Measure actual voltage (CH1|CH2|CH3|ALL or None for selected)"""
        if channel:
            return instrument.query(f'MEAS:VOLT? {channel}')
        return instrument.query('MEAS:VOLT?')

    def measure_current(self, instrument, channel: str = None) -> str:
        """Measure actual current (CH1|CH2|CH3|ALL or None for selected)"""
        if channel:
            return instrument.query(f'MEAS:CURR? {channel}')
        return instrument.query('MEAS:CURR?')

    def measure_power(self, instrument, channel: str = None) -> str:
        """Measure actual power (CH1|CH2|CH3|ALL or None for selected)"""
        if channel:
            return instrument.query(f'MEAS:POW? {channel}')
        return instrument.query('MEAS:POW?')

    def measure_all_voltages(self, instrument) -> str:
        """Measure voltage for all channels"""
        return instrument.query('MEAS:VOLT:ALL?')

    def measure_all_currents(self, instrument) -> str:
        """Measure current for all channels"""
        return instrument.query('MEAS:CURR:ALL?')

    # Combine Mode Commands
    def set_series_mode(self, instrument):
        """Enable series mode (CH1+CH2)"""
        instrument.write('INST:COMB:SER')

    def set_parallel_mode(self, instrument):
        """Enable parallel mode (CH1+CH2)"""
        instrument.write('INST:COMB:PARA')

    def disable_combine_mode(self, instrument):
        """Disable series/parallel mode"""
        instrument.write('INST:COMB:OFF')

    def get_combine_mode(self, instrument) -> str:
        """Query combine mode status"""
        return instrument.query('INST:COMB?')