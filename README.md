# **PyTurboWizard**

## **Open-Source Software Disclaimer**

This deliverable depends on Open-Source Software (OSS), which are subject to their own terms & conditions and may
contain vulnerabilities.
Ansys is not responsible for such Third-Party Software.

Please check the [LICENSE-file](./LICENSE).

It is recommended to consult your company’s Software Security department before installing any software on company
hardware.

## **Overview**

This project aims to provide a standardized testing setup for turbomachinery-cases in Ansys Fluent through the Pythonic
access with PyFluent.
The functionalities are displayed in the following Feature-Matrix:
| Case | Fluid | Inlet BC | Outlet BC | Expression Template | Stages | Interface Types | Parametric Study Support |
|---------------------------|------------|----------------------------------|------------------------------------------------|---------------------|---------------------|------------------------------------------------------|--------------------------|
| Gas Turbine (compressible)| Ideal Air | Total Pressure, Mass Flow, Volume Flow | Static Pressure, Exit Corrected Mass
Flow, Mass Flow, Volume Flow | yes | Unlimited | General, Periodic, No Pitch-Scale, Pitch-Scale, Mixing Plane | yes |
| Compressor (compressible) | Ideal Air | Total Pressure, Mass Flow, Volume Flow | Static Pressure, Exit Corrected Mass
Flow, Mass Flow, Volume Flow | yes | Unlimited | General, Periodic, No Pitch-Scale, Pitch-Scale, Mixing Plane | yes |
| Gas Turbine (inccompressible) | Ideal Air | Total Pressure, Mass Flow, Volume Flow | Static Pressure, Exit Corrected
Mass Flow, Mass Flow, Volume Flow | yes | Unlimited | General, Periodic, No Pitch-Scale, Pitch-Scale, Mixing Plane |
yes |
| Compressor (inccompressible) | Ideal Air | Total Pressure, Mass Flow, Volume Flow | Static Pressure, Exit Corrected
Mass Flow, Mass Flow, Volume Flow | yes | Unlimited | General, Periodic, No Pitch-Scale, Pitch-Scale, Mixing Plane |
yes |

**Note: Default rotation axis is expected to be z-axis (0,0,1) with axis origin (0,0,0)**

## **Getting Started**

The PyTurboWizard has been developed for Ansys Fluent versions 2024R1 and latter versions.
It can also be used running the Ansys GPU Solver (use '-gpu' flag in launching options), but not all features will be
supported, though!

### Installation

It is recommended to create a python virtual environment to install the PyTurboWizard.

To create and install a virtual environment, please have a look at
the [Ansys Python Manager](https://github.com/ansys/python-installer-qt-gui/releases)

Install PyTurboWizard using `pip` in your dedicated virtual-environment:

`pip install ansys-ptw`

All needed libraries wil be installed automatically.

#### For developers

If you plan on doing local *development* of PyTurboWizard with Git, install
the latest release with:

- `git clone https://github.com/ansys-internal/pyturbowizard`
- `pip install -e .`

### **How to Run**

- Install latest version of PyTurboWizard, see [installation instructions](#Installation).
- Prepare data in your working directory
    - Copy Fluent data into the folder, e.g. mesh data, profiles, etc.
    - Copy a Configuration File to your Fluent working directory
    - Adjust the Configuration File to your setup ([Configuration File Setup](doc/ConfigFile.md))
- Execute script:

  `ansys-ptw <PathToConfigurationFile.json/yaml>`

## Useful Documents

- [Configuration File Setup](doc/ConfigFile.md)
- [Tutorial: Speedline Simulation Setup](doc/examples/Speedline_Tutorial/speedline_tutorial.md)
