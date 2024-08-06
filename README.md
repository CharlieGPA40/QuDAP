# <img src="https://github.com/CharlieGPA40/QuDAP/blob/main/QuDAP/GUI/Icon/logo.svg" width="300"/>
<h3 align="left">Quantum Materials Data Acquisition and Processing</h3>

![GitHub release version](https://img.shields.io/github/v/release/CharlieGPA40/QuDAP?color=%2350C878&include_prereleases)
![License](https://img.shields.io/github/license/CharlieGPA40/QuDAP)
![GitHub Size](https://img.shields.io/github/repo-size/CharlieGPA40/QuDAP)
![Python Versions](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![Last updated](https://img.shields.io/github/last-commit/CharlieGPA40/QuDAP/main?label=Last%20updated&style=flat)


## Table of Content
1. [Description](README.md#Description)
2. [Requirements](README.md#Requirements)
3. [Installation](README.md#Installation)
5. [Contact](README.md#Contact)

## Description
Quantum Materials Data Acquisition and Processing (QuDAP), a Python-based and open-source software package, is designed to control and automate material characterizations based on the Physical Property Measurement System (PPMS). The software supports major hardware interfaces and protocols (USB, RS232, GPIB, and Ethernet), enabling communication with the measurement modules associated with the PPMS. It integrates multiple Python libraries to realize instrument control, data acquisition, and real-time data visualization. Here, we present features of QuDAP, including direct control of instruments without relying on proprietary software, real-time data plotting for immediate verification and analysis, full automation of data acquisition and storage, and real-time notifications of experiment status and errors. These capabilities enhance experimental efficiency, reliability, and reproducibility.

The software provides the benefits as summarized below:

1. Provide direct Python script communication and control of PPMS and instruments without using the built-in software, which improves the tunability and efficiency of the experiment.
    
2. Built-in demagnetization process before each measurement to enhance the reliability of the measurement.
    
3. Fully automated data acquisition and saving process with real-time plotting and progress visualization.
    
4. Save the data with specific identifiers to avoid data overwrite and record the experiment configuration of each measurement.
    
5. Real-time notification on the measurement status and program error through push notification, allowing the user to promptly identify and verify the experimental and parameter setup.

Note: This package is for academic and educational research (WITHOUT WARRANTIES, our software does not collect any data from users).

## Requirements
1. This package is compatible with Python 3.10 or newer. 

## Installation
QuDAP is available via [PyPi](https://pypi.org/project/QuDAP/) for Windows.

```console
(venv) $ pip install QuDAP
```

## Contact
This project is contributed by:
* Chunli Tang (Auburn University – Electrical and Computer Engineering: chunli.tang@auburn.edu)

Advisor:
* [Dr. Masoud Mahjouri-Samani](http://wp.auburn.edu/Mahjouri/) (Auburn University – Electrical and Computer Engineering: Mahjouri@auburn.edu)
* [Dr. Wencan Jin](http://wp.auburn.edu/JinLab/) (Auburn University – Physics Department: wjin@auburn.edu)
