# ========================================================= #
# --------- Developed by Chunli Tang---------- #
# ========================================================= #

import time
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pyvisa as visa
import MultiPyVu
import sys
import math

import MultiPyVu as mpv


# ========================================================= #
# ---------Open Dynacool MuliVu (Don't run as Admin)-------- #
# ========================================================= #
start_time = time.time()
rm = visa.ResourceManager()  # Open a VISA resource manager pointing to the installation folder for the Keysight Visa libraries.
# Nanovoltmeter
keithley_2182A_NV = rm.open_resource("GPIB1::7::INSTR", timeout=10000)
time.sleep(2)
# Current Source
keithley_6221_Curr_Src = rm.open_resource('GPIB1::13::INSTR')
time.sleep(2)
# PPMS
host = "127.0.0.1"
port = 5000

# =============================== Set the current ==================================== #
current = [f"{i}e-6" for i in range(40, 60, 20)]   # Set the current to 20 µA
number_of_current = len(current)

# =============================== Set Temperature ==================================== #
TempList = [10, 50, 100, 150, 200, 250, 300]
CurTemp = 10
StepTemp = 10
FinalTemp = 300  # Next temperature set in the end
number_of_temp = len(TempList)

# =============================== Setup the Field ==================================== #

# ||-----deltaH_large------||--deltaH_med---||--------------deltaH_small-----------------||------deltaH_med---||-------deltaH_large---||
# botField ------------ -B2 ----------- -B1 ------------- zeroField --------------- +B1 ---------------- +B2--------------- topField

topField = 6000
zeroField = 0
botField = -6000
deltaH = 40
fieldRate = 220
fieldRateSlow = 10
tempRate = 50
number_of_field = 2*(topField-botField)/deltaH

# ---------------- Set the File Name -----------------------#



def save_temp_field_chamber():
    T, sT = client.get_temperature()
    F, sF = client.get_field()
    C = client.get_chamber()
    print(f'{T:{7}.{3}f} {sT:{10}} {F:{7}} {sF:{20}} {C:{15}}')

# def deltaH_chk(deltaH_small, deltaH_med, deltaH_large, currentField):
#     if (currentField <= LowerB2 or currentField >= UpperB2):
#         deltaH = deltaH_large
#
#     elif (currentField > LowerB2 and currentField <= LowerB1):
#         deltaH = deltaH_med
#
#     elif (currentField < UpperB2 and currentField >= UpperB1):
#         deltaH = deltaH_med
#
#     elif (currentField > LowerB1 and currentField < UpperB1):
#         deltaH = deltaH_small
#
#     return deltaH

