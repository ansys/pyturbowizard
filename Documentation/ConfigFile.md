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

``` exitatend ``` can be used to specify wether you want to close Fluent after the script is finished.
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
      ....
      },
      "Case_2": {
      ....
      }
```
