# -----------------------------------------------------------#
# Name: Chunli Tang                                          #
# School: Auburn University                                  #
# -----------------------------------------------------------#

import os
from tkinter import *
from matplotlib import pyplot
import matplotlib.patches as patches
import numpy as np
from tkinter import filedialog
import math

#  Initialization
avg_x = 0
avg_y = 0
iteration = 0
deg_file_org = []
sig_file_org = []
deg_file = []
sig_file = []

file_name = "LSMO_10K_large"

SHGpath = 'SHG'  # Processed data directory
isExist = os.path.exists(SHGpath)
if not isExist:  # Create a new directory because it does not exist
    os.makedirs(SHGpath)
    print("The new directory is created!")
    print('--------------------------------------------\n')

# Select the data folder
root = Tk()
root.withdraw()
folder_selected = filedialog.askdirectory(initialdir="")
folder_selected = folder_selected + "/"
data_sel = 'n'

# Enter the experiment angle interval (in degree)
step_size = int(input('What is the step size (in degree)? '))

# Find the desire data point coordinator
# for degree in range(0, 365, step_size):
SHG_Raw = np.loadtxt(folder_selected + file_name + "_{}deg".format(10) + ".txt", dtype=int, delimiter=',')
fig, ax = pyplot.subplots()
im = ax.imshow(SHG_Raw, vmin=1600, vmax=2900)
fig.colorbar(im, ax=ax, label='Interactive colorbar')
pyplot.show()

#  Enter the center info
center_x = int(input('Enter the center for x axis: '))
center_y = int(input('Enter the center for y axis: '))
region_size = int(input('Enter the box size: '))
half_region_size = (np.ceil(region_size / 2)).astype(int)
# Read the data file
SHG_Raw = np.loadtxt(folder_selected + file_name + "_{}deg".format(0) + ".txt", dtype=int, delimiter=',')
# Define the data box
region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
         center_y - half_region_size: center_y + half_region_size]
# Plot the selected box to verify
fig, ax = pyplot.subplots()
im = ax.imshow(SHG_Raw, vmin=1600, vmax=2900)
fig.colorbar(im, ax=ax, label='Interactive colorbar')
ax.scatter(center_x, center_y, s=30, color='tomato', marker='x')
rect = patches.Rectangle((center_x - half_region_size, center_y - half_region_size),
                         region_size, region_size, linewidth=1, edgecolor='r', facecolor='none')
# Add the patch to the Axes
ax.add_patch(rect)
pyplot.show()

# Background substration and stacking process
for degree in range(0, 360, step_size):
    deg_file = np.append(deg_file, degree)
    SHG_Raw = np.loadtxt(folder_selected + file_name + "_{}deg".format(degree) + ".txt", dtype=int, delimiter=',')
    region = SHG_Raw[center_x - half_region_size: center_x + half_region_size,
             center_y - half_region_size: center_y + half_region_size]
    BKG_region = SHG_Raw[450 - half_region_size: 450 + half_region_size,
                 50 - half_region_size: 50 + half_region_size]
    # Sum data region
    small_sum = sum(map(sum, region))
    # Sum entire data
    large_sum = sum(map(sum, BKG_region))
    # Cal backgroung pixel
    bkg_pixel = (large_sum - small_sum) / (512 ** 2 - region_size ** 2)
    sig = small_sum - bkg_pixel * region_size ** 2
    sig_file = np.append(sig_file, sig)

# Plot signal data
sig_file = sig_file.astype(np.float64)
# sig_file = sig_file.tolist()
max_lim = max(sig_file)
min_lim = min(sig_file)
deg_file = deg_file * np.pi / 180
deg_file = deg_file.astype(np.float64)
fig, ax = pyplot.subplots(subplot_kw={'projection': 'polar'})
ax.plot(deg_file, sig_file, color='red')
ax.set_ylim(bottom=min_lim, top=max_lim)
pyplot.show()
pyplot.plot(deg_file, sig_file, linewidth=3, color='blue')
pyplot.show()
slope = (sig_file[-1] - sig_file[0]) / (deg_file[-1] - deg_file[0])
const = sig_file[-1] - slope * deg_file[-1]

for i in range(len(sig_file)):
    sig_file[i] = sig_file[i] - (slope * deg_file[i] + const)
    sig_file[i] = sig_file[i]/2000000


pyplot.plot(deg_file, sig_file, linewidth=3, color='blue')
pyplot.show()
print(deg_file)
print(sig_file)
max_lim = max(sig_file)
min_lim = min(sig_file)

fig, ax = pyplot.subplots(subplot_kw={'projection': 'polar'})
ax.plot(deg_file, sig_file, color='red')
ax.set_ylim(bottom=min_lim, top=max_lim)
pyplot.show()

def fitting(x, a, b, c, t):
    return 1/16 * ((a+b+c)**2) * ((math.sin(4*x))**2) * ((math.sin(t))**2)

def fitting_2(x, zxzx, yxyx, theta, yyxx, yyyy):
    return (zxzx ** 2 + (4 * yxyx * ((math.sin(x)) ** 4) + 4 * yxyx * ((math.cos(x)) ** 4) + 2 * yyxx * (math.cos(4 * x) - 1)
                         - yyyy * (math.cos(4 * x) - 1)) ** 2 / 16) * ((math.sin(theta)) ** 2) * ((math.cos(theta)) ** 2)