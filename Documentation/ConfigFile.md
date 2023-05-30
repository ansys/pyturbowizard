# Setup of the Configuration File
This guide aims to give an overview on how to adjust the Configuration File for single case setups and parametric studies.
## Single Case Setup
The Configuration file for single case setups can be found in the [main branch](https://github.com/ansys-internal/turbotestsuite/tree/main) as ``` TurboSetupConfig.json ```.

It serves as input file for the launch options, boundary conditions, as well as the numeric and simulation setups needed to run the main script. In the following the different sections of the Configuration File are explained in detail.

### Setup Subroutines
Under the section ``` functions ``` different subroutines for the numerical setup, post processing or the parametric studies can be specified:
```
"functions":
    {
      "numerics": "numerics_01",
      "postproc": "post_01",
      "parametricstudy": "study_01"
    },
```
Currently only the default routines are available for the setup.

### Launch Options
Under the section ``` launching ``` different options for launching options for Fluent can be specified, like the version, number of processes and single or double precision solver.
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
