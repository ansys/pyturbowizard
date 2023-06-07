from tts_subroutines import utilities


def setup(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = utilities.get_funcname_and_upd_funcdict(
        parentEl=data,
        functionEl=functionEl,
        funcElName="setup",
        defaultName="setup_01",
    )
    print('Running Setup Function "' + functionName + '"...')
    if functionName == "setup_01":
        setup_01(data, solver)
    else:
        print('Prescribed Function "' + functionName + '" not known. Skipping Setup!')

    print("\nRunning Setup Function... finished!\n")


def setup_01(data, solver):
    # Set physics
    physics_01(solver)
    # Materials
    material_01(data, solver)
    # Set Boundaries
    boundary_01(data, solver)

    # Do some Mesh Checks
    solver.mesh.check()
    solver.mesh.quality()

    return


def material_01(data, solver):
    solver.setup.materials.fluid.rename("air-cfx", "air")
    solver.setup.materials.fluid["air-cfx"] = {
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

    # Boundary Conditions
    solver.setup.general.operating_conditions.operating_pressure = "BC_pref"

    return


def physics_01(solver):
    solver.setup.models.energy = {"enabled": True, "viscous_dissipation": True}
    return


def boundary_01(data, solver):
    # Enable Turbo Models
    solver.tui.define.turbo_model.enable_turbo_model("yes")

    # Get rotation axis info: default is z-axis
    rot_ax_dir = data.get("rotation_axis_direction", [0.0, 0.0, 1.0])
    rot_ax_orig = data.get("rotation_axis_origin", [0.0, 0.0, 0.0])

    # Do important steps at startup in specified order
    # 1. Fluid cell zone conditions
    cz_rot_list = data["locations"].get("cz_rotating_names")
    for cz_name in solver.setup.cell_zone_conditions.fluid():
        # Check if it´s a rotating cell-zone
        if (cz_rot_list is not None) and (cz_name in cz_rot_list):
            print(f"Prescribing rotating cell zone: {cz_name}")
            solver.setup.cell_zone_conditions.fluid[cz_name] = {
                "reference_frame_axis_origin": rot_ax_orig,
                "reference_frame_axis_direction": rot_ax_dir,
                "mrf_motion": True,
                "mrf_omega": "BC_RPM",
            }
        # otherwise its stationary
        else:
            print(f"Prescribing stationary cell zone: {cz_name}")
            solver.setup.cell_zone_conditions.fluid[cz_name] = {
                "reference_frame_axis_origin": rot_ax_orig,
                "reference_frame_axis_direction": rot_ax_dir,
            }

    # 2. Search for periodic interfaces
    peri_if_El = data["locations"].get("bz_interfaces_periodic_names")
    if peri_if_El is not None:
        for key_if in peri_if_El:
            print(f"Setting up periodic BC: {key_if}")
            side1 = peri_if_El[key_if].get("side1")
            side2 = peri_if_El[key_if].get("side2")
            solver.tui.mesh.modify_zones.create_periodic_interface(
                "auto", key_if, side1, side2, "yes", "no", "no", "yes", "yes"
            )

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
                    print(f"Prescribing a Massflow-Inlet BC @{inletName}")
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[inletName], new_type="mass-flow-inlet"
                    )
                    inBC = solver.setup.boundary_conditions.mass_flow_inlet[inletName]
                    inBC.flow_spec = "Mass Flow Rate"
                    inBC.mass_flow = "BC_IN_MassFlow"
                    inBC.gauge_pressure = "BC_IN_p_gauge"
                    inBC.direction_spec = "Normal to Boundary"
                    inBC.t0 = "BC_IN_Tt"

                elif data["expressions"].get("BC_IN_pt") is not None:
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[inletName], new_type="pressure-inlet"
                    )
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
                        inBC.t0 = {
                            "option": "profile",
                            "profile_name": "inlet-bc",
                            "field_name": "tt-in",
                        }
                    else:
                        inBC.gauge_total_pressure = "BC_IN_pt"
                        inBC.gauge_pressure = "BC_IN_p_gauge"
                        inBC.direction_spec = "Normal to Boundary"
                        inBC.t0 = "BC_IN_Tt"

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
                    print(
                        f"Prescribing a Exit-Corrected Massflow-Outlet BC @{outletName}"
                    )
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[outletName], new_type="mass-flow-outlet"
                    )
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
                    print(f"Prescribing a Massflow-Outlet BC @{outletName}")
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[outletName], new_type="mass-flow-outlet"
                    )
                    outBC = solver.setup.boundary_conditions.mass_flow_outlet[
                        outletName
                    ]
                    outBC.flow_spec = "Mass Flow Rate"
                    outBC.mass_flow = "BC_OUT_MassFlow"

                elif data["expressions"].get("BC_OUT_p") is not None:
                    print(f"Prescribing a Pressure-Outlet BC @{outletName}")
                    solver.setup.boundary_conditions.change_type(
                        zone_list=[outletName], new_type="pressure-outlet"
                    )
                    outBC = solver.setup.boundary_conditions.pressure_outlet[outletName]
                    # Check Profile data exists
                    profileName = data.get("profileName_Out")
                    useProfileData = (profileName is not None) and (profileName != "")
                    outBC.prevent_reverse_flow = True
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
                    outBC.avg_press_spec = True
                    # Set additional pressure-outlet-bc settings if available in config file
                    try:
                        p_pbf = data["setup"]["BC_OUT_p_pbf"]
                        p_numbins = data["setup"]["BC_OUT_p_numbins"]
                        solver.tui.define.boundary_conditions.bc_settings.pressure_outlet(
                            p_pbf, p_numbins
                        )
                    except KeyError as e:
                        print(
                            f"KeyError: Key not found in ConfigFile: {str(e)} \nAdditional pressure-outlet-bc settings skipped!"
                        )

            # Walls
        # elif key == "bz_walls_shroud_names":
        #    solver.setup.boundary_conditions.wall[data["locations"][key]] = {"motion_bc": "Moving Wall","relative": False,"rotating": True}

        elif key == "bz_walls_counterrotating_names":
            keyEl = data["locations"].get(key)
            for key_cr in keyEl:
                print(f"Prescribing a counter-rotating wall: {key_cr}")
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
                print(f"Prescribing a rotating wall: {key_r}")
                solver.setup.boundary_conditions.wall[key_r] = {
                    "motion_bc": "Moving Wall",
                    "relative": False,
                    "rotating": True,
                    "omega": "BC_RPM",
                    "rotation_axis_origin": rot_ax_orig,
                    "rotation_axis_direction": rot_ax_dir,
                }

        elif key == "bz_walls_freeslip_names":
            keyEl = data["locations"].get(key)
            for key_free in keyEl:
                print(f"Prescribing a free slip wall: {key_free}")
                solver.setup.boundary_conditions.wall[key_free] = {
                    "shear_bc": "Specified Shear"
                }

        # Interfaces
        elif key == "bz_interfaces_general_names":
            solver.tui.define.mesh_interfaces.one_to_one_pairing("no")
            keyEl = data["locations"].get(key)
            for key_if in keyEl:
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
            side1 = keyEl[key_if].get("side1")
            side2 = keyEl[key_if].get("side2")
            solver.tui.define.turbo_model.turbo_create(
                key_if, side1, "()", side2, "()", "2"
            )

    # setup turbo topology
    keyEl = data["locations"].get("tz_turbo_topology_names")
    if keyEl is not None:
        print("Setting up turbo topology for post processing.\n")
        for key_topo in keyEl:
            turbo_name = f'"{key_topo}"'
            hub_names = keyEl[key_topo].get("tz_hub_names")
            shroud_names = keyEl[key_topo].get("tz_shroud_names")
            inlet_names = keyEl[key_topo].get("tz_inlet_names")
            outlet_names = keyEl[key_topo].get("tz_outlet_names")
            blade_names = keyEl[key_topo].get("tz_blade_names")
            periodic_names = keyEl[key_topo].get("tz_theta_periodic_names")
            try:
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
                print(f"An error occurred while defining topology: {e}")

    return


