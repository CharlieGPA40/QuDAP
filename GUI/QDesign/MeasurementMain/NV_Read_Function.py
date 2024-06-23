def NV_Read(keithley_2182A_NV, MyField, myTemp, csv_filename, current):

    import pyvisa as visa
    import time
    import csv

    # rm = visa.ResourceManager()
    # keithley_2182A_NV = rm.open_resource("GPIB1::7::INSTR", timeout=10000)

    # Set the measurement parametersCO (DC voltage)
    #keithley_2182A_NV.write("FUNC:VOLT:DC")  # Configure to measure DC voltage
    # keithley_2182A_NV.write("SENS:CHAN 1")
    # keithley_2182A_NV.write("VOLT:DC:NPLC 1.2")  # Set integration time to 10 PLCs (adjust as needed)
    # keithley_2182A_NV.write("SENS:CHAN1:RANG AUTO")
    # keithley_2182A_NV.write("SENS:CHAN2:RANG AUTO")
    # Define the measurement duration
    measurement_duration = 2  # seconds

    # Initialize variables for accumulating readings and counting samples
    total_voltage_chan1 = 0.0
    total_voltage_chan2 = 0.0
    num_samples = 0

    # Measure voltage for the specified duration
    # start_time = time.time()
    # while time.time() - start_time < measurement_duration:

        # Trigger a single measurement and read the result
        # keithley_2182A_NV.write(":INIT")  # Trigger a single measurement
        # time.sleep(1)  # Wait for measurement to complete
        # keithley_2182A_NV.write("SENS:FUNC:VOLT:DC")  # Configure to measure DC voltage
        # keithley_2182A_NV.write("SENS:CHAN 1")
    # time.sleep(2)  # Adjust delay as necessary for proper initialization

    # Initialize and configure the instrument
    keithley_2182A_NV.write("*RST")
    keithley_2182A_NV.write("*CLS")
    time.sleep(2)  # Wait for the reset to complete

    keithley_2182A_NV.write("SENS:FUNC 'VOLT:DC'")
    keithley_2182A_NV.write("VOLT:DC:NPLC 1.2")
    time.sleep(2)  # Wait for the configuration to complete

    keithley_2182A_NV.write("SENS:CHAN 1")
    volt = keithley_2182A_NV.query("READ?")
    Chan_1_voltage = float(volt)
    print(f"Channel 1 Voltage: {Chan_1_voltage} V")

        # keithley_2182A_NV.write("SENS:FUNC:VOLT:DC")  # Configure to measure DC voltage
        # keithley_2182A_NV.write("SENS:CHAN 2")
        # # keithley_2182A_NV.write("SENS:CHAN2:RANG AUTO")
        # Chan_2_voltage = float(keithley_2182A_NV.query("FETCH?"))  # Read the measurement result
    Chan_2_voltage = 0
    total_voltage_chan1 += Chan_1_voltage
    total_voltage_chan2 += Chan_2_voltage
    num_samples += 1


    # Calculate the average voltage
    average_voltage_chan_1 = total_voltage_chan1 / num_samples
    resistance_chan_1 = average_voltage_chan_1/current

    average_voltage_chan_2 = total_voltage_chan2 / num_samples
    resistance_chan_2 = average_voltage_chan_2 / current

    # Append the data to the CSV file
    with open(csv_filename, "a", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)

        if csvfile.tell() == 0:  # Check if file is empty
            csv_writer.writerow(["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                      "Resistance ("
                                                                                                      "Ohm)",
                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])
        csv_writer.writerow([MyField, resistance_chan_1, average_voltage_chan_1, resistance_chan_2,
                             average_voltage_chan_2, myTemp, current])
        print(f'Data Saved for {MyField} Oe at {myTemp} K')

    #return average_voltage

    #print("Average Voltage:", average_voltage, "V")

    # Close the connection when done
    # keithley_2182A_NV.close()
