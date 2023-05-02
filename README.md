# **PyTurboWizard**

## **OSS disclaimer**

PyTurboWizard depends on OSS (Open Source Software), which is subject to its own terms and conditions and might contain vulnerabilities.
Ansys is not responsible for such third-party software.

You should consult your company’s software security department before installing any software on company hardware.

PyTurboWizard is licensed under the [MIT License](./LICENSE).

## **Overview**

PyTurboWizard provides a standardized testing setup for turbomachinery cases in Ansys Fluent through Pythonic access with PyFluent. This matrix describes functionalities:

| Case | Fluid | Inlet BC | Outlet BC | Expression template | Stages | Interface types | Parametric study support |
|---------------------------|------------|----------------------------------|------------------------------------------------|---------------------|---------------------|------------------------------------------------------|--------------------------|
| Gas turbine (compressible)| Ideal air | Total pressure, mass flow, volume flow | Static pressure, exit corrected mass
Flow, mass flow, volume Flow | Yes | Unlimited | General, periodic, no pitch-scale, pitch-scale, mixing plane | Yes |
| Compressor (compressible) | Ideal air | Total pressure, mass flow, volume flow | Static pressure, exit corrected mass
Flow, mass flow, volume flow | Yes | Unlimited | General, periodic, no pitch-scale, pitch-scale, mixing plane | Yes |
| Gas turbine (incompressible) | Ideal air | Total pressure, mass flow, volume flow | Static pressure, exit corrected mass
Flow, mass flow, volume flow | Yes | Unlimited | General, periodic, no pitch-scale, pitch-scale, mixing plane | Yes |
Compressor (incompressible) | Ideal air | Total pressure, mass flow, volume flow | Static pressure, exit corrected mass
Flow, mass flow, volume flow | Yes | Unlimited | General, periodic, no pitch-scale, pitch-scale, mixing plane | Yes |

**Note:** The default rotation axis is expected to be the z-axis (0,0,1) with axis origin (0,0,0).

## **Getting started**

PyTurboWizard is developed for Ansys Fluent 2024 R1 and later. When running the Ansys GPU Solver, you can use PyTurboWizard with the `-gpu` flag in the launching options. However, not all features
are supported.

### Installation

You should create a dedicated Python virtual environment to install
PyTurboWizard in. To quickly create and install this environment, consider using the [Ansys Python Manager](https://github.com/ansys/python-installer-qt-gui).

Use `pip` to install PyTurboWizard in this environment:

`pip install ansys-ptw`

All needed libraries are installed automatically.

#### For developers

If you plan on doing local *development* of PyTurboWizard with Git, install the latest release:

```bash
git clone https://github.com/ansys/pyturbowizard
pip install -e .
```

### **How to run**

After installing the latest version of PyTurboWizard, you can prepare data in your working directory and then run it:

1. Copy Fluent data, including mesh data and profiles, into you working directory.
1. Copy a configuration file to your Fluent working directory.
1. Adjust the configuration file to your setup. For more information, see [Set up the configuration file](doc/ConfigFile.md).
1. Execute the script:

   `ansys-ptw <PathToConfigurationFile.json/yaml>`

## Useful documents

- [Set up the configuration file](doc/ConfigFile.md)
- [Speedline simulation setup example](doc/examples/Speedline_Example/speedline_example.md)
