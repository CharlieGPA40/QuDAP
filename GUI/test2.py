# -----------------------------------------------------------#
# Name: Chunli Tang                                          #
# School: Auburn University                                  #
# -----------------------------------------------------------#

from tkinter import *

import matplotlib.pyplot as plt
# from matplotlib import pyplot, spines
import numpy as np
from tkinter import filedialog
import matplotlib.patches as patches
import pandas as pd
from PIL import Image
import os

root = Tk()
# root.withdraw()
folder_selected = filedialog.askdirectory(initialdir="/Users/labaccess/Library/CloudStorage/Box-Box/Jin Lab Shared Folder/SHG-RA data")
dir_list = os.listdir(folder_selected)

file_name = dir_list[0]
file_name_1 = dir_list[1]
for i in range(len(file_name)-1, 0, -1):
    if file_name[i] == '_':
        file_name = file_name[:i]
        break


folder_selected = folder_selected + "/"
data_sel = 'n'
avg_x = 0
avg_y = 0
iteration = 0
deg_file_org = []
sig_file_org = []
temp_file = []
sig_file = []
center_x = 247
center_y = 260
region_size = 100
half_region_size = (np.ceil(region_size / 2)).astype(int)
auto = True
Parameter = pd.read_csv(folder_selected + "Experimental_Parameters.txt", header=None, sep=':')
exposure_time = str(float(Parameter.iat[9, 1]))
filename = Parameter.iat[1, 1]
filename = (filename[1:]) # + '_0deg')
print(filename)

title = str(Parameter.iat[1, 1]) + '' + str(Parameter.iat[2, 1]) + '' + str(Parameter.iat[3, 1]) \
            + '\n' + str(Parameter.iat[4, 1]) + 'mW Exposure Time ' + exposure_time + 's Averaging ' \
            + str(int(Parameter.iat[11, 1]))
polarization = Parameter.iat[8, 1]
print(Parameter)
start_temp = int(Parameter.iat[12, 1])

final_temp = int(Parameter.iat[13, 1])
step_temp = int(Parameter.iat[14, 1])


fig, ax = plt.subplots()
# SHG_Raw = np.loadtxt(folder_selected + filename + '_{}K_Warm_Up'.format(start_temp) + ".txt", dtype=int, delimiter=',')
# SHG_Raw = np.loadtxt(folder_selected + '/STO_0_0035_Temp_Dep_RA' + '_{}K_0deg'.format(start_temp) + ".txt", dtype=int, delimiter=',')
SHG_Raw = np.loadtxt(folder_selected + filename + '_0deg_{}K_Warm_Up'.format(start_temp) + ".txt", dtype=int, delimiter=',')
# SHG_Raw = np.loadtxt(folder_selected + filename + '_{}K_1_0deg'.format(start_temp) + ".txt", dtype=int, delimiter=',')
# STO_FILM_temp_dep_0deg_8K_Cooling_Down
# SHG_Raw = np.loadtxt(folder_selected + "STO_Nb_0_0035_Cover_0deg{}K".format(10) + ".txt", dtype=int, delimiter=',')
# SHG_Raw = np.loadtxt(folder_selected + "STO_Nb_0_0035_Cover_0deg_"+"{}K".format(10) + "_Cooling_Down.txt", dtype=int, delimiter=',')


region_size = 120

# Variables to store the maximum intensity and its corresponding position
max_intensity = -np.inf
max_intensity_position = None

# Iterate over all possible square regions
for i in range(SHG_Raw.shape[0] - region_size + 1):
    for j in range(SHG_Raw.shape[1] - region_size + 1):
        # Extract the current square region
        region = SHG_Raw[i:i + region_size, j:j + region_size]

        # Calculate the intensity of the region
        intensity = np.sum(region)

        # Check if the current intensity is the maximum
        if intensity > max_intensity:
            max_intensity = intensity
            max_intensity_position = (i, j)

# Get the coordinates of the square region with the maximum intensity
top_left_row, top_left_col = max_intensity_position
bottom_right_row = top_left_row + region_size - 1
bottom_right_col = top_left_col + region_size - 1

region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
                 center_y - half_region_size: center_y + half_region_size]
