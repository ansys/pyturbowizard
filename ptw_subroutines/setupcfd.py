# Logger
from ptw_subroutines.utils import ptw_logger, dict_utils, misc_utils, fluent_utils
import os
from packaging.version import Version
import csv

logger = ptw_logger.getLogger()


def setup(data, solver, functionEl, gpu):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="setup",
        defaultName="setup_compressible_01",
    )
    logger.info(f"Running Setup Function '{functionName}' ...")
    if functionName == "setup_compressible_01":
        setup_compressible_01(data, solver, gpu, True)
    elif functionName == "setup_compressible_woBCs":
        setup_compressible_01(data, solver, gpu, False)
    elif functionName == "setup_incompressible_01":
        setup_incompressible_01(data, solver, gpu, True)
    elif functionName == "setup_incompressible_woBCs":
        setup_incompressible_01(data, solver, gpu, False)
    else:
        logger.info(f"Prescribed Function '{functionName}' not known. Skipping Setup!")

    logger.info("Running Setup Function... finished!")


def setup_compressible_01(data, solver, gpu, bcs):
    setup_01(data=data, solver=solver, solve_energy=True, bcs=bcs, gpu=gpu)
    return


def setup_incompressible_01(data, solver, gpu, bcs):
    setup_01(data=data, solver=solver, solve_energy=False, bcs=bcs, gpu=gpu)
    return


def setup_01(
    data,
    solver,
    solve_energy: bool = True,
    gpu: bool = False,
    bcs: bool = True,
    material: bool = True,
    physics: bool = True,
):
    # Set physics
    if physics:
        set_physics(data=data, solver=solver, solve_energy=solve_energy, gpu=gpu)
    # Materials
    if material:
        set_material(data=data, solver=solver, solve_energy=solve_energy)
    # Set Boundaries
    if bcs:
        set_boundaries(data=data, solver=solver, solve_energy=solve_energy, gpu=gpu)

    # Do some Mesh Checks
    solver.settings.mesh.size_info()
    solver.settings.mesh.check()
    solver.settings.mesh.quality()

    return


def set_material(data, solver, solve_energy: bool = True):
    fl_prop_el = data["fluid_properties"]
    fl_name = fl_prop_el.get("fl_name")
    if fl_name is None:
        if solve_energy:
            fl_name = "custom-comp-fluid"
        else:
            fl_name = "custom-incomp-fluid"
        fl_prop_el["fl_name"] = fl_name

    logger.info(f"Setting Material '{fl_name}'...")
    fluid_list = list(solver.settings.setup.materials.fluid.keys())

    solver.settings.setup.materials.fluid.rename(fl_name, fluid_list[0])
    material_object = solver.settings.setup.materials.fluid[fl_name]
    if solve_energy:
        add_material_property(
            material_object=material_object,
            fl_prop_name="density",
            fl_prop_data=fl_prop_el["fl_density"],
        )
        add_material_property(
            material_object=material_object,
            fl_prop_name="specific_heat",
            fl_prop_data=fl_prop_el["fl_specific_heat"],
        )
        add_material_property(
            material_object=material_object,
            fl_prop_name="thermal_conductivity",
            fl_prop_data=fl_prop_el["fl_thermal_conductivity"],
        )
        add_material_property(
            material_object=material_object,
            fl_prop_name="molecular_weight",
            fl_prop_data=fl_prop_el["fl_mol_wight"],
        )
        add_material_property(
            material_object=material_object,
            fl_prop_name="viscosity",
            fl_prop_data=fl_prop_el["fl_viscosity"],
        )
    else:
        add_material_property(
            material_object=material_object,
            fl_prop_name="density",
            fl_prop_data=fl_prop_el["fl_density"],
        )
        add_material_property(
            material_object=material_object,
            fl_prop_name="viscosity",
            fl_prop_data=fl_prop_el["fl_viscosity"],
        )

    logger.info(f"Setting Material '{fl_name}'... done!")
    return


def add_material_property(material_object, fl_prop_name: str, fl_prop_data):
    logger.info(f"Setting property '{fl_prop_name}'...")
    material_prop = getattr(material_object, fl_prop_name)
    if material_prop is not None:
        if isinstance(fl_prop_data, dict):
            fl_option = fl_prop_data.get("option")
            fl_settings = fl_prop_data.get("settings")
            if fl_option is not None:
                material_prop.option = fl_option
                try:
                    settings_obj = getattr(material_prop, fl_option)
                except:
                    settings_obj = None
                if settings_obj is not None:
                    if fl_settings is not None:
                        if isinstance(fl_settings, dict):
                            for setting in fl_settings:
                                setting_attr = getattr(settings_obj, setting)
                                try:
                                    setting_attr.set_state(fl_settings.get(setting))
                                except Exception as e:
                                    logger.warning(
                                        f"Specifying material-setting '{setting}' for '{fl_prop_name}' failed!"
                                    )
                        else:
                            try:
                                settings_obj.set_state(fl_settings)
                            except Exception as e:
                                logger.warning(
                                    f"Specifying material-settings for '{fl_prop_name}' failed: 'settings'= {fl_settings}!"
                                )
                    else:
                        logger.info(
                            f"Material-settings for '{fl_prop_name}' not specified: 'settings'= {fl_settings}! "
                            f"Fluent-default values are used!"
                        )
            else:
                logger.warning(
                    f"Material-option for '{fl_prop_name}' not specified: 'option'= {fl_option}!"
                    f"Fluent-default values are used!"
                )
        elif isinstance(fl_prop_data, int) or isinstance(fl_prop_data, float):
            material_prop.option = "constant"
            material_prop.value = fl_prop_data
        elif isinstance(fl_prop_data, str):
            material_prop.option = fl_prop_data
        else:
            logger.error(
                f"Material property for '{fl_prop_name}' not specified properly: {fl_prop_data}!"
            )
    else:
        logger.warning(f"Material property '{fl_prop_name}' not known or available!")


def set_physics(data, solver, solve_energy: bool = True, gpu: bool = False):
    if solve_energy:
        solver.settings.setup.models.energy = {
            "enabled": True,
            "viscous_dissipation": True,
        }

    gravityVector = data.get("gravity_vector")
    if isinstance(gravityVector, list) and (len(gravityVector) == 3):
        logger.info(f"Specification of Gravity-Vector: {gravityVector}")
        solver.settings.setup.general.operating_conditions.gravity.enable = True
        solver.settings.setup.general.operating_conditions.gravity.components = (
            gravityVector
        )

    # Set turbulence model
    # if not set or in supported list, sst
    default_turb_model = "sst"
    turb_model = data["setup"].setdefault("turbulence_model", default_turb_model)
    supported_kw_models = (
        solver.settings.setup.models.viscous.k_omega_model.allowed_values()
    )
    # filtering specifically for transition models not available
    supported_transition_models = [
        "transition-sst",
        "transition-gamma",
        "transition-algebraic",
    ]

    if turb_model in supported_kw_models:
        logger.info(f"Setting kw-turbulence-model: '{turb_model}'")
        solver.settings.setup.models.viscous.model = "k-omega"
        solver.settings.setup.models.viscous.k_omega_model = turb_model

        # Set geko Model Parameters
        if turb_model == "geko":
            c_sep = data["setup"].get("geko_csep")
            if c_sep is not None:
                solver.tui.define.models.viscous.geko_options.csep("yes", f"{c_sep}")

            c_nw = data["setup"].get("geko_cnw")
            if c_nw is not None:
                solver.tui.define.models.viscous.geko_options.cnw("yes", f"{c_nw}")

            c_jet = data["setup"].get("geko_cjet")
            if c_jet is not None:
                solver.tui.define.models.viscous.geko_options.cjet("yes", f"{c_jet}")

    elif turb_model in supported_transition_models:
        if turb_model == "transition-sst":
            solver.settings.setup.models.viscous.model = turb_model
        elif turb_model == "transition-gamma":
            solver.settings.setup.models.viscous.model = "k-omega"
            solver.settings.setup.models.viscous.k_omega_model = "sst"
            solver.settings.setup.models.viscous.transition_module = (
                "gamma-transport-eqn"
            )
        elif turb_model == "transition-algebraic":
            solver.settings.setup.models.viscous.model = "k-omega"
            solver.settings.setup.models.viscous.k_omega_model = "sst"
            solver.settings.setup.models.viscous.transition_module = "gamma-algebraic"
    else:
        logger.warning(
            f"Specified turbulence-model not supported: '{turb_model}'! \
                Default turbulence model will be used: '{default_turb_model}'!"
        )
        data["setup"]["turbulence_model"] = default_turb_model
        solver.settings.setup.models.viscous.model = "k-omega"
        solver.settings.setup.models.viscous.k_omega_model = default_turb_model

    # rp-variable to avoid turb-visc overshoots at mixing planes
    # default: 0 -> recommended by development: 4
    mpm_copy_method = data["setup"].get("mpm_copy_method")
    if isinstance(mpm_copy_method, int):
        logger.info(
            f"Key 'mpm_copy_method' found in config-file! \
                Mixing-Plane copy method will be changed to: '{mpm_copy_method}'!"
        )
        solver.execute_tui(
            rf"""(rpsetvar 'mpm/rg-and-g-copy-method {mpm_copy_method})"""
        )

    return


