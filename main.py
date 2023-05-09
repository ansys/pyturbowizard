# TurboTest


external = True
import os
import json


if external:
    import ansys.fluent.core as pyfluent
    #import utilities import writeExpressionFile
    import utilities
    import meshimport
    import mysetup
    import numerics
    import postproc
    import solve

else:
    from importlib.machinery import SourceFileLoader
    utilities = SourceFileLoader("utilities", "./utilities.py").load_module()
    meshimport = SourceFileLoader("meshimport", "./meshimport.py").load_module()
    mysetup = SourceFileLoader("mysetup", "./mysetup.py").load_module()
    numerics = SourceFileLoader("numerics", "./numerics.py").load_module()
    postproc = SourceFileLoader("postproc", "./postproc.py").load_module()
    solve = SourceFileLoader("solve", "./solve.py").load_module()


#pyfluent.set_log_level('DEBUG')
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

working_Dir = os.path.normpath(turboData["launching"]["workingDir"])

if external:    # Fluent without pyConsole
    global solver

    solver = pyfluent.launch_fluent(precision=turboData["launching"]["precision"], processor_count=int(turboData["launching"]["noCore"]),
                                    mode="solver", show_gui=True,
                                   product_version = turboData["launching"]["fl_version"], cwd=working_Dir)


# Start Setup
for caseEl in turboData["cases"]:
    print("Running Case: " + caseEl + "\n")
    trnFileName = caseEl + ".trn"

    solver.file.start_transcript(file_name=trnFileName)
    #


    # Mesh import, expressions, profiles
    result = meshimport.import_01(turboData["cases"][caseEl], solver)

    utilities.writeExpressionFile(turboData["cases"][caseEl],working_Dir)
    solver.tui.define.named_expressions.import_from_tsv(turboData["cases"][caseEl]["expressionFilename"])

    # Enable Beta-Features
    solver.tui.define.beta_feature_access("yes ok")


    # Case Setup
    mysetup.setup_01(turboData["cases"][caseEl], solver)

    mysetup.report_01(turboData["cases"][caseEl], solver)
    #Solution


       #Set Solver Settings
    numerics.numerics_01(turboData["cases"][caseEl], solver)
    #Activate Turbonumerics


        #Initialization
    solve.init_01(turboData["cases"][caseEl], solver)

    solver.file.write(file_type = "case-data", file_name = turboData["cases"][caseEl]["caseFilename"])
    settingsFilename = "\"" + turboData["cases"][caseEl]["caseFilename"] + ".set\""
    solver.tui.file.write_settings(settingsFilename)

        #Solve
    if turboData["cases"][caseEl]["solution"]["runSolver"]:
        solve.solve_01(data, solver)


        filename = turboData["cases"][caseEl]["caseFilename"] + "_fin"
        solver.file.write(file_type = "case-data", file_name = filename)

        filename = turboData["cases"][caseEl]["caseFilename"] + "_" + turboData["cases"][caseEl]["results"]["filename_outputParameter_pf"]
    #solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
        tuicommand = "define parameters output-parameters write-all-to-file \"" + filename + "\""
        solver.execute_tui(tuicommand)
        filename = caseFilename + "_" + turboData["cases"][caseEl]["results"]["filename_summary_pf"]
        solver.results.report.summary(write_to_file = True, file_name = filename)
        # Write out system time
        solver.report.system.time_statistics()

      #Finalize
    solver.file.stop_transcript()
    #solver.exit()
