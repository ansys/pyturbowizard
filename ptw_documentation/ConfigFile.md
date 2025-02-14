# Setup of the Configuration File

This guide aims to give an overview on how to adjust the Configuration File for single case study and parametric
studies.
The Configuration File can contain the following sections/dicts:

- ```launching```: Defines the launching options of the Fluent session ([Launching Options](#launching-options))
- ```functions```: Defines the subroutines for the numerical setup, post-processing, the parametric studies,
  etc. ([Functions](#functions))
- ```cases```: Contains the definition of a single case study ([Single Case Study](#single-case-study))
- ```studies```: Contains the definition of parametric studies ([Parametric Study](#parametric-study))

## Launching Options

Under the section ``` launching ```, different options for launching options for Fluent can be specified, like the
version, number of processes and single or double precision solver.

- ```"workingDir"``` specifies the Fluent working directory, if ```workingDir``` is not set, the script will use the
  directory of the configuration file as fluent working directory
- ```"fl_version"``` specifies version of Fluent (supported versions: ```"23.2.0","24.1.0"```)
- ```"noCore"``` specifies the number of cores/processes for the Fluent session
- ```"precision"``` specifies solver-precision (**default: true**):
    - ```true```: double-precision
    - ```false```: single-precision
- ```"show_gui"```  specifies whether a GUI should be shown or not during simulation (**default: true**)
- ```"py"```  enables python-console (**default: false**)
- ```"gpu"```  enables gpu-solver -> check current model limitations (**default: false**)
- ```"exitatend"``` is used to specify whether the Fluent session should be closed after the script is finished (*
  *default: true**)
- ```"ptw_cleanup"``` (**default: false**):
    - If enabled (```"ptw_cleanup": true```) following files are removed from the ```"workingDir"``` after exiting the
      fluent session:
        - 'fluent\*.trn'
        - '\*slurm\*'
    - If you define ```"ptw_cleanup"``` as a list of strings, the defined files will be removed,
      e.g. ```"ptw_cleanup": ["myFile.txt","*.log"]```

For running Fluent on Linux or a Cluster, there are two options:

- Submit job to a slurm-queue: ```queue_slurm``` (e.g. ```"ottc01"```) and a maximal waiting time in
  sec ```queue_waiting_time``` (default: 600sec). Further, if additional launch arguments are needed
  (e.g. for launching session in GPU queue) these can be specified with ```additional_args```
  (e.g. ```"-scheduler_ppn=4 -scheduler_gpn=4"```).
  Other options identical to usual launching options
- Hook on to an existing Fluent session ([How to Run on Linux](/README.md#linux--cluster-1)): For this a server file
  name has to be specified under ``` serverfilename ```. When hooking onto a existing Fluent session
  the ``` launching ``` options are not used, except for ```workingDir```.

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

Examples for the ``` launching ``` configurations can be
found [here](/ptw_examples/ConfigFileTemplates/launcherConfig_examples.json).

## Functions

Under the section ``` functions ```, different subroutines for the numerical setup, post processing or the parametric
studies can be specified:

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

The following functions and corresponding options are available:

- ```setup```:
    - Specify setup function
    - Available functions:
        - **"setup_compressible_01" (default):** standard setup for compressible fluids
        - "setup_incompressible_01": standard setup for incompressible fluids
        - "setup_compressible_woBCs": reduced setup function for compressible fluids, just material & physics are set,
          no boundary conditions
        - "setup_incompressible_woBCs": reduced setup function for incompressible fluids, just material & physics are
          set, no boundary conditions
- ```numerics```:
    - Specify numeric settings
    - Available functions:
        - "numerics_defaults": Use Fluent default settings
        - **"numerics_bp_tn_2305" (default):**  Use turbo best practice settings from May 2023 in combination with
          Fluent default discretization-schemes and Green-Gauss Node-based gradient discretization-scheme
        - "numerics_bp_tn_2305_lsq" : Use turbo best practice settings from May 2023, but usage of LSQ gradient
          discretization-scheme
        - "numerics_bp_all_2305": Use turbo best practice settings from May 2023, additionally set explicitly all
          discretization-schemes to second order
        - "numerics_defaults_pseudo_timestep": default numerics with pseudo-transient vp-coupling

- ```initialization```:
    - Specify initialization settings
    - Available functions:
        - "init_standard_01": standard initialization, using inlet data as reference
        - "init_standard_02": standard initialization, using 0 velocity, 0.01 TKE , 0.01 Omega, inlet temperature,
          initial gauge pressure
        - "init_hybrid_01": Hybrid initialization using initial gauge pressure
        - **"init_fmg_01"(default):** FMG initialization, using standard "init_standard_01" for pre-initialization
        - "init_fmg_02": FMG initialization, using standard "init_standard_02" for pre-initialization
        - "init_fmg_03": FMG initialization, using standard "init_hybrid_01" for pre-initialization

- ```postproc```:
    - Specify postproc function
    - Available functions:
        - **"post_01" (default):** standard postprocessing
        -
- ```parametricstudy```:
    - Specify parametricstudy function
    - Available functions:
        - **"study_01" (default):** standard parametricstudy

- ```parametricstudy_post```:
    - Specifies the function which is used to evaluate the parametric study results.
    - Available functions:
        - **"study_post_01" (default):**
            - Operating Point Maps for each Monitor Point (Value over mass/volume flow)
            - For each design point:
                - Properties are plotted against iteration number (each Design Point is treated as beginning from
                  iteration 0)
                - CoV-Plot: Calculated for monitored properties of each Design Point (beginning from iteration 50)
                - Residual-Plot: Residual values for each Design Point
                - Monitor Points: Monitor Point values for each Design Point
                - Examples of the plots are shown below:

                  <img src="/ptw_documentation/images/operating_map_example.png" alt="operating point map example" style="height: 400px; width:500px;"/>

                  <img src="/ptw_documentation/images/cov_plot_DP10.png" alt="cov plot" style="height: 450px; width:700px;"/>

**Notes:**

- If the section 'functions' is not defined the default functions are used. Therefore, the definition of this section is
  not required, unless the user wants to prescribe non-default functions
- You can also specify a function section in the definition of each [case](#cases)

## Single Case Study

The Configuration file for single case study can be found in the [ptw_examples section](/ptw_examples),
e.g. [Darmstadt-Compressor Setup](/ptw_examples/TestCases/1_Darmstadt/turboSetupConfig.json).

When running the script from outside Fluent, you can also use the yaml-file format for the configuration file.

It serves as input file for the boundary conditions, as well as the numeric and simulation setups needed to run the main
script. In the following the different sections of the Configuration File are explained in detail.

To run a Single Case Study the Configuration-File needs to contain a ``` launching ``` object to start a Fluent session,
see [Launching Options](#launching-options)

### Cases

Under the ``` cases ``` section different case setups can be specified for the script to run (different meshes,
numerical settings etc.).

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
        "isentropic_efficiency_ratio": "TotaltoTotal"
        ...
      },
      "Case_2": {
      ....
      }
```

First, different general case parameters, like the final ``` caseFilename ``` and the initial ``` meshFilename ``` have
to be specified.
Supported file types for meshes are .def, .cgns, .msh and .cas. Make sure that the mesh consists is located in the
Fluent working directory.
msh- and cas-files can be prescribed as list (e.g. ```"meshFilename": ["mesh1.msh","mesh2.msh"]```), in this case the
files are imported in the prescribed order.

Optional objects are:

- ```functions```:
    - Define special functions for the specific case
    - If not defined, the default or global functions are used (if defined in the root path of your configuration file)
    - More details: [Functions](#functions)
- ```gravity_vector```:  Vector defining gravity, e.g. ```[0.0, 0.0, -9.81]```, default: not set, gravity off
- Definition of Rotation Axis
    - ```rotation_axis_direction```: Vector defining axis direction, default: ```[0.0, 0.0, 1.0]```
    - ```rotation_axis_origin```: Vector defining axis origin, default: ```[0.0, 0.0, 0.0]```
- ```isentropic_efficiency_ratio```: Calculation of Isentropic Efficiency (supported arguments: "TotalToTotal", "
  TotalToStatic", "StaticToStatic")
- ```skip_execution```: Skips the execution of the case, default: ```false```
- ```run_extsch```: Run extsch-script: extracts all rp-variables of the case-file as ascii-file (linux-platforms
  only!) , default: ```false```
- You can hook additional journal files to the setup/solution procedure, using following keywords the case-dictionary:
    - ```post_meshimport_journal_filenames```: Run a journal files after mesh has been imported (for example defining
      not-supported BCs), expects a list,
      e.g. ```['myJournal1.jou', 'myJournal2.jou']```
    - ```pre_init_journal_filenames```: Run a journal files before initializing solution, expects a list,
      e.g. ```['myJournal1.jou', 'myJournal2.jou']```
    - ```pre_solve_journal_filenames```: Run a journal files before solver starts, expects a list,
      e.g. ```['myJournal1.jou', 'myJournal2.jou']```
    - ```pre_exit_journal_filenames```: Run a journal files before exiting fluent (for example for custom
      postprocessing), expects a list,
      e.g. ```['myJournal1.jou', 'myJournal2.jou']```

#### Profiles

You can choose to specify a profile for your inlet or outlet boundaries by providing the ``` profileName ``` in your
Fluent working directory.
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

**Note**: If you want to use the csv-table-format as profile input, Fluent expects the specific file with the file
extension "csv"!

Example snippet for a inlet profile data table (csv-format):

```
[Name]
inlet-bc

[Data]
radius, pt-in, tt-in, vax-dir, vrad-dir, vtang-dir
6.6247E-02, 5.4357E+04, 2.8787E+02, 9.9025E-01, 7.4542E-02, 4.1016E-02
...
```

#### Expression Templates

Next, you can choose your ``` expressionTemplate ```. Currently, there are expression templates available for a
compressors, fans, pumps, turbine & cascade setups, as well as for compressible and incompressible setups:

- "expressionTemplate_cascade_comp.tsv": Accounting for cascades or non-turbo-machinery applications, compressible
  fluids
- "expressionTemplate_compressor_comp.tsv": Accounting for compressors, compressible fluids
- "expressionTemplate_compressor_incomp.tsv": Accounting for compressors, incompressible fluids
- "expressionTemplate_fan_comp.tsv": Accounting for fans, compressible fluids
- "expressionTemplate_fan_incomp.tsv": Accounting for fans, incompressible fluids
- "expressionTemplate_pump_incomp.tsv": Accounting for pumps, incompressible fluids
- "expressionTemplate_turbine_comp.tsv": Accounting for turbines, compressible fluids
- "expressionTemplate_turbine_incomp.tsv": Accounting for turbines, incompressible fluids

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

### Boundary Conditions

Now you can specify values your boundary condition and geometric expressions, that are available in your expression
template. Make sure to leave the corresponding values blank, if you use profile data.
Available Boundary Conditions Include:

- Geometric
    - ```GEO_IN_No_Passages``` Number of inlet passages in the computational domain
    - ```GEO_IN_No_Passages_360``` Total number of inlet passages
    - ```GEO_OUT_No_Passages``` Number of outlet passages in the computational domain
    - ```GEO_OUT_No_Passages_360``` Total number of outlet passages
- General
    - ```BC_pref``` Reference Pressure
    - ```BC_omega``` Rotational Velocity
- Inlet
    - ```BC_IN_p_gauge``` Initial gauge pressure
    - ```BC_IN_TuIn``` Turbulent intensity (from 0 - 1)
    - ```BC_IN_TuVR``` Turbulent viscosity ratio
    - ```BC_IN_Tt``` Total temperature
    - ```BC_IN_MassFlow``` Mass flow inlet boundary condition
    - ```BC_IN_pt``` Total pressure inlet boundary condition
    - ```BC_IN_VolumeFlow``` Volume flow inlet boundary condition (mass flow inlet)
        - ```BC_VolumeFlowDensity``` Fluid Density of inlet volume flow
- Outlet
    - ```BC_OUT_p``` Static pressure outlet boundary condition
    - ```BC_OUT_MassFlow``` Mass flow outlet boundary condition
    - ```BC_OUT_ECMassFlow``` Exit corrected mass flow outlet boundary condition
        - ```BC_ECMassFlow_pref``` Exit corrected mass flow reference pressure
        - ```BC_ECMassFlow_tref``` Exit corrected mass flow reference temperature
    - ```BC_OUT_VolumeFlow``` Volume flow outlet boundary condition (mass flow inlet)
        - ```BC_OUT_VolumeFlowDensity``` Fluid Density of outlet volume flow

**Note**: If you want to use profile data for inlet/outlet you still need to define a corresponding expression (you can
specify a dummy value). Example: A profile for outlet pressure is specified: ```"BC_OUT_p": "-1 [Pa]"```

#### Domain mapping

Under the ```locations``` section the different regions of your mesh have to be mapped accordingly. Note that every
location input is a list, so that you can map multiple regions, e.g. ``` ["inlet1","inlet2"] ```. Interfaces can also be
specified for:

- General Connection under ```bz_interfaces_general_names```
- Mixing-Plane Models under ```bz_interfaces_mixingplane_names```
- No Pitch-Scale Interfaces under ```bz_interfaces_no_pitchscale_names```
- Pitch-Scale Interfaces under ```bz_interfaces_pitchscale_names```
- Periodic Interfaces under ```bz_interfaces_periodic_names```

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
                  "bz_interfaces_no_pitchscale_names": {
                    "c-stator-2-to-b-stator-1-nps": {
                      "side1": "c-stator-2-to-b-stator-1-side-1",
                      "side2": "c-stator-2-to-b-stator-1-side-2"
                    },
                  "bz_interfaces_pitchscale_names": {
                    "c-stator-2-to-d-rotor-2-ps": {
                      "side1": "c-stator-2-to-d-rotor-2-side-1",
                      "side2": "c-stator-2-to-d-rotor-2-side-2"
                    }
                  },
                  "bz_interfaces_general_names": {
                    "a-rotor-1-tip": {
                      "side1": "a-rotor-1-to-a-rotor-1-internal-side-1",
                      "side2": "a-rotor-1-to-a-rotor-1-internal-side-2"
                    }
                  },
                  "bz_walls_torque": ["r1-blade","r1-shroud","r1-hub"],
                  "bz_ep1_Euler": ["b-stator-1-to-a-rotor-1-side-1"],
                  "bz_ep2_Euler": ["c-stator-2-to-b-stator-1-side-1"],                     
                  ...
```

**Notes**:

- ```bz_walls```: Define change bc to type walls
- ```bz_walls_torque```: Define all walls which should be accounted to calculate a reference torque
- ```bz_ep1_Euler``` / ```bz_ep2_Euler```: Inlet (1) and outlet (2) evaluation planes to calculate the efficiency based
  on the Euler turbine equation
- periodic interfaces have to be conformal for the turbo-toplogy setup to function properly

In the ```locations``` section a turbo topolgy for post processing in Fluent can be defined. For different mesh
regions (e.g. rotors and stators), separate topologies have to be created.

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

**Note**:  If a periodic interface specified under ```"tz_theta_periodic_names"``` is non-conformal, it will be
automatically handled by the script.

This completes the setup of the ``` locations ``` section.

### Solution & Results Setup

#### Solution Settings

```
       "solution": {
          "reportlist": ["MP_IN_MassFlow_360","MP_OUT_MassFlow_360","MP_Isentropic_Efficiency","MP_PRt"],
          "res_crit": 1.0e-4,
          "cov_list": [
            "MP_Isentropic_Efficiency",
            "MP_IN_MassFlow_360",
            "MP_PRt"
          ],
          "cov_crit": 1.0e-4,
          "iter_count": 10,
          "time_step_factor": 5,
          "runSolver": true
        }
```

In the section ```solution``` the convergence criteria and solve settings can be specified.

In ```reportlist``` the expressions for monitoring (plotting and file save) can be set. All expressions in
the ```reportlist``` will be defined as output-parameters.

``` res_crit``` is used to specify the normalized local residual convergence limit.

```cov_list``` and  ``` cov_crit ``` are used to specify the parameters and convergence criteria used for a Coefficient
of Variation.

```conv_check_freq``` is an optional argument and can be used to define the convergence check frequency (**default: 5**)

```tsn``` is an optional argument, that explicitly turns on turbo machinery specific numerics as beta feature.

The automatic time step factor and iteration count can be set via ```time_step_factor``` (length-scale-method =
conservative) or ```pseudo_timestep``` and ``` iter_count ``` respectively.

``` runSolver``` can be used to specify whether the simulation should start to run at the end of the setup.

```reorder_domain``` is an optional argument, that turns on/off domain reordering before initialization (**default: true
**)

##### Basic Report Definitions

It is optional to define basic report definitions with the keyword ``` basic_reports ``` in the ``` solution ```
section.
Basic refers to these report definitions being created as surface, volume, force, drag, lift,
moment or flux (only mass flux supported) reports.
When using the GPU solver, this is currently the only option to monitor desired quantities for every iteration as
report definitions from expressions are not supported yet.

The keyword ``` per_zone ``` is optional (default: false). With this option you can select if the corresponding
definition is separated for all selected surfaces.

The keyword ``` per_zone ``` is optional (default: false). With this option you can select if the corresponding 
definition is separated for all selected surfaces.

```
 "Case_1": {
       "solution": {
           "basic_reports": {
              "IN_massflowave_pt": {
                "scope": "surface",
                "type": "surface-massavg",
                "zones": ["inblock-inflow"],
                "variable": "total-pressure"                
              },
              "OUT_massflowave_pt": {
                "scope": "surface",
                "type": "surface-massavg",
                "zones": ["outblock-outflow"],
                "variable": "total-pressure"
              },
              "Vol_Ave_pt": {
                "scope": "volume",
                "type": "volume-massavg",
                "zones": ["passage"],
                "variable": "total-pressure"
              },
              "Force_blades_Z": {
                "scope": "force",
                "zones": ["blade","bld-geo-high","bld-geo-low","bld-high"],
                "force_vector": [0,0,1]
                "per_zone": false
              },
              "Drag_blades_Z": {
                "scope": "drag",
                "zones": ["blade","bld-geo-high","bld-geo-low","bld-high"],
                "force_vector": [0,0,1],
                "report_output_type": "Drag Force"
                "per_zone": true
              },
              "Lift_blades_Z": {
                "scope": "lift",
                "zones": ["blade","bld-geo-high","bld-geo-low","bld-high"],
                "force_vector": [0,0,1],
                "report_output_type": "Lift Force"
              },
              "Moment_blades_Z": {
                "scope": "moment",
                "zones": ["blade","bld-geo-high","bld-geo-low","bld-high"],
                "mom_center": [0,0,0],
                "mom_axis": [0,0,1],
                "report_output_type": "Moment"
              },
              "Flux_Mass_In": {
                "scope": "flux",
                "type": "flux-massflow",
                "zones": ["inblock-inflow"]
              }
            },
      ...
```

#### Results

```
        "results": {
          "filename_inputParameter": "inputParameters.out",
          "filename_outputParameter": "outParameters.out",
          "filename_summary": "report.sum",
          "span_plot_var": ["total-pressure","total-temperature","velocity-magnitude"],
          "span_plot_height": [0.2, 0.5, 0.9],
          "pathlines_releaseSurfaces": ["inblock-inflow"],
          "pathlines_var": ["absolute-pressure"],
          "oilflow_pathlines_surfaces": ["blade-ps", "blade-ss", "blade-te"],
          "oilflow_pathlines_var": ["absolute-pressure"]
        }
```

In the ```results``` section, the simulation output data can be set, as well as the creation of span-wise contour plots.

```filename_inputParameter``` and ```filename_outputParameter``` are used to specify the names of the files containing
the input and output parameters.

```span_plot_var``` is used to define the variable names, for which the contour plots are created. You can use the
command:
```solver.field_data.get_scalar_field_data.field_name.allowed_values()``` in the Fluent python console to check for the
correct variable names.

```span_plot_height``` is used to specify the relative channel height, at which the different variable contour plots are
created. Note that all variable plots are created for each respective channel height.

To create pathlines, ```pathlines_releaseSurfaces``` is used to define the surfaces, from which pathlines are released.
```pathlines_var``` is used to define the variable names, for which the pathlines are created.

To create oil flow pathlines, ```oilflow_pathlines_surfaces``` is used to define surfaces, on which the pathlines are
generated.
With ```oilflow_pathlines_var```, variables are defined for which the oil flow pathlines are generated. Besides the
pathline object,
a scene containing the pathline object and a mesh object with surfaces defined in ```oilflow_pathlines_surfaces``` is
created.

### Additional Setup Specifications

In the ```setup``` section you can modify basic settings of your setup, all subelements are optional.
If there are no subelements defined, Fluent defaults will be used.

Available options:

- Special settings for pressure-outlet-BCs:
    - ```BC_settings_pout_blendf```: Prescribe the 'Pressure blending factor',e.g. ```0.05```
    - ```BC_settings_pout_bins```: Prescribe the 'Number of bins',e.g. ```65 ```
    - **Note For older Fluent versions (R23.1 & R23.2):** Use ```BC_settings_pout``` as keyword to prescribe 'Pressure
      blending factor' & 'Number of bins' as list,
      e.g. ```[0.05, 65]```
- ```BC_IN_reverse```: Prevent Reverse Flow for Pressure-Inlet BCs (**default: false**)
- ```BC_OUT_reverse```: Prevent Reverse Flow for Pressure-Outlet BCs (**default: true**)
- ```BC_OUT_avg_p```: Use average pressure specification for Pressure-Outlet BCs (**default: true**)
- ```turbulence_model```: Use a specific turbulence model
    - currently only k-omega variants are supported: ```wj-bsl-earsm```, ```standard```, ```sst```, ```geko```,```bsl```
    - additionally the following transition models (SST-based) are supported:
        - ```transition-sst```: Transition SST model (&gamma;-Re<sub>&theta;</sub>-model): two additional
          transport-equations
        - ```transition-gamma```: Intermittency Transition Model (&gamma;-model): one additional transport-equation
        - ```transition-algebraic```:  Algebraic Transition Model: zero additional transport-equation

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

In the example "Case_CoarseMesh" includes all setup definitions, case "Case_FineMesh" just refers with ```refCase```
to "Case_CoarseMesh".
This means all objects are copied from case "Case_CoarseMesh" except the elements prescribed in the case itself, in this
case the objects ```caseFilename``` and ```meshFilename```.
**Note:** If you specify a new element with sub-elements (i.e. a new dict), all sub-elements need to be specified in the
new element!

## Parametric Study

The Configuration file for a parametric study can be found in the [ptw_examples section](/ptw_examples),
e.g. [Darmstadt-Compressor Study](/ptw_examples/TestCases/1_Darmstadt/turboStudyConfig.json).

To run a Parametric Study the Configuration-File needs to contain a ``` launching ``` object to start a Fluent session,
see [Launching Options](#launching-options)

### Study Configuration

In the ```studies``` section different study setups can be created.

- ```skip_execution``` sets whether a study should be executed or not, default: ```False```

- ```overwriteExisting``` sets whether an existing study with the same name should be overwritten.

- ```runExistingProject``` specifies if an existing study setup with the same name should be used.

- ```write_data``` gives the option to save the simulation data for all design points (**default: false**). **Note: If
  the initialization method is set to ```initMethod: "prevDP"```, data will be written anyway!**

- ```simulation_report``` turns on/off if the simulation report data should be captured for the design-points (*
  *default: false**)

- The reference case file name for the base case has to be specified under ```refCaseFilename``` and has to be in the
  Fluent working directory.

- ```initMethod``` specifies initialization method for design-points, following options are available:
    - ```base_ini```: Use initialization method of base case
        - **Note:** Does not work with FMG initialization!
    - ```baseDP```: Use solution of base design point **(default)**
    - ```prevDP```: Use solution of previous design point

- ```updateAllDPs``` specifies whether the study should be run after the setup.

- The expressions to be varied for the different design points are specified in the  ```inputparameters```. The
  option ```useScaleFactor``` can be set to ```true``` for each selected Inputparameter to use a scale factor from the
  base case value.

- The ```valueList``` holds either the scale factors or the specific values to be used for the different design points
  of the study.

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

