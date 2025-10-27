class RIGOL_COMMAND:
    """
    RIGOL DSA800 Series Spectrum Analyzer Command Class
    Supports models: DSA815, DSA832, DSA875 (and -TG variants)
    """

    # ========================================================================================
    # IEEE488.2 Common Commands
    # ========================================================================================

    def clear(self, instrument):
        """Clear all status registers and error queue"""
        instrument.write('*CLS')

    def get_id(self, instrument) -> str:
        """Get instrument identification
        Returns: Manufacturer, Model, Serial Number, Firmware Version
        """
        return instrument.query('*IDN?')

    def reset(self, instrument):
        """Reset instrument to factory default settings"""
        instrument.write('*RST')

    def get_error(self, instrument) -> str:
        """Query and remove oldest error from error queue
        Returns: error_code,"error_message"
        """
        return instrument.query('*ESR?')

    def operation_complete(self, instrument):
        """Set operation complete flag when current operation finishes"""
        instrument.write('*OPC')

    def query_operation_complete(self, instrument) -> str:
        """Query if current operation is complete
        Returns: 1 if complete, 0 if not
        """
        return instrument.query('*OPC?')

    def trigger(self, instrument):
        """Trigger a single sweep or measurement"""
        instrument.write('*TRG')

    def wait(self, instrument):
        """Wait for all pending operations to complete"""
        instrument.write('*WAI')

    def self_test(self, instrument) -> str:
        """Perform instrument self-test
        Returns: 0 if passed
        """
        return instrument.query('*TST?')

    # ========================================================================================
    # System Commands
    # ========================================================================================

    def get_system_error(self, instrument) -> str:
        """Query and clear system error from error queue
        Returns: error_code,"error_message"
        """
        return instrument.query(':SYSTem:ERRor:NEXT?')

    def preset(self, instrument):
        """Recall preset settings"""
        instrument.write(':SYSTem:PRESet')

    def set_preset_type(self, instrument, preset_type: str):
        """Set preset type (FACTory|USER1|USER2|USER3|USER4|USER5|USER6)"""
        if preset_type in ['FACTory', 'USER1', 'USER2', 'USER3', 'USER4', 'USER5', 'USER6']:
            instrument.write(f':SYSTem:PRESet:TYPE {preset_type}')

    def get_preset_type(self, instrument) -> str:
        """Query preset type"""
        return instrument.query(':SYSTem:PRESet:TYPE?')

    def set_language(self, instrument, language: str):
        """Set system language (ENGLish|CHINese|JAPan|PORTugese|GERMan|POLish|KORea|TCHinese)"""
        if language in ['ENGLish', 'CHINese', 'JAPan', 'PORTugese', 'GERMan', 'POLish', 'KORea', 'TCHinese']:
            instrument.write(f':SYSTem:LANGuage {language}')

    def get_language(self, instrument) -> str:
        """Query system language"""
        return instrument.query(':SYSTem:LANGuage?')

    def set_beeper_state(self, instrument, state: str):
        """Set beeper state for pass/fail test (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SYSTem:BEEPer:STATe {state}')

    def get_beeper_state(self, instrument) -> str:
        """Query beeper state"""
        return instrument.query(':SYSTem:BEEPer:STATe?')

    def get_system_version(self, instrument) -> str:
        """Query SCPI version"""
        return instrument.query(':SYSTem:VERSion?')

    def get_options(self, instrument) -> str:
        """Query installed options"""
        return instrument.query(':SYSTem:OPTions?')

    # ========================================================================================
    # Frequency Control Commands
    # ========================================================================================

    def set_center_frequency(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set center frequency (0 Hz to 7.5 GHz)
        Units: Hz, kHz, MHz, GHz
        """
        instrument.write(f':SENSe:FREQuency:CENTer {frequency}{unit}')

    def get_center_frequency(self, instrument) -> str:
        """Query center frequency in Hz"""
        return instrument.query(':SENSe:FREQuency:CENTer?')

    def set_frequency_span(self, instrument, span: float, unit: str = 'Hz'):
        """Set frequency span (0 Hz to 7.5 GHz)
        Units: Hz, kHz, MHz, GHz
        """
        instrument.write(f':SENSe:FREQuency:SPAN {span}{unit}')

    def get_frequency_span(self, instrument) -> str:
        """Query frequency span in Hz"""
        return instrument.query(':SENSe:FREQuency:SPAN?')

    def set_start_frequency(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set start frequency (0 Hz to 7.5 GHz)"""
        instrument.write(f':SENSe:FREQuency:STARt {frequency}{unit}')

    def get_start_frequency(self, instrument) -> str:
        """Query start frequency in Hz"""
        return instrument.query(':SENSe:FREQuency:STARt?')

    def set_stop_frequency(self, instrument, frequency: float, unit: str = 'Hz'):
        """Set stop frequency (0 Hz to 7.5 GHz)"""
        instrument.write(f':SENSe:FREQuency:STOP {frequency}{unit}')

    def get_stop_frequency(self, instrument) -> str:
        """Query stop frequency in Hz"""
        return instrument.query(':SENSe:FREQuency:STOP?')

    def set_full_span(self, instrument):
        """Set span to maximum (full span)"""
        instrument.write(':SENSe:FREQuency:SPAN:FULL')

    def zoom_in(self, instrument):
        """Zoom in (span = span/2)"""
        instrument.write(':SENSe:FREQuency:SPAN:ZIN')

    def zoom_out(self, instrument):
        """Zoom out (span = span*2)"""
        instrument.write(':SENSe:FREQuency:SPAN:ZOUT')

    def center_frequency_up(self, instrument):
        """Increase center frequency by step size"""
        instrument.write(':SENSe:FREQuency:CENTer:UP')

    def center_frequency_down(self, instrument):
        """Decrease center frequency by step size"""
        instrument.write(':SENSe:FREQuency:CENTer:DOWN')

    def set_center_frequency_step(self, instrument, step: float, unit: str = 'Hz'):
        """Set center frequency step size"""
        instrument.write(f':SENSe:FREQuency:CENTer:STEP:INCRement {step}{unit}')

    def get_center_frequency_step(self, instrument) -> str:
        """Query center frequency step size in Hz"""
        return instrument.query(':SENSe:FREQuency:CENTer:STEP:INCRement?')

    def set_center_frequency_step_auto(self, instrument, state: str):
        """Set auto center frequency step (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:FREQuency:CENTer:STEP:AUTO {state}')

    def get_center_frequency_step_auto(self, instrument) -> str:
        """Query auto center frequency step state"""
        return instrument.query(':SENSe:FREQuency:CENTer:STEP:AUTO?')

    # ========================================================================================
    # Amplitude Control Commands
    # ========================================================================================

    def set_reference_level(self, instrument, level: float, unit: str = 'dBm'):
        """Set reference level (-100 to 20 dBm)
        Units: dBm, dBmV, dBuV, V, W
        """
        instrument.write(f':DISPlay:WINdow:TRACe:Y:SCALe:RLEVel {level}{unit}')

    def get_reference_level(self, instrument) -> str:
        """Query reference level"""
        return instrument.query(':DISPlay:WINdow:TRACe:Y:SCALe:RLEVel?')

    def set_reference_level_offset(self, instrument, offset: float):
        """Set reference level offset (-300 to 300 dB)"""
        instrument.write(f':DISPlay:WINdow:TRACe:Y:SCALe:RLEVel:OFFSet {offset}')

    def get_reference_level_offset(self, instrument) -> str:
        """Query reference level offset"""
        return instrument.query(':DISPlay:WINdow:TRACe:Y:SCALe:RLEVel:OFFSet?')

    def set_attenuation(self, instrument, attenuation: int):
        """Set RF attenuation (0 to 30 dB)"""
        if 0 <= attenuation <= 30:
            instrument.write(f':SENSe:POWer:RF:ATTenuation {attenuation}')

    def get_attenuation(self, instrument) -> str:
        """Query RF attenuation"""
        return instrument.query(':SENSe:POWer:RF:ATTenuation?')

    def set_attenuation_auto(self, instrument, state: str):
        """Set auto attenuation (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:POWer:RF:ATTenuation:AUTO {state}')

    def get_attenuation_auto(self, instrument) -> str:
        """Query auto attenuation state"""
        return instrument.query(':SENSe:POWer:RF:ATTenuation:AUTO?')

    def set_preamp_state(self, instrument, state: str):
        """Set preamplifier state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:POWer:RF:GAIN:STATe {state}')

    def get_preamp_state(self, instrument) -> str:
        """Query preamplifier state"""
        return instrument.query(':SENSe:POWer:RF:GAIN:STATe?')

    def set_scale_per_division(self, instrument, scale: float):
        """Set Y-axis scale per division (0.1 to 20 dB)"""
        instrument.write(f':DISPlay:WINdow:TRACe:Y:SCALe:PDIVision {scale}')

    def get_scale_per_division(self, instrument) -> str:
        """Query Y-axis scale per division"""
        return instrument.query(':DISPlay:WINdow:TRACe:Y:SCALe:PDIVision?')

    def set_amplitude_unit(self, instrument, unit: str):
        """Set amplitude unit (DBM|DBMV|DBUV|V|W)"""
        if unit in ['DBM', 'DBMV', 'DBUV', 'V', 'W']:
            instrument.write(f':UNIT:POWer {unit}')

    def get_amplitude_unit(self, instrument) -> str:
        """Query amplitude unit"""
        return instrument.query(':UNIT:POWer?')

    def auto_scale(self, instrument):
        """Auto scale amplitude display"""
        instrument.write(':SENSe:POWer:ASCale')

    def auto_tune(self, instrument):
        """Auto tune to find and optimize signal"""
        instrument.write(':SENSe:POWer:ATUNe')

    def auto_range(self, instrument):
        """Auto range amplitude settings"""
        instrument.write(':SENSe:POWer:ARANge')

    # ========================================================================================
    # Bandwidth Control Commands
    # ========================================================================================

    def set_resolution_bandwidth(self, instrument, bandwidth: float, unit: str = 'Hz'):
        """Set resolution bandwidth (10 Hz to 1 MHz)
        Units: Hz, kHz, MHz
        """
        instrument.write(f':SENSe:BANDwidth:RESolution {bandwidth}{unit}')

    def get_resolution_bandwidth(self, instrument) -> str:
        """Query resolution bandwidth in Hz"""
        return instrument.query(':SENSe:BANDwidth:RESolution?')

    def set_rbw_auto(self, instrument, state: str):
        """Set auto resolution bandwidth (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:BANDwidth:RESolution:AUTO {state}')

    def get_rbw_auto(self, instrument) -> str:
        """Query auto RBW state"""
        return instrument.query(':SENSe:BANDwidth:RESolution:AUTO?')

    def set_video_bandwidth(self, instrument, bandwidth: float, unit: str = 'Hz'):
        """Set video bandwidth (1 Hz to 3 MHz)
        Units: Hz, kHz, MHz
        """
        instrument.write(f':SENSe:BANDwidth:VIDeo {bandwidth}{unit}')

    def get_video_bandwidth(self, instrument) -> str:
        """Query video bandwidth in Hz"""
        return instrument.query(':SENSe:BANDwidth:VIDeo?')

    def set_vbw_auto(self, instrument, state: str):
        """Set auto video bandwidth (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:BANDwidth:VIDeo:AUTO {state}')

    def get_vbw_auto(self, instrument) -> str:
        """Query auto VBW state"""
        return instrument.query(':SENSe:BANDwidth:VIDeo:AUTO?')

    def set_vbw_to_rbw_ratio(self, instrument, ratio: float):
        """Set VBW/RBW ratio (0.000001 to 30000)"""
        instrument.write(f':SENSe:BANDwidth:VIDeo:RATio {ratio}')

    def get_vbw_to_rbw_ratio(self, instrument) -> str:
        """Query VBW/RBW ratio"""
        return instrument.query(':SENSe:BANDwidth:VIDeo:RATio?')

    # ========================================================================================
    # Sweep Control Commands
    # ========================================================================================

    def set_sweep_time(self, instrument, time: float, unit: str = 's'):
        """Set sweep time (20 us to 7500 s)
        Units: s, ms, us, ks
        """
        instrument.write(f':SENSe:SWEep:TIME {time}{unit}')

    def get_sweep_time(self, instrument) -> str:
        """Query sweep time in seconds"""
        return instrument.query(':SENSe:SWEep:TIME?')

    def set_sweep_time_auto(self, instrument, state: str):
        """Set auto sweep time (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:SWEep:TIME:AUTO {state}')

    def get_sweep_time_auto(self, instrument) -> str:
        """Query auto sweep time state"""
        return instrument.query(':SENSe:SWEep:TIME:AUTO?')

    def set_sweep_points(self, instrument, points: int):
        """Set sweep points (101 to 3001)"""
        if 101 <= points <= 3001:
            instrument.write(f':SENSe:SWEep:POINts {points}')

    def get_sweep_points(self, instrument) -> str:
        """Query sweep points"""
        return instrument.query(':SENSe:SWEep:POINts?')

    def set_continuous_sweep(self, instrument, state: str):
        """Set continuous sweep mode (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':INITiate:CONTinuous {state}')

    def get_continuous_sweep(self, instrument) -> str:
        """Query continuous sweep state"""
        return instrument.query(':INITiate:CONTinuous?')

    def single_sweep(self, instrument):
        """Trigger a single sweep"""
        instrument.write(':INITiate:IMMediate')

    def abort_sweep(self, instrument):
        """Abort current sweep"""
        instrument.write(':ABORt')

    # ========================================================================================
    # Trace Control Commands
    # ========================================================================================

    def set_trace_mode(self, instrument, trace_number: int, mode: str):
        """Set trace mode (trace: 1-3)
        Modes: WRITe, MAXHold, MINHold, VIEW, BLANk, VIDeoavg, POWeravg
        """
        if 1 <= trace_number <= 3 and mode in ['WRITe', 'MAXHold', 'MINHold', 'VIEW', 'BLANk', 'VIDeoavg', 'POWeravg']:
            instrument.write(f':TRACe{trace_number}:MODE {mode}')

    def get_trace_mode(self, instrument, trace_number: int) -> str:
        """Query trace mode (trace: 1-3)"""
        if 1 <= trace_number <= 3:
            return instrument.query(f':TRACe{trace_number}:MODE?')

    def set_trace_average_count(self, instrument, count: int):
        """Set trace average count (1 to 1000)"""
        if 1 <= count <= 1000:
            instrument.write(f':TRACe:AVERage:COUNt {count}')

    def get_trace_average_count(self, instrument) -> str:
        """Query trace average count"""
        return instrument.query(':TRACe:AVERage:COUNt?')

    def get_current_average_count(self, instrument) -> str:
        """Query current average count"""
        return instrument.query(':TRACe:AVERage:COUNt:CURRent?')

    def clear_average(self, instrument):
        """Clear trace average"""
        instrument.write(':TRACe:AVERage:CLEar')

    def reset_average(self, instrument):
        """Reset trace average"""
        instrument.write(':TRACe:AVERage:RESet')

    def set_trace_average_type(self, instrument, trace_number: int, avg_type: str):
        """Set trace average type (trace: 1-3, type: VIDeo|RMS)"""
        if 1 <= trace_number <= 3 and avg_type in ['VIDeo', 'RMS']:
            instrument.write(f':TRACe{trace_number}:AVERage:TYPE {avg_type}')

    def get_trace_average_type(self, instrument, trace_number: int) -> str:
        """Query trace average type"""
        if 1 <= trace_number <= 3:
            return instrument.query(f':TRACe{trace_number}:AVERage:TYPE?')

    def get_trace_data(self, instrument, trace: str) -> str:
        """Read trace data (TRACE1|TRACE2|TRACE3|TRACE4)"""
        if trace in ['TRACE1', 'TRACE2', 'TRACE3', 'TRACE4']:
            return instrument.query(f':TRACe:DATA? {trace}')

    def clear_all_traces(self, instrument):
        """Clear all traces"""
        instrument.write(':TRACe:CLEar:ALL')

    # ========================================================================================
    # Marker Control Commands
    # ========================================================================================

    def set_marker_state(self, instrument, marker_number: int, state: str):
        """Set marker state (marker: 1-4, state: ON|OFF|1|0)"""
        if 1 <= marker_number <= 4 and state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALCulate:MARKer{marker_number}:STATe {state}')

    def get_marker_state(self, instrument, marker_number: int) -> str:
        """Query marker state (marker: 1-4)"""
        if 1 <= marker_number <= 4:
            return instrument.query(f':CALCulate:MARKer{marker_number}:STATe?')

    def set_marker_frequency(self, instrument, marker_number: int, frequency: float, unit: str = 'Hz'):
        """Set marker X position (frequency)"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:X {frequency}{unit}')

    def get_marker_frequency(self, instrument, marker_number: int) -> str:
        """Query marker X position (frequency) in Hz"""
        if 1 <= marker_number <= 4:
            return instrument.query(f':CALCulate:MARKer{marker_number}:X?')

    def get_marker_amplitude(self, instrument, marker_number: int) -> str:
        """Query marker Y value (amplitude)"""
        if 1 <= marker_number <= 4:
            return instrument.query(f':CALCulate:MARKer{marker_number}:Y?')

    def set_marker_mode(self, instrument, marker_number: int, mode: str):
        """Set marker mode (marker: 1-4, mode: POSition|DELTa|BAND|SPAN)"""
        if 1 <= marker_number <= 4 and mode in ['POSition', 'DELTa', 'BAND', 'SPAN']:
            instrument.write(f':CALCulate:MARKer{marker_number}:MODE {mode}')

    def get_marker_mode(self, instrument, marker_number: int) -> str:
        """Query marker mode"""
        if 1 <= marker_number <= 4:
            return instrument.query(f':CALCulate:MARKer{marker_number}:MODE?')

    def marker_peak_search(self, instrument, marker_number: int):
        """Perform peak search with marker"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:MAXimum:MAX')

    def marker_next_peak(self, instrument, marker_number: int):
        """Move marker to next peak"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:MAXimum:NEXT')

    def marker_peak_left(self, instrument, marker_number: int):
        """Move marker to peak on left"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:MAXimum:LEFT')

    def marker_peak_right(self, instrument, marker_number: int):
        """Move marker to peak on right"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:MAXimum:RIGHt')

    def marker_minimum(self, instrument, marker_number: int):
        """Move marker to minimum"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:MINimum')

    def marker_to_center(self, instrument, marker_number: int):
        """Set marker frequency to center frequency"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:SET:CENTer')

    def marker_to_reference_level(self, instrument, marker_number: int):
        """Set marker amplitude to reference level"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:SET:RLEVel')

    def marker_to_start(self, instrument, marker_number: int):
        """Set marker frequency to start frequency"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:SET:STARt')

    def marker_to_stop(self, instrument, marker_number: int):
        """Set marker frequency to stop frequency"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:SET:STOP')

    def peak_to_center(self, instrument, marker_number: int):
        """Peak search and set to center frequency"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:PEAK:SET:CF')

    def set_marker_peak_threshold(self, instrument, marker_number: int, threshold: float):
        """Set marker peak threshold (-200 to 0 dBm)"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:PEAK:THReshold {threshold}')

    def get_marker_peak_threshold(self, instrument, marker_number: int) -> str:
        """Query marker peak threshold"""
        if 1 <= marker_number <= 4:
            return instrument.query(f':CALCulate:MARKer{marker_number}:PEAK:THReshold?')

    def set_marker_peak_excursion(self, instrument, marker_number: int, excursion: float):
        """Set marker peak excursion (0 to 200 dB)"""
        if 1 <= marker_number <= 4:
            instrument.write(f':CALCulate:MARKer{marker_number}:PEAK:EXCursion {excursion}')

    def get_marker_peak_excursion(self, instrument, marker_number: int) -> str:
        """Query marker peak excursion"""
        if 1 <= marker_number <= 4:
            return instrument.query(f':CALCulate:MARKer{marker_number}:PEAK:EXCursion?')

    def set_continuous_peak(self, instrument, marker_number: int, state: str):
        """Set continuous peak search (ON|OFF|1|0)"""
        if 1 <= marker_number <= 4 and state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALCulate:MARKer{marker_number}:CPEak:STATe {state}')

    def get_continuous_peak(self, instrument, marker_number: int) -> str:
        """Query continuous peak search state"""
        if 1 <= marker_number <= 4:
            return instrument.query(f':CALCulate:MARKer{marker_number}:CPEak:STATe?')

    def set_marker_table_state(self, instrument, state: str):
        """Set marker table display (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALCulate:MARKer:TABLe:STATe {state}')

    def get_marker_table_state(self, instrument) -> str:
        """Query marker table state"""
        return instrument.query(':CALCulate:MARKer:TABLe:STATe?')

    def marker_all_off(self, instrument):
        """Turn off all markers"""
        instrument.write(':CALCulate:MARKer:AOFF')

    # Frequency Counter
    def set_frequency_counter_state(self, instrument, state: str):
        """Set frequency counter state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALCulate:MARKer:FCOunt:STATe {state}')

    def get_frequency_counter_state(self, instrument) -> str:
        """Query frequency counter state"""
        return instrument.query(':CALCulate:MARKer:FCOunt:STATe?')

    def get_frequency_counter_value(self, instrument) -> str:
        """Query frequency counter reading in Hz"""
        return instrument.query(':CALCulate:MARKer:FCOunt:X?')

    def set_frequency_counter_resolution(self, instrument, resolution: str):
        """Set frequency counter resolution (1|10|100|1000|10000|100000 Hz)"""
        if resolution in ['1', '10', '100', '1000', '10000', '100000']:
            instrument.write(f':CALCulate:MARKer:FCOunt:RESolution {resolution}')

    def get_frequency_counter_resolution(self, instrument) -> str:
        """Query frequency counter resolution"""
        return instrument.query(':CALCulate:MARKer:FCOunt:RESolution?')

    # ========================================================================================
    # Detector Control Commands
    # ========================================================================================

    def set_detector_type(self, instrument, detector: str):
        """Set detector type
        Types: POSitive, NEGative, NORMal, SAMPle, RMS, VAVerage, QPEak
        """
        if detector in ['POSitive', 'NEGative', 'NORMal', 'SAMPle', 'RMS', 'VAVerage', 'QPEak']:
            instrument.write(f':SENSe:DETector:FUNCtion {detector}')

    def get_detector_type(self, instrument) -> str:
        """Query detector type"""
        return instrument.query(':SENSe:DETector:FUNCtion?')

    # ========================================================================================
    # Trigger Control Commands
    # ========================================================================================

    def set_trigger_source(self, instrument, source: str):
        """Set trigger source (IMMediate|VIDeo|EXTernal)"""
        if source in ['IMMediate', 'VIDeo', 'EXTernal']:
            instrument.write(f':TRIGger:SEQuence:SOURce {source}')

    def get_trigger_source(self, instrument) -> str:
        """Query trigger source"""
        return instrument.query(':TRIGger:SEQuence:SOURce?')

    def set_video_trigger_level(self, instrument, level: float):
        """Set video trigger level (-300 to 50 dBm)"""
        instrument.write(f':TRIGger:SEQuence:VIDeo:LEVel {level}')

    def get_video_trigger_level(self, instrument) -> str:
        """Query video trigger level"""
        return instrument.query(':TRIGger:SEQuence:VIDeo:LEVel?')

    def set_external_trigger_slope(self, instrument, slope: str):
        """Set external trigger slope (POSitive|NEGative)"""
        if slope in ['POSitive', 'NEGative']:
            instrument.write(f':TRIGger:SEQuence:EXTernal:SLOPe {slope}')

    def get_external_trigger_slope(self, instrument) -> str:
        """Query external trigger slope"""
        return instrument.query(':TRIGger:SEQuence:EXTernal:SLOPe?')

    # ========================================================================================
    # Display Control Commands
    # ========================================================================================

    def set_display_enable(self, instrument, state: str):
        """Enable/disable display updates (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':DISPlay:ENABle {state}')

    def get_display_enable(self, instrument) -> str:
        """Query display enable state"""
        return instrument.query(':DISPlay:ENABle?')

    def set_display_brightness(self, instrument, brightness: int):
        """Set display brightness (1 to 10)"""
        if 1 <= brightness <= 10:
            instrument.write(f':DISPlay:BRIGhtness {brightness}')

    def get_display_brightness(self, instrument) -> str:
        """Query display brightness"""
        return instrument.query(':DISPlay:BRIGhtness?')

    def set_y_scale_spacing(self, instrument, spacing: str):
        """Set Y-axis scale type (LINear|LOGarithmic)"""
        if spacing in ['LINear', 'LOGarithmic']:
            instrument.write(f':DISPlay:WINdow:TRACe:Y:SCALe:SPACing {spacing}')

    def get_y_scale_spacing(self, instrument) -> str:
        """Query Y-axis scale type"""
        return instrument.query(':DISPlay:WINdow:TRACe:Y:SCALe:SPACing?')

    def set_x_scale_spacing(self, instrument, spacing: str):
        """Set X-axis scale type (LINear|LOGarithmic)"""
        if spacing in ['LINear', 'LOGarithmic']:
            instrument.write(f':DISPlay:WINdow:TRACe:X:SCALe:SPACing {spacing}')

    def get_x_scale_spacing(self, instrument) -> str:
        """Query X-axis scale type"""
        return instrument.query(':DISPlay:WINdow:TRACe:X:SCALe:SPACing?')

    def set_display_line(self, instrument, amplitude: float):
        """Set display line position (dBm)"""
        instrument.write(f':DISPlay:WINdow:TRACe:Y:DLINe {amplitude}')

    def get_display_line(self, instrument) -> str:
        """Query display line position"""
        return instrument.query(':DISPlay:WINdow:TRACe:Y:DLINe?')

    def set_display_line_state(self, instrument, state: str):
        """Set display line visibility (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':DISPlay:WINdow:TRACe:Y:DLINe:STATe {state}')

    def get_display_line_state(self, instrument) -> str:
        """Query display line state"""
        return instrument.query(':DISPlay:WINdow:TRACe:Y:DLINe:STATe?')

    def set_annotation_clock(self, instrument, state: str):
        """Set time/date display (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':DISPlay:ANNotation:CLOCk:STATe {state}')

    def get_annotation_clock(self, instrument) -> str:
        """Query time/date display state"""
        return instrument.query(':DISPlay:ANNotation:CLOCk:STATe?')

    # ========================================================================================
    # Measurement Functions (Requires Advanced Measurement Option)
    # ========================================================================================

    def configure_channel_power(self, instrument):
        """Enter channel power measurement mode"""
        instrument.write(':CONFigure:CHPower')

    def configure_adjacent_channel_power(self, instrument):
        """Enter adjacent channel power measurement mode"""
        instrument.write(':CONFigure:ACPower')

    def configure_occupied_bandwidth(self, instrument):
        """Enter occupied bandwidth measurement mode"""
        instrument.write(':CONFigure:OBWidth')

    def configure_emission_bandwidth(self, instrument):
        """Enter emission bandwidth measurement mode"""
        instrument.write(':CONFigure:EBWidth')

    def configure_harmonic_distortion(self, instrument):
        """Enter harmonic distortion measurement mode"""
        instrument.write(':CONFigure:HDISt')

    def configure_time_domain_power(self, instrument):
        """Enter time domain power measurement mode"""
        instrument.write(':CONFigure:TPOWer')

    def configure_toi(self, instrument):
        """Enter TOI (third order intercept) measurement mode"""
        instrument.write(':CONFigure:TOI')

    def configure_carrier_to_noise(self, instrument):
        """Enter carrier to noise ratio measurement mode"""
        instrument.write(':CONFigure:CNRatio')

    def configure_spectrum_analyzer(self, instrument):
        """Return to spectrum analyzer mode"""
        instrument.write(':CONFigure:SANalyzer')

    def query_current_measurement(self, instrument) -> str:
        """Query current measurement type"""
        return instrument.query(':CONFigure?')

    # Channel Power Measurement
    def set_channel_power_integration_bw(self, instrument, bandwidth: float, unit: str = 'Hz'):
        """Set channel power integration bandwidth (100 Hz to 7.5 GHz)"""
        instrument.write(f':SENSe:CHPower:BANDwidth:INTegration {bandwidth}{unit}')

    def get_channel_power_integration_bw(self, instrument) -> str:
        """Query channel power integration bandwidth"""
        return instrument.query(':SENSe:CHPower:BANDwidth:INTegration?')

    def set_channel_power_span(self, instrument, span: float, unit: str = 'Hz'):
        """Set channel power measurement span (100 Hz to 7.5 GHz)"""
        instrument.write(f':SENSe:CHPower:FREQuency:SPAN {span}{unit}')

    def get_channel_power_span(self, instrument) -> str:
        """Query channel power measurement span"""
        return instrument.query(':SENSe:CHPower:FREQuency:SPAN?')

    def read_channel_power(self, instrument) -> str:
        """Measure and read channel power (returns: power, density)"""
        return instrument.query(':READ:CHPower?')

    def fetch_channel_power(self, instrument) -> str:
        """Fetch last channel power measurement"""
        return instrument.query(':FETCh:CHPower?')

    # Adjacent Channel Power Measurement
    def set_acp_main_channel_bw(self, instrument, bandwidth: float, unit: str = 'Hz'):
        """Set ACP main channel bandwidth (33 Hz to 2.5 GHz)"""
        instrument.write(f':SENSe:ACPower:BANDwidth:INTegration {bandwidth}{unit}')

    def get_acp_main_channel_bw(self, instrument) -> str:
        """Query ACP main channel bandwidth"""
        return instrument.query(':SENSe:ACPower:BANDwidth:INTegration?')

    def set_acp_adjacent_channel_bw(self, instrument, bandwidth: float, unit: str = 'Hz'):
        """Set ACP adjacent channel bandwidth (33 Hz to 2.5 GHz)"""
        instrument.write(f':SENSe:ACPower:BANDwidth:ACHannel {bandwidth}{unit}')

    def get_acp_adjacent_channel_bw(self, instrument) -> str:
        """Query ACP adjacent channel bandwidth"""
        return instrument.query(':SENSe:ACPower:BANDwidth:ACHannel?')

    def set_acp_channel_spacing(self, instrument, spacing: float, unit: str = 'Hz'):
        """Set ACP channel spacing (33 Hz to 2.5 GHz)"""
        instrument.write(f':SENSe:ACPower:CSPacing {spacing}{unit}')

    def get_acp_channel_spacing(self, instrument) -> str:
        """Query ACP channel spacing"""
        return instrument.query(':SENSe:ACPower:CSPacing?')

    def read_acp(self, instrument) -> str:
        """Measure and read ACP (returns: main, lower, lower_dBc, upper, upper_dBc)"""
        return instrument.query(':READ:ACPower?')

    def fetch_acp(self, instrument) -> str:
        """Fetch last ACP measurement"""
        return instrument.query(':FETCh:ACPower?')

    # Occupied Bandwidth Measurement
    def set_obw_span(self, instrument, span: float, unit: str = 'Hz'):
        """Set occupied bandwidth measurement span (100 Hz to 7.5 GHz)"""
        instrument.write(f':SENSe:OBWidth:FREQuency:SPAN {span}{unit}')

    def get_obw_span(self, instrument) -> str:
        """Query occupied bandwidth span"""
        return instrument.query(':SENSe:OBWidth:FREQuency:SPAN?')

    def set_obw_percent(self, instrument, percent: float):
        """Set occupied bandwidth power percentage (1 to 99.99%)"""
        if 1 <= percent <= 99.99:
            instrument.write(f':SENSe:OBWidth:PERCent {percent}')

    def get_obw_percent(self, instrument) -> str:
        """Query occupied bandwidth percentage"""
        return instrument.query(':SENSe:OBWidth:PERCent?')

    def read_obw(self, instrument) -> str:
        """Measure and read OBW (returns: obw, frequency_error)"""
        return instrument.query(':READ:OBWidth?')

    def fetch_obw(self, instrument) -> str:
        """Fetch last OBW measurement"""
        return instrument.query(':FETCh:OBWidth?')

    # Harmonic Distortion Measurement
    def set_harmonic_number(self, instrument, number: int):
        """Set number of harmonics to measure (2 to 10)"""
        if 2 <= number <= 10:
            instrument.write(f':SENSe:HDISt:NUMBers {number}')

    def get_harmonic_number(self, instrument) -> str:
        """Query number of harmonics"""
        return instrument.query(':SENSe:HDISt:NUMBers?')

    def read_harmonic_distortion(self, instrument) -> str:
        """Measure and read total harmonic distortion percentage"""
        return instrument.query(':READ:HARMonics:DISTortion?')

    def fetch_harmonic_distortion(self, instrument) -> str:
        """Fetch last harmonic distortion measurement"""
        return instrument.query(':FETCh:HARMonics:DISTortion?')

    def read_harmonic_frequencies(self, instrument) -> str:
        """Read all harmonic frequencies"""
        return instrument.query(':READ:HARMonics:FREQuency:ALL?')

    def read_harmonic_amplitudes(self, instrument) -> str:
        """Read all harmonic amplitudes"""
        return instrument.query(':READ:HARMonics:AMPLitude:ALL?')

    def read_fundamental_frequency(self, instrument) -> str:
        """Read fundamental frequency"""
        return instrument.query(':READ:HARMonics:FUNDamental?')

    # Time Domain Power Measurement
    def set_time_power_mode(self, instrument, mode: str):
        """Set time domain power mode (AVERage|PEAK|RMS)"""
        if mode in ['AVERage', 'PEAK', 'RMS']:
            instrument.write(f':SENSe:TPOWer:MODE {mode}')

    def get_time_power_mode(self, instrument) -> str:
        """Query time domain power mode"""
        return instrument.query(':SENSe:TPOWer:MODE?')

    def set_time_power_start_line(self, instrument, time: float, unit: str = 's'):
        """Set time domain power start time"""
        instrument.write(f':SENSe:TPOWer:LLIMit {time}{unit}')

    def get_time_power_start_line(self, instrument) -> str:
        """Query time domain power start time"""
        return instrument.query(':SENSe:TPOWer:LLIMit?')

    def set_time_power_stop_line(self, instrument, time: float, unit: str = 's'):
        """Set time domain power stop time"""
        instrument.write(f':SENSe:TPOWer:RLIMit {time}{unit}')

    def get_time_power_stop_line(self, instrument) -> str:
        """Query time domain power stop time"""
        return instrument.query(':SENSe:TPOWer:RLIMit?')

    def read_time_power(self, instrument) -> str:
        """Measure and read time domain power"""
        return instrument.query(':READ:TPOWer?')

    def fetch_time_power(self, instrument) -> str:
        """Fetch last time domain power measurement"""
        return instrument.query(':FETCh:TPOWer?')

    # ========================================================================================
    # Limit Line / Pass-Fail Test Commands
    # ========================================================================================

    def set_limit_line_state(self, instrument, line_number: int, state: str):
        """Set limit line state (line: 1=lower, 2=upper, state: ON|OFF|1|0)"""
        if line_number in [1, 2] and state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALCulate:LLINe{line_number}:STATe {state}')

    def get_limit_line_state(self, instrument, line_number: int) -> str:
        """Query limit line state"""
        if line_number in [1, 2]:
            return instrument.query(f':CALCulate:LLINe{line_number}:STATe?')

    def set_limit_line_data(self, instrument, line_number: int, data: str):
        """Set limit line data points
        Format: <x>,<y>,<connect>{,<x>,<y>,<connect>}
        x=frequency(Hz), y=amplitude(dBm), connect=0|1
        """
        if line_number in [1, 2]:
            instrument.write(f':CALCulate:LLINe{line_number}:DATA {data}')

    def get_limit_line_data(self, instrument, line_number: int) -> str:
        """Query limit line data"""
        if line_number in [1, 2]:
            return instrument.query(f':CALCulate:LLINe{line_number}:DATA?')

    def delete_limit_line(self, instrument, line_number: int):
        """Delete specified limit line (1=lower, 2=upper)"""
        if line_number in [1, 2]:
            instrument.write(f':CALCulate:LLINe{line_number}:DELete')

    def delete_all_limit_lines(self, instrument):
        """Delete all limit lines"""
        instrument.write(':CALCulate:LLINe:ALL:DELete')

    def get_limit_test_result(self, instrument) -> str:
        """Query pass/fail test result (returns: PASS|FAIL|UNMEAS)"""
        return instrument.query(':CALCulate:LLINe:FAIL?')

    def get_limit_fail_ratio(self, instrument) -> str:
        """Query fail ratio percentage"""
        return instrument.query(':CALCulate:LLINe:FAIL:RATio?')

    def set_limit_stop_on_fail(self, instrument, state: str):
        """Set stop on fail (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALCulate:LLINe:FAIL:STOP:STATe {state}')

    def get_limit_stop_on_fail(self, instrument) -> str:
        """Query stop on fail state"""
        return instrument.query(':CALCulate:LLINe:FAIL:STOP:STATe?')

    def set_limit_line_domain(self, instrument, domain: str):
        """Set limit line X-axis domain (FREQuency|TIME)"""
        if domain in ['FREQuency', 'TIME']:
            instrument.write(f':CALCulate:LLINe:CONTrol:DOMain {domain}')

    def get_limit_line_domain(self, instrument) -> str:
        """Query limit line domain"""
        return instrument.query(':CALCulate:LLINe:CONTrol:DOMain?')

    # ========================================================================================
    # Amplitude Correction Commands
    # ========================================================================================

    def set_all_corrections_state(self, instrument, state: str):
        """Enable/disable all amplitude corrections (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:CORRection:CSET:ALL:STATe {state}')

    def get_all_corrections_state(self, instrument) -> str:
        """Query all corrections state"""
        return instrument.query(':SENSe:CORRection:CSET:ALL:STATe?')

    def set_correction_state(self, instrument, correction_number: int, state: str):
        """Set correction state (correction: 1=antenna, 2=cable, 3=other, 4=user)"""
        if 1 <= correction_number <= 4 and state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:CORRection:CSET{correction_number}:STATe {state}')

    def get_correction_state(self, instrument, correction_number: int) -> str:
        """Query correction state"""
        if 1 <= correction_number <= 4:
            return instrument.query(f':SENSe:CORRection:CSET{correction_number}:STATe?')

    def set_correction_data(self, instrument, correction_number: int, data: str):
        """Set correction data points
        Format: <freq>,<ampl>{,<freq>,<ampl>}
        freq=frequency(Hz), ampl=amplitude(dB)
        """
        if 1 <= correction_number <= 4:
            instrument.write(f':SENSe:CORRection:CSET{correction_number}:DATA {data}')

    def get_correction_data(self, instrument, correction_number: int) -> str:
        """Query correction data"""
        if 1 <= correction_number <= 4:
            return instrument.query(f':SENSe:CORRection:CSET{correction_number}:DATA?')

    def delete_correction(self, instrument, correction_number: int):
        """Delete correction table (1=antenna, 2=cable, 3=other, 4=user)"""
        if 1 <= correction_number <= 4:
            instrument.write(f':SENSe:CORRection:CSET{correction_number}:DELete')

    def delete_all_corrections(self, instrument):
        """Delete all correction tables"""
        instrument.write(':SENSe:CORRection:CSET:ALL:DELete')

    def set_correction_table_state(self, instrument, state: str):
        """Set correction table display (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:CORRection:CSET:TABLe:STATe {state}')

    def get_correction_table_state(self, instrument) -> str:
        """Query correction table display state"""
        return instrument.query(':SENSe:CORRection:CSET:TABLe:STATe?')

    # ========================================================================================
    # Tracking Generator Commands (For -TG Models Only)
    # ========================================================================================

    def set_tracking_generator_output(self, instrument, state: str):
        """Set tracking generator output state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':OUTPut:STATe {state}')

    def get_tracking_generator_output(self, instrument) -> str:
        """Query tracking generator output state"""
        return instrument.query(':OUTPut:STATe?')

    def set_tg_power_level(self, instrument, power: float):
        """Set TG output power level (-40 to 0 dBm)"""
        instrument.write(f':SOURce:POWer:LEVel:IMMediate:AMPLitude {power}')

    def get_tg_power_level(self, instrument) -> str:
        """Query TG output power level"""
        return instrument.query(':SOURce:POWer:LEVel:IMMediate:AMPLitude?')

    def set_tg_power_mode(self, instrument, mode: str):
        """Set TG power mode (FIXed|SWEep)"""
        if mode in ['FIXed', 'SWEep']:
            instrument.write(f':SOURce:POWer:MODE {mode}')

    def get_tg_power_mode(self, instrument) -> str:
        """Query TG power mode"""
        return instrument.query(':SOURce:POWer:MODE?')

    def set_tg_power_offset(self, instrument, offset: float):
        """Set TG power offset (-200 to 200 dB)"""
        instrument.write(f':SOURce:CORRection:OFFSet {offset}')

    def get_tg_power_offset(self, instrument) -> str:
        """Query TG power offset"""
        return instrument.query(':SOURce:CORRection:OFFSet?')

    def set_normalization_state(self, instrument, state: str):
        """Set normalization state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALCulate:NTData:STATe {state}')

    def get_normalization_state(self, instrument) -> str:
        """Query normalization state"""
        return instrument.query(':CALCulate:NTData:STATe?')

    def store_normalization_reference(self, instrument):
        """Store normalization reference trace"""
        instrument.write(':SOURce:TRACe:STORref')

    def set_normalization_reference_display(self, instrument, state: str):
        """Set normalization reference trace display (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SOURce:TRACe:REF:STATe {state}')

    def get_normalization_reference_display(self, instrument) -> str:
        """Query normalization reference trace display state"""
        return instrument.query(':SOURce:TRACe:REF:STATe?')

    # ========================================================================================
    # File Operations Commands
    # ========================================================================================

    def save_state_file(self, instrument, filename: str):
        """Save current state to file (.sta)
        Example: 'E:\\setup.sta' or 'D:\\State0:mysetup.sta'
        """
        instrument.write(f':MMEMory:STORe:STATe 1,\'{filename}\'')

    def load_state_file(self, instrument, filename: str):
        """Load state from file (.sta)"""
        instrument.write(f':MMEMory:LOAD:STATe 1,\'{filename}\'')

    def save_setup_file(self, instrument, filename: str):
        """Save current setup to file (.set)
        Example: 'D:\\Setup0:mysetup.set'
        """
        instrument.write(f':MMEMory:STORe:SETUp \'{filename}\'')

    def load_setup_file(self, instrument, filename: str):
        """Load setup from file (.set)"""
        instrument.write(f':MMEMory:LOAD:SETUp \'{filename}\'')

    def save_trace_file(self, instrument, trace: str, filename: str):
        """Save trace to file (.trc)
        trace: TRACE1|TRACE2|TRACE3|MATH|ALL
        Example: 'D:\\Trace0:data.trc'
        """
        if trace in ['TRACE1', 'TRACE2', 'TRACE3', 'MATH', 'ALL']:
            instrument.write(f':MMEMory:STORe:TRACe {trace},\'{filename}\'')

    def load_trace_file(self, instrument, filename: str):
        """Load trace from file (.trc)"""
        instrument.write(f':MMEMory:LOAD:TRACe \'{filename}\'')

    def save_screenshot(self, instrument, filename: str):
        """Save screenshot to file (.bmp/.jpg/.png)
        Example: 'E:\\screenshot.png'
        """
        instrument.write(f':MMEMory:STORe:SCReen \'{filename}\'')

    def save_limit_line(self, instrument, filename: str):
        """Save limit line to file (.lim)"""
        instrument.write(f':MMEMory:STORe:LIMit \'{filename}\'')

    def load_limit_line(self, instrument, filename: str):
        """Load limit line from file (.lim)"""
        instrument.write(f':MMEMory:LOAD:LIMit \'{filename}\'')

    def save_correction_table(self, instrument, correction_number: int, filename: str):
        """Save correction table to file (.cbl)
        correction: 1=antenna, 2=cable, 3=other, 4=user
        """
        corrections = ['ANTenna', 'CABLe', 'OTHer', 'USER']
        if 1 <= correction_number <= 4:
            instrument.write(f':MMEMory:STORe:CORRection {corrections[correction_number - 1]},\'{filename}\'')

    def load_correction_table(self, instrument, correction_number: int, filename: str):
        """Load correction table from file (.cbl)"""
        corrections = ['ANTenna', 'CABLe', 'OTHer', 'USER']
        if 1 <= correction_number <= 4:
            instrument.write(f':MMEMory:LOAD:CORRection {corrections[correction_number - 1]},\'{filename}\'')

    def delete_file(self, instrument, filename: str):
        """Delete specified file"""
        instrument.write(f':MMEMory:DELete \'{filename}\'')

    def get_disk_information(self, instrument) -> str:
        """Query disk information"""
        return instrument.query(':MMEMory:DISK:INFormation?')

    # ========================================================================================
    # Data Format Commands
    # ========================================================================================

    def set_data_format(self, instrument, format_type: str):
        """Set trace data format (ASCII|REAL)"""
        if format_type in ['ASCII', 'REAL']:
            instrument.write(f':FORMat:TRACe:DATA {format_type}')

    def get_data_format(self, instrument) -> str:
        """Query trace data format"""
        return instrument.query(':FORMat:TRACe:DATA?')

    def set_byte_order(self, instrument, order: str):
        """Set binary data byte order (NORMal|SWAPped)"""
        if order in ['NORMal', 'SWAPped']:
            instrument.write(f':FORMat:BORDer {order}')

    def get_byte_order(self, instrument) -> str:
        """Query byte order"""
        return instrument.query(':FORMat:BORDer?')

    # ========================================================================================
    # Calibration Commands
    # ========================================================================================

    def calibrate(self, instrument):
        """Perform full calibration"""
        instrument.write(':CALibration:ALL')

    def set_auto_calibration(self, instrument, state: str):
        """Set auto calibration state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALibration:AUTO {state}')

    def get_auto_calibration(self, instrument) -> str:
        """Query auto calibration state"""
        return instrument.query(':CALibration:AUTO?')

    # ========================================================================================
    # Demodulation Commands
    # ========================================================================================

    def set_demodulation_type(self, instrument, demod_type: str):
        """Set demodulation type (AM|FM|OFF)"""
        if demod_type in ['AM', 'FM', 'OFF']:
            instrument.write(f':SENSe:DEMod {demod_type}')

    def get_demodulation_type(self, instrument) -> str:
        """Query demodulation type"""
        return instrument.query(':SENSe:DEMod?')

    def set_demodulation_state(self, instrument, state: str):
        """Set demodulation state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:DEMod:STATe {state}')

    def get_demodulation_state(self, instrument) -> str:
        """Query demodulation state"""
        return instrument.query(':SENSe:DEMod:STATe?')

    def set_demodulation_time(self, instrument, time: float, unit: str = 's'):
        """Set demodulation dwell time (5 ms to 1000 s)"""
        instrument.write(f':SENSe:DEMod:TIME {time}{unit}')

    def get_demodulation_time(self, instrument) -> str:
        """Query demodulation dwell time"""
        return instrument.query(':SENSe:DEMod:TIME?')

    def set_speaker_state(self, instrument, state: str):
        """Set speaker/earphone state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SYSTem:SPEaker:STATe {state}')

    def get_speaker_state(self, instrument) -> str:
        """Query speaker state"""
        return instrument.query(':SYSTem:SPEaker:STATe?')

    def set_speaker_volume(self, instrument, volume: int):
        """Set speaker volume (0 to 255)"""
        if 0 <= volume <= 255:
            instrument.write(f':SYSTem:SPEaker:VOLume {volume}')

    def get_speaker_volume(self, instrument) -> str:
        """Query speaker volume"""
        return instrument.query(':SYSTem:SPEaker:VOLume?')

        # ========================================================================================
        # Trace Math Commands
        # ========================================================================================

    def set_trace_math_state(self, instrument, state: str):
        """Set trace math state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':TRACe:MATH:STATe {state}')

    def get_trace_math_state(self, instrument) -> str:
        """Query trace math state"""
        return instrument.query(':TRACe:MATH:STATe?')

    def set_trace_math_type(self, instrument, math_type: str):
        """Set trace math operation (A-B|A+CONST|A-CONST)"""
        if math_type in ['A-B', 'A+CONST', 'A-CONST']:
            instrument.write(f':TRACe:MATH:TYPE {math_type}')

    def get_trace_math_type(self, instrument) -> str:
        """Query trace math type"""
        return instrument.query(':TRACe:MATH:TYPE?')

    def set_trace_math_operand_a(self, instrument, trace: str):
        """Set trace math operand A (T1|T2|T3)"""
        if trace in ['T1', 'T2', 'T3']:
            instrument.write(f':TRACe:MATH:A {trace}')

    def get_trace_math_operand_a(self, instrument) -> str:
        """Query trace math operand A"""
        return instrument.query(':TRACe:MATH:A?')

    def set_trace_math_operand_b(self, instrument, trace: str):
        """Set trace math operand B (T1|T2|T3)"""
        if trace in ['T1', 'T2', 'T3']:
            instrument.write(f':TRACe:MATH:B {trace}')

    def get_trace_math_operand_b(self, instrument) -> str:
        """Query trace math operand B"""
        return instrument.query(':TRACe:MATH:B?')

    def set_trace_math_constant(self, instrument, constant: float):
        """Set trace math constant (-300 to 300 dB)"""
        instrument.write(f':TRACe:MATH:CONSt {constant}')

    def get_trace_math_constant(self, instrument) -> str:
        """Query trace math constant"""
        return instrument.query(':TRACe:MATH:CONSt?')

        # ========================================================================================
        # Peak Table Commands
        # ========================================================================================

    def set_peak_table_state(self, instrument, state: str):
        """Set peak table display (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':TRACe:MATH:PEAK:TABLe:STATe {state}')

    def get_peak_table_state(self, instrument) -> str:
        """Query peak table state"""
        return instrument.query(':TRACe:MATH:PEAK:TABLe:STATe?')

    def set_peak_table_sort(self, instrument, sort_type: str):
        """Set peak table sort (AMPLitude|FREQuency)"""
        if sort_type in ['AMPLitude', 'FREQuency']:
            instrument.write(f':TRACe:MATH:PEAK:SORT {sort_type}')

    def get_peak_table_sort(self, instrument) -> str:
        """Query peak table sort"""
        return instrument.query(':TRACe:MATH:PEAK:SORT?')

    def set_peak_table_threshold(self, instrument, threshold: str):
        """Set peak table threshold mode (NORMal|DLMore|DLLess)"""
        if threshold in ['NORMal', 'DLMore', 'DLLess']:
            instrument.write(f':TRACe:MATH:PEAK:THReshold {threshold}')

    def get_peak_table_threshold(self, instrument) -> str:
        """Query peak table threshold mode"""
        return instrument.query(':TRACe:MATH:PEAK:THReshold?')

    def get_peak_table_data(self, instrument) -> str:
        """Query peak table data (frequency and amplitude pairs)"""
        return instrument.query(':TRACe:MATH:PEAK:DATA?')

    def get_peak_table_points(self, instrument) -> str:
        """Query number of peaks in table (0-10)"""
        return instrument.query(':TRACe:MATH:PEAK:POINts?')

        # ========================================================================================
        # Network Configuration Commands
        # ========================================================================================

    def set_dhcp_state(self, instrument, state: str):
        """Set DHCP state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SYSTem:COMMunicate:LAN:DHCP:STATe {state}')

    def get_dhcp_state(self, instrument) -> str:
        """Query DHCP state"""
        return instrument.query(':SYSTem:COMMunicate:LAN:DHCP:STATe?')

    def set_ip_address(self, instrument, ip_address: str):
        """Set IP address (format: nnn.nnn.nnn.nnn)"""
        instrument.write(f':SYSTem:COMMunicate:LAN:IP:ADDress {ip_address}')

    def get_ip_address(self, instrument) -> str:
        """Query IP address"""
        return instrument.query(':SYSTem:COMMunicate:LAN:IP:ADDress?')

    def set_subnet_mask(self, instrument, mask: str):
        """Set subnet mask (format: nnn.nnn.nnn.nnn)"""
        instrument.write(f':SYSTem:COMMunicate:LAN:IP:SUBMask {mask}')

    def get_subnet_mask(self, instrument) -> str:
        """Query subnet mask"""
        return instrument.query(':SYSTem:COMMunicate:LAN:IP:SUBMask?')

    def set_gateway(self, instrument, gateway: str):
        """Set default gateway (format: nnn.nnn.nnn.nnn)"""
        instrument.write(f':SYSTem:COMMunicate:LAN:IP:GATeway {gateway}')

    def get_gateway(self, instrument) -> str:
        """Query default gateway"""
        return instrument.query(':SYSTem:COMMunicate:LAN:IP:GATeway?')

    def set_dns_server(self, instrument, dns: str):
        """Set DNS server (format: nnn.nnn.nnn.nnn)"""
        instrument.write(f':SYSTem:COMMunicate:LAN:IP:DNSServer {dns}')

    def get_dns_server(self, instrument) -> str:
        """Query DNS server"""
        return instrument.query(':SYSTem:COMMunicate:LAN:IP:DNSServer?')

    def reset_lan_settings(self, instrument):
        """Reset LAN settings to default"""
        instrument.write(':SYSTem:COMMunicate:LAN:RESet')

    def set_gpib_address(self, instrument, address: int):
        """Set GPIB address (0 to 30)"""
        if 0 <= address <= 30:
            instrument.write(f':SYSTem:COMMunicate:GPIB:SELF:ADDRess {address}')

    def get_gpib_address(self, instrument) -> str:
        """Query GPIB address"""
        return instrument.query(':SYSTem:COMMunicate:GPIB:SELF:ADDRess?')

        # ========================================================================================
        # Measurement Average Commands
        # ========================================================================================

    def set_measurement_average_state(self, instrument, measurement: str, state: str):
        """Set measurement average state (ON|OFF|1|0)
        measurement: CHPower|ACPower|OBWidth|EBWidth|HDISt|TPOWer|TOI|CNRatio
        """
        measurements = ['CHPower', 'ACPower', 'OBWidth', 'EBWidth', 'HDISt', 'TPOWer', 'TOI', 'CNRatio']
        if measurement in measurements and state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':SENSe:{measurement}:AVERage:STATe {state}')

    def get_measurement_average_state(self, instrument, measurement: str) -> str:
        """Query measurement average state"""
        return instrument.query(f':SENSe:{measurement}:AVERage:STATe?')

    def set_measurement_average_count(self, instrument, measurement: str, count: int):
        """Set measurement average count (1 to 1000)"""
        if 1 <= count <= 1000:
            instrument.write(f':SENSe:{measurement}:AVERage:COUNt {count}')

    def get_measurement_average_count(self, instrument, measurement: str) -> str:
        """Query measurement average count"""
        return instrument.query(f':SENSe:{measurement}:AVERage:COUNt?')

    def set_measurement_average_type(self, instrument, measurement: str, avg_type: str):
        """Set measurement average type (EXPonential|REPeat)"""
        if avg_type in ['EXPonential', 'REPeat']:
            instrument.write(f':SENSe:{measurement}:AVERage:TCONtrol {avg_type}')

    def get_measurement_average_type(self, instrument, measurement: str) -> str:
        """Query measurement average type"""
        return instrument.query(f':SENSe:{measurement}:AVERage:TCONtrol?')

        # ========================================================================================
        # Utility Commands
        # ========================================================================================

    def set_date(self, instrument, year: int, month: int, day: int):
        """Set system date (year: 2000-2099, month: 1-12, day: 1-31)"""
        instrument.write(f':SYSTem:DATE {year},{month:02d},{day:02d}')

    def get_date(self, instrument) -> str:
        """Query system date (format: YYYY,MM,DD)"""
        return instrument.query(':SYSTem:DATE?')

    def set_time(self, instrument, hour: int, minute: int, second: int):
        """Set system time (hour: 0-23, minute: 0-59, second: 0-59)"""
        instrument.write(f':SYSTem:TIME {hour:02d},{minute:02d},{second:02d}')

    def get_time(self, instrument) -> str:
        """Query system time (format: HH,MM,SS)"""
        return instrument.query(':SYSTem:TIME?')

    def set_signal_tracking(self, instrument, state: str):
        """Set signal tracking state (ON|OFF|1|0)"""
        if state in ['ON', 'OFF', '1', '0']:
            instrument.write(f':CALCulate:MARKer:TRACking:STATe {state}')

    def get_signal_tracking(self, instrument) -> str:
        """Query signal tracking state"""
        return instrument.query(':CALCulate:MARKer:TRACking:STATe?')

    def set_n_db_bandwidth(self, instrument, n_value: float):
        """Set N dB bandwidth value (-100 to 100 dB)"""
        instrument.write(f':CALCulate:BANDwidth:NDB {n_value}')

    def get_n_db_bandwidth(self, instrument) -> str:
        """Query N dB bandwidth value"""
        return instrument.query(':CALCulate:BANDwidth:NDB?')

    def get_n_db_bandwidth_result(self, instrument) -> str:
        """Query N dB bandwidth measurement result in Hz"""
        return instrument.query(':CALCulate:BANDwidth:RESult?')

    def couple_parameters(self, instrument, coupling: str):
        """Set parameter coupling (ALL|NONE)"""
        if coupling in ['ALL', 'NONE']:
            instrument.write(f':COUPle {coupling}')

    def get_coupling(self, instrument) -> str:
        """Query parameter coupling state"""
        return instrument.query(':COUPle?')

    def set_input_impedance(self, instrument, impedance: int):
        """Set input impedance (50|75 Ohm)"""
        if impedance in [50, 75]:
            instrument.write(f':INPut:IMPedance {impedance}')

    def get_input_impedance(self, instrument) -> str:
        """Query input impedance"""
        return instrument.query(':INPut:IMPedance?')

    def get_configuration_info(self, instrument) -> str:
        """Query system configuration information"""
        return instrument.query(':SYSTem:CONFigure:INFormation?')

        # ========================================================================================
        # Status Register Commands
        # ========================================================================================

    def set_operation_enable(self, instrument, value: int):
        """Set operation status enable register"""
        instrument.write(f':STATus:OPERation:ENABle {value}')

    def get_operation_enable(self, instrument) -> str:
        """Query operation status enable register"""
        return instrument.query(':STATus:OPERation:ENABle?')

    def get_operation_condition(self, instrument) -> str:
        """Query operation status condition register"""
        return instrument.query(':STATus:OPERation:CONDition?')

    def get_operation_event(self, instrument) -> str:
        """Query operation status event register"""
        return instrument.query(':STATus:OPERation:EVENt?')

    def set_questionable_enable(self, instrument, value: int):
        """Set questionable status enable register"""
        instrument.write(f':STATus:QUEStionable:ENABle {value}')

    def get_questionable_enable(self, instrument) -> str:
        """Query questionable status enable register"""
        return instrument.query(':STATus:QUEStionable:ENABle?')

    def get_questionable_condition(self, instrument) -> str:
        """Query questionable status condition register"""
        return instrument.query(':STATus:QUEStionable:CONDition?')

    def get_questionable_event(self, instrument) -> str:
        """Query questionable status event register"""
        return instrument.query(':STATus:QUEStionable:EVENt?')

    def preset_status(self, instrument):
        """Preset status registers"""
        instrument.write(':STATus:PRESet')

# ========================================================================================
# Example Usage
# ========================================================================================

if __name__ == "__main__":
    """
    Example usage of DSA800_COMMAND class
    """
    import pyvisa

    # Initialize VISA resource manager
    rm = pyvisa.ResourceManager()

    # Connect to instrument (USB example)
    # dsa = rm.open_resource('USB0::0x1AB1::0x0960::DSA8xxxxxxxx::INSTR')

    # Or connect via LAN
    # dsa = rm.open_resource('TCPIP0::192.168.1.100::INST0::INSTR')

    # For demonstration, we'll use a placeholder
    # Uncomment the line above with your actual instrument address

    # Create command object
    cmd = COMMAND()

    # Example 1: Basic instrument identification
    # idn = cmd.get_id(dsa)
    # print(f"Instrument ID: {idn}")

    # Example 2: Configure basic spectrum measurement
    # cmd.reset(dsa)
    # cmd.set_center_frequency(dsa, 2.4, 'GHz')
    # cmd.set_frequency_span(dsa, 100, 'MHz')
    # cmd.set_resolution_bandwidth(dsa, 100, 'kHz')
    # cmd.set_reference_level(dsa, 0)

    # Example 3: Marker operations
    # cmd.set_marker_state(dsa, 1, 'ON')
    # cmd.marker_peak_search(dsa, 1)
    # freq = cmd.get_marker_frequency(dsa, 1)
    # ampl = cmd.get_marker_amplitude(dsa, 1)
    # print(f"Peak at {freq} Hz: {ampl} dBm")

    # Example 4: Trace control
    # cmd.set_trace_mode(dsa, 1, 'MAXHold')
    # cmd.set_continuous_sweep(dsa, 'ON')

    # Example 5: Channel power measurement (requires option)
    # cmd.configure_channel_power(dsa)
    # cmd.set_channel_power_integration_bw(dsa, 200, 'kHz')
    # result = cmd.read_channel_power(dsa)
    # print(f"Channel power: {result}")

    # Example 6: Save screenshot
    # cmd.save_screenshot(dsa, 'E:\\measurement.png')

    # Close connection
    # dsa.close()

    print("DSA800_COMMAND class initialized successfully")
    print("Please uncomment the example code and connect to your instrument")