# ========================================================= #
# --------- Developed by Muntasir Mahdi (mzm0296) ---------- #
# --------- Phone: +1 334 524 0977 ------------------------- #
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
pts = 0

rm = visa.ResourceManager()  # Open a VISA resource manager pointing to the installation folder for the Keysight Visa libraries.
keithley_2182A_NV = rm.open_resource("GPIB1::7::INSTR", timeout=10000)
keithley_6221_Curr_Src = rm.open_resource('GPIB1::13::INSTR')

# =============================== Set the current ==================================== #
current = 0.5e-3  # Set the current to 20 µA
current_in_uA = round(current / 1e-6, 1)
current_in_mA = round(current / 1e-3, 1)
keithley_6221_Curr_Src.write(":SOUR:FUNC CURR")  # Set source function to current
keithley_6221_Curr_Src.write(":SOUR:CURR:MODE FIX")  # Set current mode to fixed
# keithley_6221_Curr_Src.write(":SOUR:CURR:LEV {current}")  # Set current level to 20 µA
keithley_6221_Curr_Src.write(f':SOUR:CURR:LEV {current}')  # Set current level to 20 µA

keithley_6221_Curr_Src.write(":OUTP ON")  # Turn on the output
print(f'DC current is set to: {current_in_mA} mA')
print(f'DC current is set to: {current_in_uA} uA')

host = "127.0.0.1"
port = 5000


def save_temp_field_chamber():
    T, sT = client.get_temperature()
    F, sF = client.get_field()
    C = client.get_chamber()
    print(f'{T:{7}.{3}f} {sT:{10}} {F:{7}} {sF:{20}} {C:{15}}')


# ========================================================= #

Temps = [20, 50, 100, 150, 200]
# newTemp = 50 #Next temperature set in the end


# ||-----deltaH_large------||--deltaH_med---||--------------deltaH_small-----------------||------deltaH_med---||-------deltaH_large---||
# botField ------------ -B2 ----------- -B1 ------------- zeroField --------------- +B1 ---------------- +B2--------------- topField

topField = 10000
zeroField = 0
botField = -10000

deltaH_large = 500
deltaH_med = 100
deltaH_small = 50
stepFieldMax = 50000
FieldDelay = 5000

fieldRate = 220
tempRate = 50

UpperB1 = 10000
LowerB1 = -10000
UpperB2 = 15000
LowerB2 = -15000


# UpperB1 = 2000
# LowerB1 = -2000
# UpperB2 = 5000
# LowerB2 = -5000


