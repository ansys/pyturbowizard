# Setup of the Configuration File
This guide aims to give an overview on how to adjust the Configuration File for single case setups and parametric studies.
## Single Case Setup
The Configuration file for single case setups can be found in the [main branch](https://github.com/ansys-internal/turbotestsuite/tree/main) as ``` TurboSetupConfig.json ```.

It serves as input file for the launch options, boundary conditions, as well as the numeric and simulation setups needed to run the main script. In the following the different sections of the Configuration File are explained in detail.

### Setup Subroutines
Under the section ``` functions ```, different subroutines for the numerical setup, post processing or the parametric studies can be specified:

```
"functions":
    {
      "numerics": "numerics_01",
      "postproc": "post_01",
      "parametricstudy": "study_01"
    },
```
**Currently only the default routines are available for the setup.**

### Launch Options
Under the section ``` launching ```, different options for launching options for Fluent can be specified, like the version, number of processes and single or double precision solver.

``` external ``` refers to if you wish to run the Script interally via the Fluent Python console or externally. **Currently only the External option is supported by the script.**

For running Fluent on Linux or a Cluster, the script needs to hook on to a existing Fluent session ([How to Run on Linux](/README.md)). For this a server file name has to be specified under ``` serverfilename ```

``` exitatend ``` can be used to specify whether you want to close Fluent after the script is finished.
```
"launching":
    {
      "workingDir": "<pathToFluentWorkingDir>",
      "fl_version": "23.2.0",
      "noCore": 2,
      "precision": "double",
      "external": true,
      "serverfilename": "",
      "exitatend": false
    },
```

### Cases
Under the ``` cases ``` section different case setups can be specified for the script to run (different meshes etc.).

```
 "cases": {
      "Case_1": {
        "caseFilename": "Case_1",
        "meshFilename": "Case_1_mesh",
        "profileName_In": "InProfile.csv",
        "profileName_Out": "",
        "expressionFilename": "exp.tsv",
        "expressionTemplate": "expressionTemplate_compressor_comp.tsv",
        ...
      },
      "Case_2": {
      ....
      }
```

First, different general case parameters, like the final ``` caseFilename ``` and the initial ``` meshFilename ``` have to be specified. 

Supported file types for meshes are .def, .cgns, .msh, .cas. Make sure that the mesh file is located in the Fluent working directory.

You can choose to specify a profile for your inlet or outlet boundaries by providing the ``` profileName ``` in your Fluent working directory. Next, you can choose your ``` expressionTemplate ```. Currently, there are expression templates availabe for a compressor and a turbine setup.

```
 "Case_1": {
       ...
       "expressions": {
          "GEO_IN_No_Passages": "1",
          "GEO_IN_No_Passages_360": "1",
          "GEO_OUT_No_Passages": "1",
          "GEO_OUT_No_Passages_360": "1",
          "BC_pref":	"0 [Pa]",
          "BC_RPM":	"17000 [rev / min]",
          "BC_IN_pt":	"",
          "BC_IN_p_gauge": 	"58000 [Pa]",
          "BC_IN_Tt":	"",
          "BC_IN_TuIn":	"0.05",
          "BC_IN_TuVR":	"10",
          "BC_OUT_p":	"60000 [Pa]"
         },
      ...
```
Now you can specify values your boundary condition and geometric expressions, that are available in your expression template. Make sure to leave the values blank, if you use profile data.

Under the ``` locations ``` section the different regions of your mesh have to be mapped accordingly. Please note that every location input is a list, so that you can map multiple regions, e.g. ``` ["inlet1","inlet2"] ```. Interfaces can also be specified for periodic and general interfaces or mixing plane models.

```
"Case_1": {
        ...
        "locations": {
                  "cz_rotating_names": ["a-rotor-1"],
                  "bz_inlet_names": ["inlet1","inlet2"],
                  "bz_outlet_names": ["outlet"],
                  "bz_walls_counterrotating_names": ["a-rotor-1-shroud"],
                  "bz_walls_rotating_names": [],
                  "bz_walls_freeslip_names": ["a-rotor-1-default"],
                  "bz_interfaces_periodic_names": {
                    "a-rotor-periodic-interface-1": {
                        "side1": "a-rotor-1-to-a-rotor-1-periodic-1-side-1",
                        "side2": "a-rotor-1-to-a-rotor-1-periodic-1-side-2"
                      },
                    "b-stator-periodic-interface-1": {
                        "side1": "b-stator-1-to-b-stator-1-periodic-1-side-1",
                        "side2": "b-stator-1-to-b-stator-1-periodic-1-side-2"
                      }
                  },
                  "bz_interfaces_mixingplane_names": {
                    "a-rotor-1-b-stator-1-mpm": {
                      "side1": "b-stator-1-to-a-rotor-1-side-1",
                      "side2": "b-stator-1-to-a-rotor-1-side-2"
                    }
                  },
                  "bz_interfaces_general_names": {
                    "a-rotor-1-tip": {
                      "side1": "a-rotor-1-to-a-rotor-1-internal-side-1",
                      "side2": "a-rotor-1-to-a-rotor-1-internal-side-2"
                    }
                  },
                  ...
```

In the ``` locations ``` section a turbo topolgy for post processing in Fluent can be defined. For different mesh regions (e.g. rotors and stators), seperate topologies have to be created.

```
...
"tz_turbo_topology_names":{
            "a-rotor-1-topology":{
              "tz_shroud_names": ["a-rotor-1-shroud"],
              "tz_hub_names": ["a-rotor-1-hub"],
              "tz_inlet_names": ["inlet"],
              "tz_outlet_names": ["b-stator-1-to-a-rotor-1-side-2"],
              "tz_blade_names": ["a-rotor-1-blade"],
              "tz_theta_periodic_names":["a-rotor-periodic-interface-1"]
            },
            "b-stator-1-topology":{
              "tz_shroud_names": ["b-stator-1-shroud"],
              "tz_hub_names": ["b-stator-1-hub"],
              "tz_inlet_names": ["b-stator-1-to-a-rotor-1-side-1"],
              "tz_outlet_names": ["outlet"],
              "tz_blade_names": ["b-stator-1-blade"],
              "tz_theta_periodic_names":["b-stator-periodic-interface-1"]
            }
          },
          ...
```

This completes the setup of the ``` locations ``` section.

### Solution & Results Setup
In the section ``` solution ``` the convergence criteria and solve settings can be specified. 

In ```reportlist``` the expressions for monitoring (plotting and file save) can be specified. 

``` res_crit``` is used to specify the normalized local residual convergence limit. 

```cov_list``` and  ``` cov_crit ``` are used to specify the parameters and convergence criteria used for a Coefficient of Variation. 

```tsn``` turns on turbo machinery specific numerics as beta feature. 

The automatic time step factor and iteration count can be set via ``` time_step_factor ``` and ``` iter_count ```. 

``` runSolver``` can be used to specify whether the simulation should start to run at the end of the setup.

```
"Case_1": {
        ...
        "solution": {
                  "reportlist": ["MP_IN_MassFlow","MP_OUT_MassFlow","MP_Isentropic_Efficiency","MP_PRt"],
                  "res_crit": 1e-5,
                  "cov_list": [
                    "MP_Isentropic_Efficiency",
                    "MP_IN_MassFlow",
                    "MP_PRt"
                  ],
                  "cov_crit": 1.0e-5,
                  "tsn": true,
                  "iter_count": 500,
                  "time_step_factor": 5,
                  "runSolver": false
                },
                "results": {
                  "filename_inputParameter_pf": "inputParameters.out",
                  "filename_outputParameter_pf": "outParameters.out",
                  "filename_summary_pf": "report.sum"
                }
```

## Parametric Study Setup
The Configuration file for a parametric study can be found in the [main branch](https://github.com/ansys-internal/turbotestsuite/tree/main) as ``` TurboStudyConfig.json ```.
### Launch Options
Under the section ``` launching ```, different options for launching options for Fluent can be specified, like the version, number of processes and single or double precision solver.

```
"launching":
    {
      "workingDir": "<pathToFluentWorkingDir>",
      "fl_version": "23.2.0",
      "noCore": 2,
      "precision": "double",
      "external": true,
      "serverfilename": "",
      "plotResults": true,
      "exitatend": false
    },
```

``` external ``` refers to if you wish to run the Script interally via the Fluent Python console or externally. **Currently only the External option is supported by the script.**

For running Fluent on Linux or a Cluster, the script needs to hook on to a existing Fluent session ([How to Run on Linux](/README.md)). For this a server file name has to be specified under ``` serverfilename ```

```plotResults``` specifies, whether a Operating Point Map should be plotted and saved from the results of the parametric study.

An example plot of the Operating Point Map is shown below:

<img src="/Documentation/images/operating_map_example.png" alt="operating point map example" style="height: 400px; width:800px;"/>

```exitatend ``` can be used to specify whether you want to close Fluent after the script is finished.

### Study Configuration
In the ```studies``` section different study setups can be created. 

```overwriteExisting``` sets whether a existing study with the same name should be overwritten. 

```runExistingProject``` specifies if a existing study setup with the same name should be used. 

```write_data``` gives the option to save the simulation data for all design points. 

The reference case file name for the base case has to be specified under ```refCaseFilename``` and has to be in the Fluent working directory.

```updateAllDPs``` specifies whether the study should be run after the setup.

If ```updateFromBaseDP``` is ```true``` the simulation of each design point is initialized from the base design point. If ```updateFromBaseDP``` is set to ```false``` the previous design point is used for initialization.

The expressions to be varied for the different design points are specified in the  ```inputparameters```. The option ```useScaleFactor``` can be set to ```true``` to use a scale factor from the base case value.

The ```valueList``` holds either the scale factors or the specific values to be used for the different design points of the study.

```
...
"studies": {
    "Study_1": {
      "overwriteExisting": true,
      "runExistingProject": false,
      "write_data": false,
      "refCaseFilename": "Case_1",
      "updateAllDPs": true,
      "updateFromBaseDP": false,
      "definition": [
        {
          "inputparameters": [
            "BC_OUT_p"
          ],
          "useScaleFactor": true,
          "valueList": [
              0.95,
              0.9,
              0.85,
              0.8,
              1.025,
              1.03,
              1.04,
              1.05
          ]
```