# im = ax.imshow(SHG_Raw)
# fig.colorbar(im, ax=ax, label='Interactive colorbar')
# ax.scatter(center_x, center_y, s=30, color='tomato', marker='x')
#
# rect = patches.Rectangle((center_x - half_region_size, center_y - half_region_size),
#                      region_size, region_size, linewidth=1, edgecolor='r', facecolor='none')
# rect = patches.Rectangle((center_x - half_region_size, center_y - half_region_size),
#                      2*half_region_size, 2*half_region_size, linewidth=1, edgecolor='b', facecolor='none')
# ax.add_patch(rect)
# plt.show()
plt.imshow(SHG_Raw, aspect='auto', vmin=0,vmax=5000)
polarization = Parameter.iat[8, 1]
plt.colorbar(label='{} Polarization'.format(polarization))
plt.scatter(top_left_col + region_size/2, top_left_row + region_size/2, s=30, color='tomato', marker='x')
plt.gca().add_patch(plt.Rectangle((top_left_col, top_left_row), region_size, region_size,
                                  edgecolor='white', facecolor='none', linewidth=2))
plt.show()

for temp in range(start_temp, final_temp + step_temp, step_temp):
    # if temp == 41:
    #     SHG_Raw = np.loadtxt(folder_selected + filename + '_0deg'+"{}.1K".format(temp) + ".txt", dtype=int, delimiter=',')
    #     region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
    #              center_y - half_region_size: center_y + half_region_size]
    #     small_sum = sum(map(sum, region))
    #     large_sum = sum(map(sum, SHG_Raw))
    #     bkg_pixel = (large_sum - small_sum) / (512 ** 2 - region_size ** 2)
    #     sig = small_sum - bkg_pixel * region_size ** 2
    #     sig_file = np.append(sig_file, sig)
    #     temp_file = np.append(temp_file, temp)
    temp_file = np.append(temp_file, temp)
    # SHG_Raw = np.loadtxt(folder_selected + filename + '_{}K_1_0deg'.format(temp) + ".txt", dtype=int, delimiter=',')
    SHG_Raw = np.loadtxt(folder_selected + 'STO_FILM_temp_dep_0deg' + '_{}K_Warm_Up'.format(temp) + ".txt", dtype=int,
                         delimiter=',')

    # SHG_Raw = np.loadtxt(folder_selected + "STO_Nb_0_0035_Cover_0deg{}K".format(temp) + ".txt",
    #                      dtype=int, delimiter=',')

    if not auto:
        region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
                 center_y - half_region_size: center_y + half_region_size]
    else:
        region = SHG_Raw[top_left_col: top_left_col + region_size, top_left_row: top_left_row + region_size]

    small_sum = sum(map(sum, region))
    large_sum = sum(map(sum, SHG_Raw))

    bkg_pixel = (large_sum - small_sum) / (512 ** 2 - region_size ** 2)
    # print('Temp: ' + str(temp) + 'K bg: ' + str(bkg_pixel) + " " + str(small_sum) + " " + str(bkg_pixel*region_size**2) )
    sig = small_sum - bkg_pixel * region_size ** 2
    # if temp > 90:
    #     sig = np.abs(sig *251883.12012012/127338.74674675)
    #     # sig =sig
    sig_file = np.append(sig_file, sig)

sig_file = sig_file.astype(np.float64)
max_lim = max(sig_file)
min_lim = min(sig_file)
deg_file = sig_file * np.pi / 180
deg_file = deg_file.astype(np.float64)

sig_df = pd.DataFrame(columns=['Temperature', 'Signal'])
sig_df_comb = pd.DataFrame(list(zip(temp_file, sig_file)))
spilt_df = pd.concat([sig_df, sig_df_comb], ignore_index=True, axis=1)
spilt_df.to_csv(folder_selected + '/temp_dep_warm_up.csv', index=False, header=False)

fig, ax = plt.subplots()
ax.plot(temp_file, sig_file, linewidth=3, color='red', label="Warming Up")
ax.scatter(temp_file, sig_file, color='red')
ax.set_xlabel('Temperature (K)')
ax.set_ylabel('SHG Intensity (counts)')
# ax.set_ylim(bottom=min_lim*0.85, top=max_lim*1.05)
plt.legend()
# ax.set_ylim(bottom=0, top=max_lim*1.05)
plt.title(title + '{} Polarization'.format(polarization), pad=10, wrap=True)
plt.tight_layout()
plt.savefig(folder_selected+"Figure_1.png")
plt.show()

#
# root = Tk()
# root.withdraw()
# folder_selected = filedialog.askdirectory(initialdir="SHG RA/SHG Data")

# folder_selected = folder_selected + "/"
data_sel = 'n'
avg_x = 0
avg_y = 0
iteration = 0
deg_file_org = []
sig_file_org = []
temp_file = []
sig_file_Cooling = []
center_x = 238
center_y = 258
region_size = 80
half_region_size = (np.ceil(region_size / 2)).astype(int)

