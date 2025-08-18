# Speedline simulation setup example

This example shows how to efficiently set up a speedline simulation for turbomachinery cases using PyTurboWizard.

All steps use the axial turbine example.

## Prepare the mesh file

1. Download the [axial_turbine_mesh.def](https://github.com/ansys/example-data/tree/main/pyfluent/tutorials/axial_turbine/axial_turbine_mesh.def) file from the Ansys `example-data` repository.

2. Copy this mesh file to your Fluent working directory.

## Set up the configuration file

1. Copy the [turboConfig_axial_turbine.json](turboConfig_axial_turbine.json) configuration file to your Fluent working directory.

2. Modify this configuration file as described in these subsections:

    - [Set up Fluent launching options](#set-up-fluent-launching-options)
    - [Set up the base case](#set-up-the-base-case)
    - [Set up the study](#set-up-the-study)

### Set up Fluent launching options

Launch Fluent using one of these methods:

- Launch Fluent on a local machine:
  ```json
  "launching":
    {
      "workingDir": "<PathToFluentWorkingDirectory>",
      "fl_version": "25.1.0",
      "noCore": 8,
      "exitatend": false,
      "precision": "double",
      "show_gui": true
    }
  ```
- Launch Fluent on a Linux cluster:
  ```json
  "launching":
    {
      "fl_version": "25.1.0",
      "noCore": 28,
      "precision": "double",
      "show_gui": true,
      "exitatend": false,
      "queue_slurm": "ottc01",
      "queue_waiting_time": 36000
    }
  ```

For more information, see **Linux/Cluster** in section in the [How to Run](https://github.com/ansys-internal/pyturbowizard/blob/main/README.md#how-to-run) section of the repository's ```README.md``` file.

For descriptions of launching options, see [Launching options](../../ConfigFile.md#launching-options) in the `ConfigFile.md` file.

### Set up the base case

The base case serves as the initial input case for your study. It provides all information about the simulation setup and initial boundary conditions.

The initialization method that you choose for the study determines the importance of the base case. For descriptions of all study settings, see [Study configuration](../../ConfigFile.md#study-configuration) in the `ConfigFile.md` file.

- When using the ```"baseDP"``` initialization method, the base case result is always used for initialization. Select a well-converged design point as the base case to ensure stable initialization for the remaining design points.

- When using the ```"prevDP"``` initialization method, the previous design point is used for initialization. Start the process from one end of the speedline, such as the surge or choke, to ensure consistent and monotonic progression in boundary condition adjustments while traversing the speedlines.

- When using the ```"base_ini"``` initialization method, each design point is initialized with the initialization method of the base case. This makes the study initialization independent of the base case convergence or boundary conditions.

  **Note:** The ```"base_ini"``` initialization method does not work for FMG.

This axial turbine example uses the ```"prevDP"``` initialization method. The boundary conditions are set to start from the choke limit of the turbine.

The ```"solution"``` argument ```"runSolver": false``` ensures that only the initialization is carried out in the base case so that solution data is available for the study.

### Set up the study

Set up the speedline simulation with a parametric study:

```json
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

The study setup includes the settings `"overwriteExisting": true` and `"runExistingProject": false`, which ensure that a fresh study is created and any existing study with the same name is overwritten.

The `"updateAllDPs": true` and `"write_data": true` settings ensure that all DAT files for the study are captured while running the entire speedline.

The ```"definition"``` section specifies the parameters to vary. In this example, the static outlet pressure is varied with explicit values. (No scale factor is used.)
