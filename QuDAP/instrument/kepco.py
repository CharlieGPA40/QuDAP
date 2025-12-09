class KEPCO_COMMAND:
    """
    KEPCO KLP Series Power Supply SCPI Command Interface
    Based on KLP Developer Guide Revision 4 - Appendix B

    This class provides methods for all SCPI commands supported by the KLP power supply.
    Commands are organized by functional groups: initialization, output control, measurement,
    list programming, status, trigger, virtual models, and system configuration.
    """

    # ==================== IEEE488.2 Common Commands ====================

    def clear(self, instrument):
        """Clear all status registers (*CLS)"""
        instrument.write('*CLS')

    def get_id(self, instrument) -> str:
        """Get instrument identification (*IDN?)"""
        return instrument.query('*IDN?')

    def reset(self, instrument):
        """Reset to default settings (*RST)"""
        instrument.write('*RST')

    def save_state(self, instrument, memory_location: int):
        """Save current settings to memory (1-40) (*SAV)"""
        if 1 <= memory_location <= 40:
            instrument.write(f'*SAV {memory_location}')

    def recall_state(self, instrument, memory_location: int):
        """Recall saved settings from memory (1-40) (*RCL)"""
        if 1 <= memory_location <= 40:
            instrument.write(f'*RCL {memory_location}')

    def get_event_status(self, instrument) -> str:
        """Read event status register (*ESR?)"""
        return instrument.query('*ESR?')

    def set_event_status_enable(self, instrument, value: int):
        """Set event status enable register (*ESE)"""
        instrument.write(f'*ESE {value}')

    def get_event_status_enable(self, instrument) -> str:
        """Query event status enable register (*ESE?)"""
        return instrument.query('*ESE?')

    def get_operation_complete(self, instrument) -> str:
        """Query operation complete (*OPC?)"""
        return instrument.query('*OPC?')

    def set_operation_complete(self, instrument):
        """Set operation complete bit (*OPC)"""
        instrument.write('*OPC')

    def get_options(self, instrument) -> str:
        """Query installed options (*OPT?)"""
        return instrument.query('*OPT?')

    def self_test(self, instrument) -> str:
        """Perform self test (*TST?)"""
        return instrument.query('*TST?')

    def wait(self, instrument):
        """Wait for all pending operations to complete (*WAI)"""
        instrument.write('*WAI')

    def set_service_request_enable(self, instrument, value: int):
        """Set service request enable register (*SRE)"""
        instrument.write(f'*SRE {value}')

    def get_service_request_enable(self, instrument) -> str:
        """Query service request enable register (*SRE?)"""
        return instrument.query('*SRE?')

    def get_status_byte(self, instrument) -> str:
        """Read status byte register (*STB?)"""
        return instrument.query('*STB?')

    def trigger(self, instrument):
        """Send trigger command (*TRG)"""
        instrument.write('*TRG')

    # ==================== Output Control Commands ====================

    def set_output_state(self, instrument, state: str):
        """Set output state (ON|OFF|1|0)"""
        if state.upper() in ['ON', 'OFF', '1', '0']:
            instrument.write(f'OUTP {state}')

    def get_output_state(self, instrument) -> str:
        """Query output state (OUTP?)"""
        return instrument.query('OUTP?')

    # ==================== Voltage Commands ====================

    def set_voltage(self, instrument, voltage: float, unit: str = 'V'):
        """Set voltage (VOLT)"""
        instrument.write(f'VOLT {voltage}{unit}')

    def get_voltage(self, instrument) -> str:
        """Query voltage setting (VOLT?)"""
        return instrument.query('VOLT?')

    def get_voltage_max(self, instrument) -> str:
        """Query maximum voltage (VOLT? MAX)"""
        return instrument.query('VOLT? MAX')

    def get_voltage_min(self, instrument) -> str:
        """Query minimum voltage (VOLT? MIN)"""
        return instrument.query('VOLT? MIN')

    def set_voltage_limit_high(self, instrument, voltage: float, unit: str = 'V'):
        """Set voltage high limit (VOLT:LIM:HIGH)"""
        instrument.write(f'VOLT:LIM:HIGH {voltage}{unit}')

    def get_voltage_limit_high(self, instrument) -> str:
        """Query voltage high limit (VOLT:LIM:HIGH?)"""
        return instrument.query('VOLT:LIM:HIGH?')

    def set_voltage_mode(self, instrument, mode: str):
        """Set voltage mode (FIXED|LIST|TRIG) (VOLT:MODE)"""
        if mode.upper() in ['FIXED', 'FIX', 'LIST', 'TRIG', 'TRIGGERED']:
            instrument.write(f'VOLT:MODE {mode}')

    def get_voltage_mode(self, instrument) -> str:
        """Query voltage mode (VOLT:MODE?)"""
        return instrument.query('VOLT:MODE?')

    def set_voltage_protection(self, instrument, voltage: float, unit: str = 'V'):
        """Set overvoltage protection level (VOLT:PROT)"""
        instrument.write(f'VOLT:PROT {voltage}{unit}')

    def get_voltage_protection(self, instrument) -> str:
        """Query overvoltage protection level (VOLT:PROT?)"""
        return instrument.query('VOLT:PROT?')

    def set_voltage_triggered(self, instrument, voltage: float, unit: str = 'V'):
        """Set triggered voltage level (VOLT:TRIG)"""
        instrument.write(f'VOLT:TRIG {voltage}{unit}')

    def get_voltage_triggered(self, instrument) -> str:
        """Query triggered voltage level (VOLT:TRIG?)"""
        return instrument.query('VOLT:TRIG?')

    # ==================== Current Commands ====================

    def set_current(self, instrument, current: float, unit: str = 'A'):
        """Set current (CURR)"""
        instrument.write(f'CURR {current}{unit}')

    def get_current(self, instrument) -> str:
        """Query current setting (CURR?)"""
        return instrument.query('CURR?')

    def get_current_max(self, instrument) -> str:
        """Query maximum current (CURR? MAX)"""
        return instrument.query('CURR? MAX')

    def get_current_min(self, instrument) -> str:
        """Query minimum current (CURR? MIN)"""
        return instrument.query('CURR? MIN')

    def set_current_limit_high(self, instrument, current: float, unit: str = 'A'):
        """Set current high limit (CURR:LIM:HIGH)"""
        instrument.write(f'CURR:LIM:HIGH {current}{unit}')

    def get_current_limit_high(self, instrument) -> str:
        """Query current high limit (CURR:LIM:HIGH?)"""
        return instrument.query('CURR:LIM:HIGH?')

    def set_current_mode(self, instrument, mode: str):
        """Set current mode (FIXED|LIST|TRIG) (CURR:MODE)"""
        if mode.upper() in ['FIXED', 'FIX', 'LIST', 'TRIG', 'TRIGGERED']:
            instrument.write(f'CURR:MODE {mode}')

    def get_current_mode(self, instrument) -> str:
        """Query current mode (CURR:MODE?)"""
        return instrument.query('CURR:MODE?')

    def set_current_protection(self, instrument, current: float, unit: str = 'A'):
        """Set overcurrent protection level (CURR:PROT)"""
        instrument.write(f'CURR:PROT {current}{unit}')

    def get_current_protection(self, instrument) -> str:
        """Query overcurrent protection level (CURR:PROT?)"""
        return instrument.query('CURR:PROT?')

    def set_current_triggered(self, instrument, current: float, unit: str = 'A'):
        """Set triggered current level (CURR:TRIG)"""
        instrument.write(f'CURR:TRIG {current}{unit}')

    def get_current_triggered(self, instrument) -> str:
        """Query triggered current level (CURR:TRIG?)"""
        return instrument.query('CURR:TRIG?')

    # ==================== Measurement Commands ====================

    def measure_voltage(self, instrument) -> str:
        """Measure actual output voltage (MEAS:VOLT?)"""
        return instrument.query('MEAS:VOLT?')

    def measure_current(self, instrument) -> str:
        """Measure actual output current (MEAS:CURR?)"""
        return instrument.query('MEAS:CURR?')

    # ==================== Function Mode Commands ====================

    def set_function_mode(self, instrument, mode: str):
        """Set function mode (VOLT|CURR) (FUNC:MODE)"""
        if mode.upper() in ['VOLT', 'VOLTAGE', 'CURR', 'CURRENT']:
            instrument.write(f'FUNC:MODE {mode}')

    def get_function_mode(self, instrument) -> str:
        """Query function mode (FUNC:MODE?)"""
        return instrument.query('FUNC:MODE?')

    # ==================== Memory Commands ====================

    def set_memory_location(self, instrument, location: int):
        """Store current settings to memory location 1-40 (MEM:LOC)"""
        if 1 <= location <= 40:
            instrument.write(f'MEM:LOC {location}')

    def get_memory_location(self, instrument, location: int) -> str:
        """Query memory location contents without applying (MEM:LOC?)"""
        if 1 <= location <= 40:
            return instrument.query(f'MEM:LOC? {location}')
        return None

    # ==================== Trigger Commands ====================

    def abort_trigger(self, instrument):
        """Cancel previously armed trigger (ABOR)"""
        instrument.write('ABOR')

    def initiate_trigger(self, instrument):
        """Arm single trigger event (INIT)"""
        instrument.write('INIT')

    def set_initiate_continuous(self, instrument, state: str):
        """Set continuous trigger mode (ON|OFF|1|0) (INIT:CONT)"""
        if state.upper() in ['ON', 'OFF', '1', '0']:
            instrument.write(f'INIT:CONT {state}')

    def get_initiate_continuous(self, instrument) -> str:
        """Query continuous trigger mode (INIT:CONT?)"""
        return instrument.query('INIT:CONT?')

    def set_trigger_source(self, instrument, source: str):
        """Set trigger source (INT|EXT) (TRIG:SOUR)"""
        if source.upper() in ['INT', 'INTERNAL', 'EXT', 'EXTERNAL']:
            instrument.write(f'TRIG:SOUR {source}')

    def get_trigger_source(self, instrument) -> str:
        """Query trigger source (TRIG:SOUR?)"""
        return instrument.query('TRIG:SOUR?')

    # ==================== LIST Programming Commands ====================

    def list_clear(self, instrument):
        """Clear all list entries (LIST:CLE)"""
        instrument.write('LIST:CLE')

    def set_list_control(self, instrument, state: str):
        """Set list relay control (1|0) (LIST:CONT)"""
        if state in ['1', '0', 'ON', 'OFF']:
            instrument.write(f'LIST:CONT {state}')

    def get_list_control(self, instrument) -> str:
        """Query list relay control (LIST:CONT?)"""
        return instrument.query('LIST:CONT?')

    def get_list_control_points(self, instrument) -> str:
        """Query number of control points (LIST:CONT:POIN?)"""
        return instrument.query('LIST:CONT:POIN?')

    def set_list_count(self, instrument, count: int):
        """Set list execution count 0-65535 (LIST:COUN)"""
        if 0 <= count <= 65535:
            instrument.write(f'LIST:COUN {count}')

    def get_list_count(self, instrument) -> str:
        """Query list execution count (LIST:COUN?)"""
        return instrument.query('LIST:COUN?')

    def set_list_count_skip(self, instrument, skip: int):
        """Set number of steps to skip after first iteration (LIST:COUN:SKIP)"""
        if 0 <= skip <= 250:
            instrument.write(f'LIST:COUN:SKIP {skip}')

    def get_list_count_skip(self, instrument) -> str:
        """Query list count skip (LIST:COUN:SKIP?)"""
        return instrument.query('LIST:COUN:SKIP?')

    def set_list_current(self, instrument, *currents):
        """Set list current values (LIST:CURR)

        Args:
            *currents: Up to 250 current values in Amps
        """
        if len(currents) > 0 and len(currents) <= 250:
            values = ','.join([str(c) for c in currents])
            instrument.write(f'LIST:CURR {values}')

    def get_list_current(self, instrument) -> str:
        """Query list current values (LIST:CURR?)"""
        return instrument.query('LIST:CURR?')

    def get_list_current_points(self, instrument) -> str:
        """Query number of current points (LIST:CURR:POIN?)"""
        return instrument.query('LIST:CURR:POIN?')

    def set_list_direction(self, instrument, direction: str):
        """Set list execution direction (UP|DOWN) (LIST:DIR)"""
        if direction.upper() in ['UP', 'DOWN']:
            instrument.write(f'LIST:DIR {direction}')

    def get_list_direction(self, instrument) -> str:
        """Query list direction (LIST:DIR?)"""
        return instrument.query('LIST:DIR?')

    def set_list_dwell(self, instrument, *dwell_times):
        """Set list dwell times (LIST:DWEL)

        Args:
            *dwell_times: Up to 250 dwell times in seconds (0.010 to 655.35)
        """
        if len(dwell_times) > 0 and len(dwell_times) <= 250:
            values = ','.join([str(d) for d in dwell_times])
            instrument.write(f'LIST:DWEL {values}')

    def get_list_dwell(self, instrument) -> str:
        """Query list dwell times (LIST:DWEL?)"""
        return instrument.query('LIST:DWEL?')

    def get_list_dwell_points(self, instrument) -> str:
        """Query number of dwell points (LIST:DWEL:POIN?)"""
        return instrument.query('LIST:DWEL:POIN?')

    def set_list_query(self, instrument, location: int):
        """Set first location for list queries (LIST:QUER)"""
        if 0 <= location <= 250:
            instrument.write(f'LIST:QUER {location}')

    def get_list_query(self, instrument) -> str:
        """Query list query location (LIST:QUER?)"""
        return instrument.query('LIST:QUER?')

    def set_list_voltage(self, instrument, *voltages):
        """Set list voltage values (LIST:VOLT)

        Args:
            *voltages: Up to 250 voltage values in Volts
        """
        if len(voltages) > 0 and len(voltages) <= 250:
            values = ','.join([str(v) for v in voltages])
            instrument.write(f'LIST:VOLT {values}')

    def get_list_voltage(self, instrument) -> str:
        """Query list voltage values (LIST:VOLT?)"""
        return instrument.query('LIST:VOLT?')

    def get_list_voltage_points(self, instrument) -> str:
        """Query number of voltage points (LIST:VOLT:POIN?)"""
        return instrument.query('LIST:VOLT:POIN?')

    # ==================== Status Commands ====================

    def get_operation_condition(self, instrument) -> str:
        """Query operation condition register (STAT:OPER:COND?)"""
        return instrument.query('STAT:OPER:COND?')

    def set_operation_enable(self, instrument, value: int):
        """Set operation enable register (STAT:OPER:ENAB)"""
        instrument.write(f'STAT:OPER:ENAB {value}')

    def get_operation_enable(self, instrument) -> str:
        """Query operation enable register (STAT:OPER:ENAB?)"""
        return instrument.query('STAT:OPER:ENAB?')

    def get_operation_event(self, instrument) -> str:
        """Query operation event register (STAT:OPER?)"""
        return instrument.query('STAT:OPER?')

    def status_preset(self, instrument):
        """Reset status reporting structure (STAT:PRES)"""
        instrument.write('STAT:PRES')

    def get_questionable_event(self, instrument) -> str:
        """Query questionable event register (STAT:QUES?)"""
        return instrument.query('STAT:QUES?')

    def get_questionable_condition(self, instrument) -> str:
        """Query questionable condition register (STAT:QUES:COND?)"""
        return instrument.query('STAT:QUES:COND?')

    def set_questionable_enable(self, instrument, value: int):
        """Set questionable enable register (STAT:QUES:ENAB)"""
        instrument.write(f'STAT:QUES:ENAB {value}')

    def get_questionable_enable(self, instrument) -> str:
        """Query questionable enable register (STAT:QUES:ENAB?)"""
        return instrument.query('STAT:QUES:ENAB?')

    # ==================== System Commands ====================

    def get_system_error(self, instrument) -> str:
        """Query next error in queue (SYST:ERR?)"""
        return instrument.query('SYST:ERR?')

    def get_system_error_code(self, instrument) -> str:
        """Query next error code (SYST:ERR:CODE?)"""
        return instrument.query('SYST:ERR:CODE?')

    def get_system_error_code_all(self, instrument) -> str:
        """Query all error codes (SYST:ERR:CODE:ALL?)"""
        return instrument.query('SYST:ERR:CODE:ALL?')

    def set_keyboard_lock(self, instrument, state: str):
        """Lock/unlock front panel (ON|OFF) (SYST:KLOC)"""
        if state.upper() in ['ON', 'OFF', '1', '0']:
            instrument.write(f'SYST:KLOC {state}')

    def get_keyboard_lock(self, instrument) -> str:
        """Query keyboard lock state (SYST:KLOC?)"""
        return instrument.query('SYST:KLOC?')

    def set_language(self, instrument, language: str):
        """Set display language (ENGLISH|CHINESE|JAPANESE) (SYST:LANG)"""
        if language.upper() in ['ENGLISH', 'CHINESE', 'JAPANESE']:
            instrument.write(f'SYST:LANG {language}')

    def get_language(self, instrument) -> str:
        """Query display language (SYST:LANG?)"""
        return instrument.query('SYST:LANG?')

    def set_system(self, instrument, settings: str):
        """Set system configuration (SYST:SET)"""
        instrument.write(f'SYST:SET {settings}')

    def get_system(self, instrument) -> str:
        """Query system configuration (SYST:SET?)"""
        return instrument.query('SYST:SET?')

    def get_version(self, instrument) -> str:
        """Query SCPI version (SYST:VERS?)"""
        return instrument.query('SYST:VERS?')

    def security_immediate(self, instrument):
        """Execute security immediate command (SYST:SEC:IMM)"""
        instrument.write('SYST:SEC:IMM')

    # ==================== Display Commands ====================

    def get_display_text(self, instrument) -> str:
        """Query front panel display text (DISP:TEXT?)"""
        return instrument.query('DISP:TEXT?')

    # ==================== Communication Commands - GPIB ====================

    def set_gpib_address(self, instrument, address: int):
        """Set GPIB address 1-30 (SYST:COMM:GPIB:ADDR)"""
        if 1 <= address <= 30:
            instrument.write(f'SYST:COMM:GPIB:ADDR {address}')

    def get_gpib_address(self, instrument) -> str:
        """Query GPIB address (SYST:COMM:GPIB:ADDR?)"""
        return instrument.query('SYST:COMM:GPIB:ADDR?')

    # ==================== Communication Commands - LAN (E-Series Only) ====================

    def set_lan_auto(self, instrument, state: str):
        """Set LAN auto configuration (ON|OFF) (SYST:COMM:LAN:AUTO)"""
        if state.upper() in ['ON', 'OFF', '1', '0']:
            instrument.write(f'SYST:COMM:LAN:AUTO {state}')

    def get_lan_auto(self, instrument) -> str:
        """Query LAN auto configuration (SYST:COMM:LAN:AUTO?)"""
        return instrument.query('SYST:COMM:LAN:AUTO?')

    def set_lan_dhcp(self, instrument, state: str):
        """Set DHCP mode (ON|OFF) (SYST:COMM:LAN:DHCP)"""
        if state.upper() in ['ON', 'OFF', '1', '0']:
            instrument.write(f'SYST:COMM:LAN:DHCP {state}')

    def get_lan_dhcp(self, instrument) -> str:
        """Query DHCP mode (SYST:COMM:LAN:DHCP?)"""
        return instrument.query('SYST:COMM:LAN:DHCP?')

    def set_lan_dns(self, instrument, dns_address: str):
        """Set DNS server address (SYST:COMM:LAN:DNS)"""
        instrument.write(f'SYST:COMM:LAN:DNS {dns_address}')

    def get_lan_dns(self, instrument) -> str:
        """Query DNS server address (SYST:COMM:LAN:DNS?)"""
        return instrument.query('SYST:COMM:LAN:DNS?')

    def set_lan_gateway(self, instrument, gateway: str):
        """Set gateway address (SYST:COMM:LAN:GATE)"""
        instrument.write(f'SYST:COMM:LAN:GATE {gateway}')

    def get_lan_gateway(self, instrument) -> str:
        """Query gateway address (SYST:COMM:LAN:GATE?)"""
        return instrument.query('SYST:COMM:LAN:GATE?')

    def set_lan_ip(self, instrument, ip_address: str):
        """Set IP address (SYST:COMM:LAN:IP)"""
        instrument.write(f'SYST:COMM:LAN:IP {ip_address}')

    def get_lan_ip(self, instrument) -> str:
        """Query IP address (SYST:COMM:LAN:IP?)"""
        return instrument.query('SYST:COMM:LAN:IP?')

    def get_lan_mac(self, instrument) -> str:
        """Query MAC address (SYST:COMM:LAN:MAC?)"""
        return instrument.query('SYST:COMM:LAN:MAC?')

    def set_lan_mask(self, instrument, subnet_mask: str):
        """Set subnet mask (SYST:COMM:LAN:MASK)"""
        instrument.write(f'SYST:COMM:LAN:MASK {subnet_mask}')

    def get_lan_mask(self, instrument) -> str:
        """Query subnet mask (SYST:COMM:LAN:MASK?)"""
        return instrument.query('SYST:COMM:LAN:MASK?')

    # ==================== Communication Commands - Serial (Standard Models Only) ====================

    def set_serial_baud(self, instrument, baud_rate: int):
        """Set serial baud rate (SYST:COMM:SER:BAUD)"""
        valid_rates = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        if baud_rate in valid_rates:
            instrument.write(f'SYST:COMM:SER:BAUD {baud_rate}')

    def get_serial_baud(self, instrument) -> str:
        """Query serial baud rate (SYST:COMM:SER:BAUD?)"""
        return instrument.query('SYST:COMM:SER:BAUD?')

    def set_serial_echo(self, instrument, state: str):
        """Set serial echo mode (ON|OFF) (SYST:COMM:SER:ECHO)"""
        if state.upper() in ['ON', 'OFF', '1', '0']:
            instrument.write(f'SYST:COMM:SER:ECHO {state}')

    def get_serial_echo(self, instrument) -> str:
        """Query serial echo mode (SYST:COMM:SER:ECHO?)"""
        return instrument.query('SYST:COMM:SER:ECHO?')

    def set_serial_enable(self, instrument, state: str):
        """Enable/disable serial interface (ON|OFF) (SYST:COMM:SER:ENAB)"""
        if state.upper() in ['ON', 'OFF', '1', '0']:
            instrument.write(f'SYST:COMM:SER:ENAB {state}')

    def get_serial_enable(self, instrument) -> str:
        """Query serial interface enable (SYST:COMM:SER:ENAB?)"""
        return instrument.query('SYST:COMM:SER:ENAB?')

    def set_serial_pace(self, instrument, mode: str):
        """Set serial pacing mode (NONE|XON|XOFF) (SYST:COMM:SER:PACE)"""
        if mode.upper() in ['NONE', 'XON', 'XOFF']:
            instrument.write(f'SYST:COMM:SER:PACE {mode}')

    def get_serial_pace(self, instrument) -> str:
        """Query serial pacing mode (SYST:COMM:SER:PACE?)"""
        return instrument.query('SYST:COMM:SER:PACE?')

    def set_serial_prompt(self, instrument, prompt: str):
        """Set serial prompt string (SYST:COMM:SER:PROM)"""
        instrument.write(f'SYST:COMM:SER:PROM {prompt}')

    def get_serial_prompt(self, instrument) -> str:
        """Query serial prompt string (SYST:COMM:SER:PROM?)"""
        return instrument.query('SYST:COMM:SER:PROM?')

    # ==================== Password Commands ====================

    def password_enable(self, instrument, password: str):
        """Enable password protection with password (SYST:PASS:CEN)"""
        instrument.write(f'SYST:PASS:CEN {password}')

    def password_disable(self, instrument, password: str):
        """Disable password protection with password (SYST:PASS:CDIS)"""
        instrument.write(f'SYST:PASS:CDIS {password}')

    def password_new(self, instrument, old_password: str, new_password: str):
        """Set new password (SYST:PASS:NEW)"""
        instrument.write(f'SYST:PASS:NEW {old_password},{new_password}')

    def get_password_state(self, instrument) -> str:
        """Query password protection state (SYST:PASS:STAT?)"""
        return instrument.query('SYST:PASS:STAT?')

    # ==================== Calibration Commands ====================

    def cal_save(self, instrument):
        """Save calibration data (CAL:SAVE)"""
        instrument.write('CAL:SAVE')

    def get_cal_status(self, instrument) -> str:
        """Query calibration status (CAL:STAT?)"""
        return instrument.query('CAL:STAT?')

    def set_cal_status(self, instrument, state: str):
        """Set calibration mode (ON|OFF) (CAL:STAT)"""
        if state.upper() in ['ON', 'OFF', '1', '0']:
            instrument.write(f'CAL:STAT {state}')


# Example usage
if __name__ == "__main__":
    """
    Example usage of KLP_COMMAND class

    # Initialize connection (using PyVISA)
    import pyvisa
    rm = pyvisa.ResourceManager()
    klp = rm.open_resource('GPIB0::5::INSTR')  # Adjust address as needed

    # Create command interface
    cmd = KLP_COMMAND()

    # Basic operations
    idn = cmd.get_id(klp)
    print(f"Instrument ID: {idn}")

    # Set output
    cmd.set_voltage(klp, 12.5)  # 12.5V
    cmd.set_current(klp, 1.0)   # 1.0A
    cmd.set_output_state(klp, 'ON')

    # Measure
    voltage = cmd.measure_voltage(klp)
    current = cmd.measure_current(klp)
    print(f"Measured: {voltage}V, {current}A")

    # Program a list
    cmd.list_clear(klp)
    cmd.set_list_voltage(klp, 5, 10, 15, 20)
    cmd.set_list_dwell(klp, 1.0, 1.0, 1.0, 1.0)
    cmd.set_list_count(klp, 10)
    cmd.set_voltage_mode(klp, 'LIST')

    # Close
    klp.close()
    """
    print("KLP_COMMAND class loaded successfully")
    print("See docstring for usage examples")