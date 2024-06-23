import time
import pyvisa as visa

# Initialize the Keithley instrument
rm = visa.ResourceManager()
keithley_6221_Curr_Src = rm.open_resource('GPIB1::13::INSTR')

current = 20e-6
# Set the current to 20 µA
keithley_6221_Curr_Src.write(":SOUR:FUNC CURR")  # Set source function to current
keithley_6221_Curr_Src.write(":SOUR:CURR:MODE FIX")  # Set current mode to fixed
keithley_6221_Curr_Src.write(":SOUR:CURR:LEV {current}")  # Set current level to 20 µA

print("DC current is set to: %f A" % current)

# Enable output
keithley_6221_Curr_Src.write(":OUTP ON")  # Turn on the output

# Wait for 10 seconds
time.sleep(5)

# Set current to zero
keithley_6221_Curr_Src.write(":SOUR:CURR:LEV 0")  # Set current level to zero

# Disable output
keithley_6221_Curr_Src.write(":OUTP OFF")  # Turn off the output

print("DC current is set to: 0.00 A")
# Close the connection
keithley_6221_Curr_Src.close()
