import os
def setup_01(data, solver):
    # Set physics
    physics_01(solver)
    # Materials
    material_01(data, solver)
    # Set Boundaries
    boundary_01(data, solver)

    #Do some Mesh Checks
    solver.mesh.check()
    solver.mesh.quality()

    return

def material_01(data, solver):
    solver.setup.materials.fluid.rename("air-cfx", "air")
    solver.setup.materials.fluid['air-cfx'] = {"density": {"option": data["fluid_properties"]["fl_density"]},
                                               "specific_heat": {"option": "constant", "value": data["fluid_properties"]["fl_specific_heat"]},
                                               "thermal_conductivity": {"option": "constant", "value": data["fluid_properties"]["fl_thermal_conductivity"]},
                                               "viscosity": {"option": "constant", "value": data["fluid_properties"]["fl_viscosity"]},
                                               "molecular_weight": {"option": "constant", "value": data["fluid_properties"]["fl_mol_wight"]}}

    # Boundary Conditions
    solver.setup.general.operating_conditions.operating_pressure = "BC_Pref"

    return


def physics_01(solver):
    solver.setup.models.energy = {"enabled": True, "viscous_dissipation": True}
    return


def boundary_01(data, solver):
    #Enable Turbo Models
    solver.tui.define.turbo_model.enable_turbo_model('yes')

    for key in data["locations"]:
        # Cell Zone Conditions
        if key == "cz_rotating_names":
            solver.setup.cell_zone_conditions.fluid[data["locations"][key]] = {"mrf_motion": True, "mrf_omega": "BC_RPM"}
        # Inlet
        elif key == "bz_inlet_name":
            inletName = data["locations"].get(key)
            inBC = None
            profileName = data.get("profileName_In")
            useProfileData = (profileName is not None) and (profileName != "")
            if data["expressions"].get("BC_MassFlow_In") is not None:
                print("Prescribing a Massflow-Inlet BC @" + inletName)
                solver.setup.boundary_conditions.change_type(zone_list=[inletName], new_type="mass-flow-inlet")
                inBC = solver.setup.boundary_conditions.mass_flow_inlet[inletName]
                inBC.flow_spec = "Mass Flow Rate"
                inBC.mass_flow = "BC_MassFlow_In"
                inBC.gauge_pressure = "BC_P_In_gauge"
                inBC.direction_spec = "Normal to Boundary"
                inBC.t0 = "BC_Tt_In"

            elif data["expressions"].get("BC_Pt_In") is not None:
                solver.setup.boundary_conditions.change_type(zone_list=[inletName], new_type="pressure-inlet")
                inBC = solver.setup.boundary_conditions.pressure_inlet[inletName]

                if useProfileData:
                    # Use profile data: total pressure boundary condition
                    # check profile naming convention:
                    # total pressure: pt-in,
                    # total temp: tt-in
                    inBC.gauge_total_pressure = {"option": "profile", "profile_name": "inlet-bc",
                                                 "field_name": "pt-in"}
                    inBC.gauge_pressure = "BC_P_In_gauge"
                    inBC.t0 = {"option": "profile", "profile_name": "inlet-bc", "field_name": "tt-in"}
                else:
                    inBC.gauge_total_pressure = "BC_Pt_In"
                    inBC.gauge_pressure = "BC_P_In_gauge"
                    inBC.direction_spec = "Normal to Boundary"
                    inBC.t0 = "BC_Tt_In"

            #Do some general settings
            if inBC is not None:
                #Turbulent Settings
                inBC.turb_intensity = "BC_TuIn_In"
                inBC.turb_viscosity_ratio = "BC_TuVR_In"

                #If Expressions for a direction are specified
                if (data["expressions"].get("BC_radDir_In") is not None) and \
                   (data["expressions"].get("BC_tangDir_In") is not None) and \
                   (data["expressions"].get("BC_axDir_In") is not None):
                    inBC.direction_spec = "Direction Vector"
                    inBC.coordinate_system = "Cylindrical (Radial, Tangential, Axial)"
                    inBC.flow_direction = ["BC_radDir_In", "BC_tangDir_In", "BC_axDir_In"]

                #Use Definitions from Profile-Data if sepcified
                # check profile naming convention:
                # directions (cylindrical): vrad-dir,vrad-dir,vax-dir
                if useProfileData:
                    inBC.direction_spec = "Direction Vector"
                    inBC.coordinate_system = "Cylindrical (Radial, Tangential, Axial)"
                    inBC.flow_direction = [{"field_name": "vrad-dir", "profile_name": "inlet-bc", "option": "profile"},
                                           {"field_name": "vtang-dir", "profile_name": "inlet-bc", "option": "profile"},
                                           {"field_name": "vax-dir", "profile_name": "inlet-bc", "option": "profile"}]


        # Outlet
        elif key == "bz_outlet_name":
            outletName = data["locations"][key]
            if data["expressions"].get("BC_ECMassFlow_Out") is not None:
                print("Prescribing a Exit-Corrected-Massflow-Outlet BC @" + outletName)
                solver.setup.boundary_conditions.change_type(zone_list=[outletName], new_type="mass-flow-outlet")
                outBC = solver.setup.boundary_conditions.mass_flow_outlet[outletName]
                outBC.flow_spec = "Exit Corrected Mass Flow Rate"
                outBC.ec_mass_flow = "BC_ECMassFlow_Out"
                outBC.pref = "BC_ECMassFlow_pref"
                outBC.tref = "BC_ECMassFlow_tref"

            elif data["expressions"].get("BC_MassFlow_Out") is not None:
                print("Prescribing a Massflow-Outlet BC @" + outletName)
                solver.setup.boundary_conditions.change_type(zone_list=[outletName], new_type="mass-flow-outlet")
                outBC = solver.setup.boundary_conditions.mass_flow_outlet[outletName]
                outBC.flow_spec = "Mass Flow Rate"
                outBC.mass_flow = "BC_MassFlow_Out"

            elif data["expressions"].get("BC_P_Out") is not None:
                print("Prescribing a Pressure-Outlet BC @" + outletName)
                solver.setup.boundary_conditions.change_type(zone_list=[outletName], new_type="pressure-outlet")
                outBC = solver.setup.boundary_conditions.pressure_outlet[outletName]
                outBC.prevent_reverse_flow = True
                outBC.gauge_pressure = "BC_P_Out"
                outBC.avg_press_spec = True
                solver.tui.define.boundary_conditions.bc_settings.pressure_outlet(data["setup"]["BC_pout_pbf"],
                                                                              data["setup"]["BC_pout_numbins"])

            # Walls
        #elif key == "bz_walls_shroud_name":
        #    solver.setup.boundary_conditions.wall[data["locations"][key]] = {"motion_bc": "Moving Wall","relative": False,"rotating": True}

        elif key == "bz_walls_counterrotating_names":
            for bz_cr in data["locations"][key]:
                solver.setup.boundary_conditions.wall[bz_cr] = {"motion_bc": "Moving Wall", "relative": False,
                                                                "rotating": True,
                                                                "omega": 0.,
                                                                "rotation_axis_origin": [0., 0., 0.],
                                                                "rotation_axis_direction": [0., 0., 1.]}
        elif key == "bz_walls_rotating_names":
            for bz_cr in data["locations"][key]:
                solver.setup.boundary_conditions.wall[bz_cr] = {"motion_bc": "Moving Wall", "relative": False,
                                                                "rotating": True,
                                                                "omega": "BC_RPM",
                                                                "rotation_axis_origin": [0., 0., 0.],
                                                                "rotation_axis_direction": [0., 0., 1.]}

        elif key == "bz_walls_freeslip_names":
            for bz_free in data["locations"][key]:
                solver.setup.boundary_conditions.wall[bz_free] = {"shear_bc": "Specified Shear"}

        # Interfaces
        elif key == "bz_interfaces_periodic_names":
            keyEl = data["locations"].get(key)
            for key_if in keyEl:
                side1 = keyEl[key_if].get("side1")
                side2 = keyEl[key_if].get("side2")
                solver.tui.mesh.modify_zones.create_periodic_interface('auto', key_if, side1, side2, 'yes', 'no', 'no',
                                                                       'yes', 'yes')
                #old command
                #solver.tui.mesh.modify_zones.make_periodic(side1, side2,'yes', 'yes')

        elif key == "bz_interfaces_general_names":
            solver.tui.define.mesh_interfaces.one_to_one_pairing('no')
            keyEl = data["locations"].get(key)
            for key_if in keyEl:
                side1 = keyEl[key_if].get("side1")
                side2 = keyEl[key_if].get("side2")
                #solver.tui.define.mesh_interfaces.create(key_if, side1, '()', side2,'()', 'no', 'no', 'no', 'yes', 'no')
                solver.tui.define.turbo_model.turbo_create(key_if, side1, '()', side2, '()', '3')

    #Setup turbo-interfaces at end
    keyEl = data["locations"].get("bz_interfaces_mixingplane_names")
    if keyEl is not None:
        for key_if in keyEl:
            side1 = keyEl[key_if].get("side1")
            side2 = keyEl[key_if].get("side2")
            solver.tui.define.turbo_model.turbo_create(key_if, side1, '()', side2, '()', '2')

    return

