import os
import json
import sys

version = "1.2.1"

# If solver variable does not exist, Fluent has been started in external mode
external = 'solver' not in globals()
if external:
    import ansys.fluent.core as pyfluent

# Get scriptpath
scriptPath = os.path.dirname(sys.argv[0])

#Load Modules
from importlib.machinery import SourceFileLoader
utilities = SourceFileLoader("utilities", scriptPath + "./utilities.py").load_module()
meshimport = SourceFileLoader("meshimport", scriptPath + "./meshimport.py").load_module()
mysetup = SourceFileLoader("mysetup", scriptPath + "./mysetup.py").load_module()
numerics = SourceFileLoader("numerics", scriptPath + "./numerics.py").load_module()
postproc = SourceFileLoader("postproc", scriptPath + "./postproc.py").load_module()
solve = SourceFileLoader("solve", scriptPath + "./solve.py").load_module()
parametricstudy = SourceFileLoader(
    "parametricstudy", scriptPath + "./parametricstudy.py"
).load_module()

# Load Json File
# Suggest Config File in python working Dir
json_filename = "turboSetupConfig.json"
# If arguments are passed take first argument as fullpath to the json file
if len(sys.argv) > 1:
    json_filename = sys.argv[1]
json_file = open(json_filename)
turboData = json.load(json_file)

# Get important Elements from json file
functionEl = turboData.get("functions")
launchEl = turboData.get("launching")

# Use directory of jason-file if not specified in config-file
fl_workingDir = launchEl.get("workingDir", os.path.dirname(json_filename))
fl_workingDir = os.path.normpath(fl_workingDir)
# Reset working dir in dict
launchEl["workingDir"] = fl_workingDir
print("Used Fluent Working-Directory: " + fl_workingDir)

if external:  # Fluent without pyConsole
    global solver
    serverfilename = launchEl.get("serverfilename")
    # If no serverFilename is specified, a new session will be started
    if serverfilename is None or serverfilename == "":
        solver = pyfluent.launch_fluent(
            precision=launchEl["precision"],
            processor_count=int(launchEl["noCore"]),
            mode="solver",
            show_gui=True,
            product_version=launchEl["fl_version"],
            cwd=fl_workingDir,
        )
    # Hook to existing Session
    else:
        fullpathtosfname = fl_workingDir + "/" + serverfilename
        fullpathtosfname = os.path.normpath(fullpathtosfname)
        print("Connecting to Fluent Session...")
        solver = pyfluent.launch_fluent(
            start_instance=False, server_info_filepath=fullpathtosfname
        )


# Start Setup
caseDict = turboData.get("cases")
if caseDict is not None:
    for casename in caseDict:
        print("Running Case: " + casename + "\n")
        caseEl = turboData["cases"][casename]

        # Start Transcript
        trnFileName = casename + ".trn"
        solver.file.start_transcript(file_name=trnFileName)

        # Mesh import, expressions, profiles
        result = meshimport.import_01(caseEl, solver)

        utilities.writeExpressionFile(caseEl, fl_workingDir)
        solver.tui.define.named_expressions.import_from_tsv(
            caseEl["expressionFilename"]
        )

        # Enable Beta-Features
        solver.tui.define.beta_feature_access("yes ok")

        # Case Setup
        if (functionEl is None) or (functionEl.get("setup") is None):
            mysetup.setup(data=caseEl, solver=solver)
        else:
            mysetup.setup(data=caseEl, solver=solver, functionName=functionEl["setup"])
        mysetup.report_01(caseEl, solver)

        # Solution
        # Set Solver Settings
        if (functionEl is None) or (functionEl.get("numerics") is None):
            numerics.numerics(data=caseEl, solver=solver)
        else:
            numerics.numerics(
                data=caseEl, solver=solver, functionName=functionEl["numerics"]
            )

        # Initialization
        solve.init_01(caseEl, solver)

        # Write case and ini-data & settings file
        solver.file.write(file_type="case-data", file_name=caseEl["caseFilename"])
        settingsFilename = '"' + caseEl["caseFilename"] + '.set"'
        solver.tui.file.write_settings(settingsFilename)

        # Solve
        if caseEl["solution"]["runSolver"]:
            solve.solve_01(caseEl, solver)

            filename = caseEl["caseFilename"] + "_fin"
            solver.file.write(file_type="case-data", file_name=filename)

        # Postprocessing
        if (functionEl is None) or (functionEl.get("postproc") is None):
            postproc.post(data=caseEl, solver=solver)
        else:
            postproc.post(
                data=caseEl, solver=solver, functionName=functionEl["postproc"]
            )

        # Finalize
        solver.file.stop_transcript()

# Do Studies
studyDict = turboData.get("studies")

if studyDict is not None:
    if (functionEl is None) or (functionEl.get("parametricstudy") is None):
        parametricstudy.study(data=turboData, solver=solver)
    else:
        parametricstudy.study(
            data=turboData,
            solver=solver,
            functionName=functionEl["parametricstudy"],
        )
    # Postprocessing of studies
    if launchEl.get("plotResults"):
        parametricstudy.studyPlot(data=turboData)

# Exit Solver
solverExit = launchEl.get("exitatend", False)
if solverExit:
    solver.exit()

print("Script successfully finished! \n")
