---
title: 'QuDAP: an Open Source Software for Quantum Materials Characterization '
tags:
  - Python
  - Quantum material
  - Physcial Property Measurement System
  - Experiment automation
authors:
  - name: Skai White
    affiliation: 1
  - name: Jingyu Jia
    affiliation: 2
  - name: Chunli Tang
    orcid: 0000-0001-8252-3195
    affiliation: 3
  - name: Masoud Mahjouri-Samani,
    orcid: 
    affiliation: 3
  - name: Wencan Jin
    affiliation: 3
  
affiliations:
 - name: Department of Mathematics, Hampton University, Hampton, VA, USA
   index: 1
 - name: Great Neck South High School, Lake Success, NY, USA
   index: 2
 - name: Auburn University, Auburn, AL, USA
   index: 3
date: 01 August 2024
bibliography: paper.bib

# Summary

Quantum Materials Data Acquisition and Processing (QuDAP), a Python-based and open-source software package, is designed to control and automate material characterizations based on the Physical Property Measurement System (PPMS). The software supports major hardware interfaces and protocols (USB, RS232, GPIB, and Ethernet), enabling communication with the measurement modules associated with the PPMS. It integrates multiple Python libraries to realize instrument control, data acquisition, and real-time data visualization. Here, we present features of QuDAP, including direct control of instruments without relying on proprietary software, real-time data plotting for immediate verification and analysis, full automation of data acquisition and storage, and real-time notifications of experiment status and errors. These capabilities enhance experimental efficiency, reliability, and reproducibility.

# Statement of need

The exploration of quantum materials [@azam2022laser, @awschalom2021quantum, @kumari2021recent, @wei2020emerging] has gained significant interest over decades, benefiting from their unique properties at the quantum level, compact size, and low energy consumption. These materials are promising candidates for applications in future quantum computers, sensors, and memory devices. Studying the intriguing properties of quantum materials demands extreme conditions such as low temperature, high magnetic field, and ultra-high vacuum environments. Therefore, many experimental approaches have been employed to characterize quantum materials, including magnetometry~\cite{foner1956vibrating}, spectroscopic techniques~\cite{tang2023spin, rahman2021recent}, electrical transport~\cite{nagaosa2010anomalous, rojo2013review}, thermal transport~\cite{goyal2023methodology, kalantari2022thermal}, and advanced microscopy ~\cite{zhang2018atomic,li2018mechanical}. Among them, the Physical Property Measurement System (PPMS, Quantum Design) provides the capability to achieve those goals with precise control of temperature and magnetic field under a high vacuum environment ~\cite{ppms}. In this process, PPMS needs to communicate with multiple peripheral instruments through hardware interfaces, including USB, RS232, GPIB, and Ethernet. To control and automate the data acquisition, software is needed to integrate the Standard Commands for Programmable Instruments (SCPI) protocol $\cite{Keysight}$. 

QuDAP is a Python-based data acquisition and processing software package to control and automate quantum material characterization experiments. It is developed based on the measurement modules of Quantum Design DynaCool PPMS including magnetometry, electrical transport, and ferromagnetic resonance spectroscopy. This software package provides a graphic user interface to visualize and process the experimental data in real-time, giving the users a more efficient way to monitor the experiment. Fig. 
$\ref{connectiondiagram}$ demonstrates the connection utility of this software. All the instruments are connected through the hardware interface of USB, RS232, GPIB, and ethernet. The commands for each instrument are sent using PyVISA ~\cite{Grecco2023} and MultiPyVu ~\cite{multipyvu}. The software provides the benefits as summarized below:
\begin{itemize}
    \item {\em Provide direct Python script communication and control of PPMS and instruments without using the built-in software, which improves the tunability and efficiency of the experiment. }
    
    \item {\em Built-in demagnetization process before each measurement to enhance the reliability of the measurement.}
    
    \item {\em Fully automated data acquisition and saving process with real-time plotting and progress visualization.}
    
    \item {\em Save the data with specific identifiers to avoid data overwrite and record the experiment configuration of each measurement.}
    
    \item {\em Real-time notification on the measurement status and program error through push notification, allowing the user to promptly identify and verify the experimental and parameter setup.}
\end{itemize}
In the following sections, we introduce the peripheral instruments we have integrated into our software and show the experiment procedure for this software. 


`Gala` is an Astropy-affiliated Python package for galactic dynamics. Python
enables wrapping low-level languages (e.g., C) for speed without losing
flexibility or ease-of-use in the user-interface. The API for `Gala` was
designed to provide a class-based and user-friendly interface to fast (C or
Cython-optimized) implementations of common operations such as gravitational
potential and force evaluation, orbit integration, dynamical transformations,
and chaos indicators for nonlinear dynamics. `Gala` also relies heavily on and
interfaces well with the implementations of physical units and astronomical
coordinate systems in the `Astropy` package [@astropy] (`astropy.units` and
`astropy.coordinates`).

`Gala` was designed to be used by both astronomical researchers and by
students in courses on gravitational dynamics or astronomy. It has already been
used in a number of scientific publications [@Pearson:2017] and has also been
used in graduate courses on Galactic dynamics to, e.g., provide interactive
visualizations of textbook material [@Binney:2008]. The combination of speed,
design, and support for Astropy functionality in `Gala` will enable exciting
scientific explorations of forthcoming data releases from the *Gaia* mission
[@gaia] by students and experts alike.

# Graphic User Interface

# Methods

Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text.

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

S. W was funded by Collaborative Approaches among Scientists and Engineers REU National Science Foundation EEC Division Grant 2349639.

# References