def report_01(data, solver):
     #Reports
    for report in data["solution"]["reportlist"]:
        reportName = report.replace("_", "-")
        reportName = "rep-" + reportName.lower()
        solver.solution.report_definitions.single_val_expression[reportName] = {}
        solver.solution.report_definitions.single_val_expression[reportName] = {"define": report}
        reportPlotName = reportName + "-plot"
        solver.solution.monitor.report_plots[reportPlotName] = {}
        solver.solution.monitor.report_plots[reportPlotName] = {"report_defs": [reportName]}

      #Report File
    solver.solution.monitor.report_files["report-file"] = {}
    reportNameList = []
    for report in data["solution"]["reportlist"]:
        reportName = report.replace("_", "-")
        reportName = "rep-" + reportName.lower()
        reportNameList.append(reportName)
    solver.solution.monitor.report_files['report-file'] = {"file_name" : "./report_0.6M.out", "report_defs" : reportNameList}

      #Set Residuals
    solver.tui.preferences.simulation.local_residual_scaling('no')
    solver.tui.solve.monitors.residual.convergence_criteria(data["solution"]["cov_crit"], data["solution"]["cov_crit"],
                                                            data["solution"]["cov_crit"], data["solution"]["cov_crit"],
                                                            data["solution"]["cov_crit"], data["solution"]["cov_crit"], data["solution"]["cov_crit"])

      #Set CoVs
    for solve_cov in data["solution"]["cov_list"]:
        reportName = solve_cov.replace("_", "-")
        reportName = "rep-" + reportName.lower()
        covName = reportName + "-cov"
        solver.solution.monitor.convergence_conditions.convergence_reports[covName] = {}
        solver.solution.monitor.convergence_conditions = {"convergence_reports": {covName : {"report_defs" : reportName, "cov" : True, "previous_values_to_consider" : 50, "stop_criterion" : data["solution"]["cov_crit"], "print" : True, "plot" : True}}}

    #Set Convergence Conditions
    solver.solution.monitor.convergence_conditions = {"condition": "any-condition-is-met"}
