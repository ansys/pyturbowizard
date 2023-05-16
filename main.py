# Test of Turbo-Workflow

import os
import json
import sys

json_filename = 'turboStudyConfig.json'
#If arguments are passed take first argument as path to the json file
if len(sys.argv) > 1:
    json_filename = sys.argv[1]

json_file = open(json_filename)
turboData = json.load(json_file)

functionEl = turboData.get("functions")
launchEl = turboData.get("launching")
external = launchEl.get("external")

if external:
    import ansys.fluent.core as pyfluent

    import utilities
    import meshimport
    import mysetup
    import numerics
    import postproc
    import solve
    import parametricstudy

else:
    from importlib.machinery import SourceFileLoader
    utilities = SourceFileLoader("utilities", "./utilities.py").load_module()
    meshimport = SourceFileLoader("meshimport", "./meshimport.py").load_module()
    mysetup = SourceFileLoader("mysetup", "./mysetup.py").load_module()
    numerics = SourceFileLoader("numerics", "./numerics.py").load_module()
    postproc = SourceFileLoader("postproc", "./postproc.py").load_module()
    solve = SourceFileLoader("solve", "./solve.py").load_module()
    parametricstudy = SourceFileLoader("parametricstudy", "./parametricstudy.py").load_module()


#pyfluent.set_log_level('DEBUG')
######################################################################################################################
#### Start up Fluent #################################################################################################
######################################################################################################################

if not external:    # pyConsole in Fluent
    try:
        import ansys.fluent.core as pyfluent
        flglobals = pyfluent.setup_for_fluent(product_version=launchEl["fl_version"],
                                              mode="solver", version="3d", precision = launchEl["precision"],
                                              processor_count=int(launchEl["noCore"]))
        globals().update(flglobals)
    except Exception:
        pass


#Use directory of jason-file if not specified in config-file
working_Dir = launchEl.get("workingDir", os.path.dirname(json_filename))
working_Dir = os.path.normpath(working_Dir)

if external:    # Fluent without pyConsole
    global solver
    serverfilename = launchEl.get("serverfilename")
    if serverfilename is None or serverfilename == "":
        solver = pyfluent.launch_fluent(precision=launchEl["precision"], processor_count=int(launchEl["noCore"]),
                                    mode="solver", show_gui=True,
                                   product_version = launchEl["fl_version"], cwd=working_Dir)
    #Hook to existing Session
    else:
        print("Connecting to Fluent Session...")
        solver = pyfluent.launch_fluent(start_instance=False,  server_info_filepath=serverfilename)


# Start Setup
caseDict = turboData.get("cases")
if caseDict is not None:
    for casename in caseDict:
        print("Running Case: " + casename + "\n")
        caseEl = turboData["cases"][casename]

        #Start Transcript
        trnFileName = casename + ".trn"
        solver.file.start_transcript(file_name=trnFileName)

        # Mesh import, expressions, profiles
        result = meshimport.import_01(caseEl, solver)

        utilities.writeExpressionFile(caseEl,working_Dir)
        solver.tui.define.named_expressions.import_from_tsv(caseEl["expressionFilename"])

        # Enable Beta-Features
        solver.tui.define.beta_feature_access("yes ok")

        # Case Setup
        mysetup.setup_01(caseEl, solver)
        mysetup.report_01(caseEl, solver)

        #Solution
           #Set Solver Settings
        if (functionEl is None) or (functionEl.get("numerics") is None):
            numerics.numerics(data=caseEl, solver=solver)
        else:
            numerics.numerics(data=caseEl, solver=solver, functionName=functionEl["numerics"])

        #Write case & settings file
        solver.file.write(file_type="case", file_name=caseEl["caseFilename"])
        settingsFilename = "\"" + caseEl["caseFilename"] + ".set\""
        solver.tui.file.write_settings(settingsFilename)

        #Initialization
        solve.init_01(caseEl, solver)
        #Write initial data
        solver.file.write(file_type="data", file_name=caseEl["caseFilename"])

        #Solve
        if caseEl["solution"]["runSolver"]:
            solve.solve_01(caseEl, solver)

            filename = caseEl["caseFilename"] + "_fin"
            solver.file.write(file_type = "case-data", file_name = filename)

        #Postprocessing
        if (functionEl is None) or (functionEl.get("postproc") is None):
            postproc.post(data=caseEl, solver=solver)
        else:
            postproc.post(data=caseEl, solver=solver,functionName=functionEl["postproc"])

        #Finalize
        solver.file.stop_transcript()

# Do Studies
studyDict = turboData.get("studies")

if studyDict is not None:
    if (functionEl is None) or (functionEl.get("parametricstudy") is None):
        parametricstudy.study(data=studyDict, solver=solver)
    else:
        parametricstudy.study(data=studyDict, solver=solver, functionName=functionEl["parametricstudy"])
    #Postprocessing of studies
    if turboData.get("plotResults"):
        parametricstudy.studyPlot(data=studyDict)

#Exit Solver
solverExit = launchEl.get("exitatend", False)
if solverExit:
    solver.exit()

print("Script successfully finished! \n")