def set_boundaries(data, solver, solve_energy: bool = True, gpu: bool = False):
    # Set operating-pressure
    solver.settings.setup.general.operating_conditions.operating_pressure = "BC_pref"

    # Enable Turbo Models
    if Version(solver._version) < Version("251"):
        solver.tui.define.turbo_model.enable_turbo_model("yes")
    else:
        solver.settings.setup.turbo_models.enabled = True

    # Get rotation axis info: default is z-axis
    rot_ax_dir = data.setdefault("rotation_axis_direction", [0.0, 0.0, 1.0])
    rot_ax_orig = data.setdefault("rotation_axis_origin", [0.0, 0.0, 0.0])

    # Do important steps at startup in specified order
    # 1. Fluid cell zone conditions
    cz_rot_list = data["locations"].get("cz_rotating_names")
    for cz_name in solver.settings.setup.cell_zone_conditions.fluid():
        # Check if it´s a rotating cell-zone
        if (cz_rot_list is not None) and (cz_name in cz_rot_list):
            logger.info(f"Prescribing rotating cell zone: {cz_name}")
            solver.settings.setup.cell_zone_conditions.fluid[
                cz_name
            ].reference_frame = {
                "reference_frame_axis_origin": rot_ax_orig,
                "reference_frame_axis_direction": rot_ax_dir,
                "frame_motion": True,
                "mrf_omega": "BC_omega",
            }
        # otherwise its stationary
        else:
            logger.info(f"Prescribing stationary cell zone: {cz_name}")
            solver.settings.setup.cell_zone_conditions.fluid[
                cz_name
            ].reference_frame = {
                "reference_frame_axis_origin": rot_ax_orig,
                "reference_frame_axis_direction": rot_ax_dir,
            }

    # 2. Search for periodic interfaces
    peri_if_El = data["locations"].get("bz_interfaces_periodic_names")
    non_conformal_list = []
    if peri_if_El is not None:
        peri_idx = 0
        for key_if in peri_if_El:
            logger.info(f"Setting up periodic BC: {key_if}")
            side1 = peri_if_El[key_if].get("side1")
            side2 = peri_if_El[key_if].get("side2")
            # check if specified sides are not already defined as periodics
            periodicIFs = solver.settings.setup.boundary_conditions.periodic
            if periodicIFs.get(side1) is not None:
                logger.info(
                    f"Prescribed Boundary-Zones '{side1}' is already defined as periodic interface. "
                    f"Creation of periodic interface is skipped!"
                )
            elif periodicIFs.get(side2) is not None:
                logger.info(
                    f"Prescribed Boundary-Zones '{side2}' is already defined as periodic interface. "
                    f"Creation of periodic interface is skipped!"
                )
            else:
                # As the origin & axis have been set for all cell-zones, these are the defaults for
                # all containing boundary zones --> Therefore, we do not need to set them
                try:
                    rotation_angle = peri_if_El[key_if].get("rotation_angle")
                    if isinstance(rotation_angle, int) or isinstance(
                        rotation_angle, float
                    ):
                        solver.tui.mesh.modify_zones.create_periodic_interface(
                            "auto",
                            key_if,
                            side1,
                            side2,
                            "yes",
                            "no",
                            "no",
                            "no",
                            rotation_angle,
                            "yes",
                        )
                        # New API:Currently this method shows up a warning message,
                        # if periodic angle does not divide 360 (deg) evenly.
                        # Should be replaced in future versions
                        # solver.settings.mesh.modify_zones.create_periodic_interface(
                        #     periodic_method="auto",
                        #     interface_name=key_if,
                        #     zone_name=side1,
                        #     shadow_zone_name=side2,
                        #     rotate_periodic=True,
                        #     new_axis=False,
                        #     new_direction=False,
                        #     auto_offset=False,
                        #     rotation_angle=rotation_angle,
                        #     nonconformal_create_periodic=True,
                        # )
                    elif peri_if_El[key_if].get("translational") is not None:
                        # setting a translational interface
                        trans_offset = peri_if_El[key_if].get("translational")
                        if isinstance(trans_offset, list) and len(trans_offset) == 3:
                            solver.tui.mesh.modify_zones.create_periodic_interface(
                                "auto",
                                key_if,
                                side1,
                                side2,
                                "no",
                                "no",
                                trans_offset[0],
                                trans_offset[1],
                                trans_offset[2],
                                "yes",
                            )
                        else:
                            solver.tui.mesh.modify_zones.create_periodic_interface(
                                "auto",
                                key_if,
                                side1,
                                side2,
                                "no",
                                "yes",
                                "yes",
                            )
                    else:
                        solver.tui.mesh.modify_zones.create_periodic_interface(
                            "auto",
                            key_if,
                            side1,
                            side2,
                            "yes",
                            "no",
                            "no",
                            "yes",
                            "yes",
                        )
                        # New API:Currently this method shows up a warning message,
                        # if periodic angle does not divide 360 (deg) evenly.
                        # Should be replaced in future versions
                        # solver.settings.mesh.modify_zones.create_periodic_interface(
                        #     periodic_method="auto",
                        #     interface_name=key_if,
                        #     zone_name=side1,
                        #     shadow_zone_name=side2,
                        #     rotate_periodic=True,
                        #     new_axis=False,
                        #     new_direction=False,
                        #     auto_offset=True,
                        #     nonconformal_create_periodic=True,
                        # )
                except Exception as e:
                    # if auto-detection of periodic angle does not work,
                    # it gets calculated from input value for number of rot passages
                    if (
                        str(e.args)
                        == "('+ (add): invalid argument [1]: wrong type [not a number]\\nError Object: #f',)"
                    ):
                        # old definition via info of expression 'GEO_ROT_No_Passages_360'
                        # last try to create manually the periodic interface
                        rotation_angle = None
                        passage_nr = data["expressions"].get("GEO_ROT_No_Passages_360")
                        if isinstance(passage_nr, int):
                            rotation_angle = 360.0 / passage_nr

                        if rotation_angle is not None:
                            solver.tui.mesh.modify_zones.create_periodic_interface(
                                "auto",
                                key_if,
                                side1,
                                side2,
                                "yes",
                                "no",
                                "no",
                                "no",
                                rotation_angle,
                                "yes",
                            )
                        else:
                            logger.error(
                                f"Specifying a manual rotation angle for '{key_if}' failed, please directly define the "
                                f"rotation angle in the periodic interface definition via the key 'rotation_angle'"
                            )

                # check for non-conformal periodics (fluent creates normal interfaces if non-conformal)
                intf_check_side1 = (
                    solver.settings.setup.boundary_conditions.interface.get(side1)
                )
                intf_check_side2 = (
                    solver.settings.setup.boundary_conditions.interface.get(side2)
                )

                if intf_check_side1 is not None and intf_check_side2 is not None:
                    logger.info(
                        f"'{key_if}' is a non-conformal periodic interface! "
                        f"Adjusting turbo-topology accordingly"
                    )
                    # Add the non-conformal interface to the list for correct turbo topology definition
                    non_conformal_list.append(key_if)

                # increase peri_idx
                peri_idx = peri_idx + 1

    # after important steps loop over all keys -> order not important
    for key in data["locations"]:
        # Inlet
        if key == "bz_inlet_names":
            bz_inlet_names = data["locations"].get(key)
            for inletName in bz_inlet_names:
                inBC = None
                profileName = data.get("profileName_In")
                useProfileData = (profileName is not None) and (profileName != "")
                if data["expressions"].get("BC_IN_MassFlow") is not None:
                    logger.info(f"Prescribing a Massflow-Inlet BC @{inletName}")
                    # settings api command
                    solver.settings.setup.boundary_conditions.set_zone_type(
                        zone_list=[inletName], new_type="mass-flow-inlet"
                    )
                    # tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    inletName, "mass-flow-inlet"
                    # )
                    inBC = solver.settings.setup.boundary_conditions.mass_flow_inlet[
                        inletName
                    ]
                    inBC.momentum.mass_flow_specification = "Mass Flow Rate"
                    inBC.momentum.mass_flow_rate = "BC_IN_MassFlow"
                    inBC.momentum.supersonic_gauge_pressure = "BC_IN_p_gauge"
                    inBC.momentum.direction_specification = "Normal to Boundary"
                    if solve_energy:
                        inBC.thermal.total_temperature = "BC_IN_Tt"

                if (
                    data["expressions"].get("BC_IN_VolumeFlow")
                    and data["expressions"].get("BC_IN_VolumeFlowDensity") is not None
                ):
                    logger.info(f"Prescribing a Volumeflow-Inlet BC @{inletName}")
                    # settings api command
                    solver.settings.setup.boundary_conditions.set_zone_type(
                        zone_list=[inletName], new_type="mass-flow-inlet"
                    )
                    # tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    inletName, "mass-flow-inlet"
                    # )
                    inBC = solver.settings.setup.boundary_conditions.mass_flow_inlet[
                        inletName
                    ]
                    inBC.momentum.mass_flow_specification = "Mass Flow Rate"
                    inBC.momentum.mass_flow_rate = (
                        "BC_IN_VolumeFlow*BC_IN_VolumeFlowDensity"
                    )
                    inBC.momentum.supersonic_gauge_pressure = "BC_IN_p_gauge"
                    inBC.momentum.direction_specification = "Normal to Boundary"
                    if solve_energy:
                        if Version(solver._version) < Version("242"):
                            inBC.thermal.t0 = "BC_IN_Tt"
                        else:
                            inBC.thermal.total_temperature = "BC_IN_Tt"

                elif data["expressions"].get("BC_IN_pt") is not None:
                    # settings api command
                    solver.settings.setup.boundary_conditions.set_zone_type(
                        zone_list=[inletName], new_type="pressure-inlet"
                    )
                    # tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    inletName, "pressure-inlet"
                    # )
                    inBC = solver.settings.setup.boundary_conditions.pressure_inlet[
                        inletName
                    ]
                    if useProfileData:
                        # check profile naming convention:
                        # profile_name: "inlet-bc"
                        # total pressure: pt-in,
                        # total temp: tt-in
                        inBC.momentum.gauge_total_pressure = {
                            "option": "profile",
                            "profile_name": "inlet-bc",
                            "field_name": "pt-in",
                        }
                        inBC.momentum.supersonic_or_initial_gauge_pressure = (
                            "BC_IN_p_gauge"
                        )
                        if solve_energy:
                            if Version(solver._version) < Version("242"):
                                inBC.thermal.t0 = {
                                    "option": "profile",
                                    "profile_name": "inlet-bc",
                                    "field_name": "tt-in",
                                }
                            else:
                                inBC.thermal.total_temperature = {
                                    "option": "profile",
                                    "profile_name": "inlet-bc",
                                    "field_name": "tt-in",
                                }
                    else:
                        inBC.momentum.gauge_total_pressure = "BC_IN_pt"
                        inBC.momentum.supersonic_or_initial_gauge_pressure = (
                            "BC_IN_p_gauge"
                        )
                        inBC.momentum.direction_specification_method = (
                            "Normal to Boundary"
                        )
                        if solve_energy:
                            if Version(solver._version) < Version("242"):
                                inBC.thermal.t0 = "BC_IN_Tt"
                            else:
                                inBC.thermal.total_temperature = "BC_IN_Tt"

                    # Set reverse BC
                    reverse_option = data["setup"].setdefault("BC_IN_reverse", False)
                    inBC.momentum.prevent_reverse_flow = reverse_option

                # Do some general settings
                if inBC is not None:
                    # Turbulent Settings
                    if data["expressions"].get("BC_IN_TuIn") is not None:
                        inBC.turbulence.turbulent_intensity = "BC_IN_TuIn"
                    if data["expressions"].get("BC_IN_TuVR") is not None:
                        if Version(solver._version) < Version("242"):
                            inBC.turbulence.turbulent_viscosity_ratio_real = (
                                "BC_IN_TuVR"
                            )
                        else:
                            inBC.turbulence.turbulent_viscosity_ratio = "BC_IN_TuVR"

                    # If Expressions for a direction are specified
                    if (
                        (data["expressions"].get("BC_IN_radDir") is not None)
                        and (data["expressions"].get("BC_IN_tangDir") is not None)
                        and (data["expressions"].get("BC_IN_axDir") is not None)
                    ):
                        if (
                            inBC.name()
                            in solver.settings.setup.boundary_conditions.mass_flow_inlet.keys()
                        ):
                            inBC.momentum.direction_specification = "Direction Vector"
                        else:
                            inBC.momentum.direction_specification_method = (
                                "Direction Vector"
                            )
                        inBC.momentum.coordinate_system = (
                            "Cylindrical (Radial, Tangential, Axial)"
                        )
                        inBC.momentum.flow_direction = [
                            "BC_IN_radDir",
                            "BC_IN_tangDir",
                            "BC_IN_axDir",
                        ]
                    elif (
                        (data["expressions"].get("BC_IN_xDir") is not None)
                        and (data["expressions"].get("BC_IN_yDir") is not None)
                        and (data["expressions"].get("BC_IN_zDir") is not None)
                    ):
                        if (
                            inBC.name()
                            in solver.settings.setup.boundary_conditions.mass_flow_inlet.keys()
                        ):
                            inBC.momentum.direction_specification = "Direction Vector"
                        else:
                            inBC.momentum.direction_specification_method = (
                                "Direction Vector"
                            )
                        inBC.momentum.coordinate_system = "Cartesian (X, Y, Z)"
                        inBC.momentum.flow_direction = [
                            "BC_IN_xDir",
                            "BC_IN_yDir",
                            "BC_IN_zDir",
                        ]

                    # Use Definitions from Profile-Data if specified
                    # check profile naming convention:
                    # profile_name: "inlet-bc"
                    # directions (cylindrical): vrad-dir,vtang-dir,vax-dir
                    if useProfileData:
                        if (
                            inBC.name()
                            in solver.settings.setup.boundary_conditions.mass_flow_inlet.keys()
                        ):
                            inBC.momentum.direction_specification = "Direction Vector"
                        else:
                            inBC.momentum.direction_specification_method = (
                                "Direction Vector"
                            )
                        inBC.momentum.coordinate_system = (
                            "Cylindrical (Radial, Tangential, Axial)"
                        )
                        inBC.momentum.flow_direction = [
                            {
                                "field_name": "vrad-dir",
                                "profile_name": "inlet-bc",
                                "option": "profile",
                            },
                            {
                                "field_name": "vtang-dir",
                                "profile_name": "inlet-bc",
                                "option": "profile",
                            },
                            {
                                "field_name": "vax-dir",
                                "profile_name": "inlet-bc",
                                "option": "profile",
                            },
                        ]

        # Outlet
        elif key == "bz_outlet_names":
            bz_outlet_names = data["locations"].get(key)
            for outletName in bz_outlet_names:
                if data["expressions"].get("BC_OUT_ECMassFlow") is not None:
                    logger.info(
                        f"Prescribing a Exit-Corrected Massflow-Outlet BC @{outletName}"
                    )
                    # settings api command
                    solver.settings.setup.boundary_conditions.set_zone_type(
                        zone_list=[outletName], new_type="mass-flow-outlet"
                    )
                    # tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    outletName, "mass-flow-outlet"
                    # )

                    outBC = solver.settings.setup.boundary_conditions.mass_flow_outlet[
                        outletName
                    ]
                    outBC.momentum.mass_flow_specification = (
                        "Exit Corrected Mass Flow Rate"
                    )
                    outBC.momentum.exit_corrected_mass_flow_rate = "BC_OUT_ECMassFlow"
                    if data["expressions"].get("BC_ECMassFlow_pref") is not None:
                        outBC.momentum.ecmf_reference_gauge_pressure = (
                            "BC_ECMassFlow_pref"
                        )
                    else:
                        outBC.momentum.ecmf_reference_gauge_pressure = "BC_IN_pt"
                    if data["expressions"].get("BC_ECMassFlow_pref") is not None:
                        outBC.momentum.ecmf_reference_temperature = "BC_ECMassFlow_tref"
                    else:
                        outBC.momentum.ecmf_reference_temperature = "BC_IN_Tt"

                elif data["expressions"].get("BC_OUT_MassFlow") is not None:
                    logger.info(f"Prescribing a Massflow-Outlet BC @{outletName}")
                    # settings api command
                    solver.settings.setup.boundary_conditions.set_zone_type(
                        zone_list=[outletName], new_type="mass-flow-outlet"
                    )
                    # tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    outletName, "mass-flow-outlet"
                    # )
                    outBC = solver.settings.setup.boundary_conditions.mass_flow_outlet[
                        outletName
                    ]
                    outBC.momentum.mass_flow_specification = "Mass Flow Rate"
                    outBC.momentum.mass_flow_rate = "BC_OUT_MassFlow"

                elif (
                    data["expressions"].get("BC_OUT_VolumeFlow")
                    and data["expressions"].get("BC_OUT_VolumeFlowDensity") is not None
                ):
                    logger.info(f"Prescribing a VolumeFlow-Outlet BC @{outletName}")
                    # settings api command
                    solver.settings.setup.boundary_conditions.set_zone_type(
                        zone_list=[outletName], new_type="mass-flow-outlet"
                    )
                    # tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    outletName, "mass-flow-outlet"
                    # )

                    outBC = solver.settings.setup.boundary_conditions.mass_flow_outlet[
                        outletName
                    ]
                    outBC.momentum.mass_flow_specification = "Mass Flow Rate"
                    outBC.momentum.mass_flow_rate = (
                        "BC_OUT_VolumeFlow*BC_OUT_VolumeFlowDensity"
                    )

                elif data["expressions"].get("BC_OUT_p") is not None:
                    logger.info(f"Prescribing a Pressure-Outlet BC @{outletName}")
                    # settings api command
                    solver.settings.setup.boundary_conditions.set_zone_type(
                        zone_list=[outletName], new_type="pressure-outlet"
                    )
                    # tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    outletName, "pressure-outlet"
                    # )
                    outBC = solver.settings.setup.boundary_conditions.pressure_outlet[
                        outletName
                    ]
                    # Check Profile data exists
                    profileName = data.get("profileName_Out")
                    useProfileData = (profileName is not None) and (profileName != "")
                    if useProfileData:
                        # check profile naming convention:
                        # profile_name: "outlet-bc"
                        # outlet pressure: p-out
                        outBC.momentum.gauge_pressure = {
                            "option": "profile",
                            "profile_name": "outlet-bc",
                            "field_name": "p-out",
                        }
                    else:
                        outBC.momentum.gauge_pressure = "BC_OUT_p"

                    # Set AVG Pressure
                    pavg_set = data["setup"].setdefault("BC_OUT_avg_p", True)
                    outBC.momentum.avg_press_spec = pavg_set

                    # Set reverse BC
                    reverse_option = data["setup"].setdefault("BC_OUT_reverse", True)
                    outBC.momentum.prevent_reverse_flow = reverse_option

                    if data["setup"].get("BC_OUT_pressure_pt") is not None:
                        logger.warning(
                            f" Keyword 'BC_OUT_pressure_pt' found, but not supported so far..."
                        )
                        # outBC.momentum.backflow_pressure_specification = data["setup"].get(
                        #    "BC_OUT_pressure_pt"
                        # )

                    # Set additional pressure-outlet-bc settings if available in config file
                    blending_factor = data["setup"].get("BC_settings_pout_blendf")
                    bin_count = data["setup"].get("BC_settings_pout_bins")

                    # using old keyword "BC_settings_pout" -> list
                    pout_settings = data["setup"].get("BC_settings_pout")
                    if isinstance(pout_settings, list) and (len(pout_settings) > 1):
                        blending_factor = pout_settings[0]
                        bin_count = pout_settings[1]
                        data["setup"]["BC_settings_pout_blendf"] = blending_factor
                        data["setup"]["BC_settings_pout_bins"] = bin_count
                        # remove from dataset as we use new keywords
                        data["setup"].pop("BC_settings_pout")

                    if bin_count:
                        solver.tui.define.boundary_conditions.bc_settings.pressure_outlet.bin_count = (
                            bin_count
                        )
                    if blending_factor:
                        solver.tui.define.boundary_conditions.bc_settings.pressure_outlet.blending_factor = (
                            blending_factor
                        )

            # Walls
        # elif key == "bz_walls_shroud_names":
        #    solver.settings.setup.boundary_conditions.wall[data["locations"][key]] = \
        # {"motion_bc": "Moving Wall","relative": False,"rotating": True}
        elif key == "bz_symmetry_names":
            keyEl = data["locations"].get(key)
            for key_symm in keyEl:
                logger.info(f"Prescribing a symmetry boundary condition: {key_symm}")
                solver.settings.setup.boundary_conditions.set_zone_type(
                    zone_list=[key_symm], new_type="symmetry"
                )
        elif key == "bz_walls_counterrotating_names":
            keyEl = data["locations"].get(key)
            for key_cr in keyEl:
                logger.info(f"Prescribing a counter-rotating wall: {key_cr}")
                # Change BC-type
                # settings api command
                solver.settings.setup.boundary_conditions.set_zone_type(
                    zone_list=[key_cr], new_type="wall"
                )
                # tui command
                # solver.tui.define.boundary_conditions.zone_type(key_cr, "wall")
                solver.settings.setup.boundary_conditions.wall[key_cr].momentum = {
                    "motion_bc": "Moving Wall",
                    "relative": False,
                    "rotating": True,
                    "omega": 0.0,
                    "rotation_axis_origin": rot_ax_orig,
                    "rotation_axis_direction": rot_ax_dir,
                }
        elif key == "bz_walls_rotating_names":
            keyEl = data["locations"].get(key)
            for key_r in keyEl:
                logger.info(f"Prescribing a rotating wall: {key_r}")
                # Change BC-type
                # settings api command
                solver.settings.setup.boundary_conditions.set_zone_type(
                    zone_list=[key_r], new_type="wall"
                )
                # tui command
                # solver.tui.define.boundary_conditions.zone_type(key_r, "wall")
                solver.settings.setup.boundary_conditions.wall[key_r].momentum = {
                    "motion_bc": "Moving Wall",
                    "relative": False,
                    "rotating": True,
                    "omega": "BC_omega",
                    "rotation_axis_origin": rot_ax_orig,
                    "rotation_axis_direction": rot_ax_dir,
                }

        elif key == "bz_walls_freeslip_names":
            keyEl = data["locations"].get(key)
            for key_free in keyEl:
                logger.info(f"Prescribing a free slip wall: {key_free}")
                # Change BC-type
                # settings api command
                solver.settings.setup.boundary_conditions.set_zone_type(
                    zone_list=[key_free], new_type="wall"
                )
                # tui command
                # solver.tui.define.boundary_conditions.zone_type(key_free, "wall")
                solver.settings.setup.boundary_conditions.wall[key_free].momentum = {
                    "shear_bc": "Specified Shear"
                }

        elif key == "bz_walls":
            keyEl = data["locations"].get(key)
            for key_wall in keyEl:
                logger.info(f"Prescribing a wall: {key_wall}")
                # Change BC-type
                # settings api command
                solver.settings.setup.boundary_conditions.set_zone_type(
                    zone_list=[key_wall], new_type="wall"
                )
                # tui command
                # solver.tui.define.boundary_conditions.zone_type(key_wall, "wall")

        # Interfaces
        elif key == "bz_interfaces_general_names":
            # solver.tui.define.mesh_interfaces.one_to_one_pairing("no")
            keyEl = data["locations"].get(key)
            for key_if in keyEl:
                logger.info(f"Setting up general interface: {key_if}")
                side1 = keyEl[key_if].get("side1")
                side2 = keyEl[key_if].get("side2")
                # Change BC-type
                # settings api command
                solver.settings.setup.boundary_conditions.set_zone_type(
                    zone_list=[side1, side2], new_type="interface"
                )
                # Create Interface
                if Version(solver._version) < Version("251"):
                    if not gpu:
                        solver.tui.define.turbo_model.turbo_create(
                            key_if, side1, "()", side2, "()", "3"
                        )
                    else:
                        if list(keyEl.keys()).index(key_if) == 0:
                            key_if = key_if.replace("-", "_")
                            solver.tui.define.mesh_interfaces.create(
                                key_if, "no", side1, side2, "()", "no"
                            )
                        else:
                            key_if = key_if.replace("-", "_")
                            solver.tui.define.mesh_interfaces.create(
                                key_if, side1, side2
                            )
                else:
                    solver.settings.setup.mesh_interfaces.interface.create(
                        name=key_if, zone1_list=[side1], zone2_list=[side2]
                    )

    # Setup turbo-interfaces at end
    keyEl = data["locations"].get("bz_interfaces_mixingplane_names")
    if keyEl is not None:
        for key_if in keyEl:
            logger.info(f"Setting up mixing plane interface: {key_if}")
            side1 = keyEl[key_if].get("side1")
            side2 = keyEl[key_if].get("side2")
            # Change BC-type
            # settings api command
            solver.settings.setup.boundary_conditions.set_zone_type(
                zone_list=[side1, side2], new_type="interface"
            )
            # tui command
            # solver.tui.define.boundary_conditions.zone_type(side1, "interface")
            # solver.tui.define.boundary_conditions.zone_type(side2, "interface")
            # Create Interface
            if gpu:
                logger.error(
                    "GTI Interfaces are not supported in GPU solver and will cause the setup to fail. Currently, only general interfaces are supported."
                )

            solver.tui.define.turbo_model.turbo_create(
                key_if, side1, "()", side2, "()", "2"
            )
    keyEl = data["locations"].get("bz_interfaces_no_pitchscale_names")
    if keyEl is not None:
        for key_if in keyEl:
            logger.info(f"Setting up no pitch-scale interface: {key_if}")
            side1 = keyEl[key_if].get("side1")
            side2 = keyEl[key_if].get("side2")
            # Change BC-type
            # settings api command
            solver.settings.setup.boundary_conditions.set_zone_type(
                zone_list=[side1, side2], new_type="interface"
            )
            # tui command
            # solver.tui.define.boundary_conditions.zone_type(side1, "interface")
            # solver.tui.define.boundary_conditions.zone_type(side2, "interface")
            # Create Interface
            if gpu:
                logger.error(
                    "GTI Interfaces are not supported in GPU solver and will cause the setup to fail. Currently, only general interfaces are supported."
                )

            solver.tui.define.turbo_model.turbo_create(
                key_if, side1, "()", side2, "()", "1"
            )
    keyEl = data["locations"].get("bz_interfaces_pitchscale_names")
    if keyEl is not None:
        for key_if in keyEl:
            logger.info(f"Setting up pitch-scale interface: {key_if}")
            side1 = keyEl[key_if].get("side1")
            side2 = keyEl[key_if].get("side2")
            # Change BC-type
            # settings api command
            solver.settings.setup.boundary_conditions.set_zone_type(
                zone_list=[side1, side2], new_type="interface"
            )
            # tui command
            # solver.tui.define.boundary_conditions.zone_type(side1, "interface")
            # solver.tui.define.boundary_conditions.zone_type(side2, "interface")
            # Create Interface
            if gpu:
                logger.error(
                    "GTI Interfaces are not supported in GPU solver and will cause the setup to fail. Currently, only general interfaces are supported."
                )

            solver.tui.define.turbo_model.turbo_create(
                key_if, side1, "()", side2, "()", "0"
            )

    # setup turbo topology
    keyEl = data["locations"].get("tz_turbo_topology_names")
    if keyEl is not None:
        logger.info("Setting up turbo topology for post processing.")
        for key_topo in keyEl:
            turbo_name = f'"{key_topo}"'
            hub_names = keyEl[key_topo].get("tz_hub_names")
            shroud_names = keyEl[key_topo].get("tz_shroud_names")
            inlet_names = keyEl[key_topo].get("tz_inlet_names")
            outlet_names = keyEl[key_topo].get("tz_outlet_names")
            blade_names = keyEl[key_topo].get("tz_blade_names")
            periodic_names = keyEl[key_topo].get("tz_theta_periodic_names")
            try:
                theta_min = []
                theta_max = []
                for periodic_name in periodic_names:
                    if periodic_name in non_conformal_list:
                        logger.info(
                            f"encountered a non-conformal periodic interface: {periodic_name}"
                        )
                        logger.info("Adjusting turbo topology")
                        theta_min.append(
                            data["locations"]["bz_interfaces_periodic_names"][
                                periodic_name
                            ].get("side1")
                        )
                        theta_max.append(
                            data["locations"]["bz_interfaces_periodic_names"][
                                periodic_name
                            ].get("side2")
                        )
                if len(theta_min) > 0 and len(theta_max) > 0:
                    solver.tui.define.turbo_model.turbo_topology.define_topology(
                        turbo_name,
                        *hub_names,
                        [],
                        *shroud_names,
                        [],
                        *inlet_names,
                        [],
                        *outlet_names,
                        [],
                        *blade_names,
                        [],
                        [],
                        *theta_min,
                        [],
                        *theta_max,
                        [],
                    )
                else:
                    solver.tui.define.turbo_model.turbo_topology.define_topology(
                        turbo_name,
                        *hub_names,
                        [],
                        *shroud_names,
                        [],
                        *inlet_names,
                        [],
                        *outlet_names,
                        [],
                        *blade_names,
                        [],
                        *periodic_names,
                        [],
                    )
            except Exception as e:
                logger.warning(f"An error occurred while defining topology: {e}")

    return


