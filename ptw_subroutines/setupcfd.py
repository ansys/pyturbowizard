# Logger
from ptw_subroutines.utils import ptw_logger, dict_utils, misc_utils, fluent_utils
import os

logger = ptw_logger.getLogger()


def setup(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="setup",
        defaultName="setup_compressible_01",
    )
    logger.info('Running Setup Function "' + functionName + '"...')
    if functionName == "setup_compressible_01":
        setup_compressible_01(data, solver)
    elif functionName == "setup_incompressible_01":
        setup_incompressible_01(data, solver)
    else:
        logger.info(
            'Prescribed Function "' + functionName + '" not known. Skipping Setup!'
        )

    logger.info("Running Setup Function... finished!")


def setup_compressible_01(data, solver):
    setup_01(data=data, solver=solver, solveEnergy=True)
    return


def setup_incompressible_01(data, solver):
    setup_01(data=data, solver=solver, solveEnergy=False)
    return


def setup_01(data, solver, solveEnergy: bool = True):
    # Set physics
    physics_01(data=data, solver=solver, solveEnergy=solveEnergy)
    # Materials
    material_01(data=data, solver=solver, solveEnergy=solveEnergy)
    # Set Boundaries
    boundary_01(data=data, solver=solver, solveEnergy=solveEnergy)

    # Do some Mesh Checks
    solver.mesh.check()
    solver.mesh.quality()

    return


def material_01(data, solver, solveEnergy: bool = True):
    fl_name = data["fluid_properties"].get("fl_name")
    if fl_name is None:
        if solveEnergy:
            fl_name = "custom-comp-fluid"
        else:
            fl_name = "custom-incomp-fluid"
        data["fluid_properties"]["fl_name"] = fl_name

    fluid_list = list(solver.setup.materials.fluid.keys())

    solver.setup.materials.fluid.rename(fl_name, fluid_list[0])

    if solveEnergy:
        solver.setup.materials.fluid[fl_name] = {

            "density": {"option": data["fluid_properties"]["fl_density"]},
            "specific_heat": {
                "option": "constant",
                "value": data["fluid_properties"]["fl_specific_heat"],
            },
            "thermal_conductivity": {
                "option": "constant",
                "value": data["fluid_properties"]["fl_thermal_conductivity"],
            },
            "viscosity": {
                "option": "constant",
                "value": data["fluid_properties"]["fl_viscosity"],
            },
            "molecular_weight": {
                "option": "constant",
                "value": data["fluid_properties"]["fl_mol_wight"],
            },
        }
    else:
        solver.setup.materials.fluid[fl_name] = {
            "density": {
                "option": "constant",
                "value": data["fluid_properties"]["fl_density"],
            },
            "viscosity": {
                "option": "constant",
                "value": data["fluid_properties"]["fl_viscosity"],
            },
        }

    # Boundary Conditions
    solver.setup.general.operating_conditions.operating_pressure = "BC_pref"

    return


def physics_01(data, solver, solveEnergy: bool = True):
    if solveEnergy:
        solver.setup.models.energy = {"enabled": True, "viscous_dissipation": True}

    gravityVector = data.get("gravity_vector")
    if (type(gravityVector) is list) and (len(gravityVector) == 3):
        logger.info(f"Specification of Gravity-Vector: {gravityVector}")
        solver.setup.general.operating_conditions.gravity.enable = True
        solver.setup.general.operating_conditions.gravity.components = gravityVector

    # Set turbulence model
    # if not set or in supported list, sst
    default_turb_model = "sst"
    turb_model = data["setup"].setdefault("turbulence_model", default_turb_model)
    supported_kw_models = solver.setup.models.viscous.k_omega_model.allowed_values()
    if turb_model in supported_kw_models:
        # Set Geko Model Parameters
        c_sep = data["setup"].setdefault("geko_csep",1.75)
        c_nw = data["setup"].setdefault("geko_cnw",0.5)
        c_jet = data["setup"].setdefault("geko_cjet",0.9)

        logger.info(f"Setting kw-turbulence-model: '{turb_model}'")
        solver.setup.models.viscous.model = "k-omega"
        solver.setup.models.viscous.k_omega_model = turb_model

        if turb_model == "geko":
            solver.tui.define.models.viscous.geko_options.csep("yes",c_sep)
            solver.tui.define.models.viscous.geko_options.csep("yes",c_nw)
            solver.tui.define.models.viscous.geko_options.cnw("yes",c_jet)
            
    else:
        logger.warning(
            f"Specified turbulence-model not supported: '{turb_model}'! Default turbulence model will be used: '{default_turb_model}'!"
        )
        data["setup"]["turbulence_model"] = default_turb_model
        solver.setup.models.viscous.model = "k-omega"
        solver.setup.models.viscous.k_omega_model = default_turb_model

    return


