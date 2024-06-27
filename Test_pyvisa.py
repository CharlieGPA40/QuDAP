import pyvisa as visa

rm = visa.ResourceManager('GUI/QDesign/visa_simulation.yaml@sim')
# rm = visa.ResourceManager('@sim')
print(rm.list_resources())
keithley_2182 = rm.open_resource('ASRL4::INSTR',  read_termination='\n')
# print("Keithley")
# keithley_2182 = rm.open_resource('GPIB0::7::INSTR')

# Set timeout to a higher value if necessary
keithley_2182.timeout = 5000  # 5000 ms
# keithley_2182.timeout = 10000  # 5000 m

# Test basic commands
# print(keithley_6221.read())
print(keithley_2182.query("READ?"))
# print(keithley_2182.query('*IDN?'))
