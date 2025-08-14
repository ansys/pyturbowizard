# Speedline simulation setup example
This example shows how to efficiently set up a speedline simulation for turbomachinery cases using PyTurboWizard.

All steps are explained using the axial turbine example.

## Prepare the mesh file

1. Download the [axial_turbine_mesh.def](https://github.com/ansys/example-data/tree/main/pyfluent/tutorials/axial_turbine/axial_turbine_mesh.def) file from the Ansys ``example-data`` repository.

2. Copy this mesh file to your Fluent working directory.

## Set up the configuration file

1. Copy the [turboConfig_axial_turbine.json](turboConfig_axial_turbine.json) configuration file to your Fluent working directory.

2. Make changes to this configuration file as indicated in these subsections:

    - [Set up Fluent launching options](#set-up-fluent-launching-options)
    - [Set up the base case](#set-up-the-base-case)
    - [Set up the study](#set-up-the-study)

### Set up Fluent launching options
You can launch Fluent in one of two ways:

- Launch Fluent on a local machine:
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
- Launch Fluent on a Linux cluster:

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
  
For more information, in the repository's ```README.md``` file, see the **Linux/Cluster** information in [How to run](https://github.com/ansys-internal/pyturbowizard/blob/main/README.md#how-to-run).

For descriptions of launching options, see [Launching options](../../ConfigFile.md#launching-options) in the ```ConfigFile.md``` file.

### Set up the base case
The base case serves as initial input case for your study. It provides all information about the simulation setup and initial boundary conditions.

Depending on the initialization method that is chosen for the study, the base case can be very important. For descriptions of all study settings, see [Study configuration](../../ConfigFile.md#study-configuration) in the ```ConfigFile.md``` file.

- When using the ```"baseDP"``` initialization method, the base case result is always used for initialization. You should pick a well converged design point as the base case to have a stable initialization for the remaining design points.

- When using the ```"prevDP"``` initialization method, the previous design point is used for initialization. Thus, you should initiate the process from one end of the speedline, such as the surge or choke, to ensure a consistent and monotonic progression in the adjustment of boundary conditions while traversing the speedlines.

- When using the ```"base_ini"``` initialization method, each design point is initialized with the initialization method of the base case. Therefore, the study initialization is independent of the base case convergence or boundary conditions.

  **Note:** The ```"base_ini"``` initialization  method does not work for FMG.

This axial turbine example uses the ```"prevDP"``` initialization method. The boundary conditions of the setup are picked accordingly to start from the choke limit of the turbine.

The ```"solution"``` argument "```"runSolver": false``` ensures that only the initialization is carried out in the base case so that solution data is available in the study.

### Set up the study

Set up the simulation of the speedline with a parametric study:

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
The study setup consists of the settings ```"overwriteExisting": true``` and ```"runExistingProject": false```, which ensure that a fresh study is created and any existing study with that name gets overwritten.

The ```"updateAllDPs": true``` and ```"write_data": true"``` settings are defined so that all DAT files for the study are captured while running the entire speedline.

The ```"definition"``` section defines the parameters to vary. In this example, the static outlet pressure is varied with explicit values. (No scale factor is used.)
