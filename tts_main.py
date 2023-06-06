import os
import json
import sys

# Load Script Modules
from tts_subroutines import (
    numerics,
    parametricstudy,
    solve,
    meshimport,
    setupcfd,
    utilities,
    postproc,
)

version = "1.3.1"

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
print("Opening ConfigFile: " + os.path.abspath(json_filename))
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
        caseFunctionEl = utilities.merge_functionEls(caseEl=caseEl, glfunctionEl=glfunctionEl)
        # Copy data from reference if refCase is set
        if caseEl.get("refCase") is not None:
            caseEl = utilities.merge_data_with_refEl(caseEl=caseEl, allCasesEl=caseDict)

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
        setupcfd.setup(data=caseEl, solver=solver, functionEl=caseFunctionEl)
        setupcfd.report_01(caseEl, solver)

        # Solution
        # Set Solver Settings
        numerics.numerics(data=caseEl, solver=solver, functionEl=caseFunctionEl)

        # Initialization
        solve.init(data=caseEl, solver=solver, functionEl=caseFunctionEl)

        # Write case and ini-data & settings file
        print("Writing initial case file\n")
        solver.file.write(file_type="case", file_name=caseEl["caseFilename"])
        settingsFilename = '"' + caseEl["caseFilename"] + '.set"'
        solver.tui.file.write_settings(settingsFilename)
        if solver.field_data.is_data_valid():
            print("Writing initial dat file\n")
            solver.file.write(file_type="dat", file_name=caseEl["caseFilename"])
        else:
            print("Skipping Writing of Initial Solution Data: No Solution Data available\n")

        # Solve
        if caseEl["solution"]["runSolver"]:
            solve.solve_01(caseEl, solver)

            filename = caseEl["caseFilename"] + "_fin"
            solver.file.write(file_type="case-data", file_name=filename)

        # Postprocessing
        if solver.field_data.is_data_valid():
            postproc.post(data=caseEl, solver=solver, functionEl=caseFunctionEl)
        else:
            print("Skipping Postprocessing: No Solution Data available\n")

        # Finalize
        solver.file.stop_transcript()

# Do Studies
studyDict = turboData.get("studies")

if studyDict is not None:
    parametricstudy.study(data=turboData, solver=solver, functionEl=glfunctionEl)

    # Postprocessing of studies
    if launchEl.get("plotResults") and external:
        parametricstudy.studyPlot(data=turboData)

# Exit Solver
solverExit = launchEl.get("exitatend", False)
if solverExit:
    solver.exit()

print("Script successfully finished! \n")