def boundary_01(data, solver, solveEnergy: bool = True):
    # Enable Turbo Models
    solver.tui.define.turbo_model.enable_turbo_model("yes")

    # Get rotation axis info: default is z-axis
    rot_ax_dir = data.setdefault("rotation_axis_direction", [0.0, 0.0, 1.0])
    rot_ax_orig = data.setdefault("rotation_axis_origin", [0.0, 0.0, 0.0])

    # Do important steps at startup in specified order
    # 1. Fluid cell zone conditions
    cz_rot_list = data["locations"].get("cz_rotating_names")
    for cz_name in solver.setup.cell_zone_conditions.fluid():
        # Check if it´s a rotating cell-zone
        if (cz_rot_list is not None) and (cz_name in cz_rot_list):
            logger.info(f"Prescribing rotating cell zone: {cz_name}")
            solver.setup.cell_zone_conditions.fluid[cz_name] = {
                "reference_frame_axis_origin": rot_ax_orig,
                "reference_frame_axis_direction": rot_ax_dir,
                "mrf_motion": True,
                "mrf_omega": "BC_omega",
            }
        # otherwise its stationary
        else:
            logger.info(f"Prescribing stationary cell zone: {cz_name}")
            solver.setup.cell_zone_conditions.fluid[cz_name] = {
                "reference_frame_axis_origin": rot_ax_orig,
                "reference_frame_axis_direction": rot_ax_dir,
            }

    # 2. Search for periodic interfaces
    peri_if_El = data["locations"].get("bz_interfaces_periodic_names")
    if peri_if_El is not None:
        non_conformal_list = []
        for key_if in peri_if_El:
            logger.info(f"Setting up periodic BC: {key_if}")
            side1 = peri_if_El[key_if].get("side1")
            side2 = peri_if_El[key_if].get("side2")
            # check if spcified sides are not already defined as periodics
            periodicIFs = solver.setup.boundary_conditions.periodic
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
                # As the origin & axis have been set for all cell-zones these are the defaults for all containing boundary zones
                # Therefore, we do not need to set them -> "no", "no"
                solver.tui.mesh.modify_zones.create_periodic_interface(
                    "auto", key_if, side1, side2, "yes", "no", "no", "yes", "yes"
                )
                # check for non-conformal periodics (fluent creates normal interfaces if non-conformal)
                intf_check_side1 = solver.setup.boundary_conditions.interface.get(side1)
                intf_check_side2 = solver.setup.boundary_conditions.interface.get(side2)

                if intf_check_side1 is not None and intf_check_side2 is not None:
                    logger.info(
                        f"'{key_if}' is a non-conformal periodic interface! "
                        f"Adjusting turbo-topology accordingly"
                    )
                    # Add the non conformal interface to the list for correct turbo topology definition
                    non_conformal_list.append(key_if)

    # after important steps loop over all keys -> no order important
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
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[inletName], new_type="mass-flow-inlet"
                    )
                    # old tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    inletName, "mass-flow-inlet"
                    # )
                    inBC = solver.setup.boundary_conditions.mass_flow_inlet[inletName]
                    inBC.flow_spec = "Mass Flow Rate"
                    inBC.mass_flow = "BC_IN_MassFlow"
                    inBC.gauge_pressure = "BC_IN_p_gauge"
                    inBC.direction_spec = "Normal to Boundary"
                    if solveEnergy:
                        inBC.t0 = "BC_IN_Tt"

                if (
                    data["expressions"].get("BC_IN_VolumeFlow")
                    and data["expressions"].get("BC_IN_VolumeFlowDensity") is not None
                ):
                    logger.info(f"Prescribing a Volumeflow-Inlet BC @{inletName}")
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[inletName], new_type="mass-flow-inlet"
                    )
                    # old tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    inletName, "mass-flow-inlet"
                    # )
                    inBC = solver.setup.boundary_conditions.mass_flow_inlet[inletName]
                    inBC.flow_spec = "Mass Flow Rate"
                    inBC.mass_flow = "BC_IN_VolumeFlow*BC_IN_VolumeFlowDensity"
                    inBC.gauge_pressure = "BC_IN_p_gauge"
                    inBC.direction_spec = "Normal to Boundary"
                    if solveEnergy:
                        inBC.t0 = "BC_IN_Tt"

                elif data["expressions"].get("BC_IN_pt") is not None:
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[inletName], new_type="pressure-inlet"
                    )
                    # old tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    inletName, "pressure-inlet"
                    # )
                    inBC = solver.setup.boundary_conditions.pressure_inlet[inletName]

                    if useProfileData:
                        # check profile naming convention:
                        # profile_name: "inlet-bc"
                        # total pressure: pt-in,
                        # total temp: tt-in
                        inBC.gauge_total_pressure = {
                            "option": "profile",
                            "profile_name": "inlet-bc",
                            "field_name": "pt-in",
                        }
                        inBC.gauge_pressure = "BC_IN_p_gauge"
                        if solveEnergy:
                            inBC.t0 = {
                                "option": "profile",
                                "profile_name": "inlet-bc",
                                "field_name": "tt-in",
                            }
                    else:
                        inBC.gauge_total_pressure = "BC_IN_pt"
                        inBC.gauge_pressure = "BC_IN_p_gauge"
                        inBC.direction_spec = "Normal to Boundary"
                        if solveEnergy:
                            inBC.t0 = "BC_IN_Tt"

                    # Set reverse BC
                    reverse_option = data["setup"].setdefault("BC_IN_reverse", False)
                    inBC.prevent_reverse_flow = reverse_option

                # Do some general settings
                if inBC is not None:
                    # Turbulent Settings
                    if data["expressions"].get("BC_IN_TuIn") is not None:
                        inBC.turb_intensity = "BC_IN_TuIn"
                    if data["expressions"].get("BC_IN_TuVR") is not None:
                        inBC.turb_viscosity_ratio = "BC_IN_TuVR"

                    # If Expressions for a direction are specified
                    if (
                        (data["expressions"].get("BC_IN_radDir") is not None)
                        and (data["expressions"].get("BC_IN_tangDir") is not None)
                        and (data["expressions"].get("BC_IN_axDir") is not None)
                    ):
                        inBC.direction_spec = "Direction Vector"
                        inBC.coordinate_system = (
                            "Cylindrical (Radial, Tangential, Axial)"
                        )
                        inBC.flow_direction = [
                            "BC_IN_radDir",
                            "BC_IN_tangDir",
                            "BC_IN_axDir",
                        ]

                    # Use Definitions from Profile-Data if sepcified
                    # check profile naming convention:
                    # profile_name: "inlet-bc"
                    # directions (cylindrical): vrad-dir,vrad-dir,vax-dir
                    if useProfileData:
                        inBC.direction_spec = "Direction Vector"
                        inBC.coordinate_system = (
                            "Cylindrical (Radial, Tangential, Axial)"
                        )
                        inBC.flow_direction = [
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
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[outletName], new_type="mass-flow-outlet"
                    )
                    # old tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    outletName, "mass-flow-outlet"
                    # )

                    outBC = solver.setup.boundary_conditions.mass_flow_outlet[
                        outletName
                    ]
                    outBC.flow_spec = "Exit Corrected Mass Flow Rate"
                    outBC.ec_mass_flow = "BC_OUT_ECMassFlow"
                    if data["expressions"].get("BC_ECMassFlow_pref") is not None:
                        outBC.pref = "BC_ECMassFlow_pref"
                    else:
                        outBC.pref = "BC_IN_pt"
                    if data["expressions"].get("BC_ECMassFlow_pref") is not None:
                        outBC.tref = "BC_ECMassFlow_tref"
                    else:
                        outBC.tref = "BC_IN_Tt"

                elif data["expressions"].get("BC_OUT_MassFlow") is not None:
                    logger.info(f"Prescribing a Massflow-Outlet BC @{outletName}")
                    # solver.setup.boundary_conditions.change_type(
                    #    zone_list=[outletName], new_type="mass-flow-outlet"
                    # )
                    solver.tui.define.boundary_conditions.zone_type(
                        outletName, "mass-flow-outlet"
                    )
                    outBC = solver.setup.boundary_conditions.mass_flow_outlet[
                        outletName
                    ]
                    outBC.flow_spec = "Mass Flow Rate"
                    outBC.mass_flow = "BC_OUT_MassFlow"

                elif (
                    data["expressions"].get("BC_OUT_VolumeFlow")
                    and data["expressions"].get("BC_OUT_VolumeFlowDensity") is not None
                ):
                    logger.info(f"Prescribing a VolumeFlow-Outlet BC @{outletName}")
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[outletName], new_type="mass-flow-outlet"
                    )
                    # old tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    outletName, "mass-flow-outlet"
                    # )

                    outBC = solver.setup.boundary_conditions.mass_flow_outlet[
                        outletName
                    ]
                    outBC.flow_spec = "Mass Flow Rate"
                    outBC.mass_flow = "BC_OUT_VolumeFlow*BC_OUT_VolumeFlowDensity"

                elif data["expressions"].get("BC_OUT_p") is not None:
                    logger.info(f"Prescribing a Pressure-Outlet BC @{outletName}")
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[outletName], new_type="pressure-outlet"
                    )
                    # old tui command
                    # solver.tui.define.boundary_conditions.zone_type(
                    #    outletName, "pressure-outlet"
                    # )
                    outBC = solver.setup.boundary_conditions.pressure_outlet[outletName]
                    # Check Profile data exists
                    profileName = data.get("profileName_Out")
                    useProfileData = (profileName is not None) and (profileName != "")
                    if useProfileData:
                        # check profile naming convention:
                        # profile_name: "outlet-bc"
                        # outlet pressure: p-out
                        outBC.gauge_pressure = {
                            "option": "profile",
                            "profile_name": "outlet-bc",
                            "field_name": "p-out",
                        }
                    else:
                        outBC.gauge_pressure = "BC_OUT_p"

                    # Set AVG Pressure
                    pavg_set = data["setup"].setdefault("BC_OUT_avg_p", True)
                    outBC.avg_press_spec = pavg_set

                    # Set reverse BC
                    reverse_option = data["setup"].setdefault("BC_OUT_reverse", True)
                    outBC.prevent_reverse_flow = reverse_option

                    if data["setup"].get("BC_OUT_pressure_pt") is not None:
                        outBC.p_backflow_spec_gen = data["setup"].get(
                            "BC_OUT_pressure_pt"
                        )
                    # Set additional pressure-outlet-bc settings if available in config file
                    pout_settings = data["setup"].get("BC_settings_pout")
                    if (type(pout_settings) is list) and (len(pout_settings) > 1):
                        solver.tui.define.boundary_conditions.bc_settings.pressure_outlet(
                            pout_settings[0], pout_settings[1]
                        )

            # Walls
        # elif key == "bz_walls_shroud_names":
        #    solver.setup.boundary_conditions.wall[data["locations"][key]] = {"motion_bc": "Moving Wall","relative": False,"rotating": True}

        elif key == "bz_walls_counterrotating_names":
            keyEl = data["locations"].get(key)
            for key_cr in keyEl:
                logger.info(f"Prescribing a counter-rotating wall: {key_cr}")
                solver.setup.boundary_conditions.wall[key_cr] = {
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
                solver.setup.boundary_conditions.wall[key_r] = {
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
                solver.setup.boundary_conditions.wall[key_free] = {
                    "shear_bc": "Specified Shear"
                }

        # Interfaces
        elif key == "bz_interfaces_general_names":
            # solver.tui.define.mesh_interfaces.one_to_one_pairing("no")
            keyEl = data["locations"].get(key)
            for key_if in keyEl:
                logger.info(f"Setting up general interface: {key_if}")
                side1 = keyEl[key_if].get("side1")
                side2 = keyEl[key_if].get("side2")
                # solver.tui.define.mesh_interfaces.create(key_if, side1, '()', side2,'()', 'no', 'no', 'no', 'yes', 'no')
                solver.tui.define.turbo_model.turbo_create(
                    key_if, side1, "()", side2, "()", "3"
                )

    # Setup turbo-interfaces at end
    keyEl = data["locations"].get("bz_interfaces_mixingplane_names")
    if keyEl is not None:
        for key_if in keyEl:
            logger.info(f"Setting up mixing plane interface: {key_if}")
            side1 = keyEl[key_if].get("side1")
            side2 = keyEl[key_if].get("side2")
            solver.tui.define.turbo_model.turbo_create(
                key_if, side1, "()", side2, "()", "2"
            )
    keyEl = data["locations"].get("bz_interfaces_no_pitchscale_names")
    if keyEl is not None:
        for key_if in keyEl:
            logger.info(f"Setting up no pitch-scale interface: {key_if}")
            side1 = keyEl[key_if].get("side1")
            side2 = keyEl[key_if].get("side2")
            solver.tui.define.turbo_model.turbo_create(
                key_if, side1, "()", side2, "()", "1"
            )
    keyEl = data["locations"].get("bz_interfaces_pitchscale_names")
    if keyEl is not None:
        for key_if in keyEl:
            logger.info(f"Setting up pitch-scale interface: {key_if}")
            side1 = keyEl[key_if].get("side1")
            side2 = keyEl[key_if].get("side2")
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


def report_01(data, solver, launchEl):
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
    reportList = solutionDict.get("reportlist")
    if reportList is not None:
        for report in reportList:
            reportName = report.replace("_", "-")
            reportName = "rep-" + reportName.lower()
            solver.solution.report_definitions.single_val_expression[reportName] = {}
            solver.solution.report_definitions.single_val_expression[reportName] = {
                "define": report
            }
            reportPlotName = reportName + "-plot"
            solver.solution.monitor.report_plots[reportPlotName] = {}
            solver.solution.monitor.report_plots[reportPlotName] = {
                "report_defs": [reportName]
            }

        # Report File
        solver.solution.monitor.report_files["report-file"] = {}
        reportNameList = []
        for report in reportList:
            reportName = report.replace("_", "-")
            reportName = "rep-" + reportName.lower()
            reportNameList.append(reportName)

        reportFileName = os.path.join(caseOutPath, "report.out")
        solver.solution.monitor.report_files["report-file"] = {
            "file_name": reportFileName,
            "report_defs": reportNameList,
        }
    else:
        logger.warning(
            f"No report-definitions specified in Case: Keyword 'reportlist'!"
        )

    # Set Residuals
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

    # Set CoVs
    cov_list = solutionDict.get("cov_list")
    if cov_list is not None:
        stop_criterion = solutionDict.setdefault("cov_crit", 1.0e-4)
        for solve_cov in cov_list:
            reportName = solve_cov.replace("_", "-")
            reportName = "rep-" + reportName.lower()
            covName = reportName + "-cov"
            solver.solution.monitor.convergence_conditions.convergence_reports[
                covName
            ] = {}
            solver.solution.monitor.convergence_conditions = {
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
    else:
        logger.warning(f"No CoV definitions specified in Case: Keyword 'cov_list'!")

    # Set Convergence Conditions
    conv_check_freq = solutionDict.setdefault("conv_check_freq", 5)
    solver.solution.monitor.convergence_conditions = {
        # "condition": "any-condition-is-met",
        "condition": "all-conditions-are-met",
        "frequency": conv_check_freq,
    }
    # Set Basic Solver-Solution-Settings
    tsf = solutionDict.get("time_step_factor", 1)
    # Check for a pseudo-time-step-size
    pseudo_timestep = solutionDict.get("pseudo_timestep")
    if pseudo_timestep is not None:
        # Use pseudo timestep
        logger.info(
            f"Direct Specification of pseudo timestep size from Configfile: {pseudo_timestep}"
        )
        solver.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = (
            "user-specified"
        )
        solver.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = (
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
        solver.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = (
            "automatic"
        )
        solver.solution.run_calculation.pseudo_time_settings.time_step_method.length_scale_methods = (
            "conservative"
        )
        solver.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_size_scale_factor = (
            tsf
        )
        # Update dict
        solutionDict["time_step_factor"] = tsf

    iter_count = solutionDict.setdefault("iter_count", 500)
    solver.solution.run_calculation.iter_count = int(iter_count)
