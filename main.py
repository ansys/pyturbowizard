# TurboTest


external = True
import os
import json
if external:
    import ansys.fluent.core as pyfluent
    #import utilities import writeExpressionFile
    import utilities
else:
    from importlib.machinery import SourceFileLoader
    utilities = SourceFileLoader("utilities", "./utilities.py").load_module()

######################################################################################################################
#### Start up Fluent #################################################################################################
######################################################################################################################


if not external:    # pyConsole in Fluent
    try:
        import ansys.fluent.core as pyfluent
        flglobals = pyfluent.setup_for_fluent(product_version="23.2.0", mode="solver", version="3d", precision="double", processor_count=32)
        globals().update(flglobals)
    except Exception:
        pass


json_file = open('turboSetupConfig.json')
turboData = json.load(json_file)
# solver.tui.define.parameters.input_parameters.edit('"BC_Pout"', '"BC_Pout"', '50000')
caseList = turboData.get("cases")
myLaunch = turboData.get("launching")

if external:    # Fluent without pyConsole
    solver = pyfluent.launch_fluent(precision=myLaunch.get("precision"), processor_count=myLaunch.get("noCore"),
                                    mode="solver", show_gui=True,
                                   product_version=myLaunch.get("fl_version"), cwd=myLaunch.get("workingDir"))


