# <img src="https://github.com/CharlieGPA40/QuDAP/blob/main/QuDAP/GUI/Icon/logo.svg" width="300"/>
<h3 align="left">Quantum Materials Data Acquisition and Processing</h3>

![GitHub release version](https://img.shields.io/github/v/release/CharlieGPA40/QuDAP?color=%2350C878&include_prereleases)
![License](https://img.shields.io/github/license/CharlieGPA40/QuDAP)
![GitHub Size](https://img.shields.io/github/repo-size/CharlieGPA40/QuDAP)
![Python Versions](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![Last updated](https://img.shields.io/github/last-commit/CharlieGPA40/QuDAP/main?label=Last%20updated&style=flat)
[![Request](https://img.shields.io/badge/request-features-orange)](mailto:chunli.tang@auburn.edu)
[![Connect](https://img.shields.io/badge/Connect_me-navy)](http://www.linkedin.com/in/chunlitang)
<a href="https://joss.theoj.org/papers/69d38a267017a55683b6bdb958846c54"><img src="https://joss.theoj.org/papers/69d38a267017a55683b6bdb958846c54/status.svg"></a>


## Table of Content
1. [Description](README.md#Description)
2. [Requirements](README.md#Requirements)
3. [Installation](README.md#Installation)
5. [Usage](README.md#Usage)
6. [Contact](README.md#Contact)

## Description
Quantum Materials Data Acquisition and Processing `QuDAP`, a Python-based and open-source software package, is designed to control and automate material characterizations based on the Physical Property Measurement System (PPMS). The software supports major hardware interfaces and protocols (USB, RS232, GPIB, and Ethernet), enabling communication with the measurement modules associated with the PPMS. It integrates multiple Python libraries to realize instrument control, data acquisition, and real-time data visualization. Here, we present features of QuDAP, including direct control of instruments without relying on proprietary software, real-time data plotting for immediate verification and analysis, full automation of data acquisition and storage, and real-time notifications of experiment status and errors. These capabilities enhance experimental efficiency, reliability, and reproducibility.

The software provides the benefits as summarized below:

1. Provide direct Python script communication and control of PPMS and instruments without using the built-in software, which improves the tunability and efficiency of the experiment.
    
2. Built-in demagnetization process before each measurement to enhance the reliability of the measurement.
    
3. Fully automated data acquisition and saving process with real-time plotting and progress visualization.
    
4. Save the data with specific identifiers to avoid data overwrite and record the experiment configuration of each measurement.
    
5. Real-time notification on the measurement status and program error through push notification, allowing the user to promptly identify and verify the experimental and parameter setup.

Note: This package is for academic and educational research (WITHOUT WARRANTIES or instrument issues; our software does not collect any data from users).

## Requirements
1. `QuDAP` is compatible with Python 3.10 or newer.

3. Hardware requirements:
   
   i). Physical Property Measurement System from Quantum Design.
   
   ii). GPIB cables, RS232, USB, or Ethernet.
   
   iii). Supported instruments (Keithley 6221, Keithley 2182, etc.) or try out our software using the demo feature.
4. Software requirements:
   
   i). **OS**: Windows 11.
   
   ii). **Dependencies**: Listed in `pyproject.toml` (no default `requirements.txt` is included — see [Generate Your Own Requirements File (Optional)](README.md#3-generate-your-own-requirements-file-optional)).

- **Experimental Features**: QuDAP’s experimental modules require the Physical Property Measurement System (PPMS) and any associated hardware (e.g., VSM attachments).  
- **Data Processing**: The processing and analysis tools can run without any specialized hardware, so you can analyze data offline without a live instrument.
  
## Installation
### 1. Option 1 - PyPi installation
`QuDAP` is available via [PyPi](https://pypi.org/project/QuDAP/) for Windows and can be installed by:

```console
$ pip install QuDAP
```
### 2. Option 2 - Clone the Repository
or installed from source:
```bash
git clone https://github.com/CharlieGPA40/QuDAP.git
cd QuDAP
pip install .
```
### 3. Generate Your Own Requirements File (Optional)
If you prefer installing pinned dependencies (exact versions for reproducibility), you can create a 'requirements.txt' from the 'pyproject.toml' using pip-tools. This way, you control which versions get installed without QuDAP shipping a pre-generated file.
1. Install 'pip-tools':
```bash
pip install pip-tools
```

2. Compile dependencies from 'pyproject.toml':
```bash
pip-compile --output-file requirements.txt pyproject.toml
```

### 4. Install Dependencies
You have two primary options:
1. Install 'pyproject.toml':
```bash
pip install .
```
This reads '[QuDAP] dependencies' in 'pyproject.toml' and installs the most recent compatible versions.
2. Install from your compiled 'requirements.txt' (for locked versions):


## Usage
To run the program, run the`QuDAP/StartGUI.py` or 
```console
$ python ./QuDAP/StartGUI.py
```
Check the [`docs`](https://github.com/CharlieGPA40/QuDAP/tree/main/doc/)  file to learn how to use the software.

Demonstration
1. Software interface and experimental setup
![line](https://github.com/CharlieGPA40/QuDAP/blob/main/doc/demo/Experiment%20Demo.gif)

2. Demo for Keithley 2182 nanovoltmeter
![line](https://github.com/CharlieGPA40/QuDAP/blob/main/doc/demo/Emulation/Keithley%202182%20demo.gif)

3. Demo for Keithley 6221 current and voltage source
![line](https://github.com/CharlieGPA40/QuDAP/blob/main/doc/demo/Emulation/Keithley%206221%20demo.gif)

4. Demo for DSP 7260 lock-in amplifier
![line](https://github.com/CharlieGPA40/QuDAP/blob/main/doc/demo/Emulation/DSP%207265%20Demo.gif)

5. Demo for sr380 lock-in amplifier
![line](https://github.com/CharlieGPA40/QuDAP/blob/main/doc/demo/Emulation/SR830%20Demo.gif)

6. Demo for experiment
![line](https://github.com/CharlieGPA40/QuDAP/blob/main/doc/demo/Emulation/Measurement%20Demo.gif)

7. Demo for Second harmonic generation data processing
![line](https://github.com/CharlieGPA40/QuDAP/blob/main/doc/demo/Emulation/SHG%20Data%20Processing%20Demo.gif)

8. Demo for PPMS VSM data extraction
![line](https://github.com/CharlieGPA40/QuDAP/blob/main/doc/demo/Emulation/VSM%20Data%20Processing%20Demo.gif)

More coming...


## Contact
This project is contributed by:
* [Chunli Tang](http://www.linkedin.com/in/chunlitang) (Auburn University, Auburn AL – Electrical and Computer Engineering: chunli.tang@auburn.edu)
* Skai White - Hampton University, Hampton, VA USA
* Jingyu Jia - Great Neck South High School, Lake Success, NY USA

Advisor:
* [Dr. Masoud Mahjouri-Samani](http://wp.auburn.edu/Mahjouri/) (Auburn University – Electrical and Computer Engineering: Mahjouri@auburn.edu)
* [Dr. Wencan Jin](http://wp.auburn.edu/JinLab/) (Auburn University – Physics Department: wjin@auburn.edu)


