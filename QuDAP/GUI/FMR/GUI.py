"""
Author  :Chunli Tang
Project :FMR Data processing GUI
FileName:GUI.py
Time    :2022/11/2f4
Affiliation:Auburn University
"""
import lmfit
# import packages
import numpy as np
import matplotlib.pyplot as plt
from sympy import *
from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import ttk
from tkinter import filedialog
import pandas as pd
import os
import time
import math
from scipy import optimize, interpolate
from mpl_toolkits.axes_grid1 import make_axes_locatable
from mplcursors import cursor
from matplotlib.ticker import (MultipleLocator, FormatStrFormatter,
                               AutoMinorLocator)
from os.path import exists as file_exists
import tkinter.messagebox as messagebox
import csv
from PIL import ImageTk, Image
from lmfit import Model
from decimal import *
import matplotlib


class quantumGUI(Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        # self.pack()  # self pack itself
        self.setup_temp()
        self.createWidget()
        self.opened = False
        self.image_window = False
        self.degree = 0

    def setup_temp(self):
        self.temps_list = [4, 5, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 105, 110, 115, 120, 130, 140, 150, 160, 170, 180,
                           190, 200, 250, 300]

    def list_init(self):
        self.freqs = []  # initialize an empty list
        self.GHz = 10 ** 9

    def view_init(self):
        self.fr_input_up = ttk.Frame(master=root)
        self.fr_input_up.grid(row=0, column=0, ipadx=100, ipady=175, sticky='NWE')
        self.fr_input_up.grid_propagate(False)
        self.fr_input_dw = Frame(master=root)
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.fr_input_right = Frame(master=root)


    def _quit(self):
        self.master.quit()  # stops mainloop
        self.master.destroy()  # this is necessary on Windows to prevent
        # Fatal Python Error: PyEval_RestoreThread: NULL tstate

    def _back_offset(self):
        exists = self.fr_input_right_image.winfo_exists()
        if exists == 1 or self.image_window == True:
            self.fr_input_right_image.destroy()

    def _back(self):
        self.fr_input_right.destroy()

        exists = self.fr_input_right_image.winfo_exists()
        if exists == 1 or self.image_window == True:
            self.fr_input_right_image.destroy()

        self.createWidget()

    def _back_interp_graph(self):
        self.fr_input_right_image.destroy()

    def _lw_back(self):
        self.fr_input_right_image.destroy()
        self.kittel_reset_bt.destroy()
        self.linewidth_back_bt.destroy()
        self.lw_plot_bt.destroy()
        self.LW_entry_lf.destroy()
        self.lw_plot_bt.destroy()
        self.lw_process_bt = ttk.Button(self.fr_input_right, text='Plot Linwewidth',
                                        command=lambda: self.Linewidth_process_init(), style='Toggle.TButton')
        self.lw_process_bt.grid(row=3, column=9, pady=25)

        self.kittel_process_bt = ttk.Button(self.fr_input_right, text='Fit Kittel',
                                            command=lambda: self.Kittel_process_init(), style='Toggle.TButton')
        self.kittel_process_bt.grid(row=3, column=7, pady=25)

        self.kittel_back_bt = ttk.Button(self.fr_input_right, text='Back',
                                         command=lambda: self._back())
        self.kittel_back_bt.grid(row=3, column=11, pady=25)

        self.kittel_reset_bt = ttk.Button(self.fr_input_right, text='Reset',
                                          command=lambda: self._reset_Kittel())
        self.kittel_reset_bt.grid(row=3, column=13, pady=25, ipadx=0.1, ipady=1)

    def _reset_raw(self):
        self.fr_input_right.destroy()
        exists = self.fr_input_right_image.winfo_exists()
        if exists == 1 or self.image_window == True:
            self.fr_input_right_image.destroy()
            self.image_window = False

        self.catagdata()

    def _reset_intp(self):
        self.fr_input_right.destroy()
        exists = self.fr_input_right_image.winfo_exists()
        if exists == 1 or self.image_window == True:
            self.fr_input_right_image.destroy()
            self.image_window = False
        self.Data_Interpolation()

    def _reset_Kittel(self):
        self.fr_input_right.destroy()
        exists = self.fr_input_right_image.winfo_exists()
        if exists == 1 or self.image_window == True:
            self.fr_input_right_image.destroy()
            self.image_window = False
        self.Init_Kittel()

    def _reset_fit(self):
        if self.opened:
            self.newWindow.destroy()

        self.fr_input_right.destroy()
        exists = self.fr_input_right_image.winfo_exists()
        if exists == 1 or self.image_window == True:
            self.fr_input_right_image.destroy()
            self.image_window = False
        self.Init_FMRFit()

    def folder_selection(self):
        self.folder_selected_d = filedialog.askdirectory(initialdir='RAW Data')
        self.fr_input_dw.destroy()
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=200, bg='#D3D3D3')
        message_folder = 'THe folder you selected is: ' + self.folder_selected_d
        self.text_box.insert('end', message_folder)
        self.text_box.grid()
        self.entry_lf = ttk.LabelFrame(self.fr_input_right, text='Entries')
        self.entry_lf.grid(row=2, column=0, columnspan=20, padx=25, pady=0, ipadx=200, ipady=80)
        self.entry_lf.grid_propagate(false)
        self.folder_selected_d = self.folder_selected_d + "/"

        self.folder_selected_Arr = []
        self.folder_selected_Arr.append(self.folder_selected_d)

        self.dir_list = os.listdir(self.folder_selected_Arr[0])[0]
        time.sleep(3)
        self.text_box.delete('1.0', 'end')
        message_folder_create = 'File naming convention is: ' + self.dir_list
        self.text_box.insert('end', message_folder_create)
        self.text_box.grid()

        self.ID_InputStr = StringVar()
        self.botFreq_InputDou = DoubleVar()
        self.stepFreq_InputDou = DoubleVar()
        self.topFreq_InputDou = DoubleVar()
        self.Output_path_InputStr = StringVar()

        self.ID_Arr = []
        self.botFreq_Arr = []
        self.stepFreq_Arr = []
        self.topFreq_Arr = []
        self.Output_path_Arr = []

        self.ID_label = ttk.Label(self.entry_lf, text="Sample ID: ", justify='left')
        self.ID_label.grid(row=2, column=1, padx=5)
        self.ID_entry = ttk.Entry(self.entry_lf, textvariable=self.ID_InputStr, justify=CENTER)
        self.ID_entry.grid(row=2, column=2, padx=25)
        self.ID_Arr.append(self.ID_entry)

        self.bot_freq_label = ttk.Label(self.entry_lf, text="Bottom Frequency (GHz): ", justify='left')
        self.bot_freq_label.grid(row=3, column=1, padx=5)
        self.botFreq_entry = ttk.Entry(self.entry_lf, textvariable=self.botFreq_InputDou, justify=CENTER)
        self.botFreq_entry.grid(row=3, column=2, padx=25)
        self.botFreq_Arr.append(self.botFreq_entry)

        self.step_freq_label = ttk.Label(self.entry_lf, text="Step Frequency (GHz): ", justify='left')
        self.step_freq_label.grid(row=4, column=1, padx=5)
        self.stepFreq_entry = ttk.Entry(self.entry_lf, textvariable=self.stepFreq_InputDou, justify=CENTER)
        self.stepFreq_entry.grid(row=4, column=2, padx=25)
        self.stepFreq_Arr.append(self.stepFreq_entry)

        self.top_freq_label = ttk.Label(self.entry_lf, text="Top Frequency (GHz): ", justify='left')
        self.top_freq_label.grid(row=5, column=1, padx=5)
        self.topFreq_entry = ttk.Entry(self.entry_lf, textvariable=self.topFreq_InputDou, justify=CENTER)
        self.topFreq_entry.grid(row=5, column=2, padx=25)
        self.topFreq_Arr.append(self.topFreq_entry)

        self.output_folder_label = ttk.Label(self.entry_lf, text="Output Folder name: ", justify='left')
        self.output_folder_label.grid(row=6, column=1, padx=5)
        self.Output_path_entry = ttk.Entry(self.entry_lf, textvariable=self.Output_path_InputStr, justify=CENTER)
        self.Output_path_entry.grid(row=6, column=2, padx=25)
        self.Output_path_Arr.append(self.Output_path_entry)

        self.progress = ttk.Progressbar(self.fr_input_right, mode="determinate")
        self.progress.grid(row=6, column=1, columnspan=18, padx=25, pady=(20, 0), sticky="ew")

        self.process_bt = ttk.Button(self.fr_input_right, text='Process',
                                     command=lambda: self.catagprocess(self.temps_list), style='Toggle.TButton')
        self.process_bt.grid(row=7, column=15, pady=25)

        self.back_bt = ttk.Button(self.fr_input_right, text='Back',
                                  command=lambda: self._back())
        self.back_bt.grid(row=7, column=17, pady=25)

        self.reset_bt = ttk.Button(self.fr_input_right, text='Reset',
                                   command=lambda: self._reset_raw())
        self.reset_bt.grid(row=7, column=16, pady=25, ipadx=0.1, ipady=1)

    def catagprocess(self, temps):
        self.folder_selected = self.folder_selected_Arr[0]
        self.ID = self.ID_Arr[0].get()
        self.botFreq = int(float(self.botFreq_Arr[0].get()) * self.GHz)
        self.stepFreq = int(float(self.stepFreq_Arr[0].get()) * self.GHz)
        self.topFreq = int(float(self.topFreq_Arr[0].get()) * self.GHz)
        self.Output_path = self.Output_path_Arr[0].get()
        self.path = 'Processed'  # Processed data directory
        isExist = os.path.exists(self.path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(self.path)
            time.sleep(3)
            self.text_box.delete('1.0', 'end')
            message_folder_create = "The new directory for processed file is created!"
            self.text_box.insert('end', message_folder_create)
            self.text_box.grid()
        self.process_path = 'Processed/{}'.format(self.Output_path)
        isExist = os.path.exists(self.process_path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(self.process_path)
            time.sleep(3)
            self.text_box.delete('1.0', 'end')
            message_folder_create_1 = "The directory " + self.Output_path + " is created!"
            self.text_box.insert('end', message_folder_create_1)
            self.text_box.grid()
        self.loop = ((self.topFreq - self.botFreq) / self.stepFreq) + 1  # Calculate the looping cycle for appending
        time.sleep(1)
        self.text_box.delete('1.0', 'end')
        message_processing = 'Processing data ......'
        self.text_box.insert('end', message_processing)
        self.text_box.grid()
        bottomfreq = self.botFreq
        for i in range(int(self.loop)):
            self.freqs.append(str(bottomfreq))  # Append all the frequency in to the list
            bottomfreq += int(self.stepFreq)
        time.sleep(1)
        self.text_box.delete('1.0', 'end')
        message_collect_freq = 'Collecting all the frequency data!'
        self.text_box.insert('end', message_collect_freq)
        self.text_box.grid()
        self.progress.destroy()
        self.progress = ttk.Progressbar(self.fr_input_right, mode="determinate")
        self.progress.grid(row=6, column=1, columnspan=18, padx=25, pady=(20, 0), sticky="ew")

        def step():
            count = 0
            for temp in temps:
                print('check {}'.format(temp))
                count = count + 1
                total_value = len(temps)
                progress_value = int(float(count / total_value) * 100)
                self.fr_input_right.update_idletasks()
                self.progress['value'] = progress_value
                df = pd.DataFrame()  # by sorting to FMR signal and Frequency
                for freq in self.freqs:
                    # print(freq)
                    path_file = self.folder_selected + '1Field_Mod_400mV_FMR-{}K-{}Hz-OOP_RuO2_15dBm.csv'.format(temp, freq)
                    # path_file = self.folder_selected + '/New_square_IP_Field_Mod_FMR_STO_0_deg-0.4v-sec-5dbm-FMR-{}K-{}Hz-10ms-IP.csv'.format(temp, freq)
                    print(path_file)
                    FileisExist = os.path.exists(path_file)
                    if not FileisExist:  # Create a new directory because it does not exist
                        file_exist_flag = 'N'
                        print("Not Exist")
                    else:
                        file_exist_flag = 'Y'
                        # print("Exist")

                    if file_exist_flag == "Y":
                        # print(path_file)
                        data = pd.read_csv(path_file, header=None)
                        # print(data)
                        field = data[14].values  # Read form PPMS generated data
                        mag = data[4].values
                        # print(field, mag)
                        add = pd.DataFrame(list(zip(field, mag)),
                                           columns=['Field', '{} GHz'.format(int(freq) / 1000000000)])
                        df = pd.concat([df, add], ignore_index=False, axis=1)

                if file_exist_flag == "Y":
                    df.to_csv(self.process_path + '/{}_FMR-{}K.csv'.format(self.ID, temp),
                              index=False,
                              encoding='utf-8-sig')
                    self.text_box.delete('1.0', 'end')
                    message_folder_create = 'Processing {} K Data ......'.format(temp)
                    self.text_box.insert('end', message_folder_create)
                    self.text_box.grid()

        step()
        self.text_box.delete('1.0', 'end')
        message_folder_create = 'Data sorting is done!'
        self.text_box.insert('end', message_folder_create)
        self.text_box.grid()

    def catagdata(self):
        self.fr_input_right.destroy()
        self.return_folder = StringVar()
        self.fr_input_right = Frame(master=root)
        self.fr_input_right.grid(row=0, column=1, ipadx=5, ipady=10)
        self.init_lf = ttk.LabelFrame(self.fr_input_right, text='Initiation')
        self.init_lf.grid(row=1, column=0, padx=25, pady=25, columnspan=20, ipadx=200, ipady=24)
        self.init_lf.grid_propagate(false)
        self.folder_label = ttk.Label(self.init_lf, text="Please select the Data Directory: ", justify='center')
        self.folder_label.grid(row=0, column=0, padx=5)
        self.file_open_bt = ttk.Button(self.init_lf, text='Select File', command=lambda: self.folder_selection())
        self.file_open_bt.grid(row=0, column=1, padx=120, ipadx=1, ipady=1)

    def Data_Interpolation(self):
        self.fr_input_right.destroy()
        self.return_folder = StringVar()
        self.fr_input_right = Frame(master=root)
        self.fr_input_right.grid(row=0, column=1, ipadx=5, ipady=10)
        self.init_lf = ttk.LabelFrame(self.fr_input_right, text='Initiation')
        self.init_lf.grid(row=1, column=0, padx=25, pady=25, columnspan=20, ipadx=200, ipady=24)
        self.init_lf.grid_propagate(false)
        self.folder_label = ttk.Label(self.init_lf, text="Please select the Data File: ", justify='center')
        self.folder_label.grid(row=0, column=0, padx=5)
        self.file_open_bt = ttk.Button(self.init_lf, text='Select File',
                                       command=lambda: self.folder_selection_Interpolation())
        self.file_open_bt.grid(row=0, column=1, padx=150, ipadx=1, ipady=1)

    def Interpolation_Proc(self):
        df = pd.read_csv(self.file_selected, header=0)
        self.ID_IntP = self.ID_IntP_Arr[0].get()
        self.Temp_IntP = self.Temp_IntP_Arr[0].get()
        row_index = []
        min_num = []
        max_num = []
        total_cols = len(df.axes[1])  # Axes of 0 is for a column
        for col in range(0, total_cols, 2):
            total_rows = len(df.axes[0])  # Define the maximum total rows in the file (largest instances)
            # Check each row number to get rid of NaN instances
            IsNaN: bool = True
            while IsNaN:
                RowFilter = df.iat[total_rows - 1, col]
                if math.isnan(RowFilter):
                    total_rows = total_rows - 1
                else:
                    processedRow_Intp = total_rows
                    row_index = np.append(row_index, processedRow_Intp)
                    IsNaN = False
                    XMax = df.iloc[:, col].max(axis=0)
                    max_num = np.append(max_num, XMax)
                    XMin = df.iloc[:, col].min(axis=0)
                    min_num = np.append(min_num, XMin)

                # Find the FMR signal maximum point and the minimum point
        min_row_index = min(row_index)
        self.bottom_mum = np.ceil(min(min_num))
        self.top_num = np.floor(max(max_num))
        print(self.bottom_mum, self.top_num)
        Output = pd.DataFrame()
        Inter_Output = pd.DataFrame()
        Org_y_out = pd.DataFrame()
        origin_lab = pd.DataFrame()
        for col in range(0, total_cols, 2):
            total_rows = len(df.axes[0])  # Define the maximum total rows in the file (largest instances)
            # Check each row number to get rid of NaN instances
            IsNaN: bool = True
            while IsNaN:
                RowFilter = df.iat[total_rows - 1, col]
                if math.isnan(RowFilter):
                    total_rows = total_rows - 1
                else:
                    processedRow = total_rows
                    IsNaN = False
            YMax = df.iloc[:, col + 1].max(axis=0)
            YMin = df.iloc[:, col + 1].min(axis=0)
            loop: bool = True
            n = 0
            while loop:
                X_current = np.ceil(df.iat[n, col])
                X_next = np.ceil(df.iat[n + 1, col])
                if X_current == X_next:
                    n += 1
                else:
                    loop = False
            X = df.iloc[n:processedRow_Intp, col]
            X = X.astype(np.float64)
            Y = df.iloc[n:processedRow_Intp, col + 1]
            Y = Y.astype(np.float64)
            # interpolation_ask = input('Do you want to do the data interpolation? (Y / N)')
            inter_result = interpolate.interp1d(X, Y, 'linear', fill_value="extrapolate")
            x_new = np.linspace(int(self.bottom_mum), int(self.top_num), num=int(self.top_num))
            print(x_new)
            y_new = inter_result(x_new)

            np.seterr(invalid='ignore', divide='ignore')

            x_new = x_new[1:-1]
            y_new = y_new[1:-1]
            freq = 1
            path = 'Interpolation_test'  # Processed data directory
            isExist = os.path.exists(path)
            if not isExist:  # Create a new directory because it does not exist
                os.makedirs(path)
                time.sleep(3)
                self.text_box.delete('1.0', 'end')
                message_folder_create = "The new directory for processed file is created!"
                self.text_box.insert('end', message_folder_create)
                self.text_box.grid()
            inter_final = pd.DataFrame(
                list(zip(x_new, y_new)))
            inter_y = pd.DataFrame(list(y_new))
            inter_x = pd.DataFrame(list(x_new))
            org_y = pd.DataFrame(list(Y))
            Org_y_out = pd.concat([Org_y_out, org_y], ignore_index=True, axis=1)
            Output = pd.concat([Output, inter_final], ignore_index=True, axis=1)
            Inter_Output = pd.concat([Inter_Output, inter_y], ignore_index=True, axis=1)

            # origin_lab = pd.concat([origin_lab, inter_x], ignore_index=True, axis=0)
            # origin_lab = pd.concat([origin_lab, inter_y], ignore_index=True, axis=1)

            freq += 1
        self.Interpolated_file = 'Interpolation_test/Interploation_Data_{}_{}K.csv'.format(self.ID_IntP, self.Temp_IntP)

        Inter_Output.to_csv(self.Interpolated_file, mode='w', index=False, encoding='utf-8-sig', header=False)
        # Output for originlab
        # self.origin_lab_file = 'Interpolation_test/Originlab_Data_{}_{}K.csv'.format(self.ID_IntP, self.Temp_IntP)
        # origin_lab.to_csv(self.origin_lab_file, mode='w', index=False, encoding='utf-8-sig', header=False)

        Output.to_csv('Interpolation_test/Data_{}_{}K.csv'.format(self.ID_IntP, self.Temp_IntP),
                      mode='w', index=False, encoding='utf-8-sig', header=False)
        Org_y_out.to_csv('Interpolation_test/ORG_Data_{}_{}K.csv'.format(self.ID_IntP, self.Temp_IntP), mode='w',
                         index=False, encoding='utf-8-sig', header=False)
        time.sleep(3)
        self.text_box.delete('1.0', 'end')
        message_folder_create = "Interpolation Complete!"
        self.text_box.insert('end', message_folder_create)
        self.text_box.grid()

        self.process_bt.destroy()
        self.process_bt = ttk.Button(self.fr_input_right, text='Plot',
                                     command=lambda: self.Interpolation_Proc_plot(), style='Toggle.TButton')
        self.process_bt.grid(row=7, column=15, pady=25)

        self.back_bt = ttk.Button(self.fr_input_right, text='Back',
                                  command=lambda: self._back())
        self.back_bt.grid(row=7, column=17, pady=25)

        self.reset_bt = ttk.Button(self.fr_input_right, text='Reset',
                                   command=lambda: self._reset_intp())
        self.reset_bt.grid(row=7, column=16, pady=25, ipadx=0.1, ipady=1)

    def Interpolation_Proc_plot(self):
        filename_color_map = self.Interpolated_file
        self.df_color_map = pd.read_csv(filename_color_map, header=None).transpose()
        self.df_color_map = self.df_color_map.to_numpy()
        for row in range(0, self.df_color_map.shape[0], 1):
            mean = np.mean(self.df_color_map[row, int(self.top_num) - 300:int(self.top_num) - 100])
            self.df_color_map[row, :] = self.df_color_map[row, :] - mean
        YMin = np.min(self.df_color_map[-1, :])
        YMax = np.max(self.df_color_map[-1, :])
        time.sleep(3)
        self.text_box.delete('1.0', 'end')
        message_folder_create = "The file for plotting is :" + self.Interpolated_file
        self.text_box.insert('end', message_folder_create)
        self.text_box.grid()
        self.fr_input_right_image = Frame(master=root)
        self.fr_input_right_image.grid(row=0, column=2)
        self.image_window = True
        self.f, self.ax = plt.subplots(figsize=(5, 5))
        self.ax.set_title("{} {} K Heat Map".format(self.ID_IntP, self.Temp_IntP), fontsize=10)
        self.canvs = FigureCanvasTkAgg(self.f, self.fr_input_right_image)
        self.canvs.get_tk_widget().grid(row=0, column=0, columnspan=10, rowspan=10)
        self.canvs._tkcanvas.grid(row=0, column=0, columnspan=10, rowspan=10)

        self.toolbar = NavigationToolbar2Tk(self.canvs, self.canvs.get_tk_widget().master, pack_toolbar=False)
        image = self.ax.imshow(self.df_color_map, aspect='auto', cmap='viridis', vmin=YMin * 0.9, vmax=YMax * 0.9,
                               origin='lower',
                               extent=[self.bottom_mum, self.top_num, 0.2, 13.8], resample='True')
        self.ax.set_xlabel("Field (Oe)", fontname="Arial", labelpad=10)
        self.ax.set_ylabel('Frequency (GHz)', fontname="Arial", labelpad=10)
        self.f.colorbar(image, ax=self.ax)
        self.f.savefig('Interpolation/{}_Heat_Map_Temp_{}K.png'.format(self.ID_IntP, self.Temp_IntP), dpi=100)
        self.f.tight_layout()
        self.toolbar.update()
        self.canvs.draw()
        self.interactive_bt = ttk.Button(self.fr_input_right_image, text='Show Interactive Plot',
                                         command=lambda: self.IntP_plot_Interactive())
        self.interactive_bt.grid(row=12, column=4, ipadx=0.1, ipady=1, padx=50)

        self.interactive_bt = ttk.Button(self.fr_input_right_image, text='Back',
                                         command=lambda: self._back_interp_graph())
        self.interactive_bt.grid(row=12, column=5, ipadx=0.1, ipady=1, padx=50)

        # self.f_save, self.ax_save = plt.subplots(figsize=(20, 20))
        # self.ax_save.set_title("{} {} K Heat Map".format(self.ID_IntP, self.Temp_IntP), fontsize=10)
        # image = self.ax_save.imshow(self.df_color_map, aspect='auto', cmap='viridis', vmin=YMin * 0.9, vmax=YMax * 0.9,
        #                        origin='lower',
        #                        extent=[0, self.top_num, 2, 11], resample='True')
        # self.ax_save.set_xlabel("Field (Oe)", fontname="Arial", labelpad=10)
        # self.ax_save.set_ylabel('Frequency (GHz)', fontname="Arial", labelpad=10)
        # self.f_save.colorbar(image, ax=self.ax)
        # self.f_save.savefig('Interpolation/{}_Heat_Map_Temp_{}K.png'.format(self.ID_IntP, self.Temp_IntP), dpi=100)

    def folder_selection_Interpolation(self):
        self.file_selected = filedialog.askopenfilename(initialdir="Processed/",
                                                        title="Select a Data File",
                                                        filetypes=(("csv files", "*.csv"), ("xlsx file", "*.xlsx"),
                                                                   ("all files", "*.*")))
        self.fr_input_dw.destroy()
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=200, bg='#D3D3D3')
        message_folder = 'The file selected is: ' + self.file_selected
        self.text_box.insert('end', message_folder)
        self.text_box.grid()

        self.IntP_entry_lf = ttk.LabelFrame(self.fr_input_right, text='Entries')
        self.IntP_entry_lf.grid(row=2, column=0, columnspan=20, padx=25, pady=0, ipadx=200, ipady=40)
        self.IntP_entry_lf.grid_propagate(false)

        self.ID_InputStr = StringVar()
        self.Temp_InputDoub = IntVar()

        self.ID_IntP_Arr = []
        self.Temp_IntP_Arr = []
        self.ID_label = ttk.Label(self.IntP_entry_lf, text="Sample ID: ", justify='left')
        self.ID_label.grid(row=2, column=1, padx=5)
        self.ID_entry = ttk.Entry(self.IntP_entry_lf, textvariable=self.ID_InputStr, justify=CENTER)
        self.ID_entry.grid(row=2, column=2, padx=25)
        self.ID_IntP_Arr.append(self.ID_entry)

        self.Temp_label = ttk.Label(self.IntP_entry_lf, text="Temperature (K): ", justify='left')
        self.Temp_label.grid(row=3, column=1, padx=5)
        self.Temp_entry = ttk.Entry(self.IntP_entry_lf, textvariable=self.Temp_InputDoub, justify=CENTER)
        self.Temp_entry.grid(row=3, column=2, padx=25)
        self.Temp_IntP_Arr.append(self.Temp_entry)

        self.process_bt = ttk.Button(self.fr_input_right, text='Continue',
                                     command=lambda: self.Interpolation_Proc(), style='Toggle.TButton')
        self.process_bt.grid(row=7, column=15, pady=25)

        self.back_bt = ttk.Button(self.fr_input_right, text='Back',
                                  command=lambda: self._back())
        self.back_bt.grid(row=7, column=17, pady=25)

        self.reset_bt = ttk.Button(self.fr_input_right, text='Reset',
                                   command=lambda: self._reset_intp())
        self.reset_bt.grid(row=7, column=16, pady=25, ipadx=0.1, ipady=1)

    def IntP_plot_Interactive(self):
        plt.close('all')
        time.sleep(3)
        self.text_box.delete('1.0', 'end')
        message_folder_create = "Open the interactive plot ......"
        self.text_box.insert('end', message_folder_create)
        self.text_box.grid()
        path = 'Coupling_Profile'  # Processed data directory
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            time.sleep(3)
            self.text_box.delete('1.0', 'end')
            message_folder_create = "The new directory is created..."
            self.text_box.insert('end', message_folder_create)
            self.text_box.grid()
        fig, main_plot = plt.subplots(figsize=(10, 5))
        divider = make_axes_locatable(main_plot)
        top_ax = divider.append_axes("top", 1.05, pad=0.1, sharex=main_plot)
        right_ax = divider.append_axes("right", 1.05, pad=0.1, sharey=main_plot)

        # make some labels invisible
        top_ax.xaxis.set_tick_params(labelbottom=False)
        top_ax.xaxis.set_label_position('top')
        top_ax.xaxis.set_tick_params(labelbottom=False)
        right_ax.yaxis.set_tick_params(labelleft=False)
        right_ax.yaxis.set_tick_params(labelleft=False)
        right_ax.yaxis.set_label_position('right')
        top_ax.set_xlabel('Intensity Profile', fontsize=15)
        right_ax.set_ylabel('Intensity Profile', fontsize=15)

        plt.rc('font', size=5)  # controls default text sizes
        main_plot.imshow(self.df_color_map, aspect='auto', cmap='viridis', vmin=-4e-6, vmax=4e-6, origin='lower',
                         extent=[0, self.top_num, 3, 10], resample='True')
        main_plot.set_xlabel("Field (Oe)", fontname="Arial", labelpad=10, fontsize=18)
        main_plot.set_ylabel('Frequency (GHz)', fontname="Arial", labelpad=10, fontsize=18)
        main_plot.tick_params(axis='both', which='major', labelsize=15)
        right_ax.tick_params(axis='both', which='major', labelsize=15)
        top_ax.tick_params(axis='both', which='major', labelsize=15)
        main_plot.autoscale(enable=False)
        right_ax.autoscale(enable=False)
        top_ax.autoscale(enable=False)
        right_ax.ticklabel_format(axis="both", style="sci")
        top_ax.ticklabel_format(axis="both", style="sci")
        right_ax.xaxis.get_offset_text().set_fontsize(12)
        top_ax.yaxis.get_offset_text().set_fontsize(12)
        right_ax.set_xlim(left=np.amin(self.df_color_map), right=np.amax(self.df_color_map))
        top_ax.set_ylim(bottom=np.amin(self.df_color_map), top=np.amax(self.df_color_map))
        main_plot.set_ylim(bottom=3, top=10)
        main_plot.set_xlim(left=0, right=self.top_num)
        v_line = main_plot.axvline(np.nan, color='r')
        h_line = main_plot.axhline(np.nan, color='b')
        array = np.linspace(3.0, 10.0, num=self.df_color_map.shape[0])
        v_prof, = right_ax.plot(np.zeros(self.df_color_map.shape[0]),
                                np.reshape(array, (self.df_color_map.shape[0], 1)), 'r-')
        h_prof, = top_ax.plot(np.arange(self.df_color_map.shape[1]), np.zeros(self.df_color_map.shape[1]), 'b-')
        add = pd.DataFrame(list(zip(['Field (Oe)'], ['Frequecny (GHz)'])))
        data = pd.DataFrame()
        data = pd.concat([data, add], ignore_index=True, axis=1)
        csv_file_name = 'Coupling_Profile/{}_{}K_Coupling_{}deg.csv'.format(self.ID_IntP_Arr[0].get(), self.Temp_IntP_Arr[0].get(), self.degree)
        time.sleep(3)
        self.text_box.delete('1.0', 'end')
        message_folder_create = "{} is created...".format(csv_file_name)
        self.text_box.insert('end', message_folder_create)
        self.text_box.grid()
        data.to_csv(csv_file_name, mode='a', index=False, encoding='utf-8-sig', header=None)
        def on_move(event):
            if event.inaxes is main_plot:
                cur_x = event.xdata
                cur_y = event.ydata

                v_line.set_xdata([cur_x, cur_x])
                h_line.set_ydata([cur_y, cur_y])
                v_prof.set_xdata(self.df_color_map[:, int(cur_x * 2198 / 2200)])
                h_prof.set_ydata(self.df_color_map[int((cur_y - 3) * self.df_color_map.shape[0] / 7), :])
                fig.canvas.draw_idle()

        def double_click(event):
            if event.dblclick:
                global cur_x, cur_y, click
                cur_x = event.xdata
                cur_y = event.ydata
                click = event.button
                if click == 1:
                    print('x: {}, y: {}'.format(cur_x, cur_y))
                    comb = pd.DataFrame(list(zip([cur_x], [cur_y])))
                    rec_data = pd.DataFrame()
                    rec_data = pd.concat([rec_data, comb], ignore_index=True, axis=1)
                    rec_data.to_csv(csv_file_name, mode='a', index=False, encoding='utf-8-sig', header=None)
        fig.canvas.mpl_connect('motion_notify_event', on_move)
        fig.canvas.mpl_connect('button_press_event', double_click)
        cursor(hover=True)
        plt.show()

    def resetCanvas(self):
        self.ax.clear()
        self.ax.set_title("{} {} K Heat Map".format(self.ID_IntP, self.Temp_IntP), fontsize=10)
        self.canvs.draw()

    def Init_FMRFit(self):
        self.fr_input_right.destroy()
        self.return_folder = StringVar()
        self.fr_input_right = Frame(master=root)
        self.fr_input_right.grid(row=0, column=1, ipadx=5, ipady=10)
        self.init_lf = ttk.LabelFrame(self.fr_input_right, text='Initiation')
        self.init_lf.grid(row=1, column=0, padx=25, pady=25, columnspan=20, ipadx=200, ipady=24)
        self.init_lf.grid_propagate(false)
        self.folder_label = ttk.Label(self.init_lf, text="Please select the Data Directory: ", justify='center')
        self.folder_label.grid(row=0, column=0, padx=5)
        self.file_open_bt = ttk.Button(self.init_lf, text='Select File', command=lambda: self.fit_init(self.temps_list))
        self.file_open_bt.grid(row=0, column=1, padx=120, ipadx=1, ipady=1)

    def fit_init(self, __temps__):
        # _reset_fit()
        self.folder_selected_data = filedialog.askdirectory(initialdir='Processed')
        self.fr_input_dw.destroy()
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=200, bg='#D3D3D3')
        message_folder = 'THe folder you selected is: ' + self.folder_selected_data
        self.text_box.insert('end', message_folder)
        self.text_box.grid()
        self.folder_selected_data_Arr = []
        self.folder_selected_data_Arr.append(self.folder_selected_data)

        self.fit_entry_lf = ttk.LabelFrame(self.fr_input_right, text='Sample ID')
        self.fit_entry_lf.grid(row=2, column=0, columnspan=20, padx=25, pady=0, ipadx=200, ipady=25)
        self.fit_entry_lf.grid_propagate(false)
        self.folder_selected_data = self.folder_selected_data + "/"

        self.ID_fit_Arr = []
        self.ID_fit_InputStr = StringVar()
        self.ID_fit_label = ttk.Label(self.fit_entry_lf, text="Sample ID: ", justify='left')
        self.ID_fit_label.grid(row=2, column=1, padx=5)
        self.ID_fit_entry = ttk.Entry(self.fit_entry_lf, textvariable=self.ID_fit_InputStr, justify=CENTER)
        self.ID_fit_entry.grid(row=2, column=2, padx=165)
        self.ID_fit_Arr.append(self.ID_fit_entry)

        self.load_bt = ttk.Button(self.fr_input_right, text='Load',
                                  command=lambda: self.fit_load(self.temps_list), style='Toggle.TButton')
        self.load_bt.grid(row=7, column=15, pady=25)

        self.back_bt = ttk.Button(self.fr_input_right, text='Back', command=lambda: self._back())
        self.back_bt.grid(row=7, column=17, pady=25)

        self.reset_bt = ttk.Button(self.fr_input_right, text='Reset', command=lambda: self._reset_fit())
        self.reset_bt.grid(row=7, column=16, pady=25, ipadx=0.1, ipady=1)

    def fit_load(self, __temps__):
        self.folder_selected_Fit = self.folder_selected_data
        self.ID_Fit = self.ID_fit_Arr[0].get()
        self.read_temp = []
        for ver_temp in __temps__:
            if file_exists(self.folder_selected_Fit + 'New_Square_{}_FMR-{}K-10ms-{}-deg-IP.csv'.format(self.ID_Fit,
                                                                                                        ver_temp,
                                                                                                        self.degree)) == True:
                self.read_temp.append(ver_temp)

        time.sleep(1)
        self.text_box.delete('1.0', 'end')
        message_read_temp = 'The temperature measurements are {} K'.format(self.read_temp)
        self.text_box.insert('end', message_read_temp)
        self.text_box.grid()

        self.load_bt.destroy()
        self.read_temp_next = 0
        self.temp_next = False
        self.next_bt = ttk.Button(self.fr_input_right, text='Next',
                                  command=lambda: self.select_fit_temp(), style='Toggle.TButton')
        self.next_bt.grid(row=7, column=15, pady=25)

    def select_fit_temp(self):
        path = 'OutputFit'  # Processed data directory
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            time.sleep(3)
            self.text_box.delete('1.0', 'end')
            message_folder_create_1 = "The directory " + path + " is created!"
            self.text_box.insert('end', message_folder_create_1)
            self.text_box.grid()

        path = 'WaterFall_Data'  # Processed data directory
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            time.sleep(3)
            self.text_box.delete('1.0', 'end')
            message_folder_create_1 = "The directory " + path + " is created!"
            self.text_box.insert('end', message_folder_create_1)
            self.text_box.grid()

        path = 'Asymmetric_Symmetric'
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            time.sleep(3)
            self.text_box.delete('1.0', 'end')
            message_folder_create_1 = "The directory " + path + " is created!"
            self.text_box.insert('end', message_folder_create_1)
            self.text_box.grid()

        path = 'Flag'  # Processed data directory
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            time.sleep(3)
            self.text_box.delete('1.0', 'end')
            message_folder_create_1 = "The directory " + path + " is created!"
            self.text_box.insert('end', message_folder_create_1)
            self.text_box.grid()

        path = 'Kittel_Linewidth'  # Processed data directory
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            print("The new directory is created!")
            print('--------------------------------------------\n')

        self.fit_entry_lf.grid(row=2, column=0, columnspan=20, padx=25, pady=0, ipadx=215, ipady=40)
        self.fit_entry_lf.grid_propagate(false)
        self.Temp_fit_Arr = []

        if self.temp_next == False:
            self.Temp_fit_InputStr = IntVar(value=self.read_temp[0])
        else:
            self.Temp_fit_InputStr = IntVar(value=self.read_temp[self.read_temp_next])
            self.temp_next = False
        self.Temp_fit_label = ttk.Label(self.fit_entry_lf, text="Fit Temperature: ", justify='left')
        self.Temp_fit_label.grid(row=3, column=1, padx=5)
        self.Temp_fit_entry = ttk.Entry(self.fit_entry_lf, textvariable=self.Temp_fit_InputStr, justify=CENTER)
        self.Temp_fit_entry.grid(row=3, column=2)
        self.Temp_fit_Arr.append(self.Temp_fit_entry)

        self.temperature_fit = self.Temp_fit_Arr[0].get()

        self.next_bt.destroy()
        self.offset_bt = ttk.Button(self.fr_input_right, text='Plot Offset',
                                    command=lambda: self.fmr_offset(self.temps_list), style='Toggle.TButton')
        self.offset_bt.grid(row=7, column=15, pady=25)
        self.strfit_bt = ttk.Button(self.fr_input_right, text='Start Fit',
                                    command=lambda: self.Fit_window(), style='Toggle.TButton')
        self.strfit_bt.grid(row=7, column=14, pady=25)
        # while self.temperature_fit not in self.read_temp:
        #     messagebox.showinfo(title="Warning", message='Invalid Entry. Please enter again!', icon='warning')

    def fmr_offset(self, __temps__):
        self.fr_input_right_image = Frame(master=root)
        self.fr_input_right_image.grid(row=0, column=2)
        self.image_window = True
        for temp_offset in self.read_temp:
            offset_val = 0
            df_offset = pd.read_csv(
                self.folder_selected_Fit + 'New_Square_{}_FMR-{}K-10ms-{}-deg-IP.csv'.format(self.ID_Fit,
                                                                                             temp_offset, self.degree),
                header=0)
            freq_df_offset = pd.read_csv(
                self.folder_selected_Fit + 'New_Square_{}_FMR-{}K-10ms-{}-deg-IP.csv'.format(self.ID_Fit, temp_offset,
                                                                                             self.degree),
                index_col=0, nrows=0).columns.tolist()  # Check the total coloumns in the file
            header_bot_freq_off = ''.join(freq_df_offset[0]).split(' ')
            CurFeq_off = float(header_bot_freq_off[0])
            header_sec_freq_off = ''.join(freq_df_offset[2]).split(' ')
            StepFeq_off = float(header_sec_freq_off[0]) - CurFeq_off
            offset_freq = CurFeq_off
            offset_setp_freq = StepFeq_off
            if file_exists('Flag/{}_{}K.csv'.format(self.ID_Fit, temp_offset)) == False:
                message = 'Plotting {}K offset plot!'.format(temp_offset)
                time.sleep(3)
                self.text_box.delete('1.0', 'end')
                message_folder_create_1 = message
                self.text_box.insert('end', message_folder_create_1)
                self.text_box.grid()
                total_cols = len(df_offset.axes[1])  # Axes of 0 is for a column

                # initialize the plot y range parameters
                plot_y_range_positive = 0
                plot_y_range_negative = 0
                # PPT Setup
                for col in range(0, total_cols, 2):
                    total_rows = len(
                        df_offset.axes[0])  # Define the maximum total rows in the file (largest instances)
                    # Check each row number to get rid of NaN instances
                    IsNaN: bool = True
                    while IsNaN:
                        RowFilter = df_offset.iat[total_rows - 1, col]
                        if math.isnan(RowFilter):
                            total_rows = total_rows - 1
                        else:
                            processedRow = total_rows
                            IsNaN = False

                    # Find the FMR signal maximum point and the minimum point
                    YMax = df_offset.iloc[:, col + 1].max(axis=0)
                    YMin = df_offset.iloc[:, col + 1].min(axis=0)
                    # Loop to find the peak and valley
                    if YMax > plot_y_range_positive:
                        plot_y_range_positive = YMax
                    if YMin < plot_y_range_negative:
                        plot_y_range_negative = YMin

                # Setup a reasonable plotting range
                y_plot_max = 1.2 * plot_y_range_positive
                y_plot_min = 1.2 * plot_y_range_negative
                if np.abs(y_plot_max) > np.abs(y_plot_min):
                    y_plot_min = -1 * y_plot_max
                elif np.abs(y_plot_max) < np.abs(y_plot_min):
                    y_plot_max = -1 * y_plot_min
                x_plot_max = df_offset.iloc[:, col].max(axis=0) + 100
                x_plot_min = df_offset.iloc[:, col].min(axis=0) - 100
                plt.rc('font', size=62)  # controls default text sizes
                plt.rc('axes', labelsize=100)  # fontsize of the x and y labels
                plt.rc('xtick', labelsize=44)  # fontsize of the tick labels
                plt.rc('ytick', labelsize=44)  # fontsize of the tick labels
                plt.rc('legend', fontsize=46)  # legend fontsize
                plt.rcParams.update({'figure.max_open_warning': 0})
                fig_size = (x_plot_max - x_plot_min) / (100) + 5
                plt.figure(figsize=(fig_size + 30, 45))

                for col in range(0, total_cols, 2):

                    total_rows = len(
                        df_offset.axes[0])  # Define the maximum total rows in the file (largest instances)
                    # Eliminate the Nan instances in each frequency
                    IsNaN: bool = True
                    while IsNaN:
                        RowFilter = df_offset.iat[total_rows - 1, col]
                        if math.isnan(RowFilter):
                            total_rows = total_rows - 1
                        else:
                            processedRow = total_rows
                            IsNaN = False
                    RealRow = processedRow  # Return the actual row number for the data processing
                    # Extract x and y values
                    X_offset = df_offset.iloc[0:RealRow, col]
                    X_offset = X_offset.astype(np.float64)
                    Y_offset = df_offset.iloc[0:RealRow, col + 1]
                    Y_offset = Y_offset.astype(np.float64)
                    plt.plot(X_offset, Y_offset + offset_val, linewidth=4.0, label='{} GHz'.format(offset_freq))
                    # plt.subplot().spines[:].set_linewidth(3.5)
                    plt.subplot().xaxis.set_major_locator(MultipleLocator(1000))
                    plt.subplot().xaxis.set_minor_locator(MultipleLocator(500))
                    plt.tick_params(axis='both', direction='in', width=8, length=15, which='major', pad=20)
                    plt.tick_params(axis='both', direction='in', width=8, length=10, which='minor', pad=20)
                    plt.ticklabel_format(axis='y', style='scientific')
                    plt.locator_params(axis="y", nbins=6)
                    plt.xlabel("Field (Oe)", fontname="Arial", labelpad=20)
                    plt.ylabel('{}K FMR (a.u)'.format(temp_offset), fontname="Arial")
                    # plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', frameon=False, labelspacing=0.3)
                    plt.tight_layout()
                    offset_freq += offset_setp_freq
                    offset_val += y_plot_max
                plt.savefig('WaterFall_Data/{}_Fitting_Temp{}_Rawdata.png'.format(self.ID_Fit, temp_offset), dpi=100)

                # offset_image_path = 'WaterFall_Data/{}_Fitting_Temp{}_Rawdata.png'.format(ID, temp_offset)
                # blank_slide_layout = prs.slide_layouts[6]
                # slide = prs.slides.add_slide(blank_slide_layout)
                # img = slide.shapes.add_picture(offset_image_path, Inches(1.0), Inches(1.0), Inches(15.0))
                # prs.save('{}_April.pptx'.format(ID))

                with open('Flag/{}_{}K.csv'.format(self.ID_Fit, temp_offset), 'w', newline='', encoding='UTF8') as test:
                    tester = csv.writer(test)
                    tester.writerow("Keep a record")

            # PPT Setup
            # if os.path.exists('{}_July.pptx'.format(ID)):
            #     prs = Presentation('{}_July.pptx'.format(ID))
            #     prs.slide_width = Inches(16)
            #     prs.slide_height = Inches(9)
            # else:
            #     prs = Presentation()
            #     prs.slide_width = Inches(16)
            #     prs.slide_height = Inches(9)
            #     title_slide_layout = prs.slide_layouts[0]
            #     slide = prs.slides.add_slide(title_slide_layout)
            #     title = slide.shapes.title
            #     title.text = "{} Fitted Data".format(ID)
            #     prs.save('{}_July.pptx'.format(ID))
            #     prs = Presentation('{}_July.pptx'.format(ID))
            #     prs.slide_width = Inches(16)
            #     prs.slide_height = Inches(9)
            #

        buttonClicked = False

        def image_forward():
            var.set(1)
            if self.click_loop < len(self.read_temp) - 1:
                self.click_loop += 1
            else:
                self.click_loop = self.click_loop

        def image_backward():
            var.set(2)
            if self.click_loop >= 1:
                self.click_loop -= 1

        def image_high_res():
            newWindow = Toplevel(root)
            self.opened = True
            newWindow.title("High Resolution Image")
            newWindow.geometry("1500x1500")
            # newWindow.eval('tk::PlaceWindow . center')
            image = Image.open(
                'WaterFall_Data/{}_Fitting_Temp{}_Rawdata.png'.format(self.ID_Fit, self.read_temp[self.click_loop]))
            resize_image = image.resize((1400, 1300))
            lst_img = ImageTk.PhotoImage(resize_image)
            self.image_label_Offset = Label(newWindow, image=lst_img)
            self.image_label_Offset.image = lst_img
            self.image_label_Offset.grid(row=0, column=0, columnspan=3)

        # for i in range(len(self.read_temp)):
        self.click_loop = 0
        while 0 <= self.click_loop < len(self.read_temp):
            image = Image.open(
                'WaterFall_Data/{}_Fitting_Temp{}_Rawdata.png'.format(self.ID_Fit, self.read_temp[self.click_loop]))
            resize_image = image.resize((400, 400))
            lst_img = ImageTk.PhotoImage(resize_image)
            self.image_label_Offset = Label(self.fr_input_right_image, image=lst_img)
            self.image_label_Offset.image = lst_img
            self.image_label_Offset.grid(row=0, column=0, columnspan=3)
            var = IntVar()
            self.img_button_nxt = Button(self.fr_input_right_image, text=">>>", command=lambda: image_forward())
            self.img_button_highres = Button(self.fr_input_right_image, text="High Resolution Image",
                                             command=lambda: image_high_res())
            self.img_button_bk = Button(self.fr_input_right_image, text="<<<", command=lambda: image_backward())
            self.img_back_bt = Button(self.fr_input_right_image, text='Back!', command=lambda: self._back_offset())
            self.img_back_bt.grid(row=2, column=1, pady=2)
            self.img_button_nxt.grid(row=1, column=2)
            self.img_button_highres.grid(row=1, column=1)
            self.img_button_bk.grid(row=1, column=0, padx=22)
            self.img_button_nxt.wait_variable(var)
        plt.close('all')

    def Fit_window(self):
        self.newWindow = Toplevel(root)
        self.newWindow.title("FMR Data Processing Window")
        # self.newWindow.eval('tk::PlaceWindow . center')
        self.opened = True
        # newWindow.geometry("500x500")
        self.fr_input_up_fit = ttk.Frame(self.newWindow)
        self.fr_input_up_fit.grid(row=0, column=0, ipadx=200, ipady=175, sticky='NWE')
        self.fr_input_up_fit.grid_propagate(False)
        self.fr_input_dw_fit = Frame(self.newWindow)
        self.fr_input_dw_fit.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw_fit.grid_propagate(False)
        self.fr_input_right_image_fit = Frame(self.newWindow)
        self.fr_input_right_image_fit.grid(row=0, column=2)
        self.image_window = True
        self.text_box_new_win = Text(self.fr_input_dw_fit, height=2, width=300, bg='#D3D3D3')

        self.rd_bt = IntVar(value=0)
        self.radio_frame = ttk.LabelFrame(self.fr_input_up_fit, text='Mode')
        self.radio_frame.grid(row=1, column=0, padx=25, pady=25, columnspan=20, ipadx=180, ipady=24)
        self.radio_frame.grid_propagate(false)
        self.manual = ttk.Radiobutton(self.radio_frame, text="Manual (Default)", variable=self.rd_bt, value=0)
        self.manual.grid(row=0, column=2, padx=15, sticky="nsew")
        self.auto = ttk.Radiobutton(self.radio_frame, text="Auto", variable=self.rd_bt, value=1, state='disabled')
        self.auto.grid(row=0, column=5, padx=15, sticky="nsew")
        if self.rd_bt.get() == 0:
            self.Mode = 'm'
        elif self.rd_bt.get() == 1:
            self.Mode = 'a'

        self.col = 0
        self.init_fitting_paras()
        self.select_freq_bool = False
        self.fit_start_bt = ttk.Button(self.fr_input_up_fit, text='Start (From Beginning)',
                                       command=lambda: self.datafit(self.temps_list), style='Toggle.TButton')
        self.fit_start_bt.grid(row=2, column=10)
        self.freqency_select = ttk.Button(self.fr_input_up_fit, text='Select Frequency',
                                          command=lambda: self.freq_select(), style='Toggle.TButton')
        self.freqency_select.grid(row=2, column=11)
        plt.close('all')
        # adding a frequency selected icon
        # Adding an icon start from begining or select specifc frequency to fit
        self.fr_input_right_image_fit = Frame(self.newWindow)
        self.fr_input_right_image_fit.grid(row=0, column=2)
        self.image_window = True

    def init_fit_list(self):
        self.FreqList = np.array([])
        offset_val = 0
        peak_one_list = []
        peak_two_list = []
        peak_three_list = []
        peak_four_list = []
        peak_five_list = []
        lw_one_list = []
        lw_one_error = []
        lw_two_list = []
        lw_two_error = []
        lw_three_list = []
        lw_three_error = []
        lw_four_list = []
        lw_four_error = []
        lw_five_list = []
        lw_five_error = []
        freq_list_one_peak = []
        freq_list_two_peak = []
        freq_list_three_peak = []
        freq_list_four_peak = []
        freq_list_five_peak = []
        kittelDF = pd.DataFrame()
        Kittel_Summary = pd.DataFrame()

    def init_fitting_paras(self):
        # Find the frequency range
        freq_df = pd.read_csv(
            self.folder_selected_Fit + 'New_Square_{}_FMR-{}K-10ms-{}-deg-IP.csv'.format(self.ID_Fit,
                                                                                         self.temperature_fit,
                                                                                         self.degree),
            index_col=0, nrows=0).columns.tolist()  # Check the total coloumns in the file
        header_bot_freq = []
        header_sec_freq = []
        header_bot_freq = ''.join(freq_df[0]).split(' ')
        self.BotFeq = float(header_bot_freq[0])
        header_sec_freq = ''.join(freq_df[2]).split(' ')
        self.StepFeq_Fit = float(header_sec_freq[0]) - self.BotFeq

        self.CurFeq = self.BotFeq
        # Read the processed data
        df = pd.read_csv(
            self.folder_selected_Fit + 'New_Square_{}_FMR-{}K-10ms-{}-deg-IP.csv'.format(self.ID_Fit,
                                                                                         self.temperature_fit,
                                                                                         self.degree),
            header=0)  # Check the total coloumns in the file
        self.total_cols = len(df.axes[1])  # Axes of 1 is for a column
        # initialize the plot y range parameters
        plot_y_range_positive = 0
        plot_y_range_negative = 0
        time.sleep(3)
        self.text_box.delete('1.0', 'end')
        message_folder_create_1 = "Initializing Parameters ......"
        self.text_box.insert('end', message_folder_create_1)
        self.text_box.grid()

    def freq_select(self):
        self.select_freq_bool = True

        #  Fix this the result is 0.02 more
        self.total_freq = int(self.total_cols / 2)
        print(self.total_cols)

        self.fit_start_bt.destroy()
        self.freqency_select.destroy()

        combolist = []
        init_freq = self.CurFeq

        getcontext().prec = 3
        for list_comb in range(self.total_freq):
            combolist.append(init_freq)
            init_freq = Decimal(init_freq) + Decimal(self.StepFeq_Fit)

        self.combolbox_freq_Arr = []
        self.combobox_label = ttk.Label(self.fr_input_up_fit, text="Select the Fitting Frequency: ")
        self.combobox_label.grid(row=2, column=0, padx=20, pady=5)
        self.Combo_Var = DoubleVar()
        self.combobox = ttk.Combobox(self.fr_input_up_fit, values=combolist, textvariable=self.Combo_Var)
        self.combobox.current(0)
        self.combobox.grid(row=2, column=1, padx=20, pady=5)
        self.combolbox_freq_Arr.append(self.combobox)
        self.freqency_submit = ttk.Button(self.fr_input_up_fit, text='Start',
                                          command=lambda: self.datafit(self.temps_list), style='Toggle.TButton')
        self.freqency_submit.grid(row=3, column=1)

    def datafit(self, __temps__):
        def Testing_ploting(X, Y, label):
            self.f_fit_test, self.ax_fit_test = plt.subplots(figsize=(10, 5))

            self.canvas = FigureCanvasTkAgg(self.f_fit_test, self.fr_input_right_image_fit)
            self.canvas.draw()
            self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=10, rowspan=10)
            self.fr_input_toolbar_fit = Frame(self.newWindow)
            self.fr_input_toolbar_fit.grid(row=2, column=0, sticky='w')
            self.fr_input_dw_fit.grid_propagate(False)
            self.toolbar = NavigationToolbar2Tk(self.canvas, self.fr_input_toolbar_fit)
            self.canvas._tkcanvas.grid(row=1, column=0, columnspan=10, rowspan=10)
            self.toolbar.update()

            self.ax_fit_test.set_title("{} {} K Test Plot".format(self.ID_Fit, self.temperature_fit), fontsize=10)
            line_plot = self.ax_fit_test.scatter(X, Y, s=0.5, color='Black')
            self.ax_fit_test.plot(X, Y, linewidth=1, color='Black', label='{} GHz'.format(label))
            plt.subplot().xaxis.set_major_locator(MultipleLocator(500))
            plt.subplot().xaxis.set_minor_locator(MultipleLocator(100))
            self.ax_fit_test.tick_params(axis='both', direction='in', width=1, length=10, which='major', pad=20)
            self.ax_fit_test.tick_params(axis='both', direction='in', width=1, length=6, which='minor', pad=20)
            self.ax_fit_test.set_xlabel("Field (Oe)")
            self.ax_fit_test.set_ylabel('{} K FMR (a.u)'.format(self.temperature_fit))
            self.ax_fit_test.legend(loc='upper right', frameon=False, labelspacing=0.3)
            plt.tight_layout()

            annotation = self.ax_fit_test.annotate(
                text='',
                xy=(0, 0),
                xytext=(15, 15),  # distance from x, y
                textcoords='offset points',
                bbox={'boxstyle': 'round', 'fc': 'w'},
                arrowprops={'arrowstyle': '->'}
            )
            annotation.set_visible(False)

            def motion_hover(event):
                annotation_visbility = annotation.get_visible()
                if event.inaxes == self.ax_fit_test:
                    is_contained, annotation_index = line_plot.contains(event)
                    if is_contained:
                        data_point_location = line_plot.get_offsets()[annotation_index['ind'][0]]
                        annotation.xy = data_point_location

                        text_label = '({0:.2f}, '.format(data_point_location[0]) + str(data_point_location[1]) + ')'
                        annotation.set_text(text_label)

                        # annotation.get_bbox_patch().set_facecolor('black')
                        annotation.set_alpha(0.4)

                        annotation.set_visible(True)
                        self.f_fit_test.canvas.draw_idle()
                    else:
                        if annotation_visbility:
                            annotation.set_visible(False)
                            self.f_fit_test.canvas.draw_idle()

            self.f_fit_test.canvas.mpl_connect('motion_notify_event', motion_hover)
            self.toolbar.update()
            self.canvas.draw()

        # while self.temperature_fit not in self.read_temp:
        #     # messagebox.showinfo(title="Warning", message='Invalid Entry. Please enter again!', icon='warning')
        # self.ID_Fit = self.ID_fit_Arr[0].get()

        self.temperature_fit = int(self.Temp_fit_Arr[0].get())
        index = self.read_temp.index(self.temperature_fit)
        read_temp_fit = self.read_temp[index:]

        p_list = np.array([])

        if self.select_freq_bool == True:
            self.freqency_submit.destroy()
            self.combobox_label.destroy()
            self.select_freq_bool = False
            self.CurFeq = float(self.combolbox_freq_Arr[0].get())
            print(self.CurFeq)
            self.col = int(2 * ((Decimal(self.CurFeq) - Decimal(self.BotFeq)) / Decimal(self.StepFeq_Fit)))
            print((Decimal(self.CurFeq) - Decimal(self.BotFeq)) / Decimal(self.StepFeq_Fit))
            print(self.col)
            self.combobox.destroy()

        range_mode = 'f'

        # fitting_acur = 99.25 / 100  # float(input('What is the desire fitting accuracy? (in percentage %) ')) / 100
        # plotting_acur = 0.1 / 100  # float(input(input'What is the desire plotting accuracy? (in percentage %) ')) / 100
        df = pd.read_csv(
            self.folder_selected_Fit + 'New_Square_{}_FMR-{}K-10ms-{}-deg-IP.csv'.format(self.ID_Fit,
                                                                                         self.temperature_fit,
                                                                                         self.degree),
            header=0)
        plot_y_range_positive = 0
        plot_y_range_negative = 0
        for col in range(0, self.total_cols, 2):
            total_rows = len(df.axes[0])  # Define the maximum total rows in the file (largest instances)
            # Check each row number to get rid of NaN instances
            IsNaN: bool = True
            while IsNaN:
                RowFilter = df.iat[total_rows - 1, col]
                if math.isnan(RowFilter):
                    total_rows = total_rows - 1
                else:
                    processedRow = total_rows
                    IsNaN = False

            # Find the FMR signal maximum point and the minimum point
            YMax = df.iloc[:, col + 1].max(axis=0)
            YMin = df.iloc[:, col + 1].min(axis=0)
            # Loop to find the peak and valley
            if YMax > plot_y_range_positive:
                plot_y_range_positive = YMax
            if YMin < plot_y_range_negative:
                plot_y_range_negative = YMin

        # Setup a reasonable plotting range
        y_plot_max = 1.2 * plot_y_range_positive
        y_plot_min = 1.2 * plot_y_range_negative
        if np.abs(y_plot_max) > np.abs(y_plot_min):
            y_plot_min = -1 * y_plot_max
        elif np.abs(y_plot_max) < np.abs(y_plot_min):
            y_plot_max = -1 * y_plot_min
        x_plot_max = df.iloc[:, col].max(axis=0) + 100
        x_plot_min = df.iloc[:, col].min(axis=0) - 100

        total_rows = len(df.axes[0])  # Define the maximum total rows in the file (largest instances)
        # Check the flag to avoid dupilicated fitting
        # if file_exists('Flag/{}_{}K_{}GHz.csv'.format(self.ID_Fit, self.temperature_fit, self.CurFeq)) == False:
        #     # Eliminate the Nan instances in each frequency
        IsNaN: bool = True
        while IsNaN:
            RowFilter = df.iat[total_rows - 1, self.col]
            if math.isnan(RowFilter):
                total_rows = total_rows - 1
            else:
                processedRow = total_rows
                IsNaN = False
        RealRow = processedRow  # Return the actual row number for the data processing
        YMax = df.iloc[:, self.col + 1].max(axis=0)
        YMin = df.iloc[:, self.col + 1].min(axis=0)
        XMax = df.iloc[:, self.col].max(axis=0)
        # Extract x and y values
        X = df.iloc[0:RealRow, self.col]
        self.X = X.astype(np.float64)
        Y = df.iloc[0:RealRow, self.col + 1]
        self.Y = Y.astype(np.float64)

        # Peak_def = Num_Peak
        label = self.CurFeq

        # Extract xmax/min  and ymax/min values
        YMaxIndex_fit = df.iloc[:, self.col + 1].idxmax(axis=0)
        CorrXMax_fit = df.iat[YMaxIndex_fit, self.col]  # The max position as field (x)
        YMinIndex_fit = df.iloc[:, self.col + 1].idxmax(axis=0)
        CorrXMin_fit = df.iat[YMinIndex_fit, self.col]

        range_min = 0
        range_max = 0
        range_setup = 700

        if CorrXMin_fit - range_setup <= 0:
            range_min = df.iloc[:, self.col].idxmin(axis=0)
            x_min_ref = df.iloc[:, self.col].min(axis=0)
        else:
            CorrXMin_fit = CorrXMin_fit - range_setup

            while df.iat[int(range_min), self.col] > CorrXMin_fit:
                range_min += 1
            x_min_ref = df.iat[range_min, self.col]

        if CorrXMin_fit + range_setup >= df.iloc[:, self.col].max(axis=0):
            range_max = df.iloc[:, self.col].idxmax(axis=0)
            x_max_ref = df.iloc[:, self.col].max(axis=0)
        else:
            while df.iat[int(range_max), self.col] > CorrXMax_fit + range_setup:
                range_max += 1
            x_max_ref = df.iat[range_max, self.col]

        total_X = np.abs(df.iat[range_min, self.col + 1] - df.iat[range_max, self.col + 1])
        # Extract x and y values
        time.sleep(3)
        self.text_box_new_win.delete('1.0', 'end')
        message_test_plot = "Test Plot ......"
        self.text_box_new_win.insert('end', message_test_plot)
        self.text_box_new_win.grid()
        Testing_ploting(X, Y, label)

        self.fit_start_bt.destroy()
        self.freqency_select.destroy()
        # test = input("Please press enter to continue...!")
        self.Peak_nxt_bt = ttk.Button(self.fr_input_up_fit, text='Next',
                                      command=lambda: self.fit_process_init(), style='Toggle.TButton')
        self.Peak_nxt_bt.grid(row=2, column=10)
        # self.ax_fit_test.clear()

    def fit_process_init(self):
        self.Peak_nxt_bt.destroy()
        self.peak_frame = ttk.LabelFrame(self.fr_input_up_fit, text='Peak Numbers Entry')
        self.peak_frame.grid(row=2, column=0, padx=25, columnspan=20, ipadx=180, ipady=24)
        self.peak_frame.grid_propagate(false)
        self.peak_peak_number_entry_Arr = []
        self.peak_number_entry_var = IntVar()
        self.peak_label = ttk.Label(self.peak_frame, text='Number of Peak')
        self.peak_label.grid(row=2, column=1, padx=25)
        self.peak_entry = ttk.Entry(self.peak_frame, textvariable=self.peak_number_entry_var, justify=CENTER)
        self.peak_entry.grid(row=2, column=3, padx=25)
        # self.peak_entry.wait_variable(self.peak_number_entry_var)
        self.peak_peak_number_entry_Arr.append(self.peak_entry)
        # self.PeakN = int(self.peak_peak_number_entry_Arr[0].get())
        self.fitted = False
        self.Fit_Next_bt = ttk.Button(self.fr_input_up_fit, text='Submit',
                                      command=lambda: self.fit_peak_process_init(), style='Toggle.TButton')
        self.Fit_Next_bt.grid(row=3, column=2, padx=150, pady=25)
        # self.peak_entry.wait_variable(self.peak_number_entry_var)
        # self.PeakN = int(self.peak_peak_number_entry_Arr[0].get())

    def peak_back(self):
        self.zero_Next_bt.destroy()
        self.zero_back.destroy()
        self.fitting_frame.destroy()
        self.fit_process_init()

    def fit_peak_process_init(self):
        self.Fit_Next_bt.destroy()
        self.PeakN = int(self.peak_peak_number_entry_Arr[0].get())
        if self.PeakN < 0 or self.PeakN > 5:
            time.sleep(3)
            self.text_box_new_win.delete('1.0', 'end')
            message_test_plot = "Please enter a valid number!"
            self.text_box_new_win.insert('end', message_test_plot)
            self.text_box_new_win.grid()
            self.fit_process_init()

        if self.PeakN == 0:
            self.fitting_frame = ttk.LabelFrame(self.fr_input_up_fit, text='Fitting Window')
            self.fitting_frame.grid(row=3, column=0, padx=25, columnspan=20, ipadx=180, ipady=30)
            self.fitting_frame.grid_propagate(false)
            self.zero_label = ttk.Label(self.fitting_frame, text='Continue to Next Fit ......')
            self.zero_label.grid(row=2, column=1, pady=15, padx=25)

            self.zero_Next_bt = ttk.Button(self.fr_input_up_fit, text='Next',
                                           command=lambda: self.Fit_process(), style='Toggle.TButton')
            self.zero_Next_bt.grid(row=4, column=2, padx=50, pady=25)
            self.zero_back = ttk.Button(self.fr_input_up_fit, text='Back',
                                        command=lambda: self.peak_back(), style='Toggle.TButton')
            self.zero_back.grid(row=4, column=3, padx=50, pady=25)

        elif self.PeakN == 1:
            self.fitting_frame = ttk.LabelFrame(self.fr_input_up_fit, text='Fitting Window')
            self.fitting_frame.grid(row=3, column=0, padx=25, columnspan=20, ipadx=180, ipady=38)
            self.fitting_frame.grid_propagate(false)
            self.one_firstPeak_Arr = []
            self.one_firstLW_Arr = []
            if self.fitted == True:
                self.one_firstPeak_entry_var = IntVar(value=self.First_Fit_result.params['hr'].value)
                self.one_firstLW_entry_var = IntVar(value=self.First_Fit_result.params['hw'].value)
            else:
                self.one_firstPeak_entry_var = IntVar()
                self.one_firstLW_entry_var = IntVar()
            self.one_firstPeak_label = ttk.Label(self.fitting_frame, text='First Resonance Peak (Oe)')
            self.one_firstPeak_label.grid(row=2, column=1, padx=25)
            self.one_firstLW_label = ttk.Label(self.fitting_frame, text='First Peak Linewidth')
            self.one_firstLW_label.grid(row=3, column=1, padx=25)

            self.one_firstPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.one_firstPeak_entry_var,
                                                 justify=CENTER)
            self.one_firstPeak_entry.grid(row=2, column=3, padx=8)
            self.one_firstLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.one_firstLW_entry_var,
                                               justify=CENTER)
            self.one_firstLW_entry.grid(row=3, column=3, padx=8)

            self.one_firstPeak_Arr.append(self.one_firstPeak_entry)
            self.one_firstLW_Arr.append(self.one_firstLW_entry)

            self.zero_Next_bt = ttk.Button(self.fr_input_up_fit, text='Fit',
                                           command=lambda: self.Fit_process(), style='Toggle.TButton')
            self.zero_Next_bt.grid(row=4, column=2, padx=50, pady=25)
            self.zero_back = ttk.Button(self.fr_input_up_fit, text='Back',
                                        command=lambda: self.peak_back(), style='Toggle.TButton')
            self.zero_back.grid(row=4, column=3, padx=50, pady=25)

        elif self.PeakN == 2:
            self.fr_input_up_fit.grid(row=0, column=0, ipadx=200, ipady=280, sticky='NWE')
            self.fr_input_up_fit.grid_propagate(False)
            self.fitting_frame = ttk.LabelFrame(self.fr_input_up_fit, text='Fitting Window')
            self.fitting_frame.grid(row=3, column=0, padx=25, columnspan=20, ipadx=180, ipady=68)
            self.fitting_frame.grid_propagate(false)

            self.two_firstPeak_Arr = []
            self.two_firstLW_Arr = []
            self.two_SecondPeak_Arr = []
            self.two_SecondLW_Arr = []

            if self.fitted == True:
                self.two_firstPeak_entry_var = IntVar(value=self.Second_Fit_result.params['hr1'].value)
                self.two_firstLW_entry_var = IntVar(value=self.Second_Fit_result.params['hw1'].value)
                self.two_SecondPeak_entry_var = IntVar(value=self.Second_Fit_result.params['hr2'].value)
                self.two_SecondLW_entry_var = IntVar(value=self.Second_Fit_result.params['hw2'].value)
            else:
                self.two_firstPeak_entry_var = IntVar()
                self.two_firstLW_entry_var = IntVar()
                self.two_SecondPeak_entry_var = IntVar()
                self.two_SecondLW_entry_var = IntVar()

            self.two_firstPeak_label = ttk.Label(self.fitting_frame, text='First Resonance Peak (Oe)')
            self.two_firstPeak_label.grid(row=2, column=1, padx=25)
            self.two_firstLW_label = ttk.Label(self.fitting_frame, text='First Peak Linewidth')
            self.two_firstLW_label.grid(row=3, column=1, padx=25)
            self.two_SecondPeak_label = ttk.Label(self.fitting_frame, text='Second Resonance Peak (Oe)')
            self.two_SecondPeak_label.grid(row=4, column=1, padx=25)
            self.two_SecondLW_label = ttk.Label(self.fitting_frame, text='Second Peak Linewidth')
            self.two_SecondLW_label.grid(row=5, column=1, padx=25)

            self.two_firstPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.two_firstPeak_entry_var,
                                                 justify=CENTER)
            self.two_firstPeak_entry.grid(row=2, column=2)
            self.two_firstLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.two_firstLW_entry_var,
                                               justify=CENTER)
            self.two_firstLW_entry.grid(row=3, column=2)
            self.two_SecondPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.two_SecondPeak_entry_var,
                                                  justify=CENTER)
            self.two_SecondPeak_entry.grid(row=4, column=2)
            self.two_SecondLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.two_SecondLW_entry_var,
                                                justify=CENTER)
            self.two_SecondLW_entry.grid(row=5, column=2)

            self.two_firstPeak_Arr.append(self.two_firstPeak_entry)
            self.two_firstLW_Arr.append(self.two_firstLW_entry)
            self.two_SecondPeak_Arr.append(self.two_SecondPeak_entry)
            self.two_SecondLW_Arr.append(self.two_SecondLW_entry)

            self.zero_Next_bt = ttk.Button(self.fr_input_up_fit, text='Fit',
                                           command=lambda: self.Fit_process(), style='Toggle.TButton')
            self.zero_Next_bt.grid(row=4, column=2, padx=50, pady=25)
            self.zero_back = ttk.Button(self.fr_input_up_fit, text='Back',
                                        command=lambda: self.peak_back(), style='Toggle.TButton')
            self.zero_back.grid(row=4, column=3, padx=50, pady=25)

        elif self.PeakN == 3:
            self.fr_input_up_fit.grid(row=0, column=0, ipadx=200, ipady=280, sticky='NWE')
            self.fr_input_up_fit.grid_propagate(False)
            self.fitting_frame = ttk.LabelFrame(self.fr_input_up_fit, text='Fitting Window')
            self.fitting_frame.grid(row=3, column=0, padx=25, columnspan=20, ipadx=180, ipady=95)
            self.fitting_frame.grid_propagate(false)

            self.three_firstPeak_Arr = []
            self.three_firstLW_Arr = []
            self.three_SecondPeak_Arr = []
            self.three_SecondLW_Arr = []
            self.three_ThirdPeak_Arr = []
            self.three_ThirdLW_Arr = []

            if self.fitted == True:
                self.three_firstPeak_entry_var = IntVar(value=self.Third_Fit_result.params['hr1'].value)
                self.three_firstLW_entry_var = IntVar(value=self.Third_Fit_result.params['hw1'].value)
                self.three_SecondPeak_entry_var = IntVar(value=self.Third_Fit_result.params['hr2'].value)
                self.three_SecondLW_entry_var = IntVar(value=self.Third_Fit_result.params['hw2'].value)
                self.three_ThirdPeak_entry_var = IntVar(value=self.Third_Fit_result.params['hr3'].value)
                self.three_ThirdLW_entry_var = IntVar(value=self.Third_Fit_result.params['hw3'].value)
            else:
                self.three_firstPeak_entry_var = IntVar()
                self.three_firstLW_entry_var = IntVar()
                self.three_SecondPeak_entry_var = IntVar()
                self.three_SecondLW_entry_var = IntVar()
                self.three_ThirdPeak_entry_var = IntVar()
                self.three_ThirdLW_entry_var = IntVar()

            self.three_firstPeak_label = ttk.Label(self.fitting_frame, text='First Resonance Peak (Oe)')
            self.three_firstPeak_label.grid(row=2, column=1, padx=25)
            self.three_firstLW_label = ttk.Label(self.fitting_frame, text='First Peak Linewidth')
            self.three_firstLW_label.grid(row=3, column=1, padx=25)
            self.three_SecondPeak_label = ttk.Label(self.fitting_frame, text='Second Resonance Peak (Oe)')
            self.three_SecondPeak_label.grid(row=4, column=1, padx=25)
            self.three_SecondLW_label = ttk.Label(self.fitting_frame, text='Second Peak Linewidth')
            self.three_SecondLW_label.grid(row=5, column=1, padx=25)
            self.three_ThirdPeak_label = ttk.Label(self.fitting_frame, text='Third Resonance Peak (Oe)')
            self.three_ThirdPeak_label.grid(row=6, column=1, padx=25)
            self.three_ThirdLW_label = ttk.Label(self.fitting_frame, text='Third Peak Linewidth')
            self.three_ThirdLW_label.grid(row=7, column=1, padx=25)

            self.three_firstPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.three_firstPeak_entry_var,
                                                   justify=CENTER)
            self.three_firstPeak_entry.grid(row=2, column=2)
            self.three_firstLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.three_firstLW_entry_var,
                                                 justify=CENTER)
            self.three_firstLW_entry.grid(row=3, column=2)
            self.three_SecondPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.three_SecondPeak_entry_var,
                                                    justify=CENTER)
            self.three_SecondPeak_entry.grid(row=4, column=2)
            self.three_SecondLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.three_SecondLW_entry_var,
                                                  justify=CENTER)
            self.three_SecondLW_entry.grid(row=5, column=2)
            self.three_ThirdPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.three_ThirdPeak_entry_var,
                                                   justify=CENTER)
            self.three_ThirdPeak_entry.grid(row=6, column=2)
            self.three_ThirdLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.three_ThirdLW_entry_var,
                                                 justify=CENTER)
            self.three_ThirdLW_entry.grid(row=7, column=2)

            self.three_firstPeak_Arr.append(self.three_firstPeak_entry)
            self.three_firstLW_Arr.append(self.three_firstLW_entry)
            self.three_SecondPeak_Arr.append(self.three_SecondPeak_entry)
            self.three_SecondLW_Arr.append(self.three_SecondLW_entry)
            self.three_ThirdPeak_Arr.append(self.three_ThirdPeak_entry)
            self.three_ThirdLW_Arr.append(self.three_ThirdLW_entry)

            self.zero_Next_bt = ttk.Button(self.fr_input_up_fit, text='Fit',
                                           command=lambda: self.Fit_process(), style='Toggle.TButton')
            self.zero_Next_bt.grid(row=4, column=2, padx=50, pady=25)
            self.zero_back = ttk.Button(self.fr_input_up_fit, text='Back',
                                        command=lambda: self.peak_back(), style='Toggle.TButton')
            self.zero_back.grid(row=4, column=3, padx=50, pady=25)

        elif self.PeakN == 4:
            self.fr_input_up_fit.grid(row=0, column=0, ipadx=200, ipady=280, sticky='NWE')
            self.fr_input_up_fit.grid_propagate(False)
            self.fitting_frame = ttk.LabelFrame(self.fr_input_up_fit, text='Fitting Window')
            self.fitting_frame.grid(row=3, column=0, padx=25, columnspan=20, ipadx=180, ipady=122)
            self.fitting_frame.grid_propagate(false)

            self.four_firstPeak_Arr = []
            self.four_firstLW_Arr = []
            self.four_SecondPeak_Arr = []
            self.four_SecondLW_Arr = []
            self.four_ThirdPeak_Arr = []
            self.four_ThirdLW_Arr = []
            self.four_FourthPeak_Arr = []
            self.four_FourthLW_Arr = []

            if self.fitted == True:
                self.four_firstPeak_entry_var = IntVar(value=self.Fourth_Fit_result.params['hr1'].value)
                self.four_firstLW_entry_var = IntVar(value=self.Fourth_Fit_result.params['hw1'].value)
                self.four_SecondPeak_entry_var = IntVar(value=self.Fourth_Fit_result.params['hr2'].value)
                self.four_SecondLW_entry_var = IntVar(value=self.Fourth_Fit_result.params['hw2'].value)
                self.four_ThirdPeak_entry_var = IntVar(value=self.Fourth_Fit_result.params['hr3'].value)
                self.four_ThirdLW_entry_var = IntVar(value=self.Fourth_Fit_result.params['hw3'].value)
                self.four_FourthPeak_entry_var = IntVar(value=self.Fourth_Fit_result.params['hr4'].value)
                self.four_FourthLW_entry_var = IntVar(value=self.Fourth_Fit_result.params['hw4'].value)
            else:
                self.four_firstPeak_entry_var = IntVar()
                self.four_firstLW_entry_var = IntVar()
                self.four_SecondPeak_entry_var = IntVar()
                self.four_SecondLW_entry_var = IntVar()
                self.four_ThirdPeak_entry_var = IntVar()
                self.four_ThirdLW_entry_var = IntVar()
                self.four_FourthPeak_entry_var = IntVar()
                self.four_FourthLW_entry_var = IntVar()

            self.four_firstPeak_label = ttk.Label(self.fitting_frame, text='First Resonance Peak (Oe)')
            self.four_firstPeak_label.grid(row=2, column=1, padx=25)
            self.four_firstLW_label = ttk.Label(self.fitting_frame, text='First Peak Linewidth')
            self.four_firstLW_label.grid(row=3, column=1, padx=25)
            self.four_SecondPeak_label = ttk.Label(self.fitting_frame, text='Second Resonance Peak (Oe)')
            self.four_SecondPeak_label.grid(row=4, column=1, padx=25)
            self.four_SecondLW_label = ttk.Label(self.fitting_frame, text='Second Peak Linewidth')
            self.four_SecondLW_label.grid(row=5, column=1, padx=25)
            self.four_ThirdPeak_label = ttk.Label(self.fitting_frame, text='Third Resonance Peak (Oe)')
            self.four_ThirdPeak_label.grid(row=6, column=1, padx=25)
            self.four_ThirdLW_label = ttk.Label(self.fitting_frame, text='Third Peak Linewidth')
            self.four_ThirdLW_label.grid(row=7, column=1, padx=25)
            self.four_FourthPeak_label = ttk.Label(self.fitting_frame, text='Fourth Resonance Peak (Oe)')
            self.four_FourthPeak_label.grid(row=8, column=1, padx=25)
            self.four_FourthLW_label = ttk.Label(self.fitting_frame, text='Fourth Peak Linewidth')
            self.four_FourthLW_label.grid(row=9, column=1, padx=25)

            self.four_firstPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.four_firstPeak_entry_var,
                                                  justify=CENTER)
            self.four_firstPeak_entry.grid(row=2, column=2)
            self.four_firstLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.four_firstLW_entry_var,
                                                justify=CENTER)
            self.four_firstLW_entry.grid(row=3, column=2)
            self.four_SecondPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.four_SecondPeak_entry_var,
                                                   justify=CENTER)
            self.four_SecondPeak_entry.grid(row=4, column=2)
            self.four_SecondLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.four_SecondLW_entry_var,
                                                 justify=CENTER)
            self.four_SecondLW_entry.grid(row=5, column=2)
            self.four_ThirdPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.four_ThirdPeak_entry_var,
                                                  justify=CENTER)
            self.four_ThirdPeak_entry.grid(row=6, column=2)
            self.four_ThirdLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.four_ThirdLW_entry_var,
                                                justify=CENTER)
            self.four_ThirdLW_entry.grid(row=7, column=2)
            self.four_FourthPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.four_FourthPeak_entry_var,
                                                   justify=CENTER)
            self.four_FourthPeak_entry.grid(row=8, column=2)
            self.four_FourthLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.four_FourthLW_entry_var,
                                                 justify=CENTER)
            self.four_FourthLW_entry.grid(row=9, column=2)

            self.four_firstPeak_Arr.append(self.four_firstPeak_entry)
            self.four_firstLW_Arr.append(self.four_firstLW_entry)
            self.four_SecondPeak_Arr.append(self.four_SecondPeak_entry)
            self.four_SecondLW_Arr.append(self.four_SecondLW_entry)
            self.four_ThirdPeak_Arr.append(self.four_ThirdPeak_entry)
            self.four_ThirdLW_Arr.append(self.four_ThirdLW_entry)
            self.four_FourthPeak_Arr.append(self.four_FourthPeak_entry)
            self.four_FourthLW_Arr.append(self.four_FourthLW_entry)

            self.zero_Next_bt = ttk.Button(self.fr_input_up_fit, text='Fit',
                                           command=lambda: self.Fit_process(), style='Toggle.TButton')
            self.zero_Next_bt.grid(row=4, column=2, padx=50, pady=25)
            self.zero_back = ttk.Button(self.fr_input_up_fit, text='Back',
                                        command=lambda: self.peak_back(), style='Toggle.TButton')
            self.zero_back.grid(row=4, column=3, padx=50, pady=25)

        elif self.PeakN == 5:
            self.fr_input_up_fit.grid(row=0, column=0, ipadx=200, ipady=280, sticky='NWE')
            self.fr_input_up_fit.grid_propagate(False)
            self.fitting_frame = ttk.LabelFrame(self.fr_input_up_fit, text='Fitting Window')
            self.fitting_frame.grid(row=3, column=0, padx=25, columnspan=20, ipadx=180, ipady=150)
            self.fitting_frame.grid_propagate(false)

            self.five_firstPeak_Arr = []
            self.five_firstLW_Arr = []
            self.five_SecondPeak_Arr = []
            self.five_SecondLW_Arr = []
            self.five_ThirdPeak_Arr = []
            self.five_ThirdLW_Arr = []
            self.five_FourthPeak_Arr = []
            self.five_FourthLW_Arr = []
            self.five_FifthPeak_Arr = []
            self.five_FifthLW_Arr = []

            if self.fitted == True:
                self.five_firstPeak_entry_var = IntVar(value=self.Fifth_Fit_result.params['hr1'].value)
                self.five_firstLW_entry_var = IntVar(value=self.Fifth_Fit_result.params['hw1'].value)
                self.five_SecondPeak_entry_var = IntVar(value=self.Fifth_Fit_result.params['hr2'].value)
                self.five_SecondLW_entry_var = IntVar(value=self.Fifth_Fit_result.params['hw2'].value)
                self.five_ThirdPeak_entry_var = IntVar(value=self.Fifth_Fit_result.params['hr3'].value)
                self.five_ThirdLW_entry_var = IntVar(value=self.Fifth_Fit_result.params['hw3'].value)
                self.five_FourthPeak_entry_var = IntVar(value=self.Fifth_Fit_result.params['hr4'].value)
                self.five_FourthLW_entry_var = IntVar(value=self.Fifth_Fit_result.params['hw4'].value)
                self.five_FifthPeak_entry_var = IntVar(value=self.Fifth_Fit_result.params['hr5'].value)
                self.five_FifthLW_entry_var = IntVar(value=self.Fifth_Fit_result.params['hw5'].value)
            else:
                self.five_firstPeak_entry_var = IntVar()
                self.five_firstLW_entry_var = IntVar()
                self.five_SecondPeak_entry_var = IntVar()
                self.five_SecondLW_entry_var = IntVar()
                self.five_ThirdPeak_entry_var = IntVar()
                self.five_ThirdLW_entry_var = IntVar()
                self.five_FourthPeak_entry_var = IntVar()
                self.five_FourthLW_entry_var = IntVar()
                self.five_FifthPeak_entry_var = IntVar()
                self.five_FifthLW_entry_var = IntVar()

            self.five_firstPeak_label = ttk.Label(self.fitting_frame, text='First Resonance Peak (Oe)')
            self.five_firstPeak_label.grid(row=2, column=1, padx=25)
            self.five_firstLW_label = ttk.Label(self.fitting_frame, text='First Peak Linewidth')
            self.five_firstLW_label.grid(row=3, column=1, padx=25)
            self.five_SecondPeak_label = ttk.Label(self.fitting_frame, text='Second Resonance Peak (Oe)')
            self.five_SecondPeak_label.grid(row=4, column=1, padx=25)
            self.five_SecondLW_label = ttk.Label(self.fitting_frame, text='Second Peak Linewidth')
            self.five_SecondLW_label.grid(row=5, column=1, padx=25)
            self.five_ThirdPeak_label = ttk.Label(self.fitting_frame, text='Third Resonance Peak (Oe)')
            self.five_ThirdPeak_label.grid(row=6, column=1, padx=25)
            self.five_ThirdLW_label = ttk.Label(self.fitting_frame, text='Third Peak Linewidth')
            self.five_ThirdLW_label.grid(row=7, column=1, padx=25)
            self.five_FourthPeak_label = ttk.Label(self.fitting_frame, text='Fourth Resonance Peak (Oe)')
            self.five_FourthPeak_label.grid(row=8, column=1, padx=25)
            self.five_FourthLW_label = ttk.Label(self.fitting_frame, text='Fourth Peak Linewidth')
            self.five_FourthLW_label.grid(row=9, column=1, padx=25)
            self.five_FifthPeak_label = ttk.Label(self.fitting_frame, text='Fifth Resonance Peak (Oe)')
            self.five_FifthPeak_label.grid(row=10, column=1, padx=25)
            self.five_FifthLW_label = ttk.Label(self.fitting_frame, text='Fifth Peak Linewidth')
            self.five_FifthLW_label.grid(row=11, column=1, padx=25)

            self.five_firstPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_firstPeak_entry_var,
                                                  justify=CENTER)
            self.five_firstPeak_entry.grid(row=2, column=2)
            self.five_firstLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_firstLW_entry_var,
                                                justify=CENTER)
            self.five_firstLW_entry.grid(row=3, column=2)
            self.five_SecondPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_SecondPeak_entry_var,
                                                   justify=CENTER)
            self.five_SecondPeak_entry.grid(row=4, column=2)
            self.five_SecondLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_SecondLW_entry_var,
                                                 justify=CENTER)
            self.five_SecondLW_entry.grid(row=5, column=2)
            self.five_ThirdPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_ThirdPeak_entry_var,
                                                  justify=CENTER)
            self.five_ThirdPeak_entry.grid(row=6, column=2)
            self.five_ThirdLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_ThirdLW_entry_var,
                                                justify=CENTER)
            self.five_ThirdLW_entry.grid(row=7, column=2)
            self.five_FourthPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_FourthPeak_entry_var,
                                                   justify=CENTER)
            self.five_FourthPeak_entry.grid(row=8, column=2)
            self.five_FourthLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_FourthLW_entry_var,
                                                 justify=CENTER)
            self.five_FourthLW_entry.grid(row=9, column=2)
            self.five_FifthPeak_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_FifthPeak_entry_var,
                                                  justify=CENTER)
            self.five_FifthPeak_entry.grid(row=10, column=2)
            self.five_FifthLW_entry = ttk.Entry(self.fitting_frame, textvariable=self.five_FifthLW_entry_var,
                                                justify=CENTER)
            self.five_FifthLW_entry.grid(row=11, column=2)

            self.five_firstPeak_Arr.append(self.five_firstPeak_entry)
            self.five_firstLW_Arr.append(self.five_firstLW_entry)
            self.five_SecondPeak_Arr.append(self.five_SecondPeak_entry)
            self.five_SecondLW_Arr.append(self.five_SecondLW_entry)
            self.five_ThirdPeak_Arr.append(self.five_ThirdPeak_entry)
            self.five_ThirdLW_Arr.append(self.five_ThirdLW_entry)
            self.five_FourthPeak_Arr.append(self.five_FourthPeak_entry)
            self.five_FourthLW_Arr.append(self.five_FourthLW_entry)
            self.five_FifthPeak_Arr.append(self.five_FifthPeak_entry)
            self.five_FifthLW_Arr.append(self.five_FifthLW_entry)

            self.zero_Next_bt = ttk.Button(self.fr_input_up_fit, text='Fit',
                                           command=lambda: self.Fit_process(), style='Toggle.TButton')
            self.zero_Next_bt.grid(row=4, column=2, padx=50, pady=25)
            self.zero_back = ttk.Button(self.fr_input_up_fit, text='Back',
                                        command=lambda: self.peak_back(), style='Toggle.TButton')
            self.zero_back.grid(row=4, column=3, padx=50, pady=25)

    def Fit_process(self):
        # Define the lorentzian function with one peak
        def lorentzian_derivative(x, a, hw, hr, s, v):
            return s * (hw ** 2 - (x - hr) ** 2) / ((x - hr) ** 2 + hw ** 2) ** 2 - a * 2 * hw * (x - hr) / (
                    (x - hr) ** 2 + hw ** 2) ** 2 + v

        # Define the lorentzian function with two peaks
        def lorentzian_derivative_two_peak(x, a1, hw1, hr1, s1, a2, hw2, hr2, s2, v):
            return lorentzian_derivative(x, a1, hw1, hr1, s1, 0) + lorentzian_derivative(x, a2, hw2, hr2, s2, v)

        def lorentzian_derivative_three_peak(x, a1, hw1, hr1, s1, a2, hw2, hr2, s2, a3, hw3, hr3, s3, v):
            return lorentzian_derivative(x, a1, hw1, hr1, s1, 0) + lorentzian_derivative(x, a2, hw2, hr2, s2, 0) \
                   + lorentzian_derivative(x, a3, hw3, hr3, s3, v)

        def lorentzian_derivative_four_peak(x, a1, hw1, hr1, s1, a2, hw2, hr2, s2, a3, hw3, hr3, s3, a4, hw4, hr4, s4,
                                            v):
            return lorentzian_derivative(x, a1, hw1, hr1, s1, 0) + lorentzian_derivative(x, a2, hw2, hr2, s2, 0) + \
                   lorentzian_derivative(x, a3, hw3, hr3, s3, 0) + lorentzian_derivative(x, a4, hw4, hr4, s4, v)

            # Define the lorentzian function with five peaks

        def lorentzian_derivative_five_peak(x, a1, hw1, hr1, s1, a2, hw2, hr2, s2, a3, hw3, hr3, s3, a4, hw4, hr4, s4,
                                            a5, hw5, hr5, s5, v):
            return lorentzian_derivative(x, a1, hw1, hr1, s1, 0) + lorentzian_derivative(x, a2, hw2, hr2, s2, 0) + \
                   lorentzian_derivative(x, a3, hw3, hr3, s3, 0) + lorentzian_derivative(x, a4, hw4, hr4, s4, 0) + \
                   lorentzian_derivative(x, a5, hw5, hr5, s5, v)

        self.init_fit_list()
        fitting_iteration = None
        # fitted_para = np.array([0])  # Store the fitted data
        # data = pd.DataFrame()
        # self.ax_fit_test.clear()
        self.FreqList = np.append(self.FreqList, self.CurFeq)
        # pyplot.close('all')
        time.sleep(3)
        self.text_box_new_win.delete('1.0', 'end')
        message_first_fit_plot = "Fitting the Data .."
        self.text_box_new_win.insert('end', message_first_fit_plot)
        self.text_box_new_win.grid()
        self.fr_input_right_fit_box = Frame(self.newWindow)
        self.fr_input_right_fit_box.grid(row=0, column=4)
        if self.PeakN == 0:
            name_list = ["NO PEAK!"]
            data_list = ["NO DATA!"]
            Result = 'y'
            time.sleep(3)
            self.text_box_new_win.delete('1.0', 'end')
            message_peak_zero = 'There is no peak in FMR Signal'
            self.text_box_new_win.insert('end', message_peak_zero)
            self.text_box_new_win.grid()

        elif self.PeakN == 1:
            self.resonance_peak = float(self.one_firstPeak_Arr[0].get())
            self.resonance_linewidth = float(self.one_firstLW_Arr[0].get())
            FirstPeak_Fitting_mod = Model(lorentzian_derivative)
            FirstPeak_Fitting_mod.set_param_hint('a', min=-1, max=1)
            FirstPeak_Fitting_mod.set_param_hint('s', min=-1, max=1)
            FirstPeak_Fitting_mod.set_param_hint('hr', value=self.resonance_peak, min=self.resonance_peak -200, max=self.resonance_peak + 200)
            FirstPeak_Fitting_mod.set_param_hint('hw', value=self.resonance_linewidth)
            First_pars = FirstPeak_Fitting_mod.make_params(a=0, s=0, v=0, hr=self.resonance_peak, hw=self.resonance_linewidth)
            self.First_Fit_result = FirstPeak_Fitting_mod.fit(self.Y, First_pars, x=self.X, max_nfev=fitting_iteration)

            if self.fitted == True:
                self.remove_line.remove()
                self.canvas.draw()

            # def test_1(params, x, ydata):
            #     s = params['s'].value
            #     hw = params['hw'].value
            #     hr = params['hr'].value
            #     a = params['a'].value
            #
            #     v = params['v'].value
            #     y_model = s * (hw ** 2 - (x - hr) ** 2) / ((x - hr) ** 2 + hw ** 2) ** 2 - \
            #               a * 2 * hw * (x - hr) / ((x - hr) ** 2 + hw ** 2) ** 2 + v
            #     return y_model - ydata
            #
            # params = lmfit.Parameters()
            # params.add('a', -0.01, min=-1, max=1)
            # params.add('s', 0.01, min=-1, max=1)
            # params.add('hr', self.resonance_peak)
            # params.add('hw', self.resonance_linewidth)
            #
            # params.add('v', 1)
            # self.First_Fit_result_Mini = lmfit.minimize(test_1, params, args=(self.X, self.Y), nan_policy='omit', method='leastsq')
            # lmfit.report_fit(self.First_Fit_result_Mini)
            #
            # self.remove_fit = self.ax_fit_test.plot(self.X, self.First_Fit_result_Mini.residual, '--', label='Mini fit',
            #                                         linewidth=2,
            #                                         color='Blue')

            self.remove_fit = self.ax_fit_test.plot(self.X, self.First_Fit_result.best_fit, '-', label='best fit',
                                                    linewidth=2, color='red')

            self.ax_fit_test.legend(frameon=False, labelspacing=0.3)
            plt.tight_layout()
            self.remove_line = self.remove_fit.pop(0)
            self.canvas.draw()
            # self.remove_line.remove()

            self.text_box_message_win = Text(self.fr_input_right_fit_box, height=30, width=40, bg='#D3D3D3')
            message_test_plot = self.First_Fit_result.fit_report()
            self.text_box_message_win.insert('end', message_test_plot)
            self.text_box_message_win.grid()
            self.fitted = True

        elif self.PeakN == 2:
            self.resonance_2peak_first = float(self.two_firstPeak_Arr[0].get())
            self.resonance_2linewidth_first = float(self.two_firstLW_Arr[0].get())
            self.resonance_2peak_second = float(self.two_SecondPeak_Arr[0].get())
            self.resonance_2linewidth_second = float(self.two_SecondLW_Arr[0].get())

            SecondPeak_Fitting_mod = Model(lorentzian_derivative_two_peak)

            SecondPeak_Fitting_mod.set_param_hint('a1', min=-1, max=1)
            SecondPeak_Fitting_mod.set_param_hint('s1', min=-1, max=1)
            SecondPeak_Fitting_mod.set_param_hint('hr1', value=self.resonance_2peak_first)
            SecondPeak_Fitting_mod.set_param_hint('hw1', value=self.resonance_2linewidth_first)
            SecondPeak_Fitting_mod.set_param_hint('a2', min=-1, max=1)
            SecondPeak_Fitting_mod.set_param_hint('s2', min=-1, max=1)
            SecondPeak_Fitting_mod.set_param_hint('hr2', value=self.resonance_2peak_second)
            SecondPeak_Fitting_mod.set_param_hint('hw2', value=self.resonance_2linewidth_second)

            Second_pars = SecondPeak_Fitting_mod.make_params(a1=0, a2=0, s1=0, s2=0, v=0)
            self.Second_Fit_result = SecondPeak_Fitting_mod.fit(self.Y, Second_pars, x=self.X, max_nfev=fitting_iteration)

            if self.fitted == True:
                self.remove_line.remove()
                self.canvas.draw()
            self.remove_fit = self.ax_fit_test.plot(self.X, self.Second_Fit_result.best_fit, '-', label='best fit',
                                                    linewidth=2,
                                                    color='red')
            self.ax_fit_test.legend(frameon=False, labelspacing=0.3)
            # plt.show()
            plt.tight_layout()
            self.remove_line = self.remove_fit.pop(0)
            self.canvas.draw()
            # self.remove_line.remove()

            self.text_box_message_win = Text(self.fr_input_right_fit_box, height=30, width=40, bg='#D3D3D3')
            message_test_plot = self.Second_Fit_result.fit_report()
            self.text_box_message_win.insert('end', message_test_plot)
            self.text_box_message_win.grid()
            self.fitted = True

        elif self.PeakN == 3:
            self.resonance_3peak_first = float(self.three_firstPeak_Arr[0].get())
            self.resonance_3linewidth_first = float(self.three_firstLW_Arr[0].get())
            self.resonance_3peak_second = float(self.three_SecondPeak_Arr[0].get())
            self.resonance_3linewidth_second = float(self.three_SecondLW_Arr[0].get())
            self.resonance_3peak_third = float(self.three_ThirdPeak_Arr[0].get())
            self.resonance_3linewidth_third = float(self.three_ThirdLW_Arr[0].get())

            ThirdPeak_Fitting_mod = Model(lorentzian_derivative_three_peak)

            ThirdPeak_Fitting_mod.set_param_hint('a1', min=-1, max=1)
            ThirdPeak_Fitting_mod.set_param_hint('s1', min=-1, max=1)
            ThirdPeak_Fitting_mod.set_param_hint('hr1', value=self.resonance_3peak_first)
            ThirdPeak_Fitting_mod.set_param_hint('hw1', value=self.resonance_3linewidth_first)
            ThirdPeak_Fitting_mod.set_param_hint('a2', min=-1, max=1)
            ThirdPeak_Fitting_mod.set_param_hint('s2', min=-1, max=1)
            ThirdPeak_Fitting_mod.set_param_hint('hr2', value=self.resonance_3peak_second)
            ThirdPeak_Fitting_mod.set_param_hint('hw2', value=self.resonance_3linewidth_second)
            ThirdPeak_Fitting_mod.set_param_hint('a3', min=-1, max=1)
            ThirdPeak_Fitting_mod.set_param_hint('s3', min=-1, max=1)
            ThirdPeak_Fitting_mod.set_param_hint('hr3', value=self.resonance_3peak_third)
            ThirdPeak_Fitting_mod.set_param_hint('hw3', value=self.resonance_3linewidth_third)

            Third_pars = ThirdPeak_Fitting_mod.make_params(a1=0, a2=0, a3=0, s1=0, s2=0, s3=0, v=0)
            self.Third_Fit_result = ThirdPeak_Fitting_mod.fit(self.Y, Third_pars, x=self.X, max_nfev=fitting_iteration)
            if self.fitted == True:
                self.remove_line.remove()
                self.canvas.draw()

            # def test(params, x, ydata):
            #     s1 = params['s1'].value
            #     hw1 = params['hw1'].value
            #     hr1 = params['hr1'].value
            #     a1 = params['a1'].value
            #     s2 = params['s2'].value
            #     hw2 = params['hw2'].value
            #     hr2 = params['hr2'].value
            #     a2 = params['a2'].value
            #     s3 = params['s3'].value
            #     hw3 = params['hw3'].value
            #     hr3 = params['hr3'].value
            #     a3 = params['a3'].value
            #     v = params['v'].value
            #     y_model = s1 * (hw1 ** 2 - (x - hr1) ** 2) / ((x - hr1) ** 2 + hw1 ** 2) ** 2 - \
            #               a1 * 2 * hw1 * (x - hr1) / ((x - hr1) ** 2 + hw1 ** 2) ** 2 + \
            #               s2 * (hw2 ** 2 - (x - hr2) ** 2) / ((x - hr2) ** 2 + hw2 ** 2) ** 2 - \
            #               a2 * 2 * hw2 * (x - hr2) / ((x - hr2) ** 2 + hw2 ** 2) ** 2 + \
            #               s3 * (hw3 ** 2 - (x - hr3) ** 2) / ((x - hr3) ** 2 + hw3 ** 2) ** 2 - \
            #               a3 * 2 * hw3 * (x - hr3) / ((x - hr3) ** 2 + hw3 ** 2) ** 2 + v
            #     return y_model - ydata
            #
            # params = lmfit.Parameters()
            # params.add('a1', -0.01, min=-1, max=1)
            # params.add('s1', 0.01, min=-1, max=1)
            # params.add('hr1', self.resonance_3peak_first)
            # params.add('hw1', self.resonance_3linewidth_first)
            # params.add('a2', -0.01, min=-1, max=1)
            # params.add('s2', 0.01, min=-1, max=1)
            # params.add('hr2', self.resonance_3peak_second)
            # params.add('hw2', self.resonance_3linewidth_second)
            # params.add('a3', -0.01, min=-1, max=1)
            # params.add('s3', 0.01, min=-1, max=1)
            # params.add('hr3', self.resonance_3peak_third)
            # params.add('hw3', self.resonance_3linewidth_third)
            # params.add('v', 1)
            # self.Third_Fit_result_Mini = lmfit.minimize(test, params, args=(self.X, self.Y), nan_policy='omit', method='leastsq')
            # lmfit.report_fit(self.Third_Fit_result_Mini)
            #
            # self.remove_fit = self.ax_fit_test.plot(self.X, self.Third_Fit_result_Mini.residual, '--', label='Mini fit',
            #                                         linewidth=2,
            #                                         color='Blue')
            #

            self.remove_fit = self.ax_fit_test.plot(self.X, self.Third_Fit_result.best_fit, '-', label='best fit',
                                                    linewidth=2,
                                                    color='red')
            self.ax_fit_test.legend(frameon=False, labelspacing=0.3)
            plt.tight_layout()
            self.remove_line = self.remove_fit.pop(0)
            self.canvas.draw()
            # self.remove_line.remove()

            self.text_box_message_win = Text(self.fr_input_right_fit_box, height=30, width=40, bg='#D3D3D3')
            message_test_plot = self.Third_Fit_result.fit_report()
            self.text_box_message_win.insert('end', message_test_plot)
            self.text_box_message_win.grid()
            self.fitted = True

        elif self.PeakN == 4:
            self.resonance_4peak_first = float(self.four_firstPeak_Arr[0].get())
            self.resonance_4linewidth_first = float(self.four_firstLW_Arr[0].get())
            self.resonance_4peak_second = float(self.four_SecondPeak_Arr[0].get())
            self.resonance_4linewidth_second = float(self.four_SecondLW_Arr[0].get())
            self.resonance_4peak_third = float(self.four_ThirdPeak_Arr[0].get())
            self.resonance_4linewidth_third = float(self.four_ThirdLW_Arr[0].get())
            self.resonance_4peak_fourth = float(self.four_FourthPeak_Arr[0].get())
            self.resonance_4linewidth_fourth = float(self.four_FourthLW_Arr[0].get())

            FourPeak_Fitting_mod = Model(lorentzian_derivative_four_peak)

            FourPeak_Fitting_mod.set_param_hint('a1', min=-1, max=1)
            FourPeak_Fitting_mod.set_param_hint('s1', min=-1, max=1)
            FourPeak_Fitting_mod.set_param_hint('hr1', value=self.resonance_4peak_first)
            FourPeak_Fitting_mod.set_param_hint('hw1', value=self.resonance_4linewidth_first)
            FourPeak_Fitting_mod.set_param_hint('a2', min=-1, max=1)
            FourPeak_Fitting_mod.set_param_hint('s2', min=-1, max=1)
            FourPeak_Fitting_mod.set_param_hint('hr2', value=self.resonance_4peak_second)
            FourPeak_Fitting_mod.set_param_hint('hw2', value=self.resonance_4linewidth_second)
            FourPeak_Fitting_mod.set_param_hint('a3', min=-1, max=1)
            FourPeak_Fitting_mod.set_param_hint('s3', min=-1, max=1)
            FourPeak_Fitting_mod.set_param_hint('hr3', value=self.resonance_4peak_third)
            FourPeak_Fitting_mod.set_param_hint('hw3', value=self.resonance_4linewidth_third)
            FourPeak_Fitting_mod.set_param_hint('a4', min=-1, max=1)
            FourPeak_Fitting_mod.set_param_hint('s4', min=-1, max=1)
            FourPeak_Fitting_mod.set_param_hint('hr4', value=self.resonance_4peak_fourth)
            FourPeak_Fitting_mod.set_param_hint('hw4', value=self.resonance_4linewidth_fourth)

            Fourth_pars = FourPeak_Fitting_mod.make_params(a1=0, a2=0, a3=0, a4=0, s1=0, s2=0, s3=0, s4=0, v=0)
            self.Fourth_Fit_result = FourPeak_Fitting_mod.fit(self.Y, Fourth_pars, x=self.X, max_nfev=fitting_iteration)

            if self.fitted == True:
                self.remove_line.remove()
                self.canvas.draw()
            self.remove_fit = self.ax_fit_test.plot(self.X, self.Fourth_Fit_result.best_fit, '-', label='best fit',
                                                    linewidth=2, color='red')
            self.ax_fit_test.legend(frameon=False, labelspacing=0.3)
            # plt.show()
            remove_line = self.remove_fit.pop(0)
            self.canvas.draw()

            self.text_box_message_win = Text(self.fr_input_right_fit_box, height=30, width=40, bg='#D3D3D3')
            message_test_plot = self.Fourth_Fit_result.fit_report()
            self.text_box_message_win.insert('end', message_test_plot)
            self.text_box_message_win.grid()
            self.fitted = True

        elif self.PeakN == 5:
            self.resonance_5peak_first = float(self.five_firstPeak_Arr[0].get())
            self.resonance_5linewidth_first = float(self.five_firstLW_Arr[0].get())
            self.resonance_5peak_second = float(self.five_SecondPeak_Arr[0].get())
            self.resonance_5linewidth_second = float(self.five_SecondLW_Arr[0].get())
            self.resonance_5peak_third = float(self.five_ThirdPeak_Arr[0].get())
            self.resonance_5linewidth_third = float(self.five_ThirdLW_Arr[0].get())
            self.resonance_5peak_fourth = float(self.five_FourthPeak_Arr[0].get())
            self.resonance_5linewidth_fourth = float(self.five_FourthLW_Arr[0].get())
            self.resonance_5peak_fifth = float(self.five_FifthPeak_Arr[0].get())
            self.resonance_5linewidth_fifth = float(self.five_FifthLW_Arr[0].get())

            FivePeak_Fitting_mod = Model(lorentzian_derivative_five_peak)

            FivePeak_Fitting_mod.set_param_hint('a1', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('s1', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('hr1', value=self.resonance_5peak_first)
            FivePeak_Fitting_mod.set_param_hint('hw1', value=self.resonance_5linewidth_first)
            FivePeak_Fitting_mod.set_param_hint('a2', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('s2', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('hr2', value=self.resonance_5peak_second)
            FivePeak_Fitting_mod.set_param_hint('hw2', value=self.resonance_5linewidth_second)
            FivePeak_Fitting_mod.set_param_hint('a3', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('s3', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('hr3', value=self.resonance_5peak_third)
            FivePeak_Fitting_mod.set_param_hint('hw3', value=self.resonance_5linewidth_third)
            FivePeak_Fitting_mod.set_param_hint('a4', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('s4', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('hr4', value=self.resonance_5peak_fourth)
            FivePeak_Fitting_mod.set_param_hint('hw4', value=self.resonance_5linewidth_fourth)
            FivePeak_Fitting_mod.set_param_hint('a5', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('s5', min=-1, max=1)
            FivePeak_Fitting_mod.set_param_hint('hr5', value=self.resonance_5peak_fifth)
            FivePeak_Fitting_mod.set_param_hint('hw5', value=self.resonance_5linewidth_fifth)

            Fifth_pars = FivePeak_Fitting_mod.make_params(a1=0, a2=0, a3=0, a4=0, a5=0, s1=0, s2=0, s3=0, s4=0,
                                                          s5=0, v=0)
            self.Fifth_Fit_result = FivePeak_Fitting_mod.fit(self.Y, Fifth_pars, x=self.X, max_nfev=fitting_iteration)

            if self.fitted == True:
                self.remove_line.remove()
                self.canvas.draw()
            self.remove_fit = self.ax_fit_test.plot(self.X, self.Fifth_Fit_result.best_fit, '-', label='best fit',
                                                    linewidth=2,
                                                    color='red')
            self.ax_fit_test.legend(frameon=False, labelspacing=0.3)
            # plt.show()
            self.remove_line = self.remove_fit.pop(0)
            self.canvas.draw()
            # remove_line.remove()

            self.text_box_message_win = Text(self.fr_input_right_fit_box, height=30, width=40, bg='#D3D3D3')
            message_test_plot = self.Fifth_Fit_result.fit_report()
            self.text_box_message_win.insert('end', message_test_plot)
            self.text_box_message_win.grid()
            self.fitted = True

        self.zero_Next_bt.destroy()
        self.zero_Next_bt = ttk.Button(self.fr_input_up_fit, text='Next Frequency',
                                       command=lambda: self.export_fit_next_fit(), style='Toggle.TButton')
        self.zero_Next_bt.grid(row=5, column=3, padx=5)
        self.zero_back.destroy()
        self.zero_back = ttk.Button(self.fr_input_up_fit, text='Reselect Peak Number',
                                    command=lambda: self.reSelect(), style='Toggle.TButton')
        self.zero_back.grid(row=5, column=4, padx=5)
        self.fit_bt = ttk.Button(self.fr_input_up_fit, text='Refit',
                                 command=lambda: self.keep_fit(), style='Toggle.TButton')
        self.fit_bt.grid(row=4, column=3, padx=5, pady=5)
        self.zero_Next_sel_bt = ttk.Button(self.fr_input_up_fit, text='Select Frequency',
                                           command=lambda: self.export_fit_sel_fit(), style='Toggle.TButton')
        self.zero_Next_sel_bt.grid(row=5, column=2, padx=5)
        # pygame.mixer.init()
        # pygame.mixer.music.load('Notification/Note.mp3')
        # pygame.mixer.music.play()

    def export(self):
        self.text_box_new_win.delete('1.0', 'end')
        message_peak_zero = 'Fitting is Successful!'
        self.text_box_new_win.insert('end', message_peak_zero)
        self.text_box_new_win.grid()

        if self.PeakN == 0:
            with open('Flag/{}_{}K_{}GHz.csv'.format(self.ID_Fit, self.temperature_fit,
                                                     self.CurFeq), 'w', newline='',
                      encoding='UTF8') as test:
                tester = csv.writer(test)
                tester.writerow("Keep a record")
        else:
            with open('Flag/{}_{}K_{}GHz.csv'.format(self.ID_Fit, self.temperature_fit,
                                                     self.CurFeq), 'w', newline='',
                      encoding='UTF8') as test:
                tester = csv.writer(test)
                tester.writerow("Keep a record")

            if self.PeakN == 1:
                Kittel_LW = pd.DataFrame()
                AS = pd.DataFrame()
                First_Curfreq = []
                First_peak = []
                First_peak_Error = []
                First_lw = []
                First_lw_Error = []
                First_asym = []
                First_asym_Error = []
                First_sym = []
                First_sym_Error = []

                First_Curfreq.append(self.CurFeq)
                First_peak.append(self.First_Fit_result.params['hr'].value)
                First_peak_Error.append(self.First_Fit_result.params['hr'].stderr)
                First_lw.append(self.First_Fit_result.params['hw'].value)
                First_lw_Error.append(self.First_Fit_result.params['hw'].stderr)
                First_asym.append(self.First_Fit_result.params['a'].value)
                First_asym_Error.append(self.First_Fit_result.params['a'].stderr)
                First_sym.append(self.First_Fit_result.params['s'].value)
                First_sym_Error.append(self.First_Fit_result.params['s'].stderr)

                add_peak_1 = pd.DataFrame(
                    list(zip(First_peak, First_peak_Error, First_Curfreq, First_lw, First_lw_Error)))
                add_as_1 = pd.DataFrame(
                    list(zip(First_Curfreq, First_asym, First_asym_Error, First_sym, First_sym_Error)))
                AS = pd.concat([AS, add_as_1], ignore_index=True, axis=1)
                AS.to_csv(
                    'Asymmetric_Symmetric/{}_Asymmetric_Symmetric_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                    mode='a', index=False, encoding='utf-8-sig', header=False)
                Kittel_LW = pd.concat([Kittel_LW, add_peak_1], ignore_index=True, axis=1)
                Kittel_LW.to_csv('Kittel_Linewidth/{}_Peak_Linewidth_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                                 mode='a', index=False, encoding='utf-8-sig', header=False)

            elif self.PeakN == 2:
                Kittel_LW = pd.DataFrame()
                AS = pd.DataFrame()
                Second_Curfreq = []
                Second_peak1 = []
                Second_peak1_Error = []
                Second_peak2 = []
                Second_peak2_Error = []
                Second_lw1 = []
                Second_lw1_Error = []
                Second_lw2 = []
                Second_lw2_Error = []
                Second_asym1 = []
                Second_asym1_Error = []
                Second_asym2 = []
                Second_asym2_Error = []
                Second_sym1 = []
                Second_sym1_Error = []
                Second_sym2 = []
                Second_sym2_Error = []

                Second_Curfreq.append(self.CurFeq)
                Second_peak1.append(self.Second_Fit_result.params['hr1'].value)
                Second_peak1_Error.append(self.Second_Fit_result.params['hr1'].stderr)
                Second_peak2.append(self.Second_Fit_result.params['hr2'].value)
                Second_peak2_Error.append(self.Second_Fit_result.params['hr2'].stderr)
                Second_lw1.append(self.Second_Fit_result.params['hw1'].value)
                Second_lw1_Error.append(self.Second_Fit_result.params['hw1'].stderr)
                Second_lw2.append(self.Second_Fit_result.params['hw2'].value)
                Second_lw2_Error.append(self.Second_Fit_result.params['hw2'].stderr)
                Second_asym1.append(self.Second_Fit_result.params['a1'].value)
                Second_asym1_Error.append(self.Second_Fit_result.params['a1'].stderr)
                Second_asym2.append(self.Second_Fit_result.params['a2'].value)
                Second_asym2_Error.append(self.Second_Fit_result.params['a2'].stderr)
                Second_sym1.append(self.Second_Fit_result.params['s1'].value)
                Second_sym1_Error.append(self.Second_Fit_result.params['s1'].stderr)
                Second_sym2.append(self.Second_Fit_result.params['s2'].value)
                Second_sym2_Error.append(self.Second_Fit_result.params['s2'].stderr)

                add_peak_1 = pd.DataFrame(
                    list(zip(Second_peak1, Second_peak1_Error, Second_Curfreq, Second_lw1, Second_lw1_Error)))
                add_peak_2 = pd.DataFrame(
                    list(zip(Second_peak2, Second_peak2_Error, Second_Curfreq, Second_lw2, Second_lw2_Error)))
                add_as_1 = pd.DataFrame(
                    list(zip(Second_Curfreq, Second_asym1, Second_asym1_Error, Second_sym1, Second_sym1_Error)))
                add_as_2 = pd.DataFrame(
                    list(zip(Second_Curfreq, Second_asym2, Second_asym2_Error, Second_sym2, Second_sym2_Error)))
                AS = pd.concat([AS, add_as_1, add_as_2], ignore_index=True, axis=1)
                AS.to_csv(
                    'Asymmetric_Symmetric/{}_Asymmetric_Symmetric_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                    mode='a', index=False, encoding='utf-8-sig', header=False)
                Kittel_LW = pd.concat([Kittel_LW, add_peak_1, add_peak_2], ignore_index=True, axis=1)
                Kittel_LW.to_csv('Kittel_Linewidth/{}_Peak_Linewidth_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                                 mode='a', index=False, encoding='utf-8-sig', header=False)

            elif self.PeakN == 3:
                Kittel_LW = pd.DataFrame()
                AS = pd.DataFrame()
                Third_Curfreq = []
                Third_peak1 = []
                Third_peak1_Error = []
                Third_peak2 = []
                Third_peak2_Error = []
                Third_peak3 = []
                Third_peak3_Error = []
                Third_lw1 = []
                Third_lw1_Error = []
                Third_lw2 = []
                Third_lw2_Error = []
                Third_lw3 = []
                Third_lw3_Error = []
                Third_asym1 = []
                Third_asym1_Error = []
                Third_asym2 = []
                Third_asym2_Error = []
                Third_asym3 = []
                Third_asym3_Error = []
                Third_sym1 = []
                Third_sym1_Error = []
                Third_sym2 = []
                Third_sym2_Error = []
                Third_sym3 = []
                Third_sym3_Error = []

                Third_Curfreq.append(self.CurFeq)
                Third_peak1.append(self.Third_Fit_result.params['hr1'].value)
                Third_peak1_Error.append(self.Third_Fit_result.params['hr1'].stderr)
                Third_peak2.append(self.Third_Fit_result.params['hr2'].value)
                Third_peak2_Error.append(self.Third_Fit_result.params['hr2'].stderr)
                Third_peak3.append(self.Third_Fit_result.params['hr3'].value)
                Third_peak3_Error.append(self.Third_Fit_result.params['hr3'].stderr)
                Third_lw1.append(self.Third_Fit_result.params['hw1'].value)
                Third_lw1_Error.append(self.Third_Fit_result.params['hw1'].stderr)
                Third_lw2.append(self.Third_Fit_result.params['hw2'].value)
                Third_lw2_Error.append(self.Third_Fit_result.params['hw2'].stderr)
                Third_lw3.append(self.Third_Fit_result.params['hw3'].value)
                Third_lw3_Error.append(self.Third_Fit_result.params['hw3'].stderr)
                Third_asym1.append(self.Third_Fit_result.params['a1'].value)
                Third_asym1_Error.append(self.Third_Fit_result.params['a1'].stderr)
                Third_asym2.append(self.Third_Fit_result.params['a2'].value)
                Third_asym2_Error.append(self.Third_Fit_result.params['a2'].stderr)
                Third_asym3.append(self.Third_Fit_result.params['a3'].value)
                Third_asym3_Error.append(self.Third_Fit_result.params['a3'].stderr)
                Third_sym1.append(self.Third_Fit_result.params['s1'].value)
                Third_sym1_Error.append(self.Third_Fit_result.params['s1'].stderr)
                Third_sym2.append(self.Third_Fit_result.params['s2'].value)
                Third_sym2_Error.append(self.Third_Fit_result.params['s2'].stderr)
                Third_sym3.append(self.Third_Fit_result.params['s3'].value)
                Third_sym3_Error.append(self.Third_Fit_result.params['s3'].stderr)

                add_peak_1 = pd.DataFrame(
                    list(zip(Third_peak1, Third_peak1_Error, Third_Curfreq, Third_lw1, Third_lw1_Error)))
                add_peak_2 = pd.DataFrame(
                    list(zip(Third_peak2, Third_peak2_Error, Third_Curfreq, Third_lw2, Third_lw2_Error)))
                add_peak_3 = pd.DataFrame(
                    list(zip(Third_peak3, Third_peak3_Error, Third_Curfreq, Third_lw3, Third_lw3_Error)))
                add_as_1 = pd.DataFrame(
                    list(zip(Third_Curfreq, Third_asym1, Third_asym1_Error, Third_sym1, Third_sym1_Error)))
                add_as_2 = pd.DataFrame(
                    list(zip(Third_Curfreq, Third_asym2, Third_asym2_Error, Third_sym2, Third_sym2_Error)))
                add_as_3 = pd.DataFrame(
                    list(zip(Third_Curfreq, Third_asym3, Third_asym3_Error, Third_sym3, Third_sym3_Error)))
                AS = pd.concat([AS, add_as_1, add_as_2, add_as_3], ignore_index=True, axis=1)
                AS.to_csv(
                    'Asymmetric_Symmetric/{}_Asymmetric_Symmetric_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                    mode='a', index=False, encoding='utf-8-sig', header=False)
                Kittel_LW = pd.concat([Kittel_LW, add_peak_1, add_peak_2, add_peak_3], ignore_index=True, axis=1)
                Kittel_LW.to_csv('Kittel_Linewidth/{}_Peak_Linewidth_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                                 mode='a', index=False, encoding='utf-8-sig', header=False)

            elif self.PeakN == 4:
                Kittel_LW = pd.DataFrame()
                AS = pd.DataFrame()
                Four_Curfreq = []
                Four_peak1 = []
                Four_peak1_Error = []
                Four_peak2 = []
                Four_peak2_Error = []
                Four_peak3 = []
                Four_peak3_Error = []
                Four_peak4 = []
                Four_peak4_Error = []
                Four_lw1 = []
                Four_lw1_Error = []
                Four_lw2 = []
                Four_lw2_Error = []
                Four_lw3 = []
                Four_lw3_Error = []
                Four_lw4 = []
                Four_lw4_Error = []
                Four_asym1 = []
                Four_asym1_Error = []
                Four_asym2 = []
                Four_asym2_Error = []
                Four_asym3 = []
                Four_asym3_Error = []
                Four_asym4 = []
                Four_asym4_Error = []
                Four_sym1 = []
                Four_sym1_Error = []
                Four_sym2 = []
                Four_sym2_Error = []
                Four_sym3 = []
                Four_sym3_Error = []
                Four_sym4 = []
                Four_sym4_Error = []

                Four_Curfreq.append(self.CurFeq)
                Four_peak1.append(self.Fourth_Fit_result.params['hr1'].value)
                Four_peak1_Error.append(self.Fourth_Fit_result.params['hr1'].stderr)
                Four_peak2.append(self.Fourth_Fit_result.params['hr2'].value)
                Four_peak2_Error.append(self.Fourth_Fit_result.params['hr2'].stderr)
                Four_peak3.append(self.Fourth_Fit_result.params['hr3'].value)
                Four_peak3_Error.append(self.Fourth_Fit_result.params['hr3'].stderr)
                Four_peak4.append(self.Fourth_Fit_result.params['hr4'].value)
                Four_peak4_Error.append(self.Fourth_Fit_result.params['hr4'].stderr)
                Four_lw1.append(self.Fourth_Fit_result.params['hw1'].value)
                Four_lw1_Error.append(self.Fourth_Fit_result.params['hw1'].stderr)
                Four_lw2.append(self.Fourth_Fit_result.params['hw2'].value)
                Four_lw2_Error.append(self.Fourth_Fit_result.params['hw2'].stderr)
                Four_lw3.append(self.Fourth_Fit_result.params['hw3'].value)
                Four_lw3_Error.append(self.Fourth_Fit_result.params['hw3'].stderr)
                Four_lw4.append(self.Fourth_Fit_result.params['hw4'].value)
                Four_lw4_Error.append(self.Fourth_Fit_result.params['hw4'].stderr)
                Four_asym1.append(self.Fourth_Fit_result.params['a1'].value)
                Four_asym1_Error.append(self.Fourth_Fit_result.params['a1'].stderr)
                Four_asym2.append(self.Fourth_Fit_result.params['a2'].value)
                Four_asym2_Error.append(self.Fourth_Fit_result.params['a2'].stderr)
                Four_asym3.append(self.Fourth_Fit_result.params['a3'].value)
                Four_asym3_Error.append(self.Fourth_Fit_result.params['a3'].stderr)
                Four_asym4.append(self.Fourth_Fit_result.params['a4'].value)
                Four_asym4_Error.append(self.Fourth_Fit_result.params['a4'].stderr)
                Four_sym1.append(self.Fourth_Fit_result.params['s1'].value)
                Four_sym1_Error.append(self.Fourth_Fit_result.params['s1'].stderr)
                Four_sym2.append(self.Fourth_Fit_result.params['s2'].value)
                Four_sym2_Error.append(self.Fourth_Fit_result.params['s2'].stderr)
                Four_sym3.append(self.Fourth_Fit_result.params['s3'].value)
                Four_sym3_Error.append(self.Fourth_Fit_result.params['s3'].stderr)
                Four_sym4.append(self.Fourth_Fit_result.params['s4'].value)
                Four_sym4_Error.append(self.Fourth_Fit_result.params['s4'].stderr)

                add_peak_1 = pd.DataFrame(
                    list(zip(Four_peak1, Four_peak1_Error, Four_Curfreq, Four_lw1, Four_lw1_Error)))
                add_peak_2 = pd.DataFrame(
                    list(zip(Four_peak2, Four_peak2_Error, Four_Curfreq, Four_lw2, Four_lw2_Error)))
                add_peak_3 = pd.DataFrame(
                    list(zip(Four_peak3, Four_peak3_Error, Four_Curfreq, Four_lw3, Four_lw3_Error)))
                add_peak_4 = pd.DataFrame(
                    list(zip(Four_peak4, Four_peak4_Error, Four_Curfreq, Four_lw4, Four_lw4_Error)))
                add_as_1 = pd.DataFrame(
                    list(zip(Four_Curfreq, Four_asym1, Four_asym1_Error, Four_sym1, Four_sym1_Error)))
                add_as_2 = pd.DataFrame(
                    list(zip(Four_Curfreq, Four_asym2, Four_asym2_Error, Four_sym2, Four_sym2_Error)))
                add_as_3 = pd.DataFrame(
                    list(zip(Four_Curfreq, Four_asym3, Four_asym3_Error, Four_sym3, Four_sym3_Error)))
                add_as_4 = pd.DataFrame(
                    list(zip(Four_Curfreq, Four_asym4, Four_asym4_Error, Four_sym4, Four_sym4_Error)))

                AS = pd.concat([AS, add_as_1, add_as_2, add_as_3, add_as_4], ignore_index=True, axis=1)
                AS.to_csv(
                    'Asymmetric_Symmetric/{}_Asymmetric_Symmetric_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                    mode='a', index=False, encoding='utf-8-sig', header=False)
                Kittel_LW = pd.concat([Kittel_LW, add_peak_1, add_peak_2, add_peak_3, add_peak_4], ignore_index=True,
                                      axis=1)
                Kittel_LW.to_csv('Kittel_Linewidth/{}_Peak_Linewidth_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                                 mode='a', index=False, encoding='utf-8-sig', header=False)

            elif self.PeakN == 5:
                Kittel_LW = pd.DataFrame()
                AS = pd.DataFrame()
                Five_Curfreq = []
                Five_peak1 = []
                Five_peak1_Error = []
                Five_peak2 = []
                Five_peak2_Error = []
                Five_peak3 = []
                Five_peak3_Error = []
                Five_peak4 = []
                Five_peak4_Error = []
                Five_peak5 = []
                Five_peak5_Error = []
                Five_lw1 = []
                Five_lw1_Error = []
                Five_lw2 = []
                Five_lw2_Error = []
                Five_lw3 = []
                Five_lw3_Error = []
                Five_lw4 = []
                Five_lw4_Error = []
                Five_lw5 = []
                Five_lw5_Error = []
                Five_asym1 = []
                Five_asym1_Error = []
                Five_asym2 = []
                Five_asym2_Error = []
                Five_asym3 = []
                Five_asym3_Error = []
                Five_asym4 = []
                Five_asym4_Error = []
                Five_asym5 = []
                Five_asym5_Error = []
                Five_sym1 = []
                Five_sym1_Error = []
                Five_sym2 = []
                Five_sym2_Error = []
                Five_sym3 = []
                Five_sym3_Error = []
                Five_sym4 = []
                Five_sym4_Error = []
                Five_sym5 = []
                Five_sym5_Error = []

                Five_Curfreq.append(self.CurFeq)
                Five_peak1.append(self.Fifth_Fit_result.params['hr1'].value)
                Five_peak1_Error.append(self.Fifth_Fit_result.params['hr1'].stderr)
                Five_peak2.append(self.Fifth_Fit_result.params['hr2'].value)
                Five_peak2_Error.append(self.Fifth_Fit_result.params['hr2'].stderr)
                Five_peak3.append(self.Fifth_Fit_result.params['hr3'].value)
                Five_peak3_Error.append(self.Fifth_Fit_result.params['hr3'].stderr)
                Five_peak4.append(self.Fifth_Fit_result.params['hr4'].value)
                Five_peak4_Error.append(self.Fifth_Fit_result.params['hr4'].stderr)
                Five_peak5.append(self.Fifth_Fit_result.params['hr5'].value)
                Five_peak5_Error.append(self.Fifth_Fit_result.params['hr5'].stderr)
                Five_lw1.append(self.Fifth_Fit_result.params['hw1'].value)
                Five_lw1_Error.append(self.Fifth_Fit_result.params['hw1'].stderr)
                Five_lw2.append(self.Fifth_Fit_result.params['hw2'].value)
                Five_lw2_Error.append(self.Fifth_Fit_result.params['hw2'].stderr)
                Five_lw3.append(self.Fifth_Fit_result.params['hw3'].value)
                Five_lw3_Error.append(self.Fifth_Fit_result.params['hw3'].stderr)
                Five_lw4.append(self.Fifth_Fit_result.params['hw4'].value)
                Five_lw4_Error.append(self.Fifth_Fit_result.params['hw4'].stderr)
                Five_lw5.append(self.Fifth_Fit_result.params['hw5'].value)
                Five_lw5_Error.append(self.Fifth_Fit_result.params['hw5'].stderr)
                Five_asym1.append(self.Fifth_Fit_result.params['a1'].value)
                Five_asym1_Error.append(self.Fifth_Fit_result.params['a1'].stderr)
                Five_asym2.append(self.Fifth_Fit_result.params['a2'].value)
                Five_asym2_Error.append(self.Fifth_Fit_result.params['a2'].stderr)
                Five_asym3.append(self.Fifth_Fit_result.params['a3'].value)
                Five_asym3_Error.append(self.Fifth_Fit_result.params['a3'].stderr)
                Five_asym4.append(self.Fifth_Fit_result.params['a4'].value)
                Five_asym4_Error.append(self.Fifth_Fit_result.params['a4'].stderr)
                Five_asym5.append(self.Fifth_Fit_result.params['a5'].value)
                Five_asym5_Error.append(self.Fifth_Fit_result.params['a5'].stderr)
                Five_sym1.append(self.Fifth_Fit_result.params['s1'].value)
                Five_sym1_Error.append(self.Fifth_Fit_result.params['s1'].stderr)
                Five_sym2.append(self.Fifth_Fit_result.params['s2'].value)
                Five_sym2_Error.append(self.Fifth_Fit_result.params['s2'].stderr)
                Five_sym3.append(self.Fifth_Fit_result.params['s3'].value)
                Five_sym3_Error.append(self.Fifth_Fit_result.params['s3'].stderr)
                Five_sym4.append(self.Fifth_Fit_result.params['s4'].value)
                Five_sym4_Error.append(self.Fifth_Fit_result.params['s4'].stderr)
                Five_sym5.append(self.Fifth_Fit_result.params['s5'].value)
                Five_sym5_Error.append(self.Fifth_Fit_result.params['s5'].stderr)

                add_peak_1 = pd.DataFrame(
                    list(zip(Five_peak1, Five_peak1_Error, Five_Curfreq, Five_lw1, Five_lw1_Error)))
                add_peak_2 = pd.DataFrame(
                    list(zip(Five_peak2, Five_peak2_Error, Five_Curfreq, Five_lw2, Five_lw2_Error)))
                add_peak_3 = pd.DataFrame(
                    list(zip(Five_peak3, Five_peak3_Error, Five_Curfreq, Five_lw3, Five_lw3_Error)))
                add_peak_4 = pd.DataFrame(
                    list(zip(Five_peak4, Five_peak4_Error, Five_Curfreq, Five_lw4, Five_lw4_Error)))
                add_peak_5 = pd.DataFrame(
                    list(zip(Five_peak5, Five_peak5_Error, Five_Curfreq, Five_lw5, Five_lw5_Error)))
                add_as_1 = pd.DataFrame(
                    list(zip(Five_Curfreq, Five_asym1, Five_asym1_Error, Five_sym1, Five_sym1_Error)))
                add_as_2 = pd.DataFrame(
                    list(zip(Five_Curfreq, Five_asym2, Five_asym2_Error, Five_sym2, Five_sym2_Error)))
                add_as_3 = pd.DataFrame(
                    list(zip(Five_Curfreq, Five_asym3, Five_asym3_Error, Five_sym3, Five_sym3_Error)))
                add_as_4 = pd.DataFrame(
                    list(zip(Five_Curfreq, Five_asym4, Five_asym4_Error, Five_sym4, Five_sym4_Error)))
                add_as_5 = pd.DataFrame(
                    list(zip(Five_Curfreq, Five_asym5, Five_asym5_Error, Five_sym5, Five_sym5_Error)))

                AS = pd.concat([AS, add_as_1, add_as_2, add_as_3, add_as_4, add_as_5], ignore_index=True, axis=1)
                AS.to_csv(
                    'Asymmetric_Symmetric/{}_Asymmetric_Symmetric_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                    mode='a', index=False, encoding='utf-8-sig', header=False)
                Kittel_LW = pd.concat([Kittel_LW, add_peak_1, add_peak_2, add_peak_3, add_peak_4, add_peak_5],
                                      ignore_index=True, axis=1)
                Kittel_LW.to_csv('Kittel_Linewidth/{}_Peak_Linewidth_{}K.csv'.format(self.ID_Fit, self.temperature_fit),
                                 mode='a', index=False, encoding='utf-8-sig', header=False)

    def keep_fit(self):
        self.fit_bt.destroy()
        self.fit_peak_process_init()
        self.zero_back.destroy()
        self.zero_Next_bt.destroy()
        self.fit_bt = ttk.Button(self.fr_input_up_fit, text='Fit',
                                 command=lambda: self.Fit_process(), style='Toggle.TButton')
        self.fit_bt.grid(row=4, column=3, padx=5, pady=5)

    def reSelect(self):
        # self.zero_Next_sel_bt.destroy()
        self.remove_line.remove()
        self.canvas.draw()
        self.fit_bt.destroy()
        self.zero_Next_sel_bt.destroy()
        self.zero_back.destroy()
        self.zero_Next_bt.destroy()
        self.fitting_frame.destroy()
        self.peak_frame.destroy()
        # self.freqency_select.destroy()
        self.fr_input_right_fit_box.destroy()
        self.fit_process_init()

    def export_fit_next_fit(self):
        self.export()
        time.sleep(3)
        self.text_box_new_win.delete('1.0', 'end')
        message_peak_first = '{}K frequency {} is done'.format(self.temperature_fit, self.CurFeq)
        self.text_box_new_win.insert('end', message_peak_first)
        self.text_box_new_win.grid()
        plt.savefig('OutputFit/{}_Fitting_Temp{}_Fre{}.png'.format(self.ID_Fit, self.temperature_fit, self.CurFeq),
                    dpi=100)
        self.ax_fit_test.clear()
        self.canvas.draw()
        self.fitting_frame.destroy()
        self.zero_back.destroy()
        self.zero_Next_bt.destroy()
        self.zero_Next_sel_bt.destroy()
        self.fr_input_right_fit_box.destroy()
        self.peak_frame.destroy()
        if self.col + 2 < self.total_cols:
            self.col += 2
            self.CurFeq += self.StepFeq_Fit
            self.datafit(self.temps_list)
        else:
            self.newWindow.destroy()
            messagebox.showinfo(title="Success", message='You reach to the last data!')
            self.fit_entry_lf.grid(row=2, column=0, columnspan=20, padx=25, pady=0, ipadx=215, ipady=25)
            self.fit_entry_lf.grid_propagate(false)
            self.Temp_fit_label.destroy()
            self.Temp_fit_entry.destroy()
            self.offset_bt.destroy()
            self.strfit_bt.destroy()
            self.temp_next = True
            if self.temperature_fit < self.read_temp[-1]:
                self.read_temp_next = self.read_temp.index(self.temperature_fit)
                self.read_temp_next += 1
                self.select_fit_temp()
            else:
                self.read_temp_next = 0
                self.select_fit_temp()

    def export_fit_sel_fit(self):
        self.export()
        time.sleep(3)
        self.text_box_new_win.delete('1.0', 'end')
        message_peak_first = '{}K frequency {} is done'.format(self.temperature_fit, self.CurFeq)
        self.text_box_new_win.insert('end', message_peak_first)
        self.text_box_new_win.grid()
        plt.savefig('OutputFit/{}_Fitting_Temp{}_Fre{}.png'.format(self.ID_Fit, self.temperature_fit, self.CurFeq),
                    dpi=100)
        self.ax_fit_test.clear()
        self.canvas.draw()
        self.newWindow.destroy()
        self.Fit_window()

    def Init_Kittel(self):
        self.fr_input_right.destroy()
        self.return_kittel_file = StringVar()
        self.fr_input_right = Frame(master=root)
        self.fr_input_right.grid(row=0, column=1, ipadx=5, ipady=10)
        self.init_lf = ttk.LabelFrame(self.fr_input_right, text='Initiation')
        self.init_lf.grid(row=1, column=0, padx=25, pady=25, columnspan=20, ipadx=200, ipady=24)
        self.init_lf.grid_propagate(false)
        self.folder_label = ttk.Label(self.init_lf, text="Please select the Data File: ", justify='center')
        self.folder_label.grid(row=0, column=0, padx=5)
        self.kittel_file_open_bt = ttk.Button(self.init_lf, text='Select File',
                                              command=lambda: self.Kittel_LW_entry())
        self.kittel_file_open_bt.grid(row=0, column=1, padx=150, ipadx=1, ipady=1)

    def Kittel_LW_entry(self):
        self.kittel_file_selected = filedialog.askopenfilename(initialdir="Kittel_Linewidth/",
                                                               title="Select a Data File",
                                                               filetypes=(
                                                                   ("csv files", "*.csv"), ("xlsx file", "*.xlsx"),
                                                                   ("all files", "*.*")))
        self.fr_input_dw.destroy()
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=200, bg='#D3D3D3')
        message_folder = 'The file selected is: ' + self.kittel_file_selected
        self.text_box.insert('end', message_folder)
        self.text_box.grid()

        self.KLW_entry_lf = ttk.LabelFrame(self.fr_input_right, text='Entries')
        self.KLW_entry_lf.grid(row=2, column=0, columnspan=20, padx=25, pady=0, ipadx=200, ipady=40)
        self.KLW_entry_lf.grid_propagate(false)
        self.ID_KLW_InputStr = StringVar()
        self.Temp_KLW_Doub = DoubleVar()
        self.ID_KLW_Arr = []
        self.Temp_KLW_Arr = []
        self.ID_KLW_label = ttk.Label(self.KLW_entry_lf, text="Sample ID: ", justify='left')
        self.ID_KLW_label.grid(row=2, column=1, padx=5)
        self.ID_KLW_entry = ttk.Entry(self.KLW_entry_lf, textvariable=self.ID_KLW_InputStr, justify=CENTER)
        self.ID_KLW_entry.grid(row=2, column=2, padx=130)
        self.ID_KLW_Arr.append(self.ID_KLW_entry)

        self.Temp_KLW_label = ttk.Label(self.KLW_entry_lf, text="Temperature (K): ", justify='left')
        self.Temp_KLW_label.grid(row=3, column=1, padx=5)
        self.Temp_KLW_entry = ttk.Entry(self.KLW_entry_lf, textvariable=self.Temp_KLW_Doub, justify=CENTER)
        self.Temp_KLW_entry.grid(row=3, column=2, padx=130)
        self.Temp_KLW_Arr.append(self.Temp_KLW_entry)

        self.Kittel_data_frame = pd.read_csv(self.kittel_file_selected, header=None)
        self.total_kittel_cols = len(self.Kittel_data_frame.axes[1])

        self.total_magnonband = int(self.total_kittel_cols / 5)

        self.lw_process_bt = ttk.Button(self.fr_input_right, text='Plot Linwewidth',
                                        command=lambda: self.Linewidth_process_init(), style='Toggle.TButton')
        self.lw_process_bt.grid(row=4, column=9, pady=25)

        self.kittel_process_bt = ttk.Button(self.fr_input_right, text='Fit Kittel',
                                            command=lambda: self.Kittel_process_init(), style='Toggle.TButton')
        self.kittel_process_bt.grid(row=4, column=7, pady=25)

        self.kittel_back_bt = ttk.Button(self.fr_input_right, text='Back',
                                         command=lambda: self._back())
        self.kittel_back_bt.grid(row=4, column=11, pady=25)

        self.kittel_reset_bt = ttk.Button(self.fr_input_right, text='Reset',
                                          command=lambda: self._reset_Kittel())
        self.kittel_reset_bt.grid(row=4, column=13, pady=25, ipadx=0.1, ipady=1)

    def Linewidth_process_init(self):
        self.lw_process_bt.destroy()
        self.kittel_process_bt.destroy()
        self.LW_entry_lf = ttk.LabelFrame(self.fr_input_right, text='Magnon Band Selection')
        self.LW_entry_lf.grid(row=3, column=0, columnspan=20, padx=25, pady=0, ipadx=200, ipady=25)
        self.LW_entry_lf.grid_propagate(false)

        self.LW_ID = self.ID_KLW_Arr[0].get()
        self.LW_Temp = self.Temp_KLW_Arr[0].get()
        # range_validation = (root.register(validate), '%P', '%W')
        self.f, self.ax_lw = plt.subplots(figsize=(10, 8))
        self.ax_lw.set_title("{} {}K LineWidth Plot".format(self.LW_ID, self.LW_Temp), fontsize=10)

        plt.close('all')
        self.fr_input_right_image = Frame(master=root)
        self.fr_input_right_image.grid(row=0, column=2)
        self.image_window = True
        self.canvas_LW = FigureCanvasTkAgg(self.f, self.fr_input_right_image)
        self.canvas_LW.get_tk_widget().grid(row=0, column=0, columnspan=10, rowspan=10)
        self.fr_input_toolbar_fit = Frame(self.fr_input_right)
        self.fr_input_toolbar_fit.grid(row=2, column=0, sticky='w')

        self.LW_Magnon_InputInt = IntVar()
        self.LW_Magnon_Arr = []
        self.LW_Magnon_label = ttk.Label(self.LW_entry_lf, text="Select Magnon Band: ", justify='left')
        self.LW_Magnon_label.grid(row=3, column=1, padx=5)
        self.LW_Magnon_spinbox = ttk.Spinbox(self.LW_entry_lf, from_=1, to=self.total_magnonband,
                                             textvariable=self.LW_Magnon_InputInt)
        self.LW_Magnon_spinbox.grid(row=3, column=2, padx=120)
        self.LW_Magnon_Arr.append(self.LW_Magnon_spinbox)

        self.lw_plot_bt = ttk.Button(self.fr_input_right, text='Plot',
                                     command=lambda: self.Linewidth_process(), style='Toggle.TButton')
        self.lw_plot_bt.grid(row=4, column=9, pady=25)

        self.kittel_back_bt.destroy()
        self.linewidth_back_bt = ttk.Button(self.fr_input_right, text='Back',
                                            command=lambda: self._lw_back())
        self.linewidth_back_bt.grid(row=4, column=11, pady=25)

    def Linewidth_process(self):

        path = 'Kittel_Linewidth_Fig'  # Processed data directory
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            self.text_box.delete('1.0', 'end')
            self.text_box = Text(self.fr_input_dw, height=2, width=200, bg='#D3D3D3')
            message_folder = "The new directory is created!"
            self.text_box.insert('end', message_folder)
            self.text_box.grid()

        self.selected_magnon_lw = int(self.LW_Magnon_Arr[0].get())
        begin_col = self.selected_magnon_lw * 5 - 5
        end_col = self.selected_magnon_lw * 5
        temporal_df = self.Kittel_data_frame.iloc[:, begin_col:end_col]
        temporal_df = temporal_df.dropna()
        temporal_df = temporal_df.reset_index(drop=True)
        col = len(temporal_df.axes[0])

        # peak_one_list = temporal_df.iloc[:, 0]
        # peak_one_list_error = temporal_df.iloc[:, 1]
        freq_list = temporal_df.iloc[:, 2]
        lw_list = temporal_df.iloc[:, 3]
        lw_list_error = temporal_df.iloc[:, 4]

        matplotlib.rcParams.update(matplotlib.rcParamsDefault)
        self.ax_lw.errorbar(freq_list, lw_list, yerr=lw_list_error, fmt='s',
                            label="{} {}K LineWidth".format(self.LW_ID, self.LW_Temp), linewidth=2.0, capsize=8,
                            markersize=8)
        self.ax_lw.ticklabel_format(axis='y', style='scientific')
        self.ax_lw.set_xlabel('Frequency (GHz)', fontname="Arial", labelpad=20)
        self.ax_lw.set_ylabel('{}K Linewidth \u0394w'.format(self.LW_Temp), fontname="Arial", labelpad=20)
        self.ax_lw.legend(loc='best', frameon=False, labelspacing=0.3)
        self.canvas_LW.draw()
        # plt.tight_layout()
        plt.savefig('Kittel_Linewidth_Fig/{}_Fitting_Temp{}_Linewidth.png'.format(self.LW_ID, self.LW_Temp), dpi=100)
        # pyplot.show()
        self.linewidth_back_bt.destroy()
        self.linewidth_back_bt = ttk.Button(self.fr_input_right, text='Back',
                                            command=lambda: self._lw_back())
        self.linewidth_back_bt.grid(row=4, column=11, pady=25)

    # add a radio button at top to select fitting model
    # the model will include the fitting of A

    def Kittel_process_init(self):
        self.newWindow = Toplevel(root)
        self.newWindow.title("Kittel Fitting Window")
        # self.newWindow.eval('tk::PlaceWindow . center')
        self.opened = True
        # newWindow.geometry("500x500")
        self.fr_input_up_kittel = ttk.Frame(self.newWindow)
        self.fr_input_up_kittel.grid(row=0, column=0, ipadx=220, ipady=175, sticky='NWE')
        self.fr_input_up_kittel.grid_propagate(False)
        self.fr_input_dw_kittel = Frame(self.newWindow)
        self.fr_input_dw_kittel.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw_kittel.grid_propagate(False)
        self.fr_input_right_image_kittel = Frame(self.newWindow)
        self.fr_input_right_image_kittel.grid(row=0, column=2)
        self.image_window = True

        self.text_box_new_win = Text(self.fr_input_dw_kittel, height=2, width=300, bg='#D3D3D3')
        self.text_box_new_win.grid()
        self.text_box = Text(self.text_box_new_win, height=2, width=200, bg='#D3D3D3')

        self.Kittel_entry_lf = ttk.LabelFrame(self.fr_input_up_kittel, text='Magnon Band Selection')
        self.Kittel_entry_lf.grid(row=2, column=0, columnspan=20, padx=25, pady=0, ipadx=200, ipady=25)
        self.Kittel_entry_lf.grid_propagate(false)
        self.Kittel_Magnon_InputInt = IntVar()
        self.Kittel_Magnon_Arr = []
        self.Kittel_Magnon_label = ttk.Label(self.Kittel_entry_lf, text="Select Magnon Band: ", justify='left')
        self.Kittel_Magnon_label.grid(row=2, column=1, padx=5)
        self.Kittel_Magnon_spinbox = ttk.Spinbox(self.Kittel_entry_lf, from_=1, to=self.total_magnonband,
                                                 textvariable=self.Kittel_Magnon_InputInt)
        self.Kittel_Magnon_spinbox.grid(row=2, column=2, padx=120)
        self.Kittel_Magnon_Arr.append(self.Kittel_Magnon_spinbox)
        self.fr_input_right_image_kittel = Frame(self.newWindow)
        self.fr_input_right_image_kittel.grid(row=0, column=2)
        self.image_window = True
        self.Kittel_preprocess()
        self.Kittel_cont_bt = ttk.Button(self.fr_input_up_kittel, text='Continue',
                                         command=lambda: self.select_kittel_model(), style='Toggle.TButton')
        self.Kittel_cont_bt.grid(row=3, column=9, pady=25)

    def Kittel_preprocess(self):
        self.Kittel_ID = self.ID_KLW_Arr[0].get()
        self.Kittel_Temp = self.Temp_KLW_Arr[0].get()
        path = 'Kittel_Linewidth_Fig'  # Processed data directory
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            self.text_box_new_win.delete('1.0', 'end')
            message_folder = "The new directory is created!"
            self.text_box.insert('end', message_folder)
            self.text_box.grid()

        self.f, self.ax_kittel = plt.subplots(figsize=(10, 8))
        self.ax_kittel.set_title("{} {}K Kittel Plot".format(self.Kittel_ID, self.Kittel_Temp), fontsize=10)
        self.canvas_Kittel = FigureCanvasTkAgg(self.f, self.fr_input_right_image_kittel)
        self.canvas_Kittel.get_tk_widget().grid(row=0, column=0, columnspan=10, rowspan=10)
        for loop in range(1, self.total_magnonband + 1, 1):
            self.selected_magnon_kittel = int(self.Kittel_Magnon_Arr[0].get())
            begin_col = loop * 5 - 5
            end_col = loop * 5
            temporal_df = self.Kittel_data_frame.iloc[:, begin_col:end_col]
            temporal_df = temporal_df.dropna()
            freq_list = temporal_df.iloc[:, 2]
            pk_list = temporal_df.iloc[:, 0]
            pk_list_error = temporal_df.iloc[:, 1]
            self.image_window = True
            matplotlib.rcParams.update(matplotlib.rcParamsDefault)
            self.ax_kittel.errorbar(pk_list, freq_list, xerr=pk_list_error, fmt='s',
                                    label="{} {}K LineWidth".format(self.Kittel_ID, self.Kittel_Temp),
                                    linewidth=2.0, capsize=8, markersize=8)
            self.ax_kittel.ticklabel_format(axis='y', style='scientific')
            self.ax_kittel.set_xlabel('Field (Oe)', fontname="Arial", labelpad=20)
            self.ax_kittel.set_ylabel('Frequency (GHz)', fontname="Arial", labelpad=20)
            self.ax_kittel.legend(loc='best', frameon=False, labelspacing=0.3)
            self.canvas_Kittel.draw()

    def select_kittel_model(self):
        self.Kittel_cont_bt.destroy()
        self.kittel_radio_frame = ttk.LabelFrame(self.fr_input_up_kittel, text='Fitting Mode Window')
        self.kittel_radio_frame.grid(row=3, column=0, padx=25, columnspan=20, ipadx=70, ipady=5)
        self.kittel_rd_bt = IntVar()
        self.general_kittel = ttk.Radiobutton(self.kittel_radio_frame, text="General Kittel", variable=self.kittel_rd_bt,
                                      value=1)
        self.general_kittel.grid(row=0, column=2, padx=15, sticky="nsew")
        self.kittel_Aex = ttk.Radiobutton(self.kittel_radio_frame, text="Kittel with Aex", variable=self.kittel_rd_bt,
                                    value=2)
        self.kittel_Aex.grid(row=0, column=5, padx=15, sticky="nsew")

        self.kittel_mode_sub = ttk.Button(self.fr_input_up_kittel, text='Continue',
                                          command=lambda: self.Kittel_process_para(), style='Toggle.TButton')
        self.kittel_mode_sub.grid(row=4, column=9, pady=25)
        self.general_kittel.bind('<Button-1>', lambda x: self.display_kittel_general())
        self.kittel_Aex.bind('<Button-1>', lambda x: self.display_kittel_Aex())

    def display_kittel_general(self):
        self.text_box.delete('1.0', 'end')
        message_folder = "gamma x sqrt(H / 1000) x (H / 1000) + M_eff)) + c"
        self.text_box.insert('end', message_folder)
        self.text_box.grid()

    def display_kittel_Aex(self):
        self.text_box.delete('1.0', 'end')
        message_folder = "\u0393sqrt((H + 2A(p\u03C0/d)^2 / M_eff) x (H + 2A(p\u03C0/d)^2 / M_eff) + 4\u03C0M_eff) + c"
        self.text_box.insert('end', message_folder)
        self.text_box.grid()

    def Kittel_process_para(self):
        self.kittel_mode_sub.destroy()
        self.kittel_fitting_frame = ttk.LabelFrame(self.fr_input_up_kittel, text='Fitting Window')

        if self.kittel_rd_bt.get() == 1:
            self.Kittel_Mode = 'G'
        elif self.kittel_rd_bt.get() == 2:
            self.Kittel_Mode = 'Aex'

        if self.Kittel_Mode == 'G':
            self.kittel_fitting_frame.grid(row=4, column=0, padx=25, columnspan=20, ipadx=200, ipady=38)
            self.kittel_fitting_frame.grid_propagate(false)
            self.gamma_Arr = []
            self.meff_Arr = []
            self.gamma_var = DoubleVar()
            self.meff_var = DoubleVar()
            self.gamma_label = ttk.Label(self.kittel_fitting_frame, text='Gamma:')
            self.gamma_label.grid(row=2, column=1, padx=25)
            self.meff_label = ttk.Label(self.kittel_fitting_frame, text='Meff:')
            self.meff_label.grid(row=3, column=1, padx=25)

            self.gamma_entry = ttk.Entry(self.kittel_fitting_frame, textvariable=self.gamma_var,
                                         justify=CENTER)
            self.gamma_entry.grid(row=2, column=3, padx=100)
            self.meff_entry = ttk.Entry(self.kittel_fitting_frame, textvariable=self.meff_var,
                                        justify=CENTER)
            self.meff_entry.grid(row=3, column=3, padx=138)

            self.gamma_Arr.append(self.gamma_entry)
            self.meff_Arr.append(self.meff_entry)

        if self.Kittel_Mode == 'Aex':
            self.Aex_Arr = []
            self.kittel_fitting_frame.grid(row=4, column=0, padx=25, columnspan=20, ipadx=25, ipady=5)
            self.gamma_Arr = []
            self.meff_Arr = []
            self.gamma_var = DoubleVar()
            self.meff_var = DoubleVar()
            self.gamma_label = ttk.Label(self.kittel_fitting_frame, text='Gamma:')
            self.gamma_label.grid(row=2, column=1, padx=25)
            self.meff_label = ttk.Label(self.kittel_fitting_frame, text='Meff:')
            self.meff_label.grid(row=3, column=1, padx=25)
            self.gamma_entry = ttk.Entry(self.kittel_fitting_frame, textvariable=self.gamma_var,
                                         justify=CENTER)
            self.gamma_entry.grid(row=2, column=3, padx=10)
            self.meff_entry = ttk.Entry(self.kittel_fitting_frame, textvariable=self.meff_var,
                                        justify=CENTER)
            self.meff_entry.grid(row=3, column=3, padx=10)

            self.gamma_Arr.append(self.gamma_entry)
            self.meff_Arr.append(self.meff_entry)
            self.Aex_var = DoubleVar()
            self.Aex_label = ttk.Label(self.kittel_fitting_frame, text='Exchange Stiffness (Aex):')
            self.Aex_label.grid(row=4, column=1, padx=25)

            self.Aex_entry = ttk.Entry(self.kittel_fitting_frame, textvariable=self.Aex_var,
                                       justify=CENTER)
            self.Aex_entry.grid(row=4, column=3, padx=10)
            self.Aex_Arr.append(self.Aex_entry)

            self.SW_mode_Arr = []
            self.SW_mode_var = IntVar()
            self.SW_mode_label = ttk.Label(self.kittel_fitting_frame, text='Spin Wave Mode (p):')
            self.SW_mode_label.grid(row=5, column=1, padx=25)

            self.SW_mode_entry = ttk.Entry(self.kittel_fitting_frame, textvariable=self.SW_mode_var,
                                           justify=CENTER)
            self.SW_mode_entry.grid(row=5, column=3, padx=10)
            self.SW_mode_Arr.append(self.SW_mode_entry)

            self.thickness_Arr = []
            self.thickness_var = DoubleVar()
            self.thickness_label = ttk.Label(self.kittel_fitting_frame, text='Sample Thickness (d):')
            self.thickness_label.grid(row=6, column=1, padx=25)

            self.thickness_entry = ttk.Entry(self.kittel_fitting_frame, textvariable=self.thickness_var,
                                           justify=CENTER)
            self.thickness_entry.grid(row=6, column=3, padx=10)
            self.thickness_Arr.append(self.thickness_entry)

        self.Kittel_Fit_bt = ttk.Button(self.fr_input_up_kittel, text='Fit',
                                        command=lambda: self.Kittel_process(), style='Toggle.TButton')
        self.Kittel_Fit_bt.grid(row=5, column=1, padx=25, pady=25)
        self.Kittel_back = ttk.Button(self.fr_input_up_kittel, text='Back Band Sel',
                                      command=lambda: self._back_kittel_mode(), style='Toggle.TButton')
        self.Kittel_back.grid(row=5, column=4, pady=25)
        self.kittel_export = ttk.Button(self.fr_input_up_kittel, text='Export',
                                      command=lambda: self.kittel_fit_export(), style='Toggle.TButton')
        self.kittel_export.grid(row=5, column=2, pady=25)
        self.Kittel_back_mode = ttk.Button(self.fr_input_up_kittel, text='Back Mode Sel',
                                      command=lambda: self._back_select_equ(), style='Toggle.TButton')
        self.Kittel_back_mode.grid(row=5, column=3, pady=25)


    def _back_kittel_mode(self):
        self.kittel_fitting_frame.destroy()
        self.Kittel_back_mode.destroy()
        self.kittel_export.destroy()
        self.kittel_radio_frame.destroy()
        self.Kittel_Fit_bt.destroy()
        self.Kittel_back.destroy()
        self.newWindow.destroy()
        self.Kittel_process_init()

    def _back_select_equ(self):
        self.Kittel_back_mode.destroy()
        self.kittel_fitting_frame.destroy()
        self.Kittel_Fit_bt.destroy()
        self.Kittel_back.destroy()
        self.kittel_export.destroy()
        self.kittel_radio_frame.destroy()
        self.select_kittel_model()

    def clear_fit_kittel(self):
        if self.remove_line == True:
            self.remove_line.remove()
        self.canvas_Kittel.draw()
        self.Kittel_process()

    def Kittel_process(self):
        def Kittel_funtions(x, gamma, M_eff, c):
            return gamma * np.sqrt((np.abs(x / 1000)) * (np.abs(x / 1000) + M_eff)) + c

        def Kittel_funtions_PSSW(x, A, c):
            return self.gamma_guess * np.sqrt((x + 2 * A * (self.SW_mode * np.pi / self.thickness) ** 2 / self.meff_guess) *
                                              (x + 2 * A * (self.SW_mode * np.pi / self.thickness) ** 2 / self.meff_guess + 4 * np.pi * self.meff_guess)) + c

        self.remove_line = False
        self.Kittel_Fit_bt.destroy()
        self.Kittel_back.destroy()
        self.Kittel_back.destroy()
        self.Kittel_Fit_bt = ttk.Button(self.fr_input_up_kittel, text='Fit',
                                        command=lambda: self.Kittel_process(), style='Toggle.TButton')
        self.Kittel_Fit_bt.grid(row=5, column=1, padx=25, pady=25)
        self.Kittel_back = ttk.Button(self.fr_input_up_kittel, text='Back Band Sel',
                                      command=lambda: self._back_kittel_mode(), style='Toggle.TButton')
        self.Kittel_back.grid(row=5, column=4, pady=25)
        self.kittel_export = ttk.Button(self.fr_input_up_kittel, text='Export',
                                        command=lambda: self.kittel_fit_export(), style='Toggle.TButton')
        self.kittel_export.grid(row=5, column=2, pady=25)
        self.Kittel_back_mode = ttk.Button(self.fr_input_up_kittel, text='Back Mode Sel',
                                           command=lambda: self._back_select_equ(), style='Toggle.TButton')
        self.Kittel_back_mode.grid(row=5, column=3, pady=25)
        self.selected_magnon = int(self.Kittel_Magnon_Arr[0].get())
        path = 'Kittel_Summary'  # Processed data directory
        isExist = os.path.exists(path)
        if not isExist:  # Create a new directory because it does not exist
            os.makedirs(path)
            self.text_box_new_win.delete('1.0', 'end')
            message_folder = "The new directory is created!"
            self.text_box.insert('end', message_folder)
            self.text_box.grid()
        begin_col = self.selected_magnon * 5 - 5
        end_col = self.selected_magnon * 5
        temporal_df = self.Kittel_data_frame.iloc[:, begin_col:end_col]
        temporal_df = temporal_df.dropna()
        freq_list = temporal_df.iloc[:, 2]
        pk_list = temporal_df.iloc[:, 0]
        pk_list_error = temporal_df.iloc[:, 1]
        self.image_window = True
        self.gamma_guess = float(self.gamma_Arr[0].get())
        self.meff_guess = float(self.meff_Arr[0].get())
        self.fr_input_right_fit_box = Frame(self.newWindow)
        self.fr_input_right_fit_box.grid(row=0, column=4)
        if self.Kittel_Mode == 'G':
            General_Kittel_mod = Model(Kittel_funtions)
            General_Kittel_mod.set_param_hint('gamma', value=2.85)  # ,  min=2.85*0.9, max=2.85*1.1
            General_Kittel_mod.set_param_hint('M_eff', value=1)
            First_pars = General_Kittel_mod.make_params(gamma=float(self.gamma_guess), M_eff=float(self.meff_guess),
                                                        c=0)
            self.First_Fit_result = General_Kittel_mod.fit(freq_list, First_pars, x=pk_list, max_nfev=400)

            self.remove_fit = self.ax_kittel.plot(pk_list, self.First_Fit_result.best_fit, '-', label='best fit',
                                                  linewidth=2)

            self.ax_kittel.legend(frameon=False, labelspacing=0.3)
            plt.tight_layout()
            self.remove_line = self.remove_fit.pop(0)
            self.canvas_Kittel.draw()
            # self.remove_line.remove()
            self.remove_line = True
            self.text_box_message_win = Text(self.fr_input_right_fit_box, height=30, width=40, bg='#D3D3D3')
            message_test_plot = self.First_Fit_result.fit_report()
            self.text_box_message_win.insert('end', message_test_plot)
            self.text_box_message_win.grid()

        elif self.Kittel_Mode == 'Aex':
            self.thickness = float(self.thickness_Arr[0].get())
            self.SW_mode = int(self.SW_mode_Arr[0].get())
            self.aex_guess = float(self.Aex_Arr[0].get())
            General_Kittel_mod = Model(Kittel_funtions_PSSW)
            # General_Kittel_mod.set_param_hint('Aex', value=2.85, min=2.85 * 0.9, max=2.85 * 1.1)
            # General_Kittel_mod.set_param_hint('M_eff', value=1)
            First_pars = General_Kittel_mod.make_params(A=self.aex_guess, c=0)
            self.First_Fit_result = General_Kittel_mod.fit(freq_list, First_pars, x=pk_list, max_nfev=400)

            self.remove_fit = self.ax_kittel.plot(freq_list, self.First_Fit_result.best_fit, '-', label='best fit',
                                                  linewidth=2)

            self.ax_kittel.legend(frameon=False, labelspacing=0.3)
            plt.tight_layout()
            self.remove_line = self.remove_fit.pop(0)
            self.canvas_Kittel.draw()
            # self.remove_line.remove()
            self.remove_line = True
            self.text_box_message_win = Text(self.fr_input_right_fit_box, height=30, width=40, bg='#D3D3D3')
            message_test_plot = self.First_Fit_result.fit_report()
            self.text_box_message_win.insert('end', message_test_plot)
            self.text_box_message_win.grid()

    def _continue_Kittel(self):
        self.Kittel_back.destroy()
        self.kittel_fitting_frame.destroy()

    def _continue_kittel(self):
        self.Kittel_back.destroy()
        self.Kittel_Fit_bt.destroy()
        self.Kittel_entry_lf.destroy()
        self.kittel_fitting_frame.destroy()
        self.Kittel_process_init()

    def kittel_fit_export(self):
        if self.Kittel_Mode == 'G':
            Kittel_fit = pd.DataFrame()
            gamma = []
            gamma_error = []
            Meff = []
            Meff_error = []
            temp = []
            temp.append(self.Kittel_Temp)
            gamma.append(self.First_Fit_result.params['gamma'].value)
            gamma_error.append(self.First_Fit_result.params['gamma'].stderr)
            Meff.append(self.First_Fit_result.params['M_eff'].value)
            Meff_error.append(self.First_Fit_result.params['M_eff'].stderr)

            kittelConca = pd.DataFrame(
                list(zip(temp, gamma, gamma_error, Meff, Meff_error)))
            Kittel_fit = pd.concat([Kittel_fit, kittelConca], ignore_index=True, axis=1)
            Kittel_fit.to_csv(
                'Kittel_Summary/{}_Kittel_Summary_{}K.csv'.format(self.Kittel_ID, self.Kittel_Temp),
                mode='a', index=False, encoding='utf-8-sig', header=False)


        #     Kittel_Summary.to_csv('Kittel_Summary/{}_Kittel_Summary_{}K.csv'.format(ID, temp), mode='a',
        #                           index=False, encoding='utf-8-sig', header=None)
        #     pyplot.rc('font', size=32)  # controls default text sizes
        #     pyplot.rc('axes', labelsize=36)  # fontsize of the x and y labels
        #     pyplot.rc('xtick', labelsize=32)  # fontsize of the tick labels
        #     pyplot.rc('ytick', labelsize=32)  # fontsize of the tick labels
        #     pyplot.rc('legend', fontsize=34)  # legend fontsize
        #     pyplot.figure(figsize=(18, 15), dpi=100)
        #     pyplot.scatter(peak_one_list, freq_list_one_peak, s=200, color='black', marker='s', label='First Peak')
        #     pyplot.scatter(peak_two_list, freq_list_two_peak, s=200, color='red', marker='s', label='Second Peak')
        #     pyplot.scatter(peak_three_list, freq_list_three_peak, s=200, color='blue', marker='s',
        #                    label='Third Peak')
        #     if (len(peak_four_list)) > 0:
        #         pyplot.scatter(peak_four_list, freq_list_four_peak, s=200, color='green', marker='s',
        #                        label='Fourth Peak')
        #     pyplot.plot(peak_one_list, k_fit1, color='black', label='1st Fitted Curve', linewidth=5.0)
        #     pyplot.plot(peak_two_list, k_fit2, color='red', label='2nd Fitted Curve', linewidth=5.0)
        #     pyplot.plot(peak_three_list, k_fit3, color='blue', label='3rd Fitted Curve', linewidth=5.0)
        #     pyplot.subplot().spines[:].set_linewidth(3.5)
        #     pyplot.subplot().xaxis.set_major_locator(MultipleLocator(500))
        #     pyplot.subplot().xaxis.set_minor_locator(MultipleLocator(100))
        #     pyplot.tick_params(axis='both', direction='in', width=5, length=12, which='major', pad=20, )
        #     pyplot.tick_params(axis='both', direction='in', width=5, length=8, which='minor', pad=20)
        #     pyplot.xlabel("Field (Oe)", fontname="Arial", labelpad=20)
        #     pyplot.ylabel('{}K Frequency (GHz)'.format(temp), fontname="Arial", labelpad=20)
        #     pyplot.legend(loc='upper left', frameon=False, labelspacing=0.3)
        #     pyplot.tight_layout()
        #     pyplot.savefig('Kittel_Linewidth_Fig/{}_Fitting_Temp{}_Kittel.png'.format(ID, temp), dpi=100)
        #     pyplot.show()
        #     test = input("Please press enter to continue...!")
        #
        # elif guess_peak == 2:
        #
        #     # para1 = optimize.curve_fit(Kittel_funtions, peak_one_list, freq_list_one_peak, p0=pk, method='lm',
        #     #                            maxfev=20000)[0]
        #
        #     para1 = \
        #     optimize.curve_fit(Kittel_funtions_no_c, peak_one_list, freq_list_one_peak, p0=pkwc, method='lm',
        #                        maxfev=20000)[0]
        #     para2 = \
        #     optimize.curve_fit(Kittel_funtions_second, peak_two_list, freq_list_two_peak, p0=pk1, method='lm',
        #                        maxfev=20000)[0]
        #
        #     # k_fit1 = np.array(
        #     #     [Kittel_funtions(H, para1[0], para1[1], para1[2]) for H in peak_one_list])
        #     k_fit1 = np.array(
        #         [Kittel_funtions_no_c(H, para1[0], para1[1]) for H in peak_one_list])
        #     k_fit2 = np.array(
        #         [Kittel_funtions_second(H, para2[0], para2[1], para2[2], para2[3]) for H in peak_two_list])
        #     returndata = {'Temp': temp, 'Gyromagnetic Ratio': 0, 'Saturation Magnetization': 0,
        #                   'Anisotropy (in plane)': 0}
        #     for i, name in enumerate(
        #             ['Gyromagnetic Ratio P1:         ', 'Saturation Magnetization P1:   '
        #              # 'Anisotropy (in plane) P1:      '
        #              ]):
        #         kittel_name_list.append(name)
        #         returndata[name] = para1[i]
        #         print(name, returndata[name])
        #
        #     for i, name in enumerate(
        #             ['Gyromagnetic Ratio P2:         ', 'Saturation Magnetization P2:   ',
        #              'Anisotropy (in plane) P2:      ', 'Constant:      ']):
        #         kittel_name_list.append(name)
        #         returndata[name] = para2[i]
        #         print(name, returndata[name])
        #
        #     Kittel_essential = []
        #     Kittel_essential.append(para1[0])
        #     Kittel_essential.append(para1[1])
        #     # Kittel_essential.append(para1[2])
        #     Kittel_essential.append(para2[0])
        #     Kittel_essential.append(para2[1])
        #     Kittel_essential.append(para2[2])
        #     Kittel_essential.append(para2[3])
        #     Add_Summary = pd.DataFrame(list(zip(kittel_name_list, Kittel_essential)))
        #     Kittel_Summary = pd.concat([Kittel_Summary, Add_Summary], ignore_index=True, axis=1)
        #     path = 'Kittel_Summary'  # Processed data directory
        #     isExist = os.path.exists(path)
        #     if not isExist:  # Create a new directory because it does not exist
        #         os.makedirs(path)
        #         print("The new directory is created!")
        #         print('--------------------------------------------\n')
        #     Kittel_Summary.to_csv('Kittel_Summary/{}_Kittel_Summary_{}K.csv'.format(ID, temp), mode='a',
        #                           index=False, encoding='utf-8-sig', header=None)
        #     pyplot.rc('font', size=32)  # controls default text sizes
        #     pyplot.rc('axes', labelsize=36)  # fontsize of the x and y labels
        #     pyplot.rc('xtick', labelsize=32)  # fontsize of the tick labels
        #     pyplot.rc('ytick', labelsize=32)  # fontsize of the tick labels
        #     pyplot.rc('legend', fontsize=34)  # legend fontsize
        #     pyplot.figure(figsize=(18, 15), dpi=100)
        #     pyplot.scatter(peak_one_list, freq_list_one_peak, s=200, color='black', marker='s', label='First Peak')
        #     pyplot.scatter(peak_two_list, freq_list_two_peak, s=200, color='red', marker='s', label='Second Peak')
        #     if (len(peak_three_list)) > 0:
        #
        #         pyplot.scatter(peak_three_list, freq_list_three_peak, s=200, color='blue', marker='s',
        #                        label='Third Peak')
        #         if (len(peak_four_list)) > 0:
        #             print(peak_four_list)
        #             print(freq_list_four_peak)
        #             pyplot.scatter(peak_four_list, freq_list_four_peak, s=200, color='green', marker='s',
        #                            label='Fourth Peak')
        #     pyplot.plot(peak_one_list, k_fit1, color='black', label='1st Fitted Curve', linewidth=5.0)
        #     pyplot.plot(peak_two_list, k_fit2, color='red', label='2nd Fitted Curve', linewidth=5.0)
        #     pyplot.subplot().spines[:].set_linewidth(3.5)
        #     pyplot.subplot().xaxis.set_major_locator(MultipleLocator(500))
        #     pyplot.subplot().xaxis.set_minor_locator(MultipleLocator(100))
        #     pyplot.tick_params(axis='both', direction='in', width=5, length=12, which='major', pad=20, )
        #     pyplot.tick_params(axis='both', direction='in', width=5, length=8, which='minor', pad=20)
        #     pyplot.xlabel("Field (Oe)", fontname="Arial", labelpad=20)
        #     pyplot.ylabel('{}K Frequency (GHz)'.format(temp), fontname="Arial", labelpad=20)
        #     pyplot.legend(loc='upper left', frameon=False, labelspacing=0.3)
        #     pyplot.tight_layout()
        #     pyplot.savefig('Kittel_Linewidth_Fig/{}_Fitting_Temp{}_Kittel.png'.format(ID, temp), dpi=100)
        #     pyplot.show()
        #     test = input("Please press enter to continue...!")
        #
        # elif guess_peak == 1:
        #     # para1 = optimize.curve_fit(Kittel_funtions, peak_one_list, freq_list_one_peak, p0=pk, method='lm',
        #     #                            maxfev=40000)[0]
        #     para1 = \
        #     optimize.curve_fit(Kittel_funtions_no_c, peak_one_list, freq_list_one_peak, p0=pkwc, method='lm',
        #                        maxfev=20000)[0]
        #     # k_fit1 = np.array(
        #     #     [Kittel_funtions(H, para1[0], para1[1], para1[2]) for H in peak_one_list])
        #     k_fit1 = np.array(
        #         [Kittel_funtions_no_c(H, para1[0], para1[1]) for H in peak_one_list])
        #     returndata = {'Temp': temp, 'Gyromagnetic Ratio': 0, 'Saturation Magnetization': 0,
        #                   'Anisotropy (in plane)': 0}
        #     for i, name in enumerate(
        #             # ['Gyromagnetic Ratio P1:         ', 'Saturation Magnetization P1:   ',
        #             #  'Anisotropy (in plane) P1:      ']):
        #             ['Gyromagnetic Ratio P1:         ', 'Saturation Magnetization P1:   ']):
        #         kittel_name_list.append(name)
        #         returndata[name] = para1[i]
        #         print(name, returndata[name])
        #
        #     Kittel_essential = []
        #     Kittel_essential.append(para1[0])
        #     Kittel_essential.append(para1[1])
        #     # Kittel_essential.append(para1[2])
        #     Add_Summary = pd.DataFrame(list(zip(kittel_name_list, Kittel_essential)))
        #     Kittel_Summary = pd.concat([Kittel_Summary, Add_Summary], ignore_index=True, axis=1)
        #     path = 'Kittel_Summary'  # Processed data directory
        #     isExist = os.path.exists(path)
        #     if not isExist:  # Create a new directory because it does not exist
        #         os.makedirs(path)
        #         print("The new directory is created!")
        #         print('--------------------------------------------\n')
        #     Kittel_Summary.to_csv('Kittel_Summary/{}_Kittel_Summary_{}K.csv'.format(ID, temp), mode='a',
        #                           index=False, encoding='utf-8-sig', header=None)
        #     pyplot.rc('font', size=32)  # controls default text sizes
        #     pyplot.rc('axes', labelsize=36)  # fontsize of the x and y labels
        #     pyplot.rc('xtick', labelsize=32)  # fontsize of the tick labels
        #     pyplot.rc('ytick', labelsize=32)  # fontsize of the tick labels
        #     pyplot.rc('legend', fontsize=34)  # legend fontsize
        #     pyplot.figure(figsize=(18, 15), dpi=100)
        #     pyplot.scatter(peak_one_list, freq_list_one_peak, s=200, color='black', marker='s', label='First Peak')
        #     if (len(peak_two_list)) > 0:
        #         pyplot.scatter(peak_two_list, freq_list_two_peak, s=200, color='red', marker='s',
        #                        label='Second Peak')
        #         if (len(peak_three_list)) > 0:
        #             pyplot.scatter(peak_three_list, freq_list_three_peak, s=200, color='blue', marker='s',
        #                            label='Third Peak')
        #             if (len(peak_four_list)) > 0:
        #                 pyplot.scatter(peak_four_list, freq_list_four_peak, s=200, color='green', marker='s',
        #                                label='Fourth Peak')
        #
        #     pyplot.plot(peak_one_list, k_fit1, color='black', label='1st Fitted Curve', linewidth=5.0)
        #     pyplot.subplot().spines[:].set_linewidth(3.5)
        #     pyplot.subplot().xaxis.set_major_locator(MultipleLocator(500))
        #     # pyplot.subplot().xaxis.set_minor_locator(MultipleLocator(100))
        #     pyplot.tick_params(axis='both', direction='in', width=5, length=12, which='major', pad=20, )
        #     pyplot.tick_params(axis='both', direction='in', width=5, length=8, which='minor', pad=20)
        #     pyplot.xlabel("Field (Oe)", fontname="Arial", labelpad=20)
        #     pyplot.ylabel('{}K Frequency (GHz)'.format(temp), fontname="Arial", labelpad=20)
        #     pyplot.legend(loc='upper left', frameon=False, labelspacing=0.3)
        #     pyplot.tight_layout()
        #     pyplot.savefig('Kittel_Linewidth_Fig/{}_Fitting_Temp{}_Kittel.png'.format(ID, temp), dpi=100)
        #     pyplot.show()
        #     test = input("Please press enter to continue...!")
        #
        # # Linewidth plotting
        # pyplot.close('all')
        # pyplot.rc('font', size=32)  # controls default text sizes
        # pyplot.rc('axes', labelsize=36)  # fontsize of the x and y labels
        # pyplot.rc('xtick', labelsize=32)  # fontsize of the tick labels
        # pyplot.rc('ytick', labelsize=32)  # fontsize of the tick labels
        # pyplot.rc('legend', fontsize=34)  # legend fontsize
        # pyplot.figure(figsize=(18, 15), dpi=100)
        # if guess_peak == 1:
        #     print(freq_list_one_peak)
        #     print(lw_one_list)
        #     pyplot.errorbar(freq_list_one_peak, np.abs(lw_one_list), yerr=lw_one_error, color='black', fmt='s',
        #                     label='First Peak', linewidth=5.0, capsize=10, markersize=15)
        #     if (len(peak_two_list)) > 0:
        #         pyplot.errorbar(freq_list_two_peak, np.abs(lw_two_list), yerr=lw_two_error, color='red', fmt='s',
        #                         label='Second Peak', linewidth=5.0, capsize=10, markersize=15)
        #         if (len(peak_three_list)) > 0:
        #             pyplot.errorbar(freq_list_three_peak, np.abs(lw_three_list), yerr=lw_three_error, color='blue',
        #                             fmt='s',
        #                             label='Third Peak', linewidth=5.0, capsize=10, markersize=15)
        #             if (len(peak_four_list)) > 0:
        #                 pyplot.errorbar(freq_list_four_peak, np.abs(lw_four_list), yerr=lw_four_error,
        #                                 color='green',
        #                                 fmt='s',
        #                                 label='Fourth Peak', linewidth=5.0, capsize=10, markersize=15)
        #                 if (len(peak_five_list)) > 0:
        #                     pyplot.errorbar(freq_list_five_peak, np.abs(lw_five_list), yerr=lw_five_error,
        #                                     color='orange',
        #                                     fmt='s',
        #                                     label='Fifth Peak', linewidth=5.0, capsize=10, markersize=15)
        # elif guess_peak == 2:
        #     pyplot.errorbar(freq_list_one_peak, np.abs(lw_one_list), yerr=lw_one_error, color='black', fmt='s',
        #                     label='First Peak', linewidth=5.0, capsize=10, markersize=15)
        #     pyplot.errorbar(freq_list_two_peak, np.abs(lw_two_list), yerr=lw_two_error, color='red', fmt='s',
        #                     label='Second Peak', linewidth=5.0, capsize=10, markersize=15)
        #     if (len(peak_three_list)) > 0:
        #         pyplot.errorbar(freq_list_three_peak, np.abs(lw_three_list), yerr=lw_three_error, color='blue',
        #                         fmt='s',
        #                         label='Third Peak', linewidth=5.0, capsize=10, markersize=15)
        #         if (len(peak_four_list)) > 0:
        #             pyplot.errorbar(freq_list_four_peak, np.abs(lw_four_list), yerr=lw_four_error, color='green',
        #                             fmt='s',
        #                             label='Fourth Peak', linewidth=5.0, capsize=10, markersize=15)
        #             if (len(peak_five_list)) > 0:
        #                 pyplot.errorbar(freq_list_five_peak, np.abs(lw_five_list), yerr=lw_five_error,
        #                                 color='orange',
        #                                 fmt='s',
        #                                 label='Fifth Peak', linewidth=5.0, capsize=10, markersize=15)
        # elif guess_peak == 3:
        #     pyplot.errorbar(freq_list_one_peak, np.abs(lw_one_list), yerr=lw_one_error, color='black', fmt='s',
        #                     label='First Peak', linewidth=5.0, capsize=10, markersize=15)
        #     pyplot.errorbar(freq_list_two_peak, np.abs(lw_two_list), yerr=lw_two_error, color='red', fmt='s',
        #                     label='Second Peak', linewidth=5.0, capsize=10, markersize=15)
        #     pyplot.errorbar(freq_list_three_peak, np.abs(lw_three_list), yerr=lw_three_error, color='blue', fmt='s',
        #                     label='Third Peak', linewidth=5.0, capsize=10, markersize=15)
        #     if (len(peak_four_list)) > 0:
        #         print(freq_list_four_peak)
        #         pyplot.errorbar(freq_list_four_peak, np.abs(lw_four_list), yerr=lw_four_error, color='green',
        #                         fmt='s',
        #                         label='Fourth Peak', linewidth=5.0, capsize=10, markersize=15)
        #         if (len(peak_five_list)) > 0:
        #             pyplot.errorbar(freq_list_five_peak, np.abs(lw_five_list), yerr=lw_five_error,
        #                             color='orange',
        #                             fmt='s',
        #                             label='Fifth Peak', linewidth=5.0, capsize=10, markersize=15)
        # elif PeakN == 4:
        #     pyplot.errorbar(freq_list_one_peak, np.abs(lw_one_list), yerr=lw_one_error, color='black', fmt='s',
        #                     label='First Peak', linewidth=5.0, capsize=10, markersize=15)
        #     pyplot.errorbar(freq_list_two_peak, np.abs(lw_two_list), yerr=lw_two_error, color='red', fmt='s',
        #                     label='Second Peak', linewidth=5.0, capsize=10, markersize=15)
        #     pyplot.errorbar(freq_list_three_peak, np.abs(lw_three_list), yerr=lw_three_error, color='blue', fmt='s',
        #                     label='Third Peak', linewidth=5.0, capsize=10, markersize=15)
        #     pyplot.errorbar(freq_list_four_peak, np.abs(lw_four_list), yerr=lw_four_error, color='green', fmt='s',
        #                     label='Fourth Peak', linewidth=5.0, capsize=10, markersize=15)
        #     if (len(peak_five_list)) > 0:
        #         pyplot.errorbar(freq_list_five_peak, np.abs(lw_five_list), yerr=lw_five_error,
        #                         color='orange',
        #                         fmt='s',
        #                         label='Fifth Peak', linewidth=5.0, capsize=10, markersize=15)
        #
        # pyplot.subplot().spines[:].set_linewidth(3.5)
        # pyplot.subplot().xaxis.set_major_locator(MultipleLocator(1))
        # pyplot.subplot().xaxis.set_minor_locator(MultipleLocator(0.5))
        # pyplot.tick_params(axis='both', direction='in', width=5, length=10, which='major', pad=20, )
        # pyplot.tick_params(axis='both', direction='in', width=5, length=6, which='minor', pad=20)
        # pyplot.ticklabel_format(axis='y', style='scientific')
        # pyplot.xlabel('Frequency (GHz)', fontname="Arial", labelpad=20)
        # pyplot.ylabel('{}K Linewidth \u0394w'.format(temp), fontname="Arial", labelpad=20)
        # pyplot.legend(loc='best', frameon=False, labelspacing=0.3)
        # pyplot.tight_layout()
        # pyplot.savefig('Kittel_Linewidth_Fig/{}_Fitting_Temp{}_Linewidth.png'.format(ID, temp), dpi=100)
        # pyplot.show()
        # test = input("Please press enter to continue...!")
        #
        #     prs = Presentation('{}_April.pptx'.format(ID))
        #     prs.slide_width = Inches(16)
        #     prs.slide_height = Inches(9)
        #     title_slide_layout = prs.slide_layouts[0]
        #     slide = prs.slides.add_slide(title_slide_layout)
        #     title = slide.shapes.title
        #     title.text = "{}K Data".format(temp)
        #     prs.save('{}_April.pptx'.format(ID))
        #     pptx_cur_freq = 2
        #     pptx_step_freq = 0.5
        #     pptx_top_freq = 23
        #     pptx_row_itr = 0
        #     pptx_col_itr = 0
        #     pptx_top = 0.5
        #     pptx_top_step = 2
        #     pptx_left = 0.3
        #     pptx_left_step = 4
        #     prs = Presentation('{}_April.pptx'.format(ID))
        #     prs.slide_width = Inches(16)
        #     prs.slide_height = Inches(9)
        #     blank_slide_layout = prs.slide_layouts[6]
        #     slide = prs.slides.add_slide(blank_slide_layout)
        #     print('\nStart PowerPoint Arrangement')
        #     while pptx_cur_freq < pptx_top_freq + pptx_step_freq:
        #         if os.path.exists('OutputFit/{}_Fitting_Temp{}_Fre{}.png'.format(ID, temp, pptx_cur_freq)):
        #             if pptx_col_itr < 4:
        #                 if pptx_row_itr < 4:
        #                     freq_image_path = 'OutputFit/{}_Fitting_Temp{}_Fre{}.png'.format(ID, temp, pptx_cur_freq)
        #                     left = Inches(pptx_left)
        #                     top = Inches(pptx_top)
        #                     img = slide.shapes.add_picture(freq_image_path, left, top, Inches(3.5))
        #                     pptx_left += pptx_left_step
        #                     pptx_row_itr += 1
        #                     pptx_cur_freq += pptx_step_freq
        #                 else:
        #                     pptx_row_itr = 0
        #                     pptx_col_itr += 1
        #                     pptx_top += pptx_top_step
        #                     pptx_left = 0.3
        #
        #             else:
        #                 pptx_row_itr = 0
        #                 pptx_col_itr = 0
        #                 pptx_left = 0.3
        #                 pptx_top = 0.5
        #                 blank_slide_layout = prs.slide_layouts[6]
        #                 slide = prs.slides.add_slide(blank_slide_layout)
        #         else:
        #             pptx_cur_freq += pptx_step_freq
        #     prs.save('{}_April.pptx'.format(ID))
        #
        #     prs = Presentation('{}_April.pptx'.format(ID))
        #     prs.slide_width = Inches(16)
        #     prs.slide_height = Inches(9)
        #     title_slide_layout = prs.slide_layouts[0]
        #     slide = prs.slides.add_slide(title_slide_layout)
        #     title = slide.shapes.title
        #     title.text = "{}K Kittel and Linewidth Data".format(temp)
        #     prs.save('{}_April.pptx'.format(ID))
        #     prs = Presentation('{}_April.pptx'.format(ID))
        #     prs.slide_width = Inches(16)
        #     prs.slide_height = Inches(9)
        #     blank_slide_layout = prs.slide_layouts[6]
        #     kittel_image_path = 'Kittel_Linewidth_Fig/{}_Fitting_Temp{}_Kittel.png'.format(ID, temp)
        #     linewidth_image_path = 'Kittel_Linewidth_Fig/{}_Fitting_Temp{}_Linewidth.png'.format(ID, temp)
        #     slide = prs.slides.add_slide(blank_slide_layout)
        #     top = Inches(2)
        #     img = slide.shapes.add_picture(kittel_image_path, Inches(1), top, Inches(6.0))
        #     img2 = slide.shapes.add_picture(linewidth_image_path, Inches(9), top, Inches(6.0))
        #     prs.save('{}_April.pptx'.format(ID))

    def SHG(self):
        print('')

    def display_Raw(self):
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=30, bg='#D3D3D3')
        message = 'Entering FMR Raw Data Processing ...'
        self.text_box.insert('end', message)
        self.text_box.grid()

    def display_Interp(self):
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=30, bg='#D3D3D3')
        message = 'Entering FMR Data Interpolation ...'
        self.text_box.insert('end', message)
        self.text_box.grid()

    def display_FMRFit(self):
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=30, bg='#D3D3D3')
        message = 'Entering FMR Data Fitting ...'
        self.text_box.insert('end', message)
        self.text_box.grid()

    def display_SHGFit(self):
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=30, bg='#D3D3D3')
        message = 'Entering SHG Data Fitting ...'
        self.text_box.insert('end', message)
        self.text_box.grid()

    def display_Kittel(self):
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=30, bg='#D3D3D3')
        message = 'Entering Kittel and Linewidth Fitting ...'
        self.text_box.insert('end', message)
        self.text_box.grid()

    def selection(self):
        self.fr_input_dw = Frame(master=root, bg='#D3D3D3')
        self.fr_input_dw.grid(row=1, column=0, columnspan=2, ipady=10, sticky='swe')
        self.fr_input_dw.grid_propagate(False)
        self.text_box = Text(self.fr_input_dw, height=2, width=30, bg='#D3D3D3')
        if self.radio_var.get() == 1:
            self.catagdata()
        elif self.radio_var.get() == 2:
            self.Data_Interpolation()
        elif self.radio_var.get() == 3:
            self.Init_FMRFit()
        elif self.radio_var.get() == 4:
            self.Init_Kittel()
        elif self.radio_var.get() == 5:
            self.Init_SHG

    def createWidget(self):
        self.list_init()
        self.view_init()
        # set up a navigation toolbar
        # create an optionMenu
        self.option_var = StringVar()
        # label
        self.labelframe = ttk.LabelFrame(self.fr_input_up, text='Select Option')
        self.labelframe.grid(row=1, column=0, padx=25, pady=25, sticky='nwse')

        self.radio_var = IntVar()
        self.Raw_processing_bt = ttk.Radiobutton(self.labelframe, text='Raw Data Processing', variable=self.radio_var,
                                                 value=1)
        self.Raw_processing_bt.grid(row=0, column=0, padx=5, pady=8, sticky='news')

        self.Data_inter_bt = ttk.Radiobutton(self.labelframe, text='Data Interpolation', variable=self.radio_var,
                                             value=2)
        self.Data_inter_bt.grid(row=1, column=0, padx=5, pady=8, sticky='news')

        self.FMR_data_fit_bt = ttk.Radiobutton(self.labelframe, text='FMR Data Fitting', variable=self.radio_var,
                                               value=3)
        self.FMR_data_fit_bt.grid(row=2, column=0, padx=5, pady=8, sticky='news')

        self.kittel_lw_bt = ttk.Radiobutton(self.labelframe, text='Kittel and Linewidth', variable=self.radio_var,
                                            value=4)
        self.kittel_lw_bt.grid(row=3, column=0, padx=5, pady=8, sticky='news')

        self.SHG_bt = ttk.Radiobutton(self.labelframe, text='SHG Data Processing', variable=self.radio_var,
                                      value=5)
        self.SHG_bt.grid(row=4, column=0, padx=5, pady=8, sticky='news')

        self.sel_bt = ttk.Button(self.fr_input_up, text='Select', command=lambda: self.selection(),
                                 style="Accent.TButton")
        self.sel_bt.grid(row=5, column=0, padx=1, pady=2)

        self.quit_bt = ttk.Button(self.fr_input_up, text='Quit',
                                  command=lambda: self._quit())
        self.quit_bt.grid(row=6, column=0)

        self.Raw_processing_bt.bind('<Button-1>', lambda x: self.display_Raw())
        self.Data_inter_bt.bind('<Button-1>', lambda x: self.display_Interp())
        self.FMR_data_fit_bt.bind('<Button-1>', lambda x: self.display_FMRFit())
        self.SHG_bt.bind('<Button-1>', lambda x: self.display_SHGFit())
        self.kittel_lw_bt.bind('<Button-1>', lambda x: self.display_Kittel())


if __name__ == '__main__':
    # construct the main window
    root = Tk()
    root.tk.call("source", "azure.tcl")
    root.tk.call("set_theme", "light")
    root.title("Quantum Data Processing Program V 0.1")
    root.geometry('+1000+300')  # window position (450 pixels from left, 200 ones from right)
    root.eval('tk::PlaceWindow . center')
    # create a substance
    window1 = quantumGUI(master=root)

    # endless loop unless quit
    root.mainloop()
