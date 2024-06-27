def run_ETO(self, append_text, progress_update, stop_measurement, keithley_6221, keithley_2182nv, current, TempList,
            topField, botField):
    number_of_current = len(current)
    number_of_temp = len(TempList)
    fieldRate = 220
    tempRate_init = 20
    zeroField = 0
    start_time = time.time()
    append_text('Measurement Start....\n', 'red')

    # Function to convert
    def listToString(s):
        # initialize an empty string
        str1 = " "
        # return string
        return (str1.join(s))

    print(TempList)
    temp_log = ''
    for i in range(len(TempList)):
        temp_log.join(str(TempList[i]))
        print(temp_log)
    print(temp_log)
    append_text('Create Log...!\n', 'green')
    f = open(self.folder_path + 'Experiment_Log.txt', "a")
    today = datetime.today()
    self.formatted_date_csv = today.strftime("%m/%d/%Y")
    f.write(f"Today's Date: {self.formatted_date_csv}\n")
    f.write(f"Sample ID: {self.ID}\n")
    f.write(f"Measurement Type: {self.Measurement}\n")
    f.write(f"Run: {self.run}\n")
    f.write(f"Comment: {self.commemt}\n")
    f.write(f"Experiment Field (Oe): {topField} to {botField}\n")
    f.write(f"Experiment Temperature (K): {temp_log}\n")
    f.write(f"Experiment Current: {listToString(current)}\n")
    f.close()
    # fieldRate = 220
    # fieldRateSweeping = 10

    self.worker.stop()

    def deltaH_chk(currentField):
        if self.ppms_field_One_zone_radio.isChecked():
            deltaH = self.zone1_step_field
        elif self.ppms_field_Two_zone_radio.isChecked():
            if (currentField <= self.zone1_top_field or currentField >= -1 * self.zone1_top_field):
                deltaH = self.zone1_step_field
            elif (currentField > -1 * self.zone2_top_field and currentField <= self.zone2_top_field):
                deltaH = self.zone2_step_field
        elif self.ppms_field_Three_zone_radio.isChecked():
            if (currentField <= self.zone1_top_field or currentField >= -1 * self.zone1_top_field):
                deltaH = self.zone1_step_field
            elif (currentField < self.zone2_top_field and currentField >= -1 * self.zone2_top_field):
                deltaH = self.zone2_step_field
            elif (currentField > -1 * self.zone3_top_field and currentField < self.zone3_top_field):
                deltaH = self.zone3_step_field
        return deltaH

    time.sleep(5)

    # -------------Temp Status---------------------
    temperature, status = self.client.get_temperature()
    tempUnits = self.client.temperature.units
    self.append_text(f'Temperature = {temperature} {tempUnits}\n', 'purple')
    self.ppms_reading_temp_label.setText(f'{temperature} {tempUnits}')
    # ------------Field Status----------------------
    field, status = self.client.get_field()
    fieldUnits = self.client.field.units
    self.log_box.append(f'Field = {field} {fieldUnits}\n')
    self.ppms_reading_field_label.setText(f'{field} {fieldUnits}')

    # ----------------- Loop Down ----------------------#
    Curlen = len(current)
    templen = len(TempList)
    totoal_progress = Curlen * templen
    for i in range(templen):

        self.log_box.append(f'Loop is at {TempList[i]} K Temperature\n')
        Tempsetpoint = TempList[i]
        if i == 0:
            self.client.set_temperature(Tempsetpoint, tempRate_init,
                                        self.client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
        else:
            self.client.set_temperature(Tempsetpoint, tempRate,
                                        self.client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
        self.log_box.append(f'Waiting for {Tempsetpoint} K Temperature\n')
        time.sleep(4)

        MyTemp, sT = self.client.get_temperature()
        self.ppms_reading_temp_label.setText(f'{MyTemp} K')
        while True:
            time.sleep(1)
            MyTemp, sT = self.client.get_temperature()
            self.ppms_reading_temp_label.setText(f'{MyTemp} K')
            self.log_box.append(f'Temperature Status: {sT}\n')
            if sT == 'Stable':
                break
        if i == 0:
            time.sleep(60)
        else:
            time.sleep(300)

        for j in range(Curlen):
            cT = self.client.get_chamber()
            self.ppms_reading_chamber_label.setText(f'{cT}')

            current_progress = int(i * j / totoal_progress)
            self.progress_bar.setValue(current_progress)
            # number_of_current = number_of_current - 1
            self.client.set_field(topField,
                                  fieldRate,
                                  self.client.field.approach_mode.linear,  # linear/oscillate
                                  self.client.field.driven_mode.driven)
            self.log_box.append(f'Waiting for {zeroField} Oe Field \n')
            time.sleep(10)
            while True:
                time.sleep(15)
                F, sF = self.client.get_field()
                self.ppms_reading_field_label.setText(f'{F} Oe')
                self.log_box.append(f'Status: {sF}\n')
                if sF == 'Holding (driven)':
                    break

            self.client.set_field(zeroField,
                                  fieldRate,
                                  self.client.field.approach_mode.oscillate,  # linear/oscillate
                                  self.client.field.driven_mode.driven)
            self.log_box.append(f'Waiting for {zeroField} Oe Field \n')
            time.sleep(10)
            while True:
                time.sleep(15)
                F, sF = self.client.get_field()
                self.ppms_reading_field_label.setText(f'{F} Oe')
                self.log_box.append(f'Status: {sF}\n')
                if sF == 'Holding (driven)':
                    break
            print('logged22')
            keithley_6221.write(":OUTP OFF")  # Set source function to current
            keithley_6221.write("CURRent:RANGe:AUTO ON \n")
            keithley_6221.write(f'CURR {current[j]} \n')
            keithley_6221.write(":OUTP ON")  # Turn on the output
            self.log_box.append(f'DC current is set to: {current_mag[j]} {self.current_unit}')
            csv_filename = f"{self.folder_path}{self.file_name}_{TempList[i]}_K_{current_mag[j]}_{self.current_unit}_Run_{self.run}.csv"
            print(csv_filename)
            print('logged23')
            self.pts = 0
            currentField = topField
            number_of_field_update = number_of_field
            self.field_array = []
            self.channel1_array = []
            self.channel2_array = []
            if self.ppms_field_mode_fixed_radio.isChecked():
                while currentField >= botField:
                    single_measurement_start = time.time()
                    self.log_box.append(f'Loop is at {currentField} Oe Field Up \n')
                    Fieldsetpoint = currentField
                    self.log_box.append(f'Set the field to {Fieldsetpoint} Oe and then collect data \n')
                    self.client.set_field(Fieldsetpoint,
                                          fieldRate,
                                          self.client.field.approach_mode.linear,
                                          self.client.field.driven_mode.driven)
                    self.log_box.append(f'Waiting for {Fieldsetpoint} Oe Field \n')
                    time.sleep(4)
                    MyField, sF = self.client.get_field()
                    self.ppms_reading_field_label.setText(f'{str(MyField)} Oe')
                    while True:
                        time.sleep(1)
                        MyField, sF = self.client.get_field()
                        self.ppms_reading_field_label.setText(f'{F} Oe')
                        self.log_box.append(f'Status: {sF}\n')
                        if sF == 'Holding (driven)':
                            break

                    MyField, sF = self.client.get_field()
                    self.ppms_reading_field_label.setText(f'{MyField} Oe')
                    # ----------------------------- Measure NV voltage -------------------
                    self.log_box.append(f'Saving data for {MyField} Oe \n')

                    keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                    keithley_2182nv.write("VOLT:DC:NPLC 1.2")
                    time.sleep(2)  # Wait for the configuration to complete
                    Chan_1_voltage = 0
                    Chan_2_voltage = 0
                    self.field_array.append(MyField)
                    if self.keithley_2182_channel_1_checkbox.isChecked():
                        keithley_2182nv.write("SENS:CHAN 1")
                        volt = keithley_2182nv.query("READ?")
                        Chan_1_voltage = float(volt)
                        self.keithley_2182_channel_1_reading_label.setText(Chan_1_voltage)
                        self.append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')

                        self.channel1_array.append(Chan_1_voltage)
                        # # Drop off the first y element, append a new one.
                        self.canvas.axes.plot(self.field_array, self.channel1_array, 'black')
                        self.canvas.draw()
                    if self.keithley_2182_channel_2_checkbox.isChecked():
                        keithley_2182nv.write("SENS:CHAN 2")
                        volt2 = keithley_2182nv.query("READ?")
                        Chan_2_voltage = float(volt2)
                        self.keithley_2182_channel_2_reading_label.setText(Chan_2_voltage)
                        self.append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                        self.channel2_array.append(Chan_2_voltage)
                        # # Drop off the first y element, append a new one.
                        self.canvas.axes.plot(self.field_array, self.channel2_array, 'red')
                        self.canvas.draw()

                    # Calculate the average voltage
                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                    resistance_chan_2 = Chan_2_voltage / float(current[j])

                    # Append the data to the CSV file
                    with open(csv_filename, "a", newline="") as csvfile:
                        csv_writer = csv.writer(csvfile)

                        if csvfile.tell() == 0:  # Check if file is empty
                            csv_writer.writerow(
                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                      "Resistance ("
                                                                                                      "Ohm)",
                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                        csv_writer.writerow([MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                             Chan_2_voltage, MyTemp, current[j]])
                        self.log_box.append(f'Data Saved for {MyField} Oe at {MyTemp} K')

                    MyField, sF = self.client.get_field()
                    self.ppms_reading_field_label.setText(f'{MyField} Oe')
                    MyTemp, sT = self.client.get_temperature()
                    self.ppms_reading_temp_label.setText(f'{MyTemp} K')
                    # ----------------------------- Measure NV voltage -------------------
                    deltaH = deltaH_chk(currentField)

                    self.log_box.append(f'deltaH = {deltaH}\n')
                    # Update currentField for the next iteration
                    currentField -= deltaH
                    self.pts += 1  # Number of self.pts count
                    single_measurement_end = time.time()
                    Single_loop = single_measurement_end - single_measurement_start
                    number_of_field_update = number_of_field_update - 1
                    self.log_box.append('Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop))
                    self.log_box.append('Estimated Single measurement (in hrs):  {} s \n'.format(
                        Single_loop * number_of_field / 60 / 60))
                    total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                            number_of_temp - i)
                    totoal_time_in_minutes = total_time_in_seconds / 60
                    total_time_in_hours = totoal_time_in_minutes / 60
                    total_time_in_days = total_time_in_hours / 24
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                            total_time_in_seconds))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                            totoal_time_in_minutes))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                            total_time_in_hours))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} days \n'.format(
                            total_time_in_days))

                # ----------------- Loop Up ----------------------#
                currentField = botField
                while currentField <= topField:
                    single_measurement_start = time.time()
                    self.log_box.append(f'\n Loop is at {currentField} Oe Field Up \n')
                    Fieldsetpoint = currentField

                    self.log_box.append(f'Set the field to {Fieldsetpoint} Oe and then collect data \n')
                    self.client.set_field(Fieldsetpoint,
                                          fieldRate,
                                          self.client.field.approach_mode.linear,
                                          self.client.field.driven_mode.driven)

                    self.log_box.append(f'Waiting for {Fieldsetpoint} Oe Field \n')
                    time.sleep(4)

                    MyField, sF = self.client.get_field()
                    self.ppms_reading_field_label.setText(f'{MyField} Oe')
                    while True:
                        time.sleep(1)
                        MyField, sF = self.client.get_field()
                        self.ppms_reading_field_label.setText(f'{MyField} Oe')
                        self.log_box.append(f'Status: {sF}')
                        if sF == 'Holding (driven)':
                            break

                    MyField, sF = self.client.get_field()
                    self.ppms_reading_field_label.setText(f'{MyField} Oe')

                    # ----------------------------- Measure NV voltage -------------------
                    self.log_box.append(f'Saving data for  {MyField} Oe\n')
                    total_voltage_chan1 = 0.0
                    total_voltage_chan2 = 0.0
                    Chan_1_voltage = 0
                    Chan_2_voltage = 0
                    keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                    keithley_2182nv.write("VOLT:DC:NPLC 1.2")
                    time.sleep(2)  # Wait for the configuration to complete
                    self.field_array.append(MyField)
                    if self.keithley_2182_channel_1_checkbox.isChecked():
                        keithley_2182nv.write("SENS:CHAN 1")
                        volt = keithley_2182nv.query("READ?")
                        Chan_1_voltage = float(volt)
                        self.keithley_2182_channel_1_reading_label.setText(Chan_1_voltage)
                        self.append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                        self.channel1_array.append(Chan_1_voltage)
                        # # Drop off the first y element, append a new one.
                        self.canvas.axes.plot(self.field_array, self.channel1_array, 'black')
                        self.canvas.draw()
                    if self.keithley_2182_channel_2_checkbox.isChecked():
                        keithley_2182nv.write("SENS:CHAN 2")
                        volt2 = keithley_2182nv.query("READ?")
                        Chan_2_voltage = float(volt2)
                        self.keithley_2182_channel_2_reading_label.setText(Chan_2_voltage)
                        self.append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                        self.channel2_array.append(Chan_2_voltage)
                        # # Drop off the first y element, append a new one.
                        self.canvas.axes.plot(self.field_array, self.channel2_array, 'red')
                        self.canvas.draw()
                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                    resistance_chan_2 = Chan_2_voltage / float(current[j])

                    # Append the data to the CSV file
                    with open(csv_filename, "a", newline="") as csvfile:
                        csv_writer = csv.writer(csvfile)

                        if csvfile.tell() == 0:  # Check if file is empty
                            csv_writer.writerow(
                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                      "Resistance ("
                                                                                                      "Ohm)",
                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])
                        MyField, sF = self.client.get_field()
                        self.ppms_reading_field_label.setText(f'{MyField} Oe')
                        MyTemp, sT = self.client.get_temperature()
                        self.ppms_reading_temp_label.setText(f'{MyTemp} K')
                        csv_writer.writerow([MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                             Chan_2_voltage, MyTemp, current[j]])
                        self.log_box.append(f'Data Saved for {MyField} Oe at {MyTemp} K\n')

                    # ----------------------------- Measure NV voltage -------------------
                    deltaH = deltaH_chk(currentField)

                    self.log_box.append(f'deltaH = {deltaH}\n')
                    # Update currentField for the next iteration
                    currentField += deltaH
                    self.pts += 1  # Number of self.pts count
                    single_measurement_end = time.time()
                    Single_loop = single_measurement_end - single_measurement_start
                    number_of_field_update = number_of_field_update - 1
                    total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                            number_of_temp - i)
                    totoal_time_in_minutes = total_time_in_seconds / 60
                    total_time_in_hours = totoal_time_in_minutes / 60
                    total_time_in_days = total_time_in_hours / 24
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                            total_time_in_seconds))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                            totoal_time_in_minutes))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                            total_time_in_hours))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} days \n'.format(
                            total_time_in_days))
            else:
                self.client.set_field(topField,
                                      fieldRate,
                                      self.client.field.approach_mode.linear,
                                      self.client.field.driven_mode.driven)
                self.log_box.append(f'Set the field to {str(topField)} Oe\n')
                MyField, sF = self.client.get_field()
                self.ppms_reading_field_label.setText(f'{str(MyField)} Oe')
                while True:
                    time.sleep(1)
                    MyField, sF = self.client.get_field()
                    self.ppms_reading_field_label.setText(f'{F} Oe')
                    self.log_box.append(f'Status: {sF}\n')
                    if sF == 'Holding (driven)':
                        break
                time.sleep(20)

                while currentField >= botField:
                    self.client.set_field(botField,
                                          fieldRate,
                                          self.client.field.approach_mode.linear,
                                          self.client.field.driven_mode.driven)
                    self.log_box.append(f'Set the field to {str(botField)} Oe and then collect data \n')
                    single_measurement_start = time.time()
                    total_voltage_chan1 = 0.0
                    total_voltage_chan2 = 0.0
                    self.NPLC = self.NPLC_entry.text()
                    keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                    keithley_2182nv.write(f"VOLT:DC:NPLC {self.NPLC}")
                    MyField, sF = self.client.get_field()

                    self.ppms_reading_field_label.setText(f'{MyField} Oe')
                    self.log_box.append(f'Saving data for {MyField} Oe \n')

                    Chan_1_voltage = 0
                    Chan_2_voltage = 0
                    self.field_array.append(MyField)
                    if self.keithley_2182_channel_1_checkbox.isChecked():
                        keithley_2182nv.write("SENS:CHAN 1")
                        volt = keithley_2182nv.query("READ?")
                        Chan_1_voltage = float(volt)
                        self.keithley_2182_channel_1_reading_label.setText(Chan_1_voltage)
                        self.append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                        self.channel1_array.append(Chan_1_voltage)
                        # # Drop off the first y element, append a new one.
                        self.canvas.axes.plot(self.field_array, self.channel1_array, 'black')
                        self.canvas.draw()
                    if self.keithley_2182_channel_2_checkbox.isChecked():
                        keithley_2182nv.write("SENS:CHAN 2")
                        volt2 = keithley_2182nv.query("READ?")
                        Chan_2_voltage = float(volt2)
                        self.keithley_2182_channel_2_reading_label.setText(Chan_2_voltage)
                        self.append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                        self.channel2_array.append(Chan_2_voltage)
                        # # Drop off the first y element, append a new one.
                        self.canvas.axes.plot(self.field_array, self.channel2_array, 'red')
                        self.canvas.draw()

                    # Calculate the average voltage
                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                    resistance_chan_2 = Chan_2_voltage / float(current[j])

                    # Append the data to the CSV file
                    with open(csv_filename, "a", newline="") as csvfile:
                        csv_writer = csv.writer(csvfile)

                        if csvfile.tell() == 0:  # Check if file is empty
                            csv_writer.writerow(
                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                      "Resistance ("
                                                                                                      "Ohm)",
                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                        csv_writer.writerow([MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                             Chan_2_voltage, MyTemp, current[j]])
                        self.log_box.append(f'Data Saved for {MyField} Oe at {MyTemp} K')

                    # ----------------------------- Measure NV voltage -------------------
                    deltaH = deltaH_chk(currentField)

                    self.log_box.append(f'deltaH = {deltaH}\n')
                    # Update currentField for the next iteration
                    currentField -= deltaH
                    self.pts += 1  # Number of self.pts count
                    single_measurement_end = time.time()
                    Single_loop = single_measurement_end - single_measurement_start
                    number_of_field_update = number_of_field_update - 1
                    self.log_box.append(
                        'Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop))
                    self.log_box.append('Estimated Single measurement (in hrs):  {} s \n'.format(
                        Single_loop * number_of_field / 60 / 60))
                    total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                            number_of_temp - i)
                    totoal_time_in_minutes = total_time_in_seconds / 60
                    total_time_in_hours = totoal_time_in_minutes / 60
                    total_time_in_days = total_time_in_hours / 24
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(
                            total_time_in_seconds))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(
                            totoal_time_in_minutes))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(
                            total_time_in_hours))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} days \n'.format(
                            total_time_in_days))

                # ----------------- Loop Up ----------------------#
                currentField = botField
                self.client.set_field(currentField,
                                      fieldRate,
                                      self.client.field.approach_mode.linear,
                                      self.client.field.driven_mode.driven)
                self.log_box.append(f'Set the field to {Fieldsetpoint} Oe and then collect data \n')
                MyField, sF = self.client.get_field()
                self.ppms_reading_field_label.setText(f'{MyField} Oe')
                while True:
                    time.sleep(1)
                    MyField, sF = self.client.get_field()
                    self.ppms_reading_field_label.setText(f'{F} Oe')
                    self.log_box.append(f'Status: {sF}\n')
                    if sF == 'Holding (driven)':
                        break
                time.sleep(20)
                while currentField <= topField:
                    self.client.set_field(topField,
                                          fieldRate,
                                          self.client.field.approach_mode.linear,
                                          self.client.field.driven_mode.driven)
                    self.log_box.append(f'Set the field to {str(botField)} Oe and then collect data \n')
                    single_measurement_start = time.time()
                    total_voltage_chan1 = 0.0
                    total_voltage_chan2 = 0.0
                    self.NPLC = self.NPLC_entry.text()
                    keithley_2182nv.write("SENS:FUNC 'VOLT:DC'")
                    keithley_2182nv.write(f"VOLT:DC:NPLC {self.NPLC}")
                    MyField, sF = self.client.get_field()

                    self.ppms_reading_field_label.setText(f'{MyField} Oe')
                    self.log_box.append(f'Saving data for  {MyField} Oe\n')

                    Chan_1_voltage = 0
                    Chan_2_voltage = 0
                    self.field_array.append(MyField)
                    if self.keithley_2182_channel_1_checkbox.isChecked():
                        keithley_2182nv.write("SENS:CHAN 1")
                        volt = keithley_2182nv.query("READ?")
                        Chan_1_voltage = float(volt)
                        self.keithley_2182_channel_1_reading_label.setText(Chan_1_voltage)
                        self.append_text(f"Channel 1 Voltage: {str(Chan_1_voltage)} V\n", 'green')
                        self.channel1_array.append(Chan_1_voltage)
                        # # Drop off the first y element, append a new one.
                        self.canvas.axes.plot(self.field_array, self.channel1_array, 'black')
                        self.canvas.draw()
                    if self.keithley_2182_channel_2_checkbox.isChecked():
                        keithley_2182nv.write("SENS:CHAN 2")
                        volt2 = keithley_2182nv.query("READ?")
                        Chan_2_voltage = float(volt2)
                        self.keithley_2182_channel_2_reading_label.setText(Chan_2_voltage)
                        self.append_text(f"Channel 2 Voltage: {str(Chan_2_voltage)} V\n", 'green')
                        self.channel2_array.append(Chan_2_voltage)
                        # # Drop off the first y element, append a new one.
                        self.canvas.axes.plot(self.field_array, self.channel2_array, 'red')
                        self.canvas.draw()

                    resistance_chan_1 = Chan_1_voltage / float(current[j])
                    resistance_chan_2 = Chan_2_voltage / float(current[j])
                    # Append the data to the CSV file
                    with open(csv_filename, "a", newline="") as csvfile:
                        csv_writer = csv.writer(csvfile)

                        if csvfile.tell() == 0:  # Check if file is empty
                            csv_writer.writerow(
                                ["Field (Oe)", "Channel 1 Resistance (Ohm)", "Channel 1 Voltage (V)", "Channel 2 "
                                                                                                      "Resistance ("
                                                                                                      "Ohm)",
                                 "Channel 2 Voltage (V)", "Temperature (K)", "Current (A)"])

                        csv_writer.writerow([MyField, resistance_chan_1, Chan_1_voltage, resistance_chan_2,
                                             Chan_2_voltage, MyTemp, current[j]])
                        self.log_box.append(f'Data Saved for {MyField} Oe at {MyTemp} K\n')

                    # ----------------------------- Measure NV voltage -------------------
                    deltaH = deltaH_chk(currentField)

                    self.log_box.append(f'deltaH = {deltaH}\n')
                    # Update currentField for the next iteration
                    currentField += deltaH
                    self.pts += 1  # Number of self.pts count
                    single_measurement_end = time.time()
                    Single_loop = single_measurement_end - single_measurement_start
                    number_of_field_update = number_of_field_update - 1
                    total_time_in_seconds = Single_loop * (number_of_field_update) * (number_of_current - j) * (
                            number_of_temp - i)
                    totoal_time_in_minutes = total_time_in_seconds / 60
                    total_time_in_hours = totoal_time_in_minutes / 60
                    total_time_in_days = total_time_in_hours / 24
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in secs):  {} s'.format(
                            total_time_in_seconds))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} mins'.format(
                            totoal_time_in_minutes))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in hrs):  {} hrs'.format(
                            total_time_in_hours))
                    self.log_box.append(
                        'Estimated Remaining Time for this round of measurement (in mins):  {} days'.format(
                            total_time_in_days))
    self.client.set_field(zeroField,
                          fieldRate,
                          self.client.field.approach_mode.oscillate,  # linear/oscillate
                          self.client.field.driven_mode.driven)
    self.log_box.append('Waiting for Zero Field')

    temperature, status = self.client.get_temperature()
    self.log_box.append(f'Finished Temperature = {temperature} {tempUnits}\n')

    field, status = self.client.get_field()
    fieldUnits = self.client.field.units
    self.append_text(f'Finisehd Field = {field} {fieldUnits}\n', 'red')

    keithley_6221.write(":SOR:CURR:LEV 0")  # Set current level to zero
    keithley_6221.write(":OUTP OFF")  # Turn off the output
    self.append_text("DC current is set to: 0.00 A\n", 'red')
    # keithley_6221_Curr_Src.close()

    # Calculate the total runtime
    end_time = time.time()
    total_runtime = (end_time - start_time) / 3600
    self.log_box.append(f"Total runtime: {total_runtime} hours\n")
    self.log_box.append(f'Total data points: {str(self.pts)} pts\n')