for caseEl in caseList:
    #Getting all input data from jason file
    caseFilename = caseEl.get("caseFilename")
    meshFilename = caseEl.get("meshFilename")
    profileName = caseEl.get("profileName")
    expressionFilename = myLaunch.get("workingDir") + "\\" + caseEl.get("expressionFilename")
    expressionTemplate = caseEl.get("expressionTemplate")

       #Locations Names
    locationsEl = caseEl.get("locations")
    cz_name = locationsEl.get("cz_name")
    bz_inlet_name = locationsEl.get("bz_inlet_name")
    bz_outlet_name = locationsEl.get("bz_outlet_name")
    bz_walls_shroud_name = locationsEl.get("bz_walls_shroud_name")
    bz_walls_hub_name = locationsEl.get("bz_walls_hub_name")
    bz_walls_blade_name = locationsEl.get("bz_walls_blade_name")
    bz_walls_freeslip_names = locationsEl.get("bz_walls_freeslip_names")
    bz_interfaces_periodic_names = locationsEl.get("bz_interfaces_periodic_names")
    bz_walls_counterrotating_names = locationsEl.get("bz_walls_counterrotating_names")

    #Setup Node
    setupEl = caseEl.get("setup")
    # BCs
    BC_pout_pbf = setupEl.get("BC_pout_pbf")
    BC_pout_numbins = setupEl.get("BC_pout_numbins")

      #Solution Node
    solutionEl = caseEl.get("solution")
    # Reports -> add Fluent Expressions which should be used as report
    reportlist = solutionEl.get("reportlist")
    #Solver Criteria
    res_crit = solutionEl.get("res_crit")
    cov_list = solutionEl.get("cov_list")
    cov_crit = solutionEl.get("cov_crit")
    iter_count = solutionEl.get("iter_count")
    runSolver = solutionEl.get("runSolver")

    # Result Node
    resultEl = caseEl.get("results")

    print("Running Case: " + caseFilename + "\n")
    trnFileName = caseFilename + ".trn"



    solver.file.start_transcript(file_name=trnFileName)

    #Mesh import
    solver.file.import_.read(file_type = "cfx-definition", file_name = meshFilename)

    #Enable Beta-Features
    if not external:
        solver.tui.define.beta_feature_access("ok yes")
    else:
        #solver.tui.define.beta_feature_access("yes", '"ok"')
        solver.scheme_eval.exec(('(ti-menu-load-string (format #f "~%/define/beta-feature-access yes ok"))',))

    solver.setup.models.energy = {"enabled" : True, "viscous_dissipation": True}

    #Materials
    solver.setup.materials.fluid.rename("air-cfx", "air")
    solver.setup.materials.fluid['air-cfx'] = {"density" : {"option" : "ideal-gas"}, "specific_heat" : {"option" : "constant", "value" : 1004.4}, "thermal_conductivity" : {"option" : "constant", "value" : 0.0261}, "viscosity" : {"option" : "constant", "value" : 1.831e-05}, "molecular_weight" : {"option" : "constant", "value" : 28.96}}

    #Adjust Fluent Expressions & Load File
    expressionEl = caseEl.get("expressions")
    utilities.writeExpressionFile(locationEl=locationsEl, expressionEl=expressionEl, templateName=expressionTemplate, fileName=expressionFilename)
    solver.tui.define.named_expressions.import_from_tsv(expressionFilename)

    #Cell Zone Conditions
    solver.setup.cell_zone_conditions.fluid[cz_name] = {"mrf_motion": True, "mrf_omega": "BC_RPM"}

    #Boundary Conditions
    solver.setup.general.operating_conditions.operating_pressure = "BC_Pref"

    #Interfaces
    for peri_interface in bz_interfaces_periodic_names:
        solver.tui.mesh.modify_zones.make_periodic(peri_interface, bz_interfaces_periodic_names.get(peri_interface), 'yes', 'yes')

    #BC Profiles
    solver.file.read_profile(file_name = profileName)

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

    #Solution

      #Reports
    for report in reportlist:
        reportName = report.replace("_", "-")
        reportName = "rep-" + reportName.lower()
        solver.solution.report_definitions.single_val_expression[reportName] = {}
        solver.solution.report_definitions.single_val_expression[reportName] = {"define" : report}
        reportPlotName = reportName + "-plot"
        solver.solution.monitor.report_plots[reportPlotName] = {}
        solver.solution.monitor.report_plots[reportPlotName] = {"report_defs" : [reportName]}

      #Report File
    solver.solution.monitor.report_files["report-file"] = {}
    reportNameList = []
    for report in reportlist:
        reportName = report.replace("_", "-")
        reportName = "rep-" + reportName.lower()
        reportNameList.append(reportName)
    solver.solution.monitor.report_files['report-file'] = {"file_name" : "./report_0.6M.out", "report_defs" : reportNameList}

      #Set Residuals
    solver.tui.preferences.simulation.local_residual_scaling('no')
    solver.tui.solve.monitors.residual.convergence_criteria(res_crit, res_crit, res_crit, res_crit, res_crit, res_crit, res_crit)

      #Set CoVs
    for solve_cov in cov_list:
        reportName = solve_cov.replace("_", "-")
        reportName = "rep-" + reportName.lower()
        covName = reportName + "-cov"
        solver.solution.monitor.convergence_conditions.convergence_reports[covName] = {}
        solver.solution.monitor.convergence_conditions = {"convergence_reports" : {covName : {"report_defs" : reportName, "cov" : True, "previous_values_to_consider" : 50, "stop_criterion" : cov_crit, "print" : True, "plot" : True}}}

       #Set Convergence Conditions
    solver.solution.monitor.convergence_conditions = {"condition" : "any-condition-is-met"}

       #Set Solver Settings
    solver.solution.methods.gradient_scheme = "green-gauss-node-based"
    #Activate Turbonumerics
    if solutionEl.get("tsn"):
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable('yes')

        #Initialization
    solver.tui.solve.initialize.compute_defaults.pressure_inlet(bz_inlet_name)
    solver.solution.initialization.standard_initialize()
    solver.solution.initialization.fmg_initialize()
    solver.file.write(file_type = "case-data", file_name = caseFilename)
    settingsFilename = "\"" + caseFilename + ".set\""
    solver.tui.file.write_settings(settingsFilename)

        #Solve
    if runSolver:
        solver.solution.run_calculation.iterate(iter_count = iter_count)
        filename = caseFilename + "_fin"
        solver.file.write(file_type = "case-data", file_name = filename)

        #Postproc
    #filename = caseFilename + "_" + resultEl.get("filename_inputParameter_pf")
    #solver.tui.define.parameters.input_parameters.write_all_to_file('filename')
    #tuicommand = "define parameters input-parameters write-all-to-file \"" + filename + "\""
    #solver.execute_tui(tuicommand)
    filename = caseFilename + "_" + resultEl.get("filename_outputParameter_pf")
    #solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
    tuicommand = "define parameters output-parameters write-all-to-file \"" + filename + "\""
    solver.execute_tui(tuicommand)
    filename = caseFilename + "_" + resultEl.get("filename_summary_pf")
    solver.results.report.summary(write_to_file = True, file_name = filename)
    # Write out system time
    solver.report.system.time_statistics()

      #Finalize
    solver.file.stop_transcript()
    #solver.exit()
