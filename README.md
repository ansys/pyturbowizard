# **TurboTestSuite**

## **Overview**
This project aims to provide a standardized testing setup for turbomachinery-cases in Ansys Fluent through the Pythonic access with PyFluent.
The functionalities are displayed in the following Feature-Matrix:
| Case        | Fluid     | Inlet BC                  | Outlet BC                                            | Expression Template | Stages                  | Interface Types                 | Parametric Study Support |
|-------------|-----------|---------------------------|------------------------------------------------------|---------------------|-------------------------|---------------------------------|--------------------------|
| Gas Turbine | Ideal Air | Total Pressure, Mass Flow | Static Pressure, Exit Corrected Mass Flow, Mass Flow | yes                 | Unlimited (1 mesh file) | Mixing Plane, General, Periodic | yes                      |
| Compressor  | Ideal Air | Total Pressure, Mass Flow | Static Pressure, Exit Corrected Mass Flow, Mass Flow | yes                 | Unlimited (1 mesh file) | Mixing Plane, General, Periodic | yes                      |
## **Getting Started**
### **PyFluent Installation**

#### Linux / Cluster
- Follow instructions on [PyFluent (sharepoint.com)](https://ansys.sharepoint.com/sites/HPC/SitePages/PyFluent.aspx?source=https%3A%2F%2Fansys.sharepoint.com%2Fsites%2FHPC%2FSitePages%2FForms%2FByAuthor.aspx&CT=1684318712517&OR=OWA-NT&CID=5df1de12-cff9-ba33-d913-507d444faf10)
#### Windows
- Install via the [Ansys Python Manager](https://github.com/ansys/python-installer-qt-gui/releases)
- Install directly from the [PyFluent Github Repository](https://github.com/ansys/pyfluent)