for temp in range(start_temp, final_temp + step_temp, step_temp):
    if temp == 3341:
        SHG_Raw = np.loadtxt(folder_selected + filename + '' + '_0deg_{}K'.format(start_temp) + ".txt", dtype=int,
                             delimiter=',')

        # SHG_Raw = np.loadtxt(folder_selected + "STO_Nb_0_0035_{}.1K".format(temp) + "_0deg" + ".txt", dtype=int, delimiter=',')
        if not auto:
            region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
                     center_y - half_region_size: center_y + half_region_size]
        else:
            region = SHG_Raw[top_left_col: top_left_col + region_size, top_left_row: top_left_row + region_size]

        small_sum = sum(map(sum, region))
        large_sum = sum(map(sum, SHG_Raw))
        bkg_pixel = (large_sum - small_sum) / (512 ** 2 - region_size ** 2)
        sig = small_sum - bkg_pixel * region_size ** 2
        sig_file_Cooling = np.append(sig_file_Cooling, sig)
        temp_file = np.append(temp_file, temp)
    temp_file = np.append(temp_file, temp)
    # SHG_Raw = np.loadtxt(folder_selected + filename + '' + '_{}K_0deg'.format(start_temp) + ".txt", dtype=int,
    #                      delimiter=',')
    SHG_Raw = np.loadtxt(folder_selected + '/STO_FILM_temp_dep_0deg' + '_{}K_Cooling_Down'.format(temp) + ".txt",
                         dtype=int,
                         delimiter=',')
    # SHG_Raw = np.loadtxt(folder_selected + filename + '_{}K_Cooling_Down'.format(temp) + ".txt", dtype=int, delimiter=',')
    # SHG_Raw = np.loadtxt(folder_selected + "STO_Nb_0_0035_Cover_0deg_{}K_Cooling_Down".format(temp) + ".txt",
    #                      dtype=int, delimiter=',')
    region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
                     center_y - half_region_size: center_y + half_region_size]
    small_sum = sum(map(sum, region))
    large_sum = sum(map(sum, SHG_Raw))

    bkg_pixel = (large_sum - small_sum) / (512 ** 2 - region_size ** 2)
    # print('Temp: ' + str(temp) + 'K bg: ' + str(bkg_pixel) + " " + str(small_sum) + " " + str(bkg_pixel*region_size**2) )
    sig = small_sum - bkg_pixel * region_size ** 2
    # if temp > 90:
    #     sig = np.abs(sig *251883.12012012/127338.74674675)
    #     # sig =sig
    sig_file_Cooling = np.append(sig_file_Cooling, sig)
    sig_df = pd.DataFrame(columns=['Temperature', 'Signal'])
    sig_df_comb = pd.DataFrame(list(zip(temp_file, sig_file_Cooling)))
    spilt_df = pd.concat([sig_df, sig_df_comb], ignore_index=True, axis=1)
    spilt_df.to_csv(folder_selected + '/temp_dep_Cooling_Down.csv', index=False, header=False)

sig_file_Cooling = sig_file_Cooling.astype(np.float64)
max_lim = max(sig_file_Cooling)
min_lim = min(sig_file_Cooling)
deg_file = temp_file * np.pi / 180
deg_file = deg_file.astype(np.float64)
# fig, ax = plt.subplots()

fig, ax = plt.subplots()
ax.plot(temp_file, sig_file_Cooling, linewidth=3, color='black', label="Cooling Down")
ax.scatter(temp_file, sig_file_Cooling, color='black')
ax.set_xlabel('Temperature (K)')
ax.set_ylabel('SHG Intensity (counts)')
# ax.set_ylim(bottom=min_lim*0.85, top=max_lim*1.05)
plt.legend()
# ax.set_ylim(bottom=0, top=max_lim*1.05)
plt.title(title + '{} Polarization'.format(polarization), pad=10, wrap=True)
plt.tight_layout()
plt.savefig(folder_selected+"Figure_2.png")
plt.show()


fig, ax = plt.subplots()
ax.plot(temp_file, sig_file, linewidth=3, color='red', label="Warm Up")
ax.scatter(temp_file, sig_file, color='red')
ax.plot(temp_file, sig_file_Cooling, linewidth=3, color='black', label="Cooling Down")
ax.scatter(temp_file, sig_file_Cooling, color='black')
ax.set_xlabel('Temperature (K)')
ax.set_ylabel('SHG Intensity (counts)')
# ax.set_ylim(bottom=min_lim*0.85, top=max_lim*1.05)
plt.legend()
# ax.set_ylim(bottom=0, top=max_lim*1.05)
plt.title(title + '{} Polarization'.format(polarization), pad=10, wrap=True)

plt.tight_layout()
plt.savefig(folder_selected+"Figure_3.png")
plt.show()

