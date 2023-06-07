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
      "setup": "setup_01",
      "numerics": "numerics_bp_all_2305",
      "initialization": "init_hybrid_01",      
      "postproc": "post_01",
      "parametricstudy": "study_01"
    },
```
Currently the following functions and corresponding options are available:
- "setup":
  - Specify setup function
  - Available functions:
    - **"setup_01" (default):** standard setup  
- "numerics": 
  - Specify numeric settings
  - Available functions:
    - "numerics_defaults": Use Fluent default settings    
    - "numerics_bp_tn_2305": Use turbo best practice settings from May 2023 in combination with Fluent default discretization-schemes
    - **"numerics_bp_all_2305" (default):** Use turbo best practice settings from May 2023, additionally set explicitly all discretization-schemes to second order    
- "initialization":
  - Specify initialization settings
  - Available functions:
    - "init_standard_01": standard initialization, using inlet data as reference    
    - **"init_hybrid_01" (default):** Hybrid initialization, using standard "init_standard_01" for pre-initialization
    - "init_fmg_01": FMG initialization, using standard "init_standard_01" for pre-initialization
- "postproc":
  - Specify postproc function
  - Available functions:
    - **"post_01" (default):** standard postprocessing
- "parametricstudy":
  - Specify parametricstudy function
  - Available functions:
    - **"study_01" (default):** standard parametricstudy

**Note: If the section 'functions' is not defined the default functions are used. Therefore, the definition of this section is not required, unless the user wants to prescribe non-default functions**


### Launch Options
Under the section ``` launching ```, different options for launching options for Fluent can be specified, like the version, number of processes and single or double precision solver.

For running Fluent on Linux or a Cluster, the script needs to hook on to a existing Fluent session ([How to Run on Linux](/README.md#linux--cluster-1)). For this a server file name has to be specified under ``` serverfilename ```. When hooking onto a existing Fluent session the ``` launching ``` options are not used, except for ```workingDir```.
```
"launching":
    {
      "workingDir": "<PathToFluentWorkingDir>",
      "fl_version": "23.2.0",
      "noCore": 8,
      "serverfilename": "",
      "precision": "double",
      "show_gui":  true
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

Supported file types for meshes are .def, .cgns, .msh and .cas. Make sure that the mesh consists of a single file and is located in the Fluent working directory.

You can choose to specify a profile for your inlet or outlet boundaries by providing the ``` profileName ``` in your Fluent working directory.
Restrictions when using profiles:
- Inlet: 
  - Profiles for Total Pressure, Total Temperature & Absolute Velocity Directions can be specified
  - Naming Convention:
    - Profilename: "inlet-bc"
    - Total Pressure: "pt-in"
    - Total Temperature: "tt-in"
    - Velocity directions in cylindrical coordinates: "vrad-dir","vrad-dir","vax-dir"
- Outlet:
    - Profile for Static Pressure
    - Naming Convention
      - Profilename: "outlet-bc"
      - Total Pressure: "p-out"
    
Next, you can choose your ``` expressionTemplate ```. Currently there are expression templates available for a compressor and a turbine setup.

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
Now you can specify values your boundary condition and geometric expressions, that are available in your expression template. Make sure to leave the corresponding values blank, if you use profile data.

Under the ```locations``` section the different regions of your mesh have to be mapped accordingly. Note that every location input is a list, so that you can map multiple regions, e.g. ``` ["inlet1","inlet2"] ```. Interfaces can also be specified for periodic and general interfaces or mixing plane models.

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

In the ```locations``` section a turbo topolgy for post processing in Fluent can be defined. For different mesh regions (e.g. rotors and stators), seperate topologies have to be created.

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
In the section ```solution``` the convergence criteria and solve settings can be specified. 

In ```reportlist``` the expressions for monitoring (plotting and file save) can be set.

``` res_crit``` is used to specify the normalized local residual convergence limit. 

```cov_list``` and  ``` cov_crit ``` are used to specify the parameters and convergence criteria used for a Coefficient of Variation. 

```tsn``` turns on turbo machinery specific numerics as beta feature. 

The automatic time step factor and iteration count can be set via ```time_step_factor``` and ``` iter_count ``` respectively. 

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
      "serverfilename": "",
      "plotResults": true
    },
```

**Notes**: 
 - Currently only the External option is supported by the script.
 - Currently only one the first defined study is executed by the script.

For running Fluent on Linux or a Cluster, the script needs to hook on to a existing Fluent session ([How to Run on Linux](/README.md)). For this a server file name has to be specified under ``` serverfilename ```

```plotResults``` specifies, whether a Operating Point Map should be plotted and saved from the results of the parametric study.

An example plot of the Operating Point Map is shown below:

<img src="/tts_documentation/images/operating_map_example.png" alt="operating point map example" style="height: 400px; width:800px;"/>

```exitatend ``` can be used to specify whether you want to close Fluent after the script is finished.

### Study Configuration
In the ```studies``` section different study setups can be created. 

```overwriteExisting``` sets whether a existing study with the same name should be overwritten. 

```runExistingProject``` specifies if a existing study setup with the same name should be used. 

```write_data``` gives the option to save the simulation data for all design points. 

The reference case file name for the base case has to be specified under ```refCaseFilename``` and has to be in the Fluent working directory.

```updateAllDPs``` specifies whether the study should be run after the setup.

If ```updateFromBaseDP``` is ```true``` the simulation of each design point is initialized from the base design point. If ```updateFromBaseDP``` is set to ```false``` the previous design point is used for initialization.

The expressions to be varied for the different design points are specified in the  ```inputparameters```. The option ```useScaleFactor``` can be set to ```true``` for each selected Inputparameter to use a scale factor from the base case value.

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
          "useScaleFactor": [true],
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

