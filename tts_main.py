import os
import json
import sys

# Load Script Modules
from tts_subroutines import (
    launcher,
    numerics,
    parametricstudy,
    solve,
    meshimport,
    setupcfd,
    utilities,
    postproc,
)


version = "1.4.4"
print(f"\n*** Starting TurboTestSuite (Version {str(version)}) ***\n\n")

# If solver variable does not exist, Fluent has been started in external mode
external = "solver" not in globals()

# Get scriptpath
scriptPath = os.path.dirname(sys.argv[0])

# Load Json File
# Suggest Config File in python working Dir
config_filename = "turboSetupConfig_axial_turbine.json"
# If arguments are passed take first argument as fullpath to the json file
if len(sys.argv) > 1:
    config_filename = sys.argv[1]
config_filename = os.path.normpath(config_filename)
print("Opening ConfigFile: " + os.path.abspath(config_filename))
config_file = open(config_filename, "r")
turboData = dict()
# Load a yaml file if specified, otherwise json
if config_filename.endswith("yaml"):
    import yaml

    turboData = yaml.safe_load(config_file)
else:
    turboData = json.load(config_file)

# Get important Elements from json file
launchEl = turboData.get("launching")
glfunctionEl = turboData.get("functions")

# Use directory of jason-file if not specified in config-file
fl_workingDir = launchEl.get("workingDir", os.path.dirname(config_filename))
fl_workingDir = os.path.normpath(fl_workingDir)
# Reset working dir in dict
launchEl["workingDir"] = fl_workingDir
print("Used Fluent Working-Directory: " + fl_workingDir)

if external:
    # Fluent starts externally
    print("Launching Fluent...")
    solver = launcher.launchFluent(launchEl)

# Start Setup
caseDict = turboData.get("cases")
if caseDict is not None:
    for casename in caseDict:
        print("Running Case: " + casename + "\n")
        caseEl = turboData["cases"][casename]
        # Merge function dicts
        caseFunctionEl = utilities.merge_functionDicts(
            caseDict=caseEl, glfunctionDict=glfunctionEl
        )
        # Copy data from reference if refCase is set
        if caseEl.get("refCase") is not None:
            utilities.merge_data_with_refDict(caseDict=caseEl, allCasesDict=caseDict)
        # Check if material from lib should be used
        utilities.get_material_from_lib(caseDict=caseEl, scriptPath=scriptPath)

        # Get base caseFilename and update dict
        caseFilename = caseEl.get("caseFilename", casename)
        caseEl["caseFilename"] = caseFilename

        # Set Batch options
        solver.file.confirm_overwrite = False

        # Start Transcript
        trnFileName = casename + ".trn"
        solver.file.start_transcript(file_name=trnFileName)

        # Mesh import, expressions, profiles
        result = meshimport.import_01(caseEl, solver)

        ### Expression Definition
        # Write ExpressionFile with specified Template
        utilities.write_expression_file(
            data=caseEl, script_dir=scriptPath, working_dir=fl_workingDir
        )
        # Reading ExpressionFile into Fluent
        solver.tui.define.named_expressions.import_from_tsv(
            caseEl["expressionFilename"]
        )
        # Check if all inputParameters are valid
        utilities.check_input_parameter_expressions(solver=solver)
        ### Expression Definition... done!

        # Enable Beta-Features
        solver.tui.define.beta_feature_access("yes ok")

        # Case Setup
        setupcfd.setup(data=caseEl, solver=solver, functionEl=caseFunctionEl)
        setupcfd.report_01(caseEl, solver)

        # Solution
        # Set Solver Settings
        numerics.numerics(data=caseEl, solver=solver, functionEl=caseFunctionEl)

        # Read Additional Journals, if specified
        utilities.read_journals(data=caseEl, solver=solver, element_name="pre_init_journal_filenames")

        # Initialization
        solve.init(data=caseEl, solver=solver, functionEl=caseFunctionEl)

        # Write case and ini-data & settings file
        print("\nWriting initial case & settings file\n")
        solver.file.write(file_type="case", file_name=caseFilename)
        settingsFilename = '"' + caseFilename + '.set"'
        solver.tui.file.write_settings(settingsFilename)
        if solver.field_data.is_data_valid():
            print("\nWriting initial dat file\n")
            solver.file.write(file_type="data", file_name=caseFilename)
        else:
            print(
                "Skipping Writing of Initial Solution Data: No Solution Data available\n"
            )

        # Read Additional Journals, if specified
        utilities.read_journals(data=caseEl, solver=solver, element_name="pre_solve_journal_filenames")

        # Solve
        if caseEl["solution"].get("runSolver", False):
            solve.solve_01(caseEl, solver)
            filename = caseFilename + "_fin"
            solver.file.write(file_type="case-data", file_name=filename)

        # Postprocessing
        if solver.field_data.is_data_valid():
            postproc.post(
                data=caseEl, solver=solver, functionEl=caseFunctionEl, launchEl=launchEl
            )
            filename = caseFilename + "_fin"
            solver.file.write(file_type="case-data", file_name=filename)
        else:
            print("Skipping Postprocessing: No Solution Data available\n")

        # Read Additional Journals, if specified
        utilities.read_journals(data=caseEl, solver=solver, element_name="pre_exit_journal_filenames")

        # Finalize
        solver.file.stop_transcript()
        # End of Case-Loop

    # Merge if multiple cases are defined
    if len(caseDict) > 1:
        postproc.mergeReportTables(turboData=turboData, solver=solver)

# Do Studies
studyDict = turboData.get("studies")

if studyDict is not None:
    parametricstudy.study(data=turboData, solver=solver, functionEl=glfunctionEl)

    # Postprocessing of studies
    if launchEl.get("plotResults"):
        parametricstudy.studyPlot(data=turboData, solver = solver)

# Exit Solver
solverExit = True #launchEl.get("exitatend", False)
if solverExit:
    solver.exit()

print("Script successfully finished! \n")