def deltaH_chk(deltaH_small, deltaH_med, deltaH_large, currentField):
    if (currentField <= LowerB2 or currentField >= UpperB2):
        deltaH = deltaH_large

    elif (currentField > LowerB2 and currentField <= LowerB1):
        deltaH = deltaH_med

    elif (currentField < UpperB2 and currentField >= UpperB1):
        deltaH = deltaH_med

    elif (currentField > LowerB1 and currentField < UpperB1):
        deltaH = deltaH_small

    return deltaH


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

        # ----------------------- Set Temperature-------------------------------------
        # CurrentTemp, sT = client.get_temperature()
        # #points = 10

        # setpoint = 1.775 #1.7 K Setpoint
        # tempRate = 50

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

        client.set_field(zeroField,
                         fieldRate,
                         client.field.approach_mode.linear,  # linear/oscillate
                         client.field.driven_mode.driven)

        print(f'\n Waiting for {zeroField} Oe Field \n')
        time.sleep(4)
        # client.wait_for(30,
        #                 timeout_sec=100,
        #                 bitmask=client.field.waitfor)
        # save_temp_field_chamber()

        for currentTemp in Temps:

            print(f'\n Loop is at {currentTemp} K Temperature\n')
            Tempsetpoint = currentTemp
            client.set_temperature(Tempsetpoint,
                                   tempRate,
                                   client.temperature.approach_mode.fast_settle)  # fast_settle/no_overshoot
            print(f'Waiting for {Tempsetpoint} K Temperature')
            time.sleep(4)

            MyTemp, sT = client.get_temperature()
            while True:
                time.sleep(1)
                MyTemp, sT = client.get_temperature()
                print(f'Status: {sT}')
                if sT == 'Stable':
                    break
            # client.wait_for(30,
            #                 timeout_sec=100,
            #                 bitmask=client.field.waitfor)

            MyTemp, sT = client.get_temperature()

            # ---------------- Set the File Name -----------------------#

            csv_filename = f"MnTiN_600C_Hall_{current_in_mA} mA_{currentTemp} K.csv"

            # ----------------------------------------------------------#

            # ----------------- Loop Down ----------------------#
            pts = 0
            currentField = topField
            while currentField >= botField:

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
                # client.wait_for(30,
                #                 timeout_sec=100,
                #                 bitmask=client.field.waitfor)

                MyField, sF = client.get_field()
                time.sleep(1)
                MyTemp, sT = client.get_temperature()
                time.sleep(1)
                # ----------------------------- Measure NV voltage -------------------
                print(f'\n Saving data for {MyField} Oe at {MyTemp} K\n')
                import NV_Read_Function

                NV_Read_Function.NV_Read(MyField, MyTemp, csv_filename, current)

                # ----------------------------- Measure NV voltage -------------------

                deltaH = deltaH_chk(deltaH_small, deltaH_med, deltaH_large, currentField)
                print(f'deltaH = {deltaH}')
                # Update currentField for the next iteration
                currentField -= deltaH
                pts += 1  # Number of pts count

            # ----------------- Loop Up ----------------------#
            currentField = botField
            while currentField <= topField:

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
                # client.wait_for(30,
                #                 timeout_sec=100,
                #                 bitmask=client.field.waitfor)

                MyField, sF = client.get_field()
                time.sleep(1)
                MyTemp, sT = client.get_temperature()
                time.sleep(1)

                # ----------------------------- Measure NV voltage -------------------
                print(f'Saving data for  {MyField} Oe')
                import NV_Read_Function

                NV_Read_Function.NV_Read(MyField, MyTemp, csv_filename, current)

                # ----------------------------- Measure NV voltage -------------------

                deltaH = deltaH_chk(deltaH_small, deltaH_med, deltaH_large, currentField)
                print(f'deltaH = {deltaH}')
                # Update currentField for the next iteration
                currentField += deltaH
                pts += 1  # Number of pts count

            client.set_field(zeroField,
                             fieldRate,
                             client.field.approach_mode.oscillate,  # linear/oscillate
                             client.field.driven_mode.driven)
            print('Waiting for Zero Field')
            time.sleep(4)
            while True:
                time.sleep(15)
                MyField, sF = client.get_field()
                print(f'Status: {sF}')
                if sF == 'Holding (driven)':
                    break
            # client.wait_for(10,
            #                 100,
            #                 client.field.waitfor)

            temperature, status = client.get_temperature()
            print(f'Temperature = {temperature} {tempUnits}')

            field, status = client.get_field()
            fieldUnits = client.field.units
            print(f'Field = {field} {fieldUnits}')

            loop_end_time = time.time()
            total_loop_runtime = (loop_end_time - start_time) / 3600
            print(f"Total Loop runtime: {total_loop_runtime} hours")
            print(f'Total data points: {pts} pts')

keithley_6221_Curr_Src.write(":SOUR:CURR:LEV 0")  # Set current level to zero
keithley_6221_Curr_Src.write(":OUTP OFF")  # Turn off the output
print("DC current is set to: 0.00 A")
keithley_6221_Curr_Src.close()

# Calculate the total runtime
end_time = time.time()
total_runtime = (end_time - start_time) / 3600
print(f"Total runtime: {total_runtime} hours")
print(f'Total data points: {pts} pts')
