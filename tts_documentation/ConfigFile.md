# Setup of the Configuration File
This guide aims to give an overview on how to adjust the Configuration File for single case setups and parametric studies.
## Single Case Setup
The Configuration file for single case setups can be found in the [main branch](https://github.com/ansys-internal/turbotestsuite/tree/main) as ``` TurboSetupConfig.json ```.

When running the script from outside Fluent, you can also use the yaml-file format for the configuration file.

It serves as input file for the launch options, boundary conditions, as well as the numeric and simulation setups needed to run the main script. In the following the different sections of the Configuration File are explained in detail.

### Setup Subroutines
Under the section ``` functions ```, different subroutines for the numerical setup, post processing or the parametric studies can be specified:

```
"functions":
    {
      "setup": "setup_compressible_01",
      "numerics": "numerics_bp_tn_2305",
      "initialization": "init_hybrid_01",      
      "postproc": "post_01",
      "parametricstudy": "study_01"
    },
```
Currently the following functions and corresponding options are available:
- "setup":
  - Specify setup function
  - Available functions:
    - **"setup_compressible_01" (default):** standard setup for compressible fluids
    - "setup_incompressible_01": standard setup for incompressible fluids (beta)
- "numerics": 
  - Specify numeric settings
  - Available functions:
    - "numerics_defaults": Use Fluent default settings    
    - **"numerics_bp_tn_2305" (default):**  Use turbo best practice settings from May 2023 in combination with Fluent default discretization-schemes
    - "numerics_bp_tn_2305_lsq" : Use turbo best practice settings from May 2023, but usage of LSQ gradient discretization-scheme
    - "numerics_bp_all_2305": Use turbo best practice settings from May 2023, additionally set explicitly all discretization-schemes to second order    
     
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

For running Fluent on Linux or a Cluster, there are two options:
   - Submit job to a slurm-queue: ```queue_slurm``` and a maximal waiting time in sec ```queue_waiting_time``` (default: 600sec). Other options identical to usual launching options
   - Hook on to an existing Fluent session ([How to Run on Linux](/README.md#linux--cluster-1)): For this a server file name has to be specified under ``` serverfilename ```. When hooking onto a existing Fluent session the ``` launching ``` options are not used, except for ```workingDir```.
```
"launching":
    {
      "workingDir": "<PathToFluentWorkingDir>",
      "fl_version": "23.2.0",
      "noCore": 8,
      "serverfilename": "server-info.txt",
      "precision": "double",
      "show_gui":  true
    },
```

**Note:** If ```workingDir``` is not set, the script will use the directory of the configuration file as fluent working directory.

### Cases
Under the ``` cases ``` section different case setups can be specified for the script to run (different meshes etc.).

```
 "cases": {
      "Case_1": {
        "caseFilename": "Case_1",
        "meshFilename": "Case_1_mesh",
        "profileName_In": "InProfile.csv",
        "profileName_Out": "",        
        "expressionTemplate": "expressionTemplate_compressor_comp.tsv",
        "gravity_vector": [0.0, 0.0, -9.81],
        "rotation_axis_direction": [0.0, 0.0, 1.0],
        "rotation_axis_origin": [0.0, 0.0, 0.0],
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
      - Static Pressure: "p-out"

**Note**: If you want to use the csv-table-format as profile input, Fluent expects the specific file with the file extension "csv"!
  
Example snippet for a inlet profile data table (csv-format):
```
[Name]
inlet-bc

[Data]
radius, pt-in, tt-in, vax-dir, vrad-dir, vtang-dir
6.6247E-02, 5.4357E+04, 2.8787E+02, 9.9025E-01, 7.4542E-02, 4.1016E-02
...
```
  
Next, you can choose your ``` expressionTemplate ```. Currently there are expression templates available for a compressor and a turbine setup.
Optional objects are:
  - ```gravity_vector```:  Vector defining gravity, e.g. [0.0, 0.0, -9.81], default: not set, gravity off
  - Definition of Rotation Axis
    - ```rotation_axis_direction```: Vector defining axis direction, default: [0.0, 0.0, 1.0]
    - ```rotation_axis_origin```: Vector defining axis origin, default: [0.0, 0.0, 0.0] 

```
 "Case_1": {
       ...
       "expressions": {
          "GEO_IN_No_Passages": "1",
          "GEO_IN_No_Passages_360": "1",
          "GEO_OUT_No_Passages": "1",
          "GEO_OUT_No_Passages_360": "1",
          "BC_pref":	"0 [Pa]",
          "BC_omega":	"17000 [rev / min]",
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

The automatic time step factor and iteration count can be set via ```time_step_factor``` (length-scale-method = conservative) or ```pseudo_timestep``` and ``` iter_count ``` respectively. 

``` runSolver``` can be used to specify whether the simulation should start to run at the end of the setup.

### Working with multiple cases

You can easily add various cases to your configuration file. The cases will be executed by the script step by step.

If you want to copy elements from a case to a new case you can use the  ```refcase``` keyword. 

Here´s an example for a mesh study:
```
"Case_CoarseMesh": {
        "caseFilename": "myCaseFileName_coarse",
        "meshFilename": "myCaseFileName_coarse.def",
        "functions": {...},
        "expressions": {...},
        "locations": {...},       
        "solution": {...},     
        "results": {...}                
        },  
        
"Case_FineMesh": {
         "refCase": "Case_CoarseMesh",
         "caseFilename": "myCaseFileName_fine",
         "meshFilename": "myCaseFileName_fine.def",          
        }   
```

In the example "Case_CoarseMesh" includes all setup definitions, case "Case_FineMesh" just refers with ```refCase``` to "Case_CoarseMesh". 
This means all objects are copied from case "Case_CoarseMesh" except the elements prescribed in the case itself, in this case the objects ```caseFilename``` and ```meshFilename```.

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

