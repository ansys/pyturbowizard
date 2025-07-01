# Speedline Simulation Setup Tutorial for PyTurboWizard
This tutorial aims to showcase how to efficiently set up a speedline simulation for turbomachinery cases using PyTurboWizard.

The steps will be explained using the axial turbine tutorial example.

## Preparing the Mesh file
The mesh file can be downloaded from sharepoint: [axial_turbine_mesh.def](https://ansys.sharepoint.com/:f:/r/sites/TurbomachineryAFT/Shared%20Documents/Standard%20PyFluent%20Turbo%20Setup/3_Tutorials/0_Speedline_Setup?csf=1&web=1&e=TOXI88)

Copy the mesh file to your Fluent working directory.
## Setting up the Config File
The Config File for the axial turbine can be found under: [turboConfig_axial_turbine.json](/ptw_examples/tutorial_speedline/turboConfig_axial_turbine.json)

Copy the Config File to your Fluent working directory.

The Config File can be split in three parts:
- setting up the Fluent launch options
- the setup of the base case
- the simulation of the speedline with a parametric study

### Setting up Fluent launch options
There are two possible scenarios:
- Running Fluent on a local machine
  ```
  "launching":
    {
      "workingDir": "<PathToFluentWorkingDirectory",
      "fl_version": "25.1.0",
      "noCore": 8,
      "exitatend": false,
      "precision": "double",
      "show_gui":  true
    }
   ```
- Running Fluent on linux/cluster ([How to Run on Linux](/README.md#linux--cluster-1))
  ```
  "launching":
    {
    "fl_version": "25.1.0",
    "noCore": 28,
    "precision": "double",
    "show_gui":  true,
    "exitatend": false,
    "queue_slurm": "ottc01",
    "queue_waiting_time":  36000
    }
   ```
For a more comprehensive description of the different launch options see: [Configuration File Setup](/ptw_documentation/ConfigFile.md#Launch-Options)

### Base Case Setup
The Base Case serves as initial input case for your study. It carries all the information about the simulation setup, as well as the initial boundary conditions used. It can be very important, depending on the initialization method that is chosen for the study. A detailed description of all the available Settings can be found here: [Configuration File Setup](/ptw_documentation/ConfigFile.md)

When using the ```"baseDP"``` initialization method, the base case result is always used for initialization. It is advised to pick a well converged design point as base case to have a stable initialization for the remaining Design Points.

When using the ```"prevDP"``` initialization method, the previous Design Point is used for initialization. When utilizing this approach, it is recommended to initiate the process from one end of the speedline, such as surge or choke, and ensure a consistent and monotonic progression in the adjustment of boundary conditions while traversing the speedlines.

When using the ```"base_ini"``` initialization method, each Design Point is initialized with the initialization method of the base case (**does not work for FMG**). Therefore, the study initialization is independent of the base case convergence or boundary conditions.

In the axial turbine example, the ``"prevDP"``` initialization is used and the boundary conditions of the setup are picked accordingly to start from the choke limit of the turbine.

The ```"solution"``` argument "```"runSolver": false``` ensures that only the initialization is carried out in the base case, so that solution data is available in the study.
### Study Setup
```
{
  "launching": {...},
  "cases": {
      "axial_turbine_test": {
        "expressions": {...},
        "locations": {...},
        "fluid_properties": "...",
        "setup": {...},
        "solution": {...},
        "results": {...}
      }
    },
    "studies": {
        "axial_turbine_test": {
          "overwriteExisting": true,
          "runExistingProject": false,
          "write_data": true,
          "refCaseFilename": "axial_turbine_test_fin",
          "updateAllDPs": true,
          "initMethod": "prevDP",
          "postProc": true,
          "definition": [
            {
              "inputparameters": ["BC_OUT_p"],
              "useScaleFactor": [false],
              "valueList": [[48000, 54000, 62000, 66000, 74000]]
            }
          ]
        }
      }
}
```
The Study Setup consists of the settings ```"overwriteExisting": true``` and ```"runExistingProject": false```, which ensures that a fresh study is created and any existing study with that name gets overwritten.

```"updateAllDPs": true``` and ```"write_data": true"``` are set to capture all .dat files for the study and to run the whole speedline.

The ```"definition"``` section is used to define the parameters to be varied. In this case the static outlet pressure is varied with explicit values (no scale factor used).
