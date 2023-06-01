import os
import json
import sys

# Load Script Modules
import utilities
import meshimport
import mysetup
import numerics
import postproc
import solve
import parametricstudy

version = "1.2.5"

# If solver variable does not exist, Fluent has been started in external mode
external = "solver" not in globals()

# Get scriptpath
scriptPath = os.path.dirname(sys.argv[0])

# Load Json File
# Suggest Config File in python working Dir
json_filename = "turboSetupConfig.json"
# If arguments are passed take first argument as fullpath to the json file
if len(sys.argv) > 1:
    json_filename = sys.argv[1]
json_filename = os.path.normpath(json_filename)
print("Opening ConfigFile: " + json_filename)
json_file = open(json_filename)
turboData = json.load(json_file)

# Get important Elements from json file
launchEl = turboData.get("launching")
glfunctionEl = turboData.get("functions")

# Use directory of jason-file if not specified in config-file
fl_workingDir = launchEl.get("workingDir", os.path.dirname(json_filename))
fl_workingDir = os.path.normpath(fl_workingDir)
# Reset working dir in dict
launchEl["workingDir"] = fl_workingDir
print("Used Fluent Working-Directory: " + fl_workingDir)

if external:
    import ansys.fluent.core as pyfluent

    # Fluent starts externally
    print("Launching Fluent...")
    solver = utilities.launchFluent(launchEl)

# Start Setup
caseDict = turboData.get("cases")
if caseDict is not None:
    for casename in caseDict:
        print("Running Case: " + casename + "\n")
        caseEl = turboData["cases"][casename]
        # Merge function dicts
        caseFunctionEl = caseEl.get("functions")
        if glfunctionEl is not None and caseFunctionEl is not None:
            helpDict = glfunctionEl.copy()
            helpDict.update(caseFunctionEl)
            caseFunctionEl = helpDict
        elif caseFunctionEl is None:
            caseFunctionEl = glfunctionEl

        # Start Transcript
        trnFileName = casename + ".trn"
        solver.file.start_transcript(file_name=trnFileName)

        # Mesh import, expressions, profiles
        result = meshimport.import_01(caseEl, solver)

        utilities.writeExpressionFile(
            data=caseEl, script_dir=scriptPath, working_dir=fl_workingDir
        )
        solver.tui.define.named_expressions.import_from_tsv(
            caseEl["expressionFilename"]
        )

        # Enable Beta-Features
        solver.tui.define.beta_feature_access("yes ok")

        # Case Setup
        mysetup.setup(data=caseEl, solver=solver, functionEl=caseFunctionEl)
        mysetup.report_01(caseEl, solver)

        # Solution
        # Set Solver Settings
        numerics.numerics(data=caseEl, solver=solver, functionEl=caseFunctionEl)

        # Initialization
        solve.init(data=caseEl, solver=solver, functionEl=caseFunctionEl)

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
        postproc.post(data=caseEl, solver=solver, functionEl=caseFunctionEl)

        # Finalize
        solver.file.stop_transcript()

# Do Studies
studyDict = turboData.get("studies")

if studyDict is not None:
    parametricstudy.study(data=turboData, solver=solver, functionEl=glfunctionEl)

    # Postprocessing of studies
    if launchEl.get("plotResults"):
        parametricstudy.studyPlot(data=turboData)

# Exit Solver
solverExit = launchEl.get("exitatend", False)
if solverExit:
    solver.exit()

print("Script successfully finished! \n")
