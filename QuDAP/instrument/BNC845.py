"""
Berkeley Nucleonics Corporation Model 845-M Signal Generator
SCPI Command Interface Class

This class provides a comprehensive interface for controlling the BNC Model 845-M
Signal Generator via SCPI commands over LAN, USB, or GPIB interfaces.

Based on Model 845-M Programmer's Manual Version 1.1, June 2011

Author: Command Interface Generator
Date: 2025
"""


class BNC_845M_COMMAND:
    """
    Command class for Berkeley Nucleonics Model 845-M Signal Generator

    Supports remote control via:
    - LAN (Sockets, VXI-11/VISA, Telnet)
    - USB (USB-TMC via VISA or BNC API)
    - GPIB

    All commands follow SCPI standard syntax
    """

    def __init__(self):
        """Initialize the BNC 845-M command class"""
        self.name = "BNC Model 845-M Signal Generator"
        self.version = "1.0"

    # ========================================================================================
    # IEEE 488.2 Common Commands
    # ========================================================================================

    def clear_status(self, instrument):
        """Clear status (*CLS) - Clears all event registers and error queue"""
        instrument.write('*CLS')

    def get_standard_event_status_enable(self, instrument) -> str:
        """Query Standard Event Status Enable Register"""
        return instrument.query('*ESE?')

    def set_standard_event_status_enable(self, instrument, value: int):
        """Set Standard Event Status Enable Register (0-255)"""
        if 0 <= value <= 255:
            instrument.write(f'*ESE {value}')

    def get_standard_event_status(self, instrument) -> str:
        """Query and clear Standard Event Status Register"""
        return instrument.query('*ESR?')

    def get_id(self, instrument) -> str:
        """Get instrument identification string"""
        return instrument.query('*IDN?')

    def operation_complete(self, instrument):
        """Set operation complete bit when all operations finished"""
        instrument.write('*OPC')

    def operation_complete_query(self, instrument) -> str:
        """Query operation complete (returns '1' when done)"""
        return instrument.query('*OPC?')

    def get_options(self, instrument) -> str:
        """Query installed options"""
        return instrument.query('*OPT?')

    def set_power_on_status_clear(self, instrument, state: str):
        """Set power-on status clear (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f'*PSC {state}')

    def get_power_on_status_clear(self, instrument) -> str:
        """Query power-on status clear setting"""
        return instrument.query('*PSC?')

    def recall_state(self, instrument, register: int):
        """Recall instrument state from memory register"""
        instrument.write(f'*RCL {register}')

    def reset(self, instrument):
        """Reset instrument to factory defaults"""
        instrument.write('*RST')

    def save_state(self, instrument, register: int):
        """Save instrument state to memory register"""
        instrument.write(f'*SAV {register}')

    def set_service_request_enable(self, instrument, value: int):
        """Set Service Request Enable Register (0-255, bit 6 ignored)"""
        if 0 <= value <= 255:
            instrument.write(f'*SRE {value}')

    def get_service_request_enable(self, instrument) -> str:
        """Query Service Request Enable Register"""
        return instrument.query('*SRE?')

    def get_status_byte(self, instrument) -> str:
        """Query status byte including master summary status"""
        return instrument.query('*STB?')

    def trigger(self, instrument):
        """Software trigger (if LAN is trigger source)"""
        instrument.write('*TRG')

    def self_test(self, instrument) -> str:
        """Perform self-test (returns 0 if pass, 1 if fail)"""
        return instrument.query('*TST?')

    def wait_to_continue(self, instrument):
        """Wait until all pending commands complete"""
        instrument.write('*WAI')

    # ========================================================================================
    # :ABORt Subsystem
    # ========================================================================================

    def abort(self, instrument):
        """Abort current sweep in progress"""
        instrument.write(':ABORt')

    # ========================================================================================
    # :DISPlay Subsystem
    # ========================================================================================

    def set_display_text_state(self, instrument, state: str):
        """Turn on/off parameter display (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':DISPlay:WINDow:TEXT:STATe {state}')

    def get_display_text_state(self, instrument) -> str:
        """Query parameter display state"""
        return instrument.query(':DISPlay:WINDow:TEXT:STATe?')

    def set_display_remote(self, instrument, state: str):
        """Turn on/off display update (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':DISPlay:REMote {state}')

    def get_display_remote(self, instrument) -> str:
        """Query display update state"""
        return instrument.query(':DISPlay:REMote?')

    # ========================================================================================
    # :INITiate Subsystem
    # ========================================================================================

    def initiate(self, instrument):
        """Set trigger to armed state"""
        instrument.write(':INITiate:IMMediate')

    def set_continuous_sweep(self, instrument, state: str):
        """Continuously rearm trigger after sweep (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':INITiate:CONTinuous {state}')

    def get_continuous_sweep(self, instrument) -> str:
        """Query continuous sweep state"""
        return instrument.query(':INITiate:CONTinuous?')

    # ========================================================================================
    # :OUTPut Subsystem
    # ========================================================================================
    def set_output(self, instrument, state: str):
        """Turn RF output on/off (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':OUTP {state}')

    def get_output(self, instrument) -> str:
        """Query RF output state"""
        return instrument.query(':OUTP?')

    def set_output_state(self, instrument, state: str):
        """Turn RF output on/off (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':OUTPut:STATe {state}')

    def get_output_state(self, instrument) -> str:
        """Query RF output state"""
        return instrument.query(':OUTPut:STATe?')

    def set_output_blanking(self, instrument, state: str):
        """Set RF blanking during frequency changes (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':OUTPut:BLANking:STATe {state}')

    def get_output_blanking(self, instrument) -> str:
        """Query RF blanking state"""
        return instrument.query(':OUTPut:BLANking:STATe?')

    # ========================================================================================
    # [SOURce]:FREQuency Subsystem
    # ========================================================================================

    def set_frequency(self, instrument, frequency: float):
        """Set frequency"""
        instrument.write(f':SOURce:FREQuency {frequency}')

    def get_frequency(self, instrument) -> str:
        """Query frequency"""
        return instrument.query(':SOURce:FREQuency?')

    def set_frequency_cw(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set CW frequency"""
        instrument.write(f':SOURce:FREQuency:CW {frequency}{unit}')

    def get_frequency_cw(self, instrument) -> str:
        """Query CW frequency"""
        return instrument.query(':SOURce:FREQuency:CW?')

    def set_frequency_mode(self, instrument, mode: str):
        """Set frequency mode (FIX|CW|SWEep|LIST)"""
        if mode in ['FIX', 'CW', 'SWEep', 'LIST']:
            instrument.write(f':SOURce:FREQuency:MODE {mode}')

    def get_frequency_mode(self, instrument) -> str:
        """Query frequency mode"""
        return instrument.query(':SOURce:FREQuency:MODE?')

    def set_frequency_start(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set sweep start frequency"""
        instrument.write(f':SOURce:FREQuency:STARt {frequency}{unit}')

    def get_frequency_start(self, instrument) -> str:
        """Query sweep start frequency"""
        return instrument.query(':SOURce:FREQuency:STARt?')

    def set_frequency_stop(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set sweep stop frequency"""
        instrument.write(f':SOURce:FREQuency:STOP {frequency}{unit}')

    def get_frequency_stop(self, instrument) -> str:
        """Query sweep stop frequency"""
        return instrument.query(':SOURce:FREQuency:STOP?')

    def set_frequency_step_linear(self, instrument, step: float, unit: str = 'Hz'):
        """Set linear sweep step size"""
        instrument.write(f':SOURce:FREQuency:STEP:LINear {step}{unit}')

    def get_frequency_step_linear(self, instrument) -> str:
        """Query linear sweep step size"""
        return instrument.query(':SOURce:FREQuency:STEP:LINear?')

    def set_frequency_step_log(self, instrument, step: float):
        """Set logarithmic sweep step size (0-255.999999999)"""
        instrument.write(f':SOURce:FREQuency:STEP:LOGarithmic {step}')

    def get_frequency_step_log(self, instrument) -> str:
        """Query logarithmic sweep step size"""
        return instrument.query(':SOURce:FREQuency:STEP:LOGarithmic?')

    # ========================================================================================
    # [SOURce]:PHASe Subsystem
    # ========================================================================================

    def set_phase_reference(self, instrument):
        """Set current phase as zero reference"""
        instrument.write(':SOURce:PHASe:REFerence')

    def set_phase_adjust(self, instrument, phase: float, unit: str = 'RAD'):
        """Adjust output phase (radians or degrees)"""
        instrument.write(f':SOURce:PHASe:ADJust {phase}{unit}')

    def get_phase_adjust(self, instrument) -> str:
        """Query phase adjustment (returns radians)"""
        return instrument.query(':SOURce:PHASe:ADJust?')

    # ========================================================================================
    # [SOURce]:POWer Subsystem
    # ========================================================================================
    def set_power(self, instrument, power: float):
        """Set sweep start power"""
        instrument.write(f':SOURce:POWer {power}')

    def get_power(self, instrument) -> str:
        """Query sweep start power"""
        return instrument.query(':SOURce:POWer?')

    def set_power_level(self, instrument, power: float, unit: str = 'dBm'):
        """Set RF output power level"""
        instrument.write(f':SOURce:POWer:LEVel:IMMediate:AMPLitude {power}{unit}')

    def get_power_level(self, instrument) -> str:
        """Query RF output power level"""
        return instrument.query(':SOURce:POWer:LEVel:IMMediate:AMPLitude?')

    def set_power_mode(self, instrument, mode: str):
        """Set power mode (FIXed|LIST|SWEep)"""
        if mode in ['FIXed', 'LIST', 'SWEep']:
            instrument.write(f':SOURce:POWer:MODE {mode}')

    def get_power_mode(self, instrument) -> str:
        """Query power mode"""
        return instrument.query(':SOURce:POWer:MODE?')

    def set_power_start(self, instrument, power: float, unit: str = 'dBm'):
        """Set sweep start power"""
        instrument.write(f':SOURce:POWer:STARt {power}{unit}')

    def get_power_start(self, instrument) -> str:
        """Query sweep start power"""
        return instrument.query(':SOURce:POWer:STARt?')

    def set_power_stop(self, instrument, power: float, unit: str = 'dBm'):
        """Set sweep stop power"""
        instrument.write(f':SOURce:POWer:STOP {power}{unit}')

    def get_power_stop(self, instrument) -> str:
        """Query sweep stop power"""
        return instrument.query(':SOURce:POWer:STOP?')

    def set_power_alc(self, instrument, state: str):
        """Turn automatic level control on/off (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:POWer:ALC {state}')

    def get_power_alc(self, instrument) -> str:
        """Query automatic level control state"""
        return instrument.query(':SOURce:POWer:ALC?')

    def set_power_alc_hold(self, instrument, state: str):
        """Set ALC hold mode (ON|OFF|1|0) - option PE only"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:POWer:ALC:HOLD {state}')

    def get_power_alc_hold(self, instrument) -> str:
        """Query ALC hold state"""
        return instrument.query(':SOURce:POWer:ALC:HOLD?')

    def set_power_attenuation(self, instrument, attenuation: float):
        """Set power range extension attenuator in dB (option PE only)"""
        instrument.write(f':SOURce:POWer:ATTenuation {attenuation}')

    def get_power_attenuation(self, instrument) -> str:
        """Query power attenuation setting"""
        return instrument.query(':SOURce:POWer:ATTenuation?')

    def set_power_attenuation_auto(self, instrument, state: str):
        """Set automatic attenuation (ON|OFF|1|0) - option PE only"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:POWer:ATTenuation:AUTO {state}')

    def get_power_attenuation_auto(self, instrument) -> str:
        """Query automatic attenuation state"""
        return instrument.query(':SOURce:POWer:ATTenuation:AUTO?')

    def get_power_attenuation_list(self, instrument) -> str:
        """Query available attenuation settings (option PE only)"""
        return instrument.query(':SOURce:POWer:ATTenuation:LIST?')

    # ========================================================================================
    # [SOURce]:ROSCillator Subsystem (Reference Oscillator)
    # ========================================================================================

    def set_reference_external_frequency(self, instrument, frequency: float):
        """Set expected external reference frequency in MHz (1-250 MHz)"""
        if 1 <= frequency <= 250:
            instrument.write(f':SOURce:ROSCillator:EXTernal:FREQuency {frequency}')

    def get_reference_external_frequency(self, instrument) -> str:
        """Query external reference frequency"""
        return instrument.query(':SOURce:ROSCillator:EXTernal:FREQuency?')

    def get_reference_locked(self, instrument) -> str:
        """Query if synthesizer is locked to external reference"""
        return instrument.query(':SOURce:ROSCillator:LOCKed?')

    def set_reference_output_state(self, instrument, state: str):
        """Enable/disable 10 MHz reference output (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:ROSCillator:OUTPut:STATe {state}')

    def get_reference_output_state(self, instrument) -> str:
        """Query 10 MHz reference output state"""
        return instrument.query(':SOURce:ROSCillator:OUTPut:STATe?')

    def set_reference_source(self, instrument, source: str):
        """Select reference source (INTernal|EXTernal)"""
        if source in ['INTernal', 'EXTernal', 'INT', 'EXT']:
            instrument.write(f':SOURce:ROSCillator:SOURce {source}')

    def get_reference_source(self, instrument) -> str:
        """Query reference source"""
        return instrument.query(':SOURce:ROSCillator:SOURce?')

    # ========================================================================================
    # [SOURce]:LIST Subsystem
    # ========================================================================================

    def set_list_direction(self, instrument, direction: str):
        """Set list/step sweep direction (UP|DOWN|RANDom)"""
        if direction in ['UP', 'DOWN', 'RANDom']:
            instrument.write(f':SOURce:LIST:DIRection {direction}')

    def get_list_direction(self, instrument) -> str:
        """Query list sweep direction"""
        return instrument.query(':SOURce:LIST:DIRection?')

    def set_list_dwell(self, instrument, dwell_times: list):
        """Set dwell time for list sweep points (seconds)"""
        dwell_str = ','.join(map(str, dwell_times))
        instrument.write(f':SOURce:LIST:DWELl {dwell_str}')

    def get_list_dwell_points(self, instrument) -> str:
        """Query number of dwell time points"""
        return instrument.query(':SOURce:LIST:DWELl:POINts?')

    def set_list_delay(self, instrument, delay_times: list):
        """Set off time for list sweep points (seconds)"""
        delay_str = ','.join(map(str, delay_times))
        instrument.write(f':SOURce:LIST:DELay {delay_str}')

    def get_list_delay_points(self, instrument) -> str:
        """Query number of delay time points"""
        return instrument.query(':SOURce:LIST:DELay:POINts?')

    def set_list_delay_auto(self, instrument, state: str):
        """Enable automatic output blanking during transients (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:LIST:DELay:AUTO {state}')

    def get_list_delay_auto(self, instrument) -> str:
        """Query automatic delay state"""
        return instrument.query(':SOURce:LIST:DELay:AUTO?')

    def get_list_frequency_points(self, instrument) -> str:
        """Query number of frequency points in list"""
        return instrument.query(':SOURce:LIST:FREQuency:POINts?')

    def set_list_frequency(self, instrument, frequencies: list, unit: str = 'Hz'):
        """Set frequency values for list sweep (max 3501 points)"""
        if len(frequencies) <= 3501:
            freq_str = ','.join([f'{f}{unit}' for f in frequencies])
            instrument.write(f':SOURce:LIST:FREQuency {freq_str}')

    def get_list_frequency(self, instrument) -> str:
        """Query list frequency values"""
        return instrument.query(':SOURce:LIST:FREQuency?')

    def set_list_manual_point(self, instrument, point):
        """Set manual list sweep point (1-3501 or UP|DOWN)"""
        instrument.write(f':SOURce:LIST:MANual {point}')

    def get_list_manual_point(self, instrument) -> str:
        """Query current manual point"""
        return instrument.query(':SOURce:LIST:MANual?')

    def set_list_mode(self, instrument, mode: str):
        """Set list mode (AUTO|MANual)"""
        if mode in ['AUTO', 'MANual']:
            instrument.write(f':SOURce:LIST:MODE {mode}')

    def get_list_mode(self, instrument) -> str:
        """Query list mode"""
        return instrument.query(':SOURce:LIST:MODE?')

    def set_list_power(self, instrument, powers: list, unit: str = 'dBm'):
        """Set power values for list sweep"""
        power_str = ','.join([f'{p}{unit}' for p in powers])
        instrument.write(f':SOURce:LIST:POWer {power_str}')

    def get_list_power(self, instrument) -> str:
        """Query list power values"""
        return instrument.query(':SOURce:LIST:POWer?')

    def get_list_power_points(self, instrument) -> str:
        """Query number of power points in list"""
        return instrument.query(':SOURce:LIST:POWer:POINts?')

    def set_list_count(self, instrument, count):
        """Set number of list executions (1-65535 or INFinity)"""
        instrument.write(f':SOURce:LIST:COUNt {count}')

    def get_list_count(self, instrument) -> str:
        """Query list count"""
        return instrument.query(':SOURce:LIST:COUNt?')

    def get_list_progress(self, instrument) -> str:
        """Query active list sweep progress (0.0-1.0)"""
        return instrument.query(':SOURce:LIST:PROGress?')

    # ========================================================================================
    # [SOURce]:LFOutput Subsystem (Low Frequency Output)
    # ========================================================================================

    def set_lf_amplitude(self, instrument, amplitude: float):
        """Set LF generator amplitude in Volts (0-2.5V)"""
        if 0 <= amplitude <= 2.5:
            instrument.write(f':SOURce:LFOutput:AMPLitude {amplitude}')

    def get_lf_amplitude(self, instrument) -> str:
        """Query LF generator amplitude"""
        return instrument.query(':SOURce:LFOutput:AMPLitude?')

    def set_lf_frequency(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set LF generator frequency (10-5000000 Hz)"""
        instrument.write(f':SOURce:LFOutput:FREQuency {frequency}{unit}')

    def get_lf_frequency(self, instrument) -> str:
        """Query LF generator frequency"""
        return instrument.query(':SOURce:LFOutput:FREQuency?')

    def set_lf_state(self, instrument, state: str):
        """Set LF output state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:LFOutput:STATe {state}')

    def get_lf_state(self, instrument) -> str:
        """Query LF output state"""
        return instrument.query(':SOURce:LFOutput:STATe?')

    def set_lf_shape(self, instrument, shape: str):
        """Set LF waveform shape (SINE|TRIangle|SQUare)"""
        if shape in ['SINE', 'TRIangle', 'SQUare']:
            instrument.write(f':SOURce:LFOutput:SHAPe {shape}')

    def get_lf_shape(self, instrument) -> str:
        """Query LF waveform shape"""
        return instrument.query(':SOURce:LFOutput:SHAPe?')

    def set_lf_source(self, instrument, source: str):
        """Set function output source (LFGenerator|PULM|TRIGger)"""
        if source in ['LFGenerator', 'PULM', 'TRIGger']:
            instrument.write(f':SOURce:LFOutput:SOURce {source}')

    def get_lf_source(self, instrument) -> str:
        """Query function output source"""
        return instrument.query(':SOURce:LFOutput:SOURce?')

    # ========================================================================================
    # [SOURce]:SWEep Subsystem
    # ========================================================================================

    def set_sweep_direction(self, instrument, direction: str):
        """Set sweep direction (UP|DOWN|RANDom)"""
        if direction in ['UP', 'DOWN', 'RANDom']:
            instrument.write(f':SOURce:SWEep:DIRection {direction}')

    def get_sweep_direction(self, instrument) -> str:
        """Query sweep direction"""
        return instrument.query(':SOURce:SWEep:DIRection?')

    def set_sweep_points(self, instrument, points: int):
        """Set number of step sweep points (2-65535)"""
        if 2 <= points <= 65535:
            instrument.write(f':SOURce:SWEep:POINts {points}')

    def get_sweep_points(self, instrument) -> str:
        """Query number of sweep points"""
        return instrument.query(':SOURce:SWEep:POINts?')

    def set_sweep_dwell(self, instrument, dwell: float, unit: str = 's'):
        """Set sweep dwell time"""
        instrument.write(f':SOURce:SWEep:DWELl {dwell}{unit}')

    def get_sweep_dwell(self, instrument) -> str:
        """Query sweep dwell time"""
        return instrument.query(':SOURce:SWEep:DWELl?')

    def set_sweep_delay(self, instrument, delay: float, unit: str = 's'):
        """Set sweep delay (off time)"""
        instrument.write(f':SOURce:SWEep:DELay {delay}{unit}')

    def get_sweep_delay(self, instrument) -> str:
        """Query sweep delay"""
        return instrument.query(':SOURce:SWEep:DELay?')

    def set_sweep_delay_auto(self, instrument, state: str):
        """Enable automatic sweep delay (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:SWEep:DELay:AUTO {state}')

    def get_sweep_delay_auto(self, instrument) -> str:
        """Query automatic sweep delay state"""
        return instrument.query(':SOURce:SWEep:DELay:AUTO?')

    def get_sweep_progress(self, instrument) -> str:
        """Query active sweep progress (0.0-1.0)"""
        return instrument.query(':SOURce:SWEep:PROGress?')

    def set_sweep_spacing(self, instrument, spacing: str):
        """Set sweep spacing (LINear|LOGarithmic)"""
        if spacing in ['LINear', 'LOGarithmic']:
            instrument.write(f':SOURce:SWEep:SPACing {spacing}')

    def get_sweep_spacing(self, instrument) -> str:
        """Query sweep spacing"""
        return instrument.query(':SOURce:SWEep:SPACing?')

    # ========================================================================================
    # [SOURce]:AM Subsystem (Amplitude Modulation)
    # ========================================================================================

    def set_am_depth(self, instrument, depth: float):
        """Set AM modulation depth (0-0.99)"""
        if 0 <= depth <= 100:
            instrument.write(f'SOUR:AM:DEPT {str(depth)}')

    def get_am_depth(self, instrument) -> str:
        """Query AM modulation depth"""
        return instrument.query(':SOURce:AM:DEPTh?')

    def set_am_internal_frequency(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set internal AM rate (10 Hz - 50 kHz)"""
        instrument.write(f':SOURce:AM:INTernal:FREQuency {frequency}{unit}')

    def get_am_internal_frequency(self, instrument) -> str:
        """Query internal AM frequency"""
        return instrument.query(':SOURce:AM:INTernal:FREQuency?')

    def set_am_source(self, instrument, source: str):
        """Set AM source (INTernal|EXTernal)"""
        if source in ['INTernal', 'EXTernal']:
            instrument.write(f':SOURce:AM:SOURce {source}')

    def get_am_source(self, instrument) -> str:
        """Query AM source"""
        return instrument.query(':SOURce:AM:SOURce?')

    def set_am_state(self, instrument, state: str):
        """Turn amplitude modulation on/off (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:AM:STATe {state}')

    def get_am_state(self, instrument) -> str:
        """Query AM state"""
        return instrument.query(':SOURce:AM:STATe?')

    # ========================================================================================
    # [SOURce]:FM Subsystem (Frequency Modulation)
    # ========================================================================================

    def set_fm_deviation(self, instrument, deviation: float, unit: str = 'Hz'):
        """Set FM deviation"""
        instrument.write(f':SOURce:FM:DEViation {deviation}{unit}')

    def get_fm_deviation(self, instrument) -> str:
        """Query FM deviation"""
        return instrument.query(':SOURce:FM:DEViation?')

    def set_fm_sensitivity(self, instrument, sensitivity: float):
        """Set FM sensitivity (Hz/V)"""
        instrument.write(f':SOURce:FM:SENSitivity {sensitivity}')

    def get_fm_sensitivity(self, instrument) -> str:
        """Query FM sensitivity"""
        return instrument.query(':SOURce:FM:SENSitivity?')

    def set_fm_internal_frequency(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set internal FM rate"""
        instrument.write(f':SOURce:FM:INTernal:FREQuency {frequency}{unit}')

    def get_fm_internal_frequency(self, instrument) -> str:
        """Query internal FM frequency"""
        return instrument.query(':SOURce:FM:INTernal:FREQuency?')

    def set_fm_source(self, instrument, source: str):
        """Set FM source (INTernal|EXTernal)"""
        if source in ['INTernal', 'EXTernal']:
            instrument.write(f':SOURce:FM:SOURce {source}')

    def get_fm_source(self, instrument) -> str:
        """Query FM source"""
        return instrument.query(':SOURce:FM:SOURce?')

    def set_fm_state(self, instrument, state: str):
        """Turn frequency modulation on/off (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:FM:STATe {state}')

    def get_fm_state(self, instrument) -> str:
        """Query FM state"""
        return instrument.query(':SOURce:FM:STATe?')

    def set_fm_coupling(self, instrument, coupling: str):
        """Set external FM signal coupling (DC|AC)"""
        if coupling in ['DC', 'AC']:
            instrument.write(f':SOURce:FM:COUPling {coupling}')

    def get_fm_coupling(self, instrument) -> str:
        """Query FM coupling"""
        return instrument.query(':SOURce:FM:COUPling?')

    # ========================================================================================
    # [SOURce]:PM Subsystem (Phase Modulation)
    # ========================================================================================

    def set_pm_deviation(self, instrument, deviation: float, unit: str = 'RAD'):
        """Set PM deviation (radians)"""
        instrument.write(f':SOURce:PM:DEViation {deviation}{unit}')

    def get_pm_deviation(self, instrument) -> str:
        """Query PM deviation"""
        return instrument.query(':SOURce:PM:DEViation?')

    def set_pm_sensitivity(self, instrument, sensitivity: float):
        """Set PM sensitivity (rad/V)"""
        instrument.write(f':SOURce:PM:SENSitivity {sensitivity}')

    def get_pm_sensitivity(self, instrument) -> str:
        """Query PM sensitivity"""
        return instrument.query(':SOURce:PM:SENSitivity?')

    def set_pm_source(self, instrument, source: str):
        """Set PM source (INTernal|EXTernal)"""
        if source in ['INTernal', 'EXTernal']:
            instrument.write(f':SOURce:PM:SOURce {source}')

    def get_pm_source(self, instrument) -> str:
        """Query PM source"""
        return instrument.query(':SOURce:PM:SOURce?')

    def set_pm_state(self, instrument, state: str):
        """Turn phase modulation on/off (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:PM:STATe {state}')

    def get_pm_state(self, instrument) -> str:
        """Query PM state"""
        return instrument.query(':SOURce:PM:STATe?')

    # ========================================================================================
    # [SOURce]:PULM Subsystem (Pulse Modulation)
    # ========================================================================================

    def set_pulse_polarity(self, instrument, polarity: str):
        """Set pulse modulation polarity (NORMal|INVerted)"""
        if polarity in ['NORMal', 'INVerted']:
            instrument.write(f':SOURce:PULM:POLarity {polarity}')

    def get_pulse_polarity(self, instrument) -> str:
        """Query pulse modulation polarity"""
        return instrument.query(':SOURce:PULM:POLarity?')

    def set_pulse_internal_frequency(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set internal pulse rate (0.1 Hz - 100 kHz)"""
        instrument.write(f':SOURce:PULM:INTernal:FREQuency {frequency}{unit}')

    def get_pulse_internal_frequency(self, instrument) -> str:
        """Query internal pulse frequency"""
        return instrument.query(':SOURce:PULM:INTernal:FREQuency?')

    def set_pulse_internal_period(self, instrument, period: float, unit: str = 's'):
        """Set pulse period (200 ns - 10 s)"""
        instrument.write(f':SOURce:PULM:INTernal:PERiod {period}{unit}')

    def get_pulse_internal_period(self, instrument) -> str:
        """Query pulse period"""
        return instrument.query(':SOURce:PULM:INTernal:PERiod?')

    def set_pulse_internal_width(self, instrument, width: float, unit: str = 's'):
        """Set pulse width (50 ns to period)"""
        instrument.write(f':SOURce:PULM:INTernal:PWIDth {width}{unit}')

    def get_pulse_internal_width(self, instrument) -> str:
        """Query pulse width"""
        return instrument.query(':SOURce:PULM:INTernal:PWIDth?')

    def set_pulse_source(self, instrument, source: str):
        """Set pulse source (INTernal|EXTernal)"""
        if source in ['INTernal', 'EXTernal']:
            instrument.write(f':SOURce:PULM:SOURce {source}')

    def get_pulse_source(self, instrument) -> str:
        """Query pulse source"""
        return instrument.query(':SOURce:PULM:SOURce?')

    def set_pulse_state(self, instrument, state: str):
        """Turn pulse modulation on/off (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:PULM:STATe {state}')

    def get_pulse_state(self, instrument) -> str:
        """Query pulse modulation state"""
        return instrument.query(':SOURce:PULM:STATe?')

    def set_pulse_mode(self, instrument, mode: str):
        """Set pulse mode (FIXed|LIST)"""
        if mode in ['FIXed', 'LIST']:
            instrument.write(f':SOURce:PULM:MODE {mode}')

    def get_pulse_mode(self, instrument) -> str:
        """Query pulse mode"""
        return instrument.query(':SOURce:PULM:MODE?')

    # ========================================================================================
    # :TRIGger Subsystem
    # ========================================================================================

    def set_trigger_type(self, instrument, trig_type: str):
        """Set trigger type (NORMal|GATE|POINt)"""
        if trig_type in ['NORMal', 'GATE', 'POINt']:
            instrument.write(f':TRIGger:SEQuence:TYPE {trig_type}')

    def get_trigger_type(self, instrument) -> str:
        """Query trigger type"""
        return instrument.query(':TRIGger:SEQuence:TYPE?')

    def set_trigger_gate_polarity(self, instrument, polarity: str):
        """Set gate trigger polarity (LOW|HIGH)"""
        if polarity in ['LOW', 'HIGH']:
            instrument.write(f':TRIGger:SEQuence:TYPE:GATE {polarity}')

    def get_trigger_gate_polarity(self, instrument) -> str:
        """Query gate trigger polarity"""
        return instrument.query(':TRIGger:SEQuence:TYPE:GATE?')

    def set_trigger_source(self, instrument, source: str):
        """Set trigger source (IMMediate|KEY|EXTernal|BUS)"""
        if source in ['IMMediate', 'KEY', 'EXTernal', 'BUS']:
            instrument.write(f':TRIGger:SEQuence:SOURce {source}')

    def get_trigger_source(self, instrument) -> str:
        """Query trigger source"""
        return instrument.query(':TRIGger:SEQuence:SOURce?')

    def set_trigger_delay(self, instrument, delay: float, unit: str = 's'):
        """Set trigger delay"""
        instrument.write(f':TRIGger:SEQuence:DELay {delay}{unit}')

    def get_trigger_delay(self, instrument) -> str:
        """Query trigger delay"""
        return instrument.query(':TRIGger:SEQuence:DELay?')

    def set_trigger_slope(self, instrument, slope: str):
        """Set external trigger slope (POSitive|NEGative)"""
        if slope in ['POSitive', 'NEGative']:
            instrument.write(f':TRIGger:SEQuence:SLOPe {slope}')

    def get_trigger_slope(self, instrument) -> str:
        """Query trigger slope"""
        return instrument.query(':TRIGger:SEQuence:SLOPe?')

    def set_trigger_retrigger(self, instrument, mode: str):
        """Set retrigger mode (ON|OFF|IMMediate)"""
        if mode in ['ON', 'OFF', 'IMMediate']:
            instrument.write(f':TRIGger:SEQuence:RETRigger {mode}')

    def get_trigger_retrigger(self, instrument) -> str:
        """Query retrigger mode"""
        return instrument.query(':TRIGger:SEQuence:RETRigger?')

    def set_trigger_event_count(self, instrument, count: int):
        """Set trigger event count modulo (1-255)"""
        if 1 <= count <= 255:
            instrument.write(f':SOURce:TRIGger:SEQuence:ECOunt {count}')

    def get_trigger_event_count(self, instrument) -> str:
        """Query trigger event count"""
        return instrument.query(':SOURce:TRIGger:SEQuence:ECOunt?')

    def set_trigger_output_polarity(self, instrument, polarity: str):
        """Set trigger output polarity (NORMal|INVerted)"""
        if polarity in ['NORMal', 'INVerted']:
            instrument.write(f':SOURce:TRIGger:SEQuence:OUTPut:POLarity {polarity}')

    def get_trigger_output_polarity(self, instrument) -> str:
        """Query trigger output polarity"""
        return instrument.query(':SOURce:TRIGger:SEQuence:OUTPut:POLarity?')

    def set_trigger_output_mode(self, instrument, mode: str):
        """Set trigger output mode (NORMal|GATE|POINt)"""
        if mode in ['NORMal', 'GATE', 'POINt']:
            instrument.write(f':SOURce:TRIGger:SEQuence:OUTPut:MODE {mode}')

    def get_trigger_output_mode(self, instrument) -> str:
        """Query trigger output mode"""
        return instrument.query(':SOURce:TRIGger:SEQuence:OUTPut:MODE?')

    # ========================================================================================
    # :STATus Subsystem
    # ========================================================================================

    def get_operation_event(self, instrument) -> str:
        """Query and clear operation status event register"""
        return instrument.query(':STATus:OPERation:EVENt?')

    def get_operation_condition(self, instrument) -> str:
        """Query operation status condition register"""
        return instrument.query(':STATus:OPERation:CONDition?')

    def set_operation_enable(self, instrument, value: int):
        """Set operation status enable mask"""
        instrument.write(f':STATus:OPERation:ENABle {value}')

    def get_operation_enable(self, instrument) -> str:
        """Query operation status enable mask"""
        return instrument.query(':STATus:OPERation:ENABle?')

    def set_operation_ptr(self, instrument, value: int):
        """Set operation status positive transition filter"""
        instrument.write(f':STATus:OPERation:PTR {value}')

    def get_operation_ptr(self, instrument) -> str:
        """Query operation status positive transition filter"""
        return instrument.query(':STATus:OPERation:PTR?')

    def set_operation_ntr(self, instrument, value: int):
        """Set operation status negative transition filter"""
        instrument.write(f':STATus:OPERation:NTR {value}')

    def get_operation_ntr(self, instrument) -> str:
        """Query operation status negative transition filter"""
        return instrument.query(':STATus:OPERation:NTR?')

    def status_preset(self, instrument):
        """Preset status system (disable events, clear NTR, set PTR)"""
        instrument.write(':STATus:PRESet')

    def get_questionable_event(self, instrument) -> str:
        """Query and clear questionable status event register"""
        return instrument.query(':STATus:QUEStionable:EVENt?')

    def get_questionable_condition(self, instrument) -> str:
        """Query questionable status condition register"""
        return instrument.query(':STATus:QUEStionable:CONDition?')

    def set_questionable_enable(self, instrument, value: int):
        """Set questionable status enable mask"""
        instrument.write(f':STATus:QUEStionable:ENABle {value}')

    def get_questionable_enable(self, instrument) -> str:
        """Query questionable status enable mask"""
        return instrument.query(':STATus:QUEStionable:ENABle?')

    def set_questionable_ptr(self, instrument, value: int):
        """Set questionable status positive transition filter"""
        instrument.write(f':STATus:QUEStionable:PTR {value}')

    def get_questionable_ptr(self, instrument) -> str:
        """Query questionable status positive transition filter"""
        return instrument.query(':STATus:QUEStionable:PTR?')

    def set_questionable_ntr(self, instrument, value: int):
        """Set questionable status negative transition filter"""
        instrument.write(f':STATus:QUEStionable:NTR {value}')

    def get_questionable_ntr(self, instrument) -> str:
        """Query questionable status negative transition filter"""
        return instrument.query(':STATus:QUEStionable:NTR?')

    # ========================================================================================
    # :SYSTem Subsystem
    # ========================================================================================

    def get_error(self, instrument) -> str:
        """Query next error in error queue"""
        return instrument.query(':SYSTem:ERRor:NEXT?')

    def get_all_errors(self, instrument) -> str:
        """Query all errors in error queue and clear it"""
        return instrument.query(':SYSTem:ERRor:ALL?')

    def system_preset(self, instrument):
        """Reset signal generator to factory defaults"""
        instrument.write(':SYSTem:PRESet')

    def get_scpi_version(self, instrument) -> str:
        """Query SCPI version compliance"""
        return instrument.query(':SYSTem:VERSion?')

    def lock_front_panel(self, instrument):
        """Lock (disable) front panel controls"""
        instrument.write(':SYSTem:LOCK')

    def unlock_front_panel(self, instrument):
        """Unlock (enable) front panel controls"""
        instrument.write(':SYSTem:LOCK:RELease')

    # ========================================================================================
    # [:SYSTem]:COMMunicate Subsystem
    # ========================================================================================

    def set_lan_config(self, instrument, config: str):
        """Set LAN IP configuration (DHCP|MANual|AUTO)"""
        if config in ['DHCP', 'MANual', 'AUTO']:
            instrument.write(f':SYSTem:COMMunicate:LAN:CONFig {config}')

    def get_lan_config(self, instrument) -> str:
        """Query LAN configuration"""
        return instrument.query(':SYSTem:COMMunicate:LAN:CONFig?')

    def lan_defaults(self, instrument):
        """Restore LAN settings to factory defaults"""
        instrument.write(':SYSTem:COMMunicate:LAN:DEFaults')

    def set_lan_dhcp_timeout(self, instrument, timeout: int):
        """Set DHCP timeout (30|60|90|120 seconds)"""
        if timeout in [30, 60, 90, 120]:
            instrument.write(f':SYSTem:COMMunicate:LAN:DHCP:TIMeout {timeout}')

    def get_lan_dhcp_timeout(self, instrument) -> str:
        """Query DHCP timeout"""
        return instrument.query(':SYSTem:COMMunicate:LAN:DHCP:TIMeout?')

    def set_lan_gateway(self, instrument, ip_address: str):
        """Set LAN gateway IP address (format: nnn.nnn.nnn.nnn)"""
        instrument.write(f':SYSTem:COMMunicate:LAN:GATeway {ip_address}')

    def get_lan_gateway(self, instrument) -> str:
        """Query LAN gateway"""
        return instrument.query(':SYSTem:COMMunicate:LAN:GATeway?')

    def set_lan_hostname(self, instrument, hostname: str):
        """Set LAN hostname (max 29 characters)"""
        if len(hostname) <= 29:
            instrument.write(f':SYSTem:COMMunicate:LAN:HOSTname {hostname}')

    def get_lan_hostname(self, instrument) -> str:
        """Query LAN hostname"""
        return instrument.query(':SYSTem:COMMunicate:LAN:HOSTname?')

    def set_lan_ip(self, instrument, ip_address: str):
        """Set LAN IP address (format: nnn.nnn.nnn.nnn)"""
        instrument.write(f':SYSTem:COMMunicate:LAN:IP {ip_address}')

    def get_lan_ip(self, instrument) -> str:
        """Query LAN IP address"""
        return instrument.query(':SYSTem:COMMunicate:LAN:IP?')

    def lan_restart(self, instrument):
        """Restart network to apply LAN configuration changes"""
        instrument.write(':SYSTem:COMMunicate:LAN:RESTart')

    def set_lan_subnet(self, instrument, subnet_mask: str):
        """Set LAN subnet mask (format: nnn.nnn.nnn.nnn)"""
        instrument.write(f':SYSTem:COMMunicate:LAN:SUBNet {subnet_mask}')

    def get_lan_subnet(self, instrument) -> str:
        """Query LAN subnet mask"""
        return instrument.query(':SYSTem:COMMunicate:LAN:SUBNet?')

    def set_socket_echo(self, instrument, state: str):
        """Turn socket echo on/off (ON|OFF|1|0) - for telnet sessions"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SYSTem:COMMunicate:SOCKet:ECHO {state}')

    def get_socket_echo(self, instrument) -> str:
        """Query socket echo state"""
        return instrument.query(':SYSTem:COMMunicate:SOCKet:ECHO?')

    # ========================================================================================
    # UNIT Subsystem
    # ========================================================================================

    def set_power_unit(self, instrument, unit: str):
        """Set power unit (W|V|DBM|DB)"""
        if unit in ['W', 'V', 'DBM', 'DB']:
            instrument.write(f':UNIT:POWer {unit}')

    def get_power_unit(self, instrument) -> str:
        """Query power unit"""
        return instrument.query(':UNIT:POWer?')

    def set_frequency_unit(self, instrument, unit: str):
        """Set frequency unit (HZ|MHZ|GHZ)"""
        if unit in ['HZ', 'MHZ', 'GHZ']:
            instrument.write(f':UNIT:FREQuency {unit}')

    def get_frequency_unit(self, instrument) -> str:
        """Query frequency unit"""
        return instrument.query(':UNIT:FREQuency?')

    # ========================================================================================
    # Convenience Methods
    # ========================================================================================

    def configure_cw_output(self, instrument, frequency: float, power: float,
                            freq_unit: str = 'MHz', power_unit: str = 'dBm'):
        """
        Convenience method to configure basic CW output

        Args:
            instrument: VISA instrument object
            frequency: Output frequency value
            power: Output power value
            freq_unit: Frequency unit (Hz, MHz, GHz)
            power_unit: Power unit (dBm, W, V, dB)
        """
        self.set_frequency_mode(instrument, 'CW')
        self.set_frequency_cw(instrument, frequency, freq_unit)
        self.set_power_mode(instrument, 'FIXed')
        self.set_power_level(instrument, power, power_unit)
        self.set_output_state(instrument, 'ON')

    def configure_frequency_sweep(self, instrument, start_freq: float, stop_freq: float,
                                  points: int, power: float, spacing: str = 'LINear'):
        """
        Convenience method to configure frequency sweep

        Args:
            instrument: VISA instrument object
            start_freq: Start frequency in Hz
            stop_freq: Stop frequency in Hz
            points: Number of sweep points
            power: Output power in dBm
            spacing: Sweep spacing (LINear or LOGarithmic)
        """
        self.set_frequency_mode(instrument, 'SWEep')
        self.set_frequency_start(instrument, start_freq, 'Hz')
        self.set_frequency_stop(instrument, stop_freq, 'Hz')
        self.set_sweep_points(instrument, points)
        self.set_sweep_spacing(instrument, spacing)
        self.set_power_mode(instrument, 'FIXed')
        self.set_power_level(instrument, power, 'dBm')

    def configure_power_sweep(self, instrument, frequency: float, start_power: float,
                              stop_power: float, points: int):
        """
        Convenience method to configure power sweep

        Args:
            instrument: VISA instrument object
            frequency: Fixed frequency in Hz
            start_power: Start power in dBm
            stop_power: Stop power in dBm
            points: Number of sweep points
        """
        self.set_frequency_mode(instrument, 'CW')
        self.set_frequency_cw(instrument, frequency, 'Hz')
        self.set_power_mode(instrument, 'SWEep')
        self.set_power_start(instrument, start_power, 'dBm')
        self.set_power_stop(instrument, stop_power, 'dBm')
        self.set_sweep_points(instrument, points)

    def configure_am_modulation(self, instrument, mod_freq: float, depth: float,
                                source: str = 'INTernal'):
        """
        Convenience method to configure amplitude modulation

        Args:
            instrument: VISA instrument object
            mod_freq: Modulation frequency in Hz
            depth: Modulation depth (0-0.99)
            source: Modulation source (INTernal or EXTernal)
        """
        self.set_am_source(instrument, source)
        if source == 'INTernal':
            self.set_am_internal_frequency(instrument, mod_freq, 'Hz')
        self.set_am_depth(instrument, depth)
        self.set_am_state(instrument, 'ON')

    def configure_fm_modulation(self, instrument, mod_freq: float, deviation: float,
                                source: str = 'INTernal'):
        """
        Convenience method to configure frequency modulation

        Args:
            instrument: VISA instrument object
            mod_freq: Modulation frequency in Hz
            deviation: Frequency deviation in Hz
            source: Modulation source (INTernal or EXTernal)
        """
        self.set_fm_source(instrument, source)
        if source == 'INTernal':
            self.set_fm_internal_frequency(instrument, mod_freq, 'Hz')
        self.set_fm_deviation(instrument, deviation, 'Hz')
        self.set_fm_state(instrument, 'ON')

    def configure_pulse_modulation(self, instrument, pulse_freq: float, pulse_width: float,
                                   source: str = 'INTernal'):
        """
        Convenience method to configure pulse modulation

        Args:
            instrument: VISA instrument object
            pulse_freq: Pulse frequency in Hz
            pulse_width: Pulse width in seconds
            source: Pulse source (INTernal or EXTernal)
        """
        self.set_pulse_source(instrument, source)
        if source == 'INTernal':
            self.set_pulse_internal_frequency(instrument, pulse_freq, 'Hz')
            self.set_pulse_internal_width(instrument, pulse_width, 's')
        self.set_pulse_state(instrument, 'ON')


# ========================================================================================
# Example Usage
# ========================================================================================

if __name__ == "__main__":
    """
    Example usage of BNC_845M_COMMAND class
    """
    import pyvisa

    # Initialize VISA resource manager
    rm = pyvisa.ResourceManager()

    # Connect to instrument via LAN (VXI-11/VISA)
    # sig_gen = rm.open_resource('TCPIP::192.168.1.100::inst0::INSTR')

    # Or connect via USB
    # sig_gen = rm.open_resource('USB0::0xXXXX::0xXXXX::SERIAL::INSTR')

    # Or connect via GPIB
    # sig_gen = rm.open_resource('GPIB0::10::INSTR')

    # Create command object
    cmd = BNC_845M_COMMAND()

    # Example 1: Basic instrument identification
    # idn = cmd.get_id(sig_gen)
    # print(f"Instrument ID: {idn}")

    # Example 2: Configure basic CW output at 1 GHz, 0 dBm
    # cmd.configure_cw_output(sig_gen, 1000, 0, 'MHz', 'dBm')
    # print("CW output configured: 1 GHz, 0 dBm, RF ON")

    # Example 3: Configure frequency sweep
    # cmd.configure_frequency_sweep(sig_gen,
    #                              start_freq=1e9,    # 1 GHz
    #                              stop_freq=2e9,     # 2 GHz
    #                              points=101,
    #                              power=-10,
    #                              spacing='LINear')
    # cmd.set_output_state(sig_gen, 'ON')
    # print("Frequency sweep configured: 1-2 GHz, 101 points, -10 dBm")

    # Example 4: Configure power sweep
    # cmd.configure_power_sweep(sig_gen,
    #                          frequency=2.4e9,    # 2.4 GHz
    #                          start_power=-20,
    #                          stop_power=0,
    #                          points=41)
    # cmd.set_output_state(sig_gen, 'ON')
    # print("Power sweep configured: 2.4 GHz, -20 to 0 dBm, 41 points")

    # Example 5: Configure AM modulation
    # cmd.set_frequency_cw(sig_gen, 1e9, 'Hz')  # 1 GHz carrier
    # cmd.set_power_level(sig_gen, 0, 'dBm')
    # cmd.configure_am_modulation(sig_gen,
    #                            mod_freq=1000,    # 1 kHz AM
    #                            depth=0.5,        # 50% modulation
    #                            source='INTernal')
    # cmd.set_output_state(sig_gen, 'ON')
    # print("AM modulation configured: 1 kHz, 50% depth")

    # Example 6: Configure FM modulation
    # cmd.set_frequency_cw(sig_gen, 100e6, 'Hz')  # 100 MHz carrier
    # cmd.set_power_level(sig_gen, -10, 'dBm')
    # cmd.configure_fm_modulation(sig_gen,
    #                            mod_freq=10000,      # 10 kHz FM
    #                            deviation=50000,     # 50 kHz deviation
    #                            source='INTernal')
    # cmd.set_output_state(sig_gen, 'ON')
    # print("FM modulation configured: 10 kHz rate, 50 kHz deviation")

    # Example 7: Configure pulse modulation
    # cmd.set_frequency_cw(sig_gen, 5e9, 'Hz')  # 5 GHz carrier
    # cmd.set_power_level(sig_gen, 5, 'dBm')
    # cmd.configure_pulse_modulation(sig_gen,
    #                               pulse_freq=1000,     # 1 kHz pulse rate
    #                               pulse_width=100e-6,  # 100 μs pulse width
    #                               source='INTernal')
    # cmd.set_output_state(sig_gen, 'ON')
    # print("Pulse modulation configured: 1 kHz, 100 μs pulse width")

    # Example 8: Configure list sweep with specific frequencies
    # freq_list = [1e9, 1.5e9, 2e9, 2.5e9, 3e9]  # 5 frequency points
    # power_list = [-10, -5, 0, -5, -10]          # Corresponding powers
    # cmd.set_frequency_mode(sig_gen, 'LIST')
    # cmd.set_list_frequency(sig_gen, freq_list, 'Hz')
    # cmd.set_power_mode(sig_gen, 'LIST')
    # cmd.set_list_power(sig_gen, power_list, 'dBm')
    # cmd.set_list_mode(sig_gen, 'AUTO')
    # cmd.set_output_state(sig_gen, 'ON')
    # print(f"List sweep configured with {len(freq_list)} points")

    # Example 9: Configure triggered sweep
    # cmd.configure_frequency_sweep(sig_gen, 1e9, 2e9, 51, 0)
    # cmd.set_trigger_source(sig_gen, 'EXTernal')
    # cmd.set_trigger_slope(sig_gen, 'POSitive')
    # cmd.set_continuous_sweep(sig_gen, 'OFF')  # Single sweep
    # cmd.initiate(sig_gen)
    # cmd.set_output_state(sig_gen, 'ON')
    # print("Triggered sweep armed: waiting for external trigger")

    # Example 10: Setup external 10 MHz reference
    # cmd.set_reference_source(sig_gen, 'EXTernal')
    # cmd.set_reference_external_frequency(sig_gen, 10)  # 10 MHz
    # locked = cmd.get_reference_locked(sig_gen)
    # print(f"External reference: {locked}")

    # Example 11: Configure LF output generator
    # cmd.set_lf_source(sig_gen, 'LFGenerator')
    # cmd.set_lf_shape(sig_gen, 'SINE')
    # cmd.set_lf_frequency(sig_gen, 1000, 'Hz')  # 1 kHz
    # cmd.set_lf_amplitude(sig_gen, 1.0)          # 1V
    # cmd.set_lf_state(sig_gen, 'ON')
    # print("LF output: 1 kHz sine wave, 1V amplitude")

    # Example 12: Network configuration (LAN setup)
    # cmd.set_lan_config(sig_gen, 'MANual')
    # cmd.set_lan_ip(sig_gen, '192.168.1.100')
    # cmd.set_lan_subnet(sig_gen, '255.255.255.0')
    # cmd.set_lan_gateway(sig_gen, '192.168.1.1')
    # cmd.set_lan_hostname(sig_gen, 'BNC-845M-001')
    # cmd.lan_restart(sig_gen)
    # print("LAN configuration updated")

    # Example 13: Error checking
    # error = cmd.get_error(sig_gen)
    # print(f"Error queue: {error}")

    # Example 14: Save and recall instrument state
    # cmd.save_state(sig_gen, 1)  # Save to register 1
    # print("State saved to register 1")
    # # ... change settings ...
    # cmd.recall_state(sig_gen, 1)  # Recall from register 1
    # print("State recalled from register 1")

    # Example 15: Advanced sweep with custom dwell and delay
    # cmd.set_frequency_mode(sig_gen, 'SWEep')
    # cmd.set_frequency_start(sig_gen, 500e6, 'Hz')
    # cmd.set_frequency_stop(sig_gen, 6e9, 'Hz')
    # cmd.set_sweep_points(sig_gen, 551)
    # cmd.set_sweep_spacing(sig_gen, 'LINear')
    # cmd.set_sweep_dwell(sig_gen, 10e-3, 's')    # 10 ms dwell
    # cmd.set_sweep_delay(sig_gen, 100e-6, 's')   # 100 μs delay
    # cmd.set_power_level(sig_gen, -5, 'dBm')
    # cmd.set_trigger_source(sig_gen, 'IMMediate')
    # cmd.set_continuous_sweep(sig_gen, 'ON')
    # cmd.initiate(sig_gen)
    # cmd.set_output_state(sig_gen, 'ON')
    # print("Advanced sweep running with custom timing")

    # Close connection
    # sig_gen.close()

    print("BNC_845M_COMMAND class initialized successfully")
    print("Please uncomment the example code and connect to your instrument")
    print("\nConnection examples:")
    print("  LAN:  'TCPIP::192.168.1.100::inst0::INSTR'")
    print("  USB:  'USB0::0xXXXX::0xXXXX::SERIAL::INSTR'")
    print("  GPIB: 'GPIB0::10::INSTR'")
    print("\nQuick start:")
    print("  1. Create VISA resource manager: rm = pyvisa.ResourceManager()")
    print("  2. Open instrument: sig_gen = rm.open_resource('YOUR_ADDRESS')")
    print("  3. Create command object: cmd = BNC_845M_COMMAND()")
    print("  4. Use commands: cmd.set_frequency_cw(sig_gen, 1e9, 'Hz')")