import pyvisa as visa
import time

# Create a Visa Resource Manager
rm = visa.ResourceManager()

# Open a connection to the Keithley 2182A using its GPIB address
keithley_2182A_NV = rm.open_resource("GPIB1::7::INSTR", timeout=10000)

# Set the measurement parameters (DC voltage)
keithley_2182A_NV.write("CONF:VOLT:DC")  # Configure to measure DC voltage
keithley_2182A_NV.write("VOLT:DC:NPLC 10")  # Set integration time to 10 PLCs (adjust as needed)

# Define the measurement duration
measurement_duration = 2  # seconds

# Initialize variables for accumulating readings and counting samples
total_voltage = 0.0
num_samples = 0

# Measure voltage for the specified duration
start_time = time.time()
while time.time() - start_time < measurement_duration:
    # Trigger a single measurement and read the result
    keithley_2182A_NV.write("INIT")  # Trigger a single measurement
    time.sleep(1)  # Wait for measurement to complete
    voltage = float(keithley_2182A_NV.query("FETCH?"))  # Read the measurement result
    total_voltage += voltage
    num_samples += 1

# Calculate the average voltage
average_voltage = total_voltage / num_samples

print("Average Voltage:", average_voltage, "V")

# Close the connection when done
keithley_2182A_NV.close()
