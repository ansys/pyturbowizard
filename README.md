# **PyTurboWizard**

## **Overview**
This project aims to provide a standardized testing setup for turbomachinery-cases in Ansys Fluent through the Pythonic access with PyFluent.
The functionalities are displayed in the following Feature-Matrix:
| Case                      | Fluid      | Inlet BC                          | Outlet BC                                      | Expression Template | Stages              | Interface Types                                      | Parametric Study Support |
|---------------------------|------------|----------------------------------|------------------------------------------------|---------------------|---------------------|------------------------------------------------------|--------------------------|
| Gas Turbine (compressible)| Ideal Air  | Total Pressure, Mass Flow, Volume Flow | Static Pressure, Exit Corrected Mass Flow, Mass Flow, Volume Flow | yes                 | Unlimited | General, Periodic, No Pitch-Scale, Pitch-Scale, Mixing Plane | yes                      |
| Compressor (compressible) | Ideal Air  | Total Pressure, Mass Flow, Volume Flow | Static Pressure, Exit Corrected Mass Flow, Mass Flow, Volume Flow | yes                 | Unlimited | General, Periodic, No Pitch-Scale, Pitch-Scale, Mixing Plane | yes                      |
| Gas Turbine (inccompressible) | Ideal Air | Total Pressure, Mass Flow, Volume Flow | Static Pressure, Exit Corrected Mass Flow, Mass Flow, Volume Flow | yes                 | Unlimited | General, Periodic, No Pitch-Scale, Pitch-Scale, Mixing Plane | yes                      |
| Compressor (inccompressible) | Ideal Air | Total Pressure, Mass Flow, Volume Flow | Static Pressure, Exit Corrected Mass Flow, Mass Flow, Volume Flow | yes                 | Unlimited | General, Periodic, No Pitch-Scale, Pitch-Scale, Mixing Plane | yes                      |


**Note: Default rotation axis is expected to be z-axis (0,0,1) with axis origin (0,0,0)**

## **Getting Started**
### **Fluent Installation**
**The script has been developed for Ansys Fluent versions 2023R2 and latter versions**
### **PyFluent Installation**

Required libraries:
- PyFluent
- Matplotlib
- NumPy
- Pandas


#### Linux / Cluster
- Follow instructions on [PyFluent (sharepoint.com)](https://ansys.sharepoint.com/sites/HPC/SitePages/PyFluent.aspx?source=https%3A%2F%2Fansys.sharepoint.com%2Fsites%2FHPC%2FSitePages%2FForms%2FByAuthor.aspx&CT=1684318712517&OR=OWA-NT&CID=5df1de12-cff9-ba33-d913-507d444faf10)
- Install matplotlib in command shell analogous to PyFluent: ```~/.virtualenvs/pyansys/bin/pip install matplotlib```
#### Windows
- Install via the [Ansys Python Manager](https://github.com/ansys/python-installer-qt-gui/releases)
- Install directly from the [PyFluent Github Repository](https://github.com/ansys/pyfluent)

### **How to Run**
#### Linux / Cluster
- Prepare data in your working directory
  - Copy Fluent data into the folder, e.g. mesh data, profiles
  - Copy a Configuration File (GitHub) to your Fluent working directory
  - Adjust the Configuration File to your setup ([Configuration File Setup](ptw_documentation/ConfigFile.md))
- Get latest Version From GitHub: [main branch](https://github.com/ansys-internal/pyturbowizard/tree/main)
  - Copy all files from GitHub to a specific folder
  - Start a Fluent job on cluster with additional arguments: ```-py -sifile=<name>.txt ```
  - Open terminal in Fluent data folder
  - Execute script 
    - Basic command: ```pyfluent ptw_main.py <PathToConfigurationFile.json/yaml>```
    - More advanced
      - Set an alias in your shell config-file, e.g.  ```alias ptw 'pyfluent /path_to_ptw/ptw_main.py'```
      - Command: ```ptw <PathToConfigurationFile.json/yaml>```
      
#### Windows
- Prepare data in you working directory
  - Copy Fluent data into the folder, e.g. mesh data, profiles
  - Copy a Configuration File (GitHub) to your Fluent working directory
  - Adjust the Configuration File to your setup ([Configuration File Setup](ptw_documentation/ConfigFile.md))
- Get latest Version From GitHub: [main branch](https://github.com/ansys-internal/pyturbowizard/tree/main)
  - Copy complete file structure from GitHub to a specific folder
  - Open Windows PowerShell in Fluent data folder
  - Execute script via: ```python <PathToPTWMain.py> <PathToConfigurationFile.json/yaml>```

## Useful Documents
- [Configuration File Setup](ptw_documentation/ConfigFile.md)
- [Tutorial: Speedline Simulation Setup](/ptw_examples/tutorial_speedline/speedline_tutorial.md)