def report_01(data, solver):
    # Reports
    for report in data["solution"]["reportlist"]:
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
    for report in data["solution"]["reportlist"]:
        reportName = report.replace("_", "-")
        reportName = "rep-" + reportName.lower()
        reportNameList.append(reportName)
    solver.solution.monitor.report_files["report-file"] = {
        "file_name": "./report.out",
        "report_defs": reportNameList,
    }

    # Set Residuals
    # solver.tui.preferences.simulation.local_residual_scaling("yes")
    solver.tui.solve.monitors.residual.scale_by_coefficient("yes", "yes", "yes")

    solver.tui.solve.monitors.residual.convergence_criteria(
        data["solution"]["cov_crit"],
        data["solution"]["cov_crit"],
        data["solution"]["cov_crit"],
        data["solution"]["cov_crit"],
        data["solution"]["cov_crit"],
        data["solution"]["cov_crit"],
        data["solution"]["cov_crit"],
    )

    # Set CoVs
    for solve_cov in data["solution"]["cov_list"]:
        reportName = solve_cov.replace("_", "-")
        reportName = "rep-" + reportName.lower()
        covName = reportName + "-cov"
        solver.solution.monitor.convergence_conditions.convergence_reports[covName] = {}
        solver.solution.monitor.convergence_conditions = {
            "convergence_reports": {
                covName: {
                    "report_defs": reportName,
                    "cov": True,
                    "previous_values_to_consider": 50,
                    "stop_criterion": data["solution"]["cov_crit"],
                    "print": True,
                    "plot": True,
                }
            }
        }

    # Set Convergence Conditions
    solver.solution.monitor.convergence_conditions = {
        # "condition": "any-condition-is-met",
        "condition": "all-conditions-are-met",
        "frequency": 5,
    }
    # Set Basic Solver-Solution-Settings
    tsf = data["solution"].get("time_step_factor", 1)
    # Check for a pseudo-time-step-size
    pseudo_timestep = data["solution"].get("pseudo_timestep")
    if pseudo_timestep is not None:
        # Use pseudo timestep
        print(
            f"Direct Specification of pseudo timestep size from Configfile: {pseudo_timestep}"
        )
        solver.solution.run_calculation.pseudo_time_settings.time_step_method.time_step_method = (
            "user-specified"
        )
        solver.solution.run_calculation.pseudo_time_settings.time_step_method.pseudo_time_step_size = (
            pseudo_timestep
        )
        # Update dict
        if data["solution"].get("time_step_factor") is not None:
            data["solution"].pop("time_step_factor")
    else:
        # Use timescale factor
        print(
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
        data["solution"]["time_step_factor"] = tsf

    iter_count = data["solution"].get("iter_count", 500)
    # Update dict
    data["solution"]["iter_count"] = iter_count
    solver.solution.run_calculation.iter_count = int(iter_count)
