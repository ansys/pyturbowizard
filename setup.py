def setup_01(myLaunch, caseEl):
    expressionFilename = myLaunch.get("workingDir") + "\\" + caseEl.get("expressionFilename")
    solver.setup.models.energy = {"enabled" : True, "viscous_dissipation": True}

    #Materials
    solver.setup.materials.fluid.rename("air-cfx", "air")
    solver.setup.materials.fluid['air-cfx'] = {"density" : {"option" : "ideal-gas"}, "specific_heat" : {"option" : "constant", "value" : 1004.4}, "thermal_conductivity" : {"option" : "constant", "value" : 0.0261}, "viscosity" : {"option" : "constant", "value" : 1.831e-05}, "molecular_weight" : {"option" : "constant", "value" : 28.96}}

    #Adjust Fluent Expressions & Load File
    expressionEl = caseEl.get("expressions")
    utilities.writeExpressionFile(locationEl=locationsEl, expressionEl=expressionEl, templateName=caseEl.get("expressionTemplate"), fileName=expressionFilename)
    solver.tui.define.named_expressions.import_from_tsv(expressionFilename)

    #Cell Zone Conditions
    solver.setup.cell_zone_conditions.fluid[cz_name] = {"mrf_motion": True, "mrf_omega": "BC_RPM"}

    #Boundary Conditions
    solver.setup.general.operating_conditions.operating_pressure = "BC_Pref"

    #Interfaces
    for peri_interface in bz_interfaces_periodic_names:
        solver.tui.mesh.modify_zones.make_periodic(peri_interface, bz_interfaces_periodic_names.get(peri_interface), 'yes', 'yes')
        #solver.tui.mesh.modify_zones.create_periodic_interface("non-conformal", "myper", "b-rotor-1-periodic-side-1",
         #                                                      "b-rotor-1-periodic-side-2", "yes", "no", "no", "yes ", "yes" )
    #BC Profiles
    solver.file.read_profile(file_name = caseEl.get("profileName"))

    #Inlet
    solver.tui.define.boundary_conditions.modify_zones.zone_type(bz_inlet_name, 'pressure-inlet')
    solver.setup.boundary_conditions.pressure_inlet[bz_inlet_name] = {"gauge_total_pressure" : {"option" : "profile", "profile_name" : "inlet-bc", "field_name" : "pt-in"}, "gauge_pressure" : "BC_P_In_gauge", "t0" : {"option" : "profile", "profile_name" : "inlet-bc", "field_name" : "tt-in"}, "direction_spec" : "Direction Vector", "coordinate_system" : "Cylindrical (Radial, Tangential, Axial)", "flow_direction" : [{"field_name" : "vrad-dir", "profile_name" : "inlet-bc", "option" : "profile"}, {"field_name" : "vtang-dir", "profile_name" : "inlet-bc", "option" : "profile"}, {"field_name" : "vax-dir", "profile_name" : "inlet-bc", "option" : "profile"}]}

    #Outlet
    solver.setup.boundary_conditions.pressure_outlet[bz_outlet_name] = {"prevent_reverse_flow" : True}
    solver.setup.boundary_conditions.pressure_outlet[bz_outlet_name] = {"gauge_pressure" : "BC_P_Out", "avg_press_spec" : True}
    solver.tui.define.boundary_conditions.bc_settings.pressure_outlet(BC_pout_pbf, BC_pout_numbins)

    #Walls
    solver.setup.boundary_conditions.wall[bz_walls_shroud_name] = {"motion_bc" : "Moving Wall", "relative" : False, "rotating" : True}
    for bz_cr in bz_walls_counterrotating_names:
        solver.setup.boundary_conditions.wall[bz_cr] = {"motion_bc": "Moving Wall", "relative": False,
                                                                   "rotating": True,
                                                                    "omega": 0.,
                                                                   "rotation_axis_origin": [0., 0., 0.],
                                                                   "rotation_axis_direction": [0., 0., 1.]}

    for bz_free in bz_walls_freeslip_names:
        solver.setup.boundary_conditions.wall[bz_free] = {"shear_bc" : "Specified Shear"}

    return True