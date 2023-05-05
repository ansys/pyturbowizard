# TurboTest


external = True
import os
import json

if external:
    import utilities
    import mesh_import
    import numerics
    import setup
    import solve
    import postproc

if external:
    import ansys.fluent.core as pyfluent
    #import utilities import writeExpressionFile

else:
    from importlib.machinery import SourceFileLoader
    utilities = SourceFileLoader("utilities", "./utilities.py").load_module()
    utilities = SourceFileLoader("mesh_import", "./mesh_import.py").load_module()
    utilities = SourceFileLoader("numerics", "./numerics.py").load_module()
    utilities = SourceFileLoader("setup", "./setup.py").load_module()
    utilities = SourceFileLoader("solve", "./solve.py").load_module()
    utilities = SourceFileLoader("postproc", "./postproc.py").load_module()


######################################################################################################################
#### Start up Fluent #################################################################################################
######################################################################################################################
json_file = open('turboSetupConfig.json')
turboData = json.load(json_file)

if not external:    # pyConsole in Fluent
    try:
        import ansys.fluent.core as pyfluent
        flglobals = pyfluent.setup_for_fluent(product_version=turboData["launching"]["fl_version"],
                                              mode="solver", version="3d", precision = turboData["launching"]["precision"],
                                              processor_count=int(turboData["launching"]["noCore"]))
        globals().update(flglobals)
    except Exception:
        pass



# solver.tui.define.parameters.input_parameters.edit('"BC_Pout"', '"BC_Pout"', '50000')


if external:    # Fluent without pyConsole
    solver = pyfluent.launch_fluent(precision=turboData["launching"]["precision"], processor_count=int(turboData["launching"]["noCore"]),
                                    mode="solver", show_gui=True,
                                   product_version = turboData["launching"]["fl_version"], cwd=turboData["launching"]["workingDir"])


for caseEl in turboData["cases"]:

    print("Running Case: " + caseEl + "\n")
    trnFileName = caseEl + ".trn"

    solver.file.start_transcript(file_name=trnFileName)

    #Mesh import
    result = import_01(turboData["caseEl"])

    #Enable Beta-Features
    if not external:
        solver.tui.define.beta_feature_access("ok yes")
    else:
        #solver.tui.define.beta_feature_access("yes", '"ok"')
        solver.scheme_eval.exec(('(ti-menu-load-string (format #f "~%/define/beta-feature-access yes ok"))',))

    # Setup Stage
    results = setup_01(myLaunch, caseEl)
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
    solver.file.write(file_type = "case-data", file_name = caseEl.get("caseFilename"))
    settingsFilename = "\"" + caseEl.get("caseFilename") + ".set\""
    solver.tui.file.write_settings(settingsFilename)

        #Solve
    if runSolver:
        solver.solution.run_calculation.iterate(iter_count = iter_count)
        filename = caseEl.get("caseFilename") + "_fin"
        solver.file.write(file_type = "case-data", file_name = filename)

        #Postproc
    #filename = caseEl.get("caseFilename") + "_" + resultEl.get("filename_inputParameter_pf")
    #solver.tui.define.parameters.input_parameters.write_all_to_file('filename')
    #tuicommand = "define parameters input-parameters write-all-to-file \"" + filename + "\""
    #solver.execute_tui(tuicommand)
    filename = caseEl.get("caseFilename") + "_" + resultEl.get("filename_outputParameter_pf")
    #solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
    tuicommand = "define parameters output-parameters write-all-to-file \"" + filename + "\""
    solver.execute_tui(tuicommand)
    filename = caseEl.get("caseFilename") + "_" + resultEl.get("filename_summary_pf")
    solver.results.report.summary(write_to_file = True, file_name = filename)
    # Write out system time
    solver.report.system.time_statistics()

      #Finalize
    solver.file.stop_transcript()
    #solver.exit()