def set_reports(data, solver, launchEl, gpu: bool = False):
    logger.info("Running set_reports()...")
    # Get Solution-Dict
    solutionDict = data.get("solution")
    # Get PTW Output folder path
    fl_workingDir = launchEl.get("workingDir")
    caseOutPath = misc_utils.ptw_output(
        fl_workingDir=fl_workingDir, case_name=data["caseFilename"]
    )

    if solutionDict is None:
        logger.warning(
            f"No Solution-Dict specified in Case: 'solution'. Skipping Report-Definition!"
        )
        return

    # Reports
    # working on a copy, as we are going to modify it
    reportList = solutionDict.get("reportlist")
    basicReportDict = solutionDict.get("basic_reports")
    # Old definitions stored directly in case section
    if data.get("basic_reports") is not None:
        if basicReportDict is None:
            basicReportDict = data.get("basic_reports")
        else:
            # Combine if both definitions should exist
            basicReportDict.update(data.get("basic_reports"))

    if reportList is not None:
        logger.info("Setting up Report Definitions...")
        for report in reportList:
            reportName = report.replace("_", "-")
            reportName = "rep-" + reportName.lower()
            if Version(solver._version) < Version("241"):
                solver.settings.solution.report_definitions.single_val_expression[
                    reportName
                ] = {}
                solver.settings.solution.report_definitions.single_val_expression[
                    reportName
                ] = {"define": report}
            else:
                solver.settings.solution.report_definitions.single_valued_expression[
                    reportName
                ] = {}
                solver.settings.solution.report_definitions.single_valued_expression[
                    reportName
                ] = {"definition": report}
            reportPlotName = reportName + "-plot"
            solver.settings.solution.monitor.report_plots[reportPlotName] = {}
            solver.settings.solution.monitor.report_plots[reportPlotName] = {
                "report_defs": [reportName]
            }

        if gpu:
            logger.warning(
                f"In GPU solver, Report Definitions specified in 'report_list' cannot be plotted or saved in the report file! However, the Report Definitions are still created.\nOnly Report Definitions specified in 'basic_reports' will be plotted and stored in the report-file."
            )

    if basicReportDict is not None:
        logger.info("Setting up Basic Report Definitions...")
        if reportList is None:
            reportList = []
        for report in basicReportDict:
            reportName = report.replace("_", "-")
            reportName = "rep-" + reportName.lower()

            scope = basicReportDict[report].get("scope")

            # define scope --> create new report definition from the specified scope
            if scope == "surface":
                surfaces = basicReportDict[report].get("zones")
                variable = basicReportDict[report].get("variable")
                type = basicReportDict[report].get("type")
                solver.settings.solution.report_definitions.surface[reportName] = {}

                # define type
                allowed_types = solver.settings.solution.report_definitions.surface[
                    reportName
                ].report_type.allowed_values()
                if type in allowed_types:
                    solver.settings.solution.report_definitions.surface[reportName] = {
                        "report_type": type
                    }
                else:
                    logger.warning(
                        f"Specified type '{type}' not known. Allowed types are: {allowed_types}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define surfaces
                allowed_surfaces = solver.settings.solution.report_definitions.surface[
                    reportName
                ].surface_names.allowed_values()
                if set(surfaces).issubset(allowed_surfaces):
                    solver.settings.solution.report_definitions.surface[reportName] = {
                        "surface_names": surfaces
                    }
                else:
                    logger.warning(
                        f"Specified surfaces '{surfaces}' not valid. Allowed surfaces are: {allowed_surfaces}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define variable
                allowed_variables = solver.settings.solution.report_definitions.surface[
                    reportName
                ].field.allowed_values()
                if variable in allowed_variables:
                    solver.settings.solution.report_definitions.surface[reportName] = {
                        "field": variable
                    }
                else:
                    logger.warning(
                        f"Specified variable '{variable}' not known. Allowed variables are: {allowed_variables}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # create output parameter
                solver.settings.solution.report_definitions.surface[
                    reportName
                ].create_output_parameter()

                # set if per_zone should be used
                solver.settings.solution.report_definitions.surface[
                    reportName
                ].per_surface = basicReportDict[report].get("per_zone", False)

            elif scope == "volume":
                cell_zones = basicReportDict[report].get("zones")
                variable = basicReportDict[report].get("variable")
                type = basicReportDict[report].get("type")
                solver.settings.solution.report_definitions.volume[reportName] = {}

                # define type
                allowed_types = solver.settings.solution.report_definitions.volume[
                    reportName
                ].report_type.allowed_values()
                if type in allowed_types:
                    solver.settings.solution.report_definitions.volume[reportName] = {
                        "report_type": type
                    }
                else:
                    logger.warning(
                        f"Specified type '{type}' not known. Allowed types are: {allowed_types}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define cell zones
                allowed_zones = solver.settings.solution.report_definitions.volume[
                    reportName
                ].cell_zones.allowed_values()
                if set(cell_zones).issubset(allowed_zones):
                    solver.settings.solution.report_definitions.volume[reportName] = {
                        "cell_zones": cell_zones
                    }
                else:
                    logger.warning(
                        f"Specified cell zones '{cell_zones}' not valid. Allowed cell zones are: {allowed_zones}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define variable
                allowed_variables = solver.settings.solution.report_definitions.volume[
                    reportName
                ].field.allowed_values()
                if variable in allowed_variables:
                    solver.settings.solution.report_definitions.volume[reportName] = {
                        "field": variable
                    }
                else:
                    logger.warning(
                        f"Specified variable '{variable}' not known. Allowed variables are: {allowed_variables}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # create output parameter
                solver.settings.solution.report_definitions.volume[
                    reportName
                ].create_output_parameter()

                # set if per_zone should be used
                solver.settings.solution.report_definitions.volume[
                    reportName
                ].per_zone = basicReportDict[report].get("per_zone", False)

            elif scope == "force":
                zones = basicReportDict[report].get("zones")
                force_vector = basicReportDict[report].get("force_vector")
                solver.settings.solution.report_definitions.force[reportName] = {}

                # define zones
                allowed_zones = solver.settings.solution.report_definitions.force[
                    reportName
                ].zones.allowed_values()
                if set(zones).issubset(allowed_zones):
                    solver.settings.solution.report_definitions.force[reportName] = {
                        "zones": zones
                    }
                else:
                    logger.warning(
                        f"Specified zones '{zones}' not valid. Allowed zones are: {allowed_zones}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define force vector
                solver.settings.solution.report_definitions.force[reportName] = {
                    "force_vector": force_vector
                }

                # create output parameter
                solver.settings.solution.report_definitions.force[
                    reportName
                ].create_output_parameter()

                # set if per_zone should be used
                solver.settings.solution.report_definitions.force[
                    reportName
                ].per_zone = basicReportDict[report].get("per_zone", False)

            elif scope == "drag":
                zones = basicReportDict[report].get("zones")
                force_vector = basicReportDict[report].get("force_vector")
                report_output_type = basicReportDict[report].get("report_output_type")
                solver.settings.solution.report_definitions.drag[reportName] = {}

                # define zones
                allowed_zones = solver.settings.solution.report_definitions.drag[
                    reportName
                ].zones.allowed_values()
                if set(zones).issubset(allowed_zones):
                    solver.settings.solution.report_definitions.drag[reportName] = {
                        "zones": zones
                    }
                else:
                    logger.warning(
                        f"Specified zones '{zones}' not valid. Allowed zones are: {allowed_zones}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define force vector
                solver.settings.solution.report_definitions.drag[reportName] = {
                    "force_vector": force_vector
                }

                # define report output type
                allowed_report_output_types = (
                    solver.settings.solution.report_definitions.drag[
                        reportName
                    ].report_output_type.allowed_values()
                )
                if report_output_type in allowed_report_output_types:
                    solver.settings.solution.report_definitions.drag[reportName] = {
                        "report_output_type": report_output_type
                    }
                else:
                    logger.warning(
                        f"Specified report output type '{report_output_type}' not valid. Allowed report output types are: {allowed_report_output_types}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # create output parameter
                solver.settings.solution.report_definitions.drag[
                    reportName
                ].create_output_parameter()

                # set if per_zone should be used
                solver.settings.solution.report_definitions.drag[
                    reportName
                ].per_zone = basicReportDict[report].get("per_zone", False)

            elif scope == "lift":
                zones = basicReportDict[report].get("zones")
                force_vector = basicReportDict[report].get("force_vector")
                report_output_type = basicReportDict[report].get("report_output_type")
                solver.settings.solution.report_definitions.lift[reportName] = {}

                # define zones
                allowed_zones = solver.settings.solution.report_definitions.lift[
                    reportName
                ].zones.allowed_values()
                if set(zones).issubset(allowed_zones):
                    solver.settings.solution.report_definitions.lift[reportName] = {
                        "zones": zones
                    }
                else:
                    logger.warning(
                        f"Specified zones '{zones}' not valid. Allowed zones are: {allowed_zones}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define force vector
                solver.settings.solution.report_definitions.lift[reportName] = {
                    "force_vector": force_vector
                }

                # define report output type
                allowed_report_output_types = (
                    solver.settings.solution.report_definitions.lift[
                        reportName
                    ].report_output_type.allowed_values()
                )
                if report_output_type in allowed_report_output_types:
                    solver.settings.solution.report_definitions.lift[reportName] = {
                        "report_output_type": report_output_type
                    }
                else:
                    logger.warning(
                        f"Specified report output type '{report_output_type}' not valid. Allowed report output types are: {allowed_report_output_types}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # create output parameter
                solver.settings.solution.report_definitions.lift[
                    reportName
                ].create_output_parameter()

                # set if per_zone should be used
                solver.settings.solution.report_definitions.lift[
                    reportName
                ].per_zone = basicReportDict[report].get("per_zone", False)

            elif scope == "moment":
                zones = basicReportDict[report].get("zones")
                mom_center = basicReportDict[report].get("mom_center")
                mom_axis = basicReportDict[report].get("mom_axis")
                report_output_type = basicReportDict[report].get("report_output_type")
                solver.settings.solution.report_definitions.moment[reportName] = {}

                # define zones
                allowed_zones = solver.settings.solution.report_definitions.moment[
                    reportName
                ].zones.allowed_values()
                if set(zones).issubset(allowed_zones):
                    solver.settings.solution.report_definitions.moment[reportName] = {
                        "zones": zones
                    }
                else:
                    logger.warning(
                        f"Specified zones '{zones}' not valid. Allowed zones are: {allowed_zones}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define moment center
                solver.settings.solution.report_definitions.moment[reportName] = {
                    "mom_center": mom_center
                }

                # define moment axis
                solver.settings.solution.report_definitions.moment[reportName] = {
                    "mom_axis": mom_axis
                }

                # define report output type
                allowed_report_output_types = (
                    solver.settings.solution.report_definitions.moment[
                        reportName
                    ].report_output_type.allowed_values()
                )
                if report_output_type in allowed_report_output_types:
                    solver.settings.solution.report_definitions.moment[reportName] = {
                        "report_output_type": report_output_type
                    }
                else:
                    logger.warning(
                        f"Specified report output type '{report_output_type}' not valid. Allowed report output types are: {allowed_report_output_types}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # create output parameter
                solver.settings.solution.report_definitions.moment[
                    reportName
                ].create_output_parameter()

                # set if per_zone should be used
                solver.settings.solution.report_definitions.moment[
                    reportName
                ].per_zone = basicReportDict[report].get("per_zone", False)

            elif scope == "flux":
                type = basicReportDict[report].get("type")
                boundaries = basicReportDict[report].get("zones")
                solver.settings.solution.report_definitions.flux[reportName] = {}

                # define type
                allowed_types = solver.settings.solution.report_definitions.flux[
                    reportName
                ].report_type.allowed_values()
                if type in allowed_types:
                    solver.settings.solution.report_definitions.flux[reportName] = {
                        "report_type": type
                    }
                else:
                    logger.warning(
                        f"Specified type '{type}' not supported. Allowed types are: {allowed_types}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # define boundaries
                allowed_boundaries = solver.settings.solution.report_definitions.flux[
                    reportName
                ].boundaries.allowed_values()
                if set(boundaries).issubset(allowed_boundaries):
                    solver.settings.solution.report_definitions.flux[reportName] = {
                        "boundaries": boundaries
                    }
                else:
                    logger.warning(
                        f"Specified boundaries '{boundaries}' not valid. Allowed boundaries are: {allowed_boundaries}.\nSkipping setup of Report '{report}'"
                    )
                    solver.tui.solve.report_definitions.delete(reportName)
                    continue

                # create output parameter
                solver.settings.solution.report_definitions.flux[
                    reportName
                ].create_output_parameter()

                # set if per_zone should be used
                solver.settings.solution.report_definitions.flux[
                    reportName
                ].per_zone = basicReportDict[report].get("per_zone", False)

            else:
                logger.warning(
                    f"Specified scope '{scope}' not supported. Skipping setup of Report '{report}'"
                )
                continue

            # create report plot and append to report file list
            reportList.append(report)
            reportPlotName = reportName + "-plot"
            solver.settings.solution.monitor.report_plots[reportPlotName] = {
                "report_defs": reportName
            }

    # Report File
    logger.info("Setting up Report File...")
    if reportList is not None:
        solver.settings.solution.monitor.report_files["report-file"] = {}
        reportNameList = []
        for report in reportList:
            reportName = report.replace("_", "-")
            reportName = "rep-" + reportName.lower()
            reportNameList.append(reportName)

        reportFileName = os.path.join(caseOutPath, "report.out")
        solver.settings.solution.monitor.report_files["report-file"] = {
            "file_name": reportFileName,
            "report_defs": reportNameList,
        }
    else:
        logger.warning(
            "No report-definitions specified in Case: Keyword 'reportlist' and 'basic_reports'!"
        )

    # Set Residuals
    logger.info("Setting up Residuals...")
    if Version(solver._version) < Version("252"):
        # solver.tui.preferences.simulation.local_residual_scaling("yes")
        solver.tui.solve.monitors.residual.scale_by_coefficient("yes", "yes", "yes")

        # Raise the limit of residual points to save and to plot to avoid data resampling/loss
        solver.tui.solve.monitors.residual.n_display(500000)
        solver.tui.solve.monitors.residual.n_save(500000)

        # Check active number of equations
        number_eqs = fluent_utils.getNumberOfEquations(solver=solver)

        resCrit = solutionDict.setdefault("res_crit", 1.0e-4)
        resCritList = [resCrit] * number_eqs
        if len(resCritList) > 0:
            solver.tui.solve.monitors.residual.convergence_criteria(*resCritList)
    else:
        # Settings some display settings
        solver.settings.solution.monitor.residual.options.n_display = 500000
        solver.settings.solution.monitor.residual.options.n_save = 500000
        # Settings local residuals
        solver.settings.solution.monitor.residual.options.residual_values.scale_residuals = (
            True
        )
        solver.settings.solution.monitor.residual.options.residual_values.compute_local_scale = (
            True
        )
        solver.settings.solution.monitor.residual.options.residual_values.reporting_option = (
            "local"
        )

        # Setting residual criteria
        resCrit = solutionDict.setdefault("res_crit", 1.0e-4)
        for equation_key in solver.settings.solution.monitor.residual.equations.keys():
            solver.settings.solution.monitor.residual.equations[
                equation_key
            ].absolute_criteria = resCrit

    # Set CoVs
    logger.info("Setting up CoVs...")
    cov_list = solutionDict.get("cov_list")
    if (cov_list is not None) and (not gpu):
        stop_criterion = solutionDict.setdefault("cov_crit", 1.0e-4)
        for solve_cov in cov_list:
            reportName = solve_cov.replace("_", "-")
            reportName = "rep-" + reportName.lower()
            covName = reportName + "-cov"
            solver.settings.solution.monitor.convergence_conditions.convergence_reports[
                covName
            ] = {}
            solver.settings.solution.monitor.convergence_conditions = {
                "convergence_reports": {
                    covName: {
                        "report_defs": reportName,
                        "cov": True,
                        "previous_values_to_consider": 50,
                        "stop_criterion": stop_criterion,
                        "print": True,
                        "plot": True,
                    }
                }
            }
    elif (cov_list is None) and (not gpu):
        logger.warning("No CoV definitions specified in Case: Keyword 'cov_list'!")
    elif (cov_list is not None) and gpu:
        logger.warning(
            "CoV is not supported in GPU solver! Sepcified CoVs will not be used!"
        )

    # Set Convergence Conditions
    logger.info("Setting up Convergence Conditions...")
    conv_check_freq = solutionDict.setdefault("conv_check_freq", 5)
    solver.settings.solution.monitor.convergence_conditions = {
        # "condition": "any-condition-is-met",
        "condition": "all-conditions-are-met",
        "frequency": conv_check_freq,
    }

    logger.info("Running set_reports()... done.")
    return


def set_run_calculation(data, solver):
    # Get Solution-Dict
    solutionDict = data.get("solution")

    if solutionDict is None:
        logger.warning(
            f"No Solution-Dict specified in Case: 'solution'. Skipping 'set_run_calculation'!"
        )
        return

    logger.info("Setting up Run Calculation settings...")
    # check if pseudo-time-step method is activated in setup
    if "pseudo_time_settings" in solver.settings.solution.run_calculation().keys():
        # Set Basic Solver-Solution-Settings
        tsf = solutionDict.get("time_step_factor", 5)
        # Check for a pseudo-time-step-size
        pseudo_timestep = solutionDict.get("pseudo_timestep")
        if pseudo_timestep is not None:
            # Use pseudo timestep
            logger.info(
                f"Direct Specification of pseudo timestep size from Configfile: {pseudo_timestep}"
            )
            solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = (
                "user-specified"
            )
            solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = (
                pseudo_timestep
            )
            # Update dict
            if solutionDict.get("time_step_factor") is not None:
                solutionDict.pop("time_step_factor")
        else:
            # Use timescale factor
            logger.info(
                f"Using 'conservative'-'automatic' timestep method with timescale-factor: {tsf}"
            )
            solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = (
                "automatic"
            )
            solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.length_scale_methods = (
                "conservative"
            )
            solver.settings.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_size_scale_factor = (
                tsf
            )
            # Update dict
            solutionDict["time_step_factor"] = tsf
    else:
        logger.info(
            "Pseudo-Time-Step Method not active, no change to timestep-settings"
        )

    iter_count = solutionDict.setdefault("iter_count", 500)
    solver.settings.solution.run_calculation.iter_count = int(iter_count)


def source_terms(data, solver):
    my_sources = data.get("source_terms")
    if my_sources is None:
        logger.info(f"No 'source_terms' defined: Skipping 'source_terms' function!")
        return
    list_fluid_zones = (
        solver.settings.setup.cell_zone_conditions.fluid.get_object_names()
    )
    for key in my_sources:
        logger.info(f"Defining source-term: '{key}'")
        exp_name = key
        exp_definition = my_sources[key]["definition"]
        myvalue = fluent_utils.create_and_evaluate_expression(
            solver,
            exp_name=exp_name,
            definition=exp_definition,
            overwrite_definition=True,
            evaluate_value=False,
        )
        if my_sources[key]["cell_zone"] in list_fluid_zones:
            solver.settings.setup.cell_zone_conditions.fluid[
                my_sources[key]["cell_zone"]
            ] = {
                "sources": {
                    "enable": True,
                    "terms": {
                        my_sources[key]["equation"]: [
                            {"option": "value", "value": exp_name}
                        ]
                    },
                }
            }

    logger.info("Definition of source-terms completed")


def blade_film_cooling(data, solver):

    def validate_injection_profile(csv_path, required_headers=None):
        if required_headers is None:
            required_headers = [
                "x [in]",
                "y [in]",
                "z [in]",
                "dia [in]",
                "flowlbm [lbm s^-1]",
                "Temp [K]",
                "x_dir[]",
                "y_dir[]",
                "z_dir[]",
            ]

        with open(csv_path, newline="") as csvfile:
            reader = csv.reader(csvfile, delimiter="\t")
            for row in reader:
                # Find header line
                if row and any(h in row[0] for h in required_headers):
                    headers = [h.strip() for h in row]
                    break
            else:
                raise ValueError(f"Could not find a header row in {csv_path}")

        missing = [h for h in required_headers if h not in headers]
        if missing:
            raise ValueError(f"{csv_path} is missing required headers: {missing}")

    solver.scheme_eval.scheme_eval("(rpsetvar 'virtualboundary/diag-level 1)")
    solver.scheme_eval.scheme_eval("(rpsetvar 'virtualboundary/bnd-ext-fac 1)")
    solver.scheme_eval.scheme_eval(
        "(rpsetvar 'virtualboundary/intersect-searchrad-fac 3)"
    )

    bf_cooling = data.get("blade_film_cooling", {})
    cooling_zones = bf_cooling.get("cooling_zones", [])
    if not cooling_zones:
        logger.info(
            f"No 'cooling_zones' defined: Skipping 'blade_film_cooling' function!"
        )
        return
    for zone in cooling_zones:
        logger.info(f"Defining blade film cooling for zone '{zone}'")
        profile_file = zone["profile_file"]
        geometry_name = zone["geometry_name"]
        interface_blade_zone = zone["interface_blade_zone"]
        vb_name = zone["virtual_boundary_name"]
        # validate_injection_profile(profile_file)

        # read cooling profile
        solver.settings.file.read_profile(file_name=profile_file)

        # virtual boundary definition
        # solver.tui.define.virtual_boundary.hole_geometry(
        #     'add', vb_name, 'coordinates', geometry_name,
        #     'direction', 'cartesian',
        #     'x-dir', 'profile', 'x_dir',
        #     'y-dir', 'profile', 'y_dir',
        #     'z-dir', 'profile', 'z_dir',
        #     'quit',
        #     'flowdir', 'hole-direction',
        #     'flowvars', 'massflow', 'profile', 'flowlbm',
        #     'temperature', 'profile', 'temp',
        #     'quit',
        #     'name', vb_name,
        #     'shape', 'cylindrical',
        #     'diameter', 'profile', 'dia',
        #     'quit',
        #     'type', 'mass-flow-inlet',
        #     'preview', 'quit', 'quit', 'quit'
        # )
        solver.tui.define.virtual_boundary.hole_geometry(
            "add",
            vb_name,
            "coordinates",
            geometry_name,
            "type",
            "mass-flow-inlet",
            "direction",
            "normal-to-boundary",
            "flowdir",
            "cartesian",
            "x-dir",
            "profile",
            "x_dir",
            "y-dir",
            "profile",
            "y_dir",
            "z-dir",
            "profile",
            "z_dir",
            "quit",  # Exits from flowdir block
            "shape",
            "cylindrical",
            "diameter",
            "profile",
            "dia",
            "quit",  # Exits from shape block
            "flowvars",
            "massflow",
            "profile",
            "flowlbm",
            "temperature",
            "profile",
            "temp",
            "quit",  # Exits from flowvars block
            "quit",  # Exits from the main block
            "quit",
            "quit",
            "quit",
        )

        # Connect boundary interface
        solver.tui.define.virtual_boundary.boundary_interface(
            "add",
            f"{vb_name}-interface",
            "boundaries",
            interface_blade_zone,
            "()",
            "geometry",
            f'"{vb_name}"',
            "()",
            "quit",
            "quit",
            "quit",
            "quit",
        )

    logger.info("Blade film cooling setup complete.")