# ---------------- Start Measurement -----------------------#
# Start the server.
with mpv.Server() as server:
    # start the client
    with mpv.Client() as client:
        # Allow the connection to complete initialization
        time.sleep(5)

        # -------------Temp Status---------------------
        temperature, status = client.get_temperature()
        tempUnits = client.temperature.units
        print(f'\nTemperature = {temperature} {tempUnits}')

        # ------------Field Status----------------------
        field, status = client.get_field()
        fieldUnits = client.field.units
        print(f'Field = {field} {fieldUnits}')

        # ------------Purge/Seal------------------------
        if temperature == 300 and field == 0:
            # Purge/Seal the chamber; wait to continue
            print('Change the chamber state to Purge/Seal')
            client.set_chamber(client.chamber.mode.purge_seal)
            # client.wait_for(10, 0, client.subsystem.chamber)

        # ---------------print a header----------------
        print('')
        hdr = '______ T ______     __________ H __________\t______ Chamber Status ______'
        print(hdr)
        save_temp_field_chamber()

        # # ----------------------- Set Temperature-------------------------------------
        # CurrentTemp, sT = client.get_temperature()
        # #points = 10
        #
        # setpoint = 1.775 #1.7 K Setpoint
        # tempRate = 50
        #
        # wait = abs(CurrentTemp-setpoint)/tempRate*60
        # message = f'Set the temperature {setpoint} K at {tempRate} K rate '
        # message += f'wait {wait} seconds'
        # print('')
        # print(message)
        # print('')
        # client.set_temperature(setpoint,
        #                        tempRate,
        #                        client.temperature.approach_mode.fast_settle) #fast_settle/no_overshoot
        # #for t in range(points):
        # save_temp_field_chamber()
        # #time.sleep(wait)
        # client.wait_for(wait, 0, client.temperature.waitfor)
        # save_temp_field_chamber()

        # ----------------------------------------------------------------------------------#
        # -------------------------------- Main Field Loop ---------------------------------#
        # currentField = 0
        # MaxField = 2000 #Oe
        # i = 0

        rm = visa.ResourceManager()
        keithley_2182A_NV = rm.open_resource("GPIB1::7::INSTR", timeout=10000)
        print(f'\n Waiting for {zeroField} Oe Field \n')
        time.sleep(10)
        # client.wait_for(30,
        #                 timeout_sec=100,
        #                 bitmask=client.field.waitfor)
        # save_temp_field_chamber()

        # ----------------- Loop Down ----------------------#
        Curlen = len(current)
        templen = len(TempList)
        
        for i in range(templen):
            # number_of_temp = number_of_temp - 1
            print(f'\n Loop is at {TempList[i]} K Temperature\n')
            Tempsetpoint = TempList[i]
            client.set_temperature(Tempsetpoint,
                                    tempRate,
                                    client.temperature.approach_mode.fast_settle) #fast_settle/no_overshoot
            print(f'Waiting for {Tempsetpoint} K Temperature')
            time.sleep(4)

            MyTemp, sT = client.get_temperature()
            while True:
                time.sleep(1)
                MyTemp, sT = client.get_temperature()
                print(f'Status: {sT}')
                if sT == 'Stable':
                    break

            for j in range(Curlen):
                # number_of_current = number_of_current - 1
                    
                
                client.set_field(topField,
                                 fieldRate,
                                 client.field.approach_mode.linear,  # linear/oscillate
                                 client.field.driven_mode.driven)
                print(f'\n Waiting for {zeroField} Oe Field \n')
                time.sleep(10)
                while True:
                    time.sleep(15)
                    F, sF = client.get_field()
                    print(f'Status: {sF}')
                    if sF == 'Holding (driven)':
                        break

                client.set_field(zeroField,
                                 fieldRate,
                                 client.field.approach_mode.oscillate,  # linear/oscillate
                                 client.field.driven_mode.driven)
                print(f'\n Waiting for {zeroField} Oe Field \n')
                time.sleep(10)
                while True:
                    time.sleep(15)
                    F, sF = client.get_field()
                    print(f'Status: {sF}')
                    if sF == 'Holding (driven)':
                        break

                current_in_uA = round(float(current[j]) / 1e-6, 1)
                current_in_mA = round(float(current[j]) / 1e-3, 1)
                keithley_6221_Curr_Src.write(":OUTP OFF")  # Set source function to current
                keithley_6221_Curr_Src.write("CURRent:RANGe:AUTO ON \n")
                keithley_6221_Curr_Src.write(f'CURR {current[j]} \n')
                # keithley_6221_Curr_Src.write(":SOUR:CURR:LEV {current}")  # Set current level to 20 µA
                # keithley_6221_Curr_Src.write(f':SOUR:CURR:LEV {current}')  # Set current level to 20 µA
                keithley_6221_Curr_Src.write(":OUTP ON")  # Turn on the output
                print(f'DC current is set to: {current_in_uA} mA')
                csv_filename = f"061524_THE_Fe_WSe2_0607-02_03_ETO_Rxy_Rxx_{current_in_uA}_uA_{TempList[i]}_K_Room_temp_Temp_Dep_Run_5.csv"
                # csv_filename = f"053024_TTU_MOS2_ThinFilm_5nm_ETO_Rxy_{current_in_uA}_uA_{CurTemp}_K_Run_Test.csv"
                pts = 0
                currentField = topField
                number_of_field_update = number_of_field
                while currentField >= botField:
                    single_measurement_start = time.time()
                    print(f'\n Loop is at {currentField} Oe Field Up \n')
                    Fieldsetpoint = currentField
                    print(f'\n Set the field to {Fieldsetpoint} Oe and then collect data \n')
                    client.set_field(Fieldsetpoint,
                                     fieldRate,
                                     client.field.approach_mode.linear,
                                     client.field.driven_mode.driven)
                    print(f'\n Waiting for {Fieldsetpoint} Oe Field \n')
                    time.sleep(4)
                    MyField, sF = client.get_field()
                    while True:
                        time.sleep(1)
                        MyField, sF = client.get_field()
                        print(f'Status: {sF}')
                        if sF == 'Holding (driven)':
                            break
    
                    MyField, sF = client.get_field()
                    # ----------------------------- Measure NV voltage -------------------
                    print(f'\n Saving data for {MyField} Oe \n')
                    import NV_Read_Function

                    NV_Read_Function.NV_Read(keithley_2182A_NV, MyField, CurTemp, csv_filename, float(current[j]))

                    # ----------------------------- Measure NV voltage -------------------

                    print(f'deltaH = {deltaH}')
                    # Update currentField for the next iteration
                    currentField -= deltaH
                    pts += 1  # Number of pts count
                    single_measurement_end = time.time()
                    Single_loop = single_measurement_end - single_measurement_start
                    number_of_field_update = number_of_field_update -1
                    print('Estimated Single Field measurement (in secs):  {} s \n'.format(Single_loop))
                    print('Estimated Single measurement (in hrs):  {} s \n'.format(Single_loop*number_of_field/60/60))
                    total_time_in_seconds =  Single_loop * (number_of_field_update) *(number_of_current - j)*(number_of_temp - i)
                    totoal_time_in_minutes = total_time_in_seconds /60
                    total_time_in_hours = totoal_time_in_minutes /60
                    total_time_in_days = total_time_in_hours / 24
                    print('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(total_time_in_seconds))
                    print('Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(totoal_time_in_minutes))
                    print('Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(total_time_in_hours))
                    print('Estimated Remaining Time for this round of measurement (in mins):  {} days \n'.format(total_time_in_days))

                # ----------------- Loop Up ----------------------#
                currentField = botField
                while currentField <= topField:
                    single_measurement_start = time.time()
                    print(f'\n Loop is at {currentField} Oe Field Up \n')
                    Fieldsetpoint = currentField

                    print(f'\n Set the field to {Fieldsetpoint} Oe and then collect data \n')
                    client.set_field(Fieldsetpoint,
                                     fieldRate,
                                     client.field.approach_mode.linear,
                                     client.field.driven_mode.driven)

                    print(f'\n Waiting for {Fieldsetpoint} Oe Field \n')
                    time.sleep(4)

                    MyField, sF = client.get_field()
                    while True:
                        time.sleep(1)
                        MyField, sF = client.get_field()
                        print(f'Status: {sF}')
                        if sF == 'Holding (driven)':
                            break

                    MyField, sF = client.get_field()

                    # ----------------------------- Measure NV voltage -------------------
                    print(f'Saving data for  {MyField} Oe')
                    import NV_Read_Function

                    NV_Read_Function.NV_Read(keithley_2182A_NV, MyField, CurTemp, csv_filename, float(current[j]))

                    # ----------------------------- Measure NV voltage -------------------

                    print(f'deltaH = {deltaH}')
                    # Update currentField for the next iteration
                    currentField += deltaH
                    pts += 1  # Number of pts count
                    single_measurement_end = time.time()
                    Single_loop = single_measurement_end - single_measurement_start
                    number_of_field_update = number_of_field_update -1
                    total_time_in_seconds =  Single_loop * (number_of_field_update) *(number_of_current - j)*(number_of_temp - i)
                    totoal_time_in_minutes = total_time_in_seconds /60
                    total_time_in_hours = totoal_time_in_minutes /60
                    total_time_in_days = total_time_in_hours / 24
                    print('Estimated Remaining Time for this round of measurement (in secs):  {} s \n'.format(total_time_in_seconds))
                    print('Estimated Remaining Time for this round of measurement (in mins):  {} mins \n'.format(totoal_time_in_minutes))
                    print('Estimated Remaining Time for this round of measurement (in hrs):  {} hrs \n'.format(total_time_in_hours))
                    print('Estimated Remaining Time for this round of measurement (in mins):  {} days \n'.format(total_time_in_days))
               
                

        client.set_field(zeroField,
                         fieldRate,
                         client.field.approach_mode.oscillate,  # linear/oscillate
                         client.field.driven_mode.driven)
        print('Waiting for Zero Field')

        client.set_temperature(CurTemp,
                               tempRate,
                               client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
        print(f'Waiting for {CurTemp} K Temperature')
        time.sleep(4)
        # client.wait_for(10,
        #                 100,
        #                 client.field.waitfor)

        temperature, status = client.get_temperature()
        print(f'Temperature = {temperature} {tempUnits}')

        field, status = client.get_field()
        fieldUnits = client.field.units
        print(f'Field = {field} {fieldUnits}')

keithley_6221_Curr_Src.write(":SOR:CURR:LEV 0")  # Set current level to zero
keithley_6221_Curr_Src.write(":OUTP OFF")  # Turn off the output
print("DC current is set to: 0.00 A")
keithley_6221_Curr_Src.close()

# Calculate the total runtime
end_time = time.time()
total_runtime = (end_time - start_time) / 3600
print(f"Total runtime: {total_runtime} hours")
print(f'Total data points: {pts} pts')
