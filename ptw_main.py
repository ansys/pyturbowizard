import os
import json
import sys
import copy

# Load Script Modules
from ptw_subroutines import (
    numerics,
    parametricstudy,
    solve,
    meshimport,
    setupcfd,
    postproc,
    parametricstudy_post,
    prepostproc
)
from ptw_subroutines.utils import (
    ptw_logger,
    launcher,
    dict_utils,
    expressions_utils,
    fluent_utils,
    misc_utils
)

# Set default Debug-Level
debug_level = 1

# Set Logger
logger = ptw_logger.init_logger(console_output=False)

version = "1.5.4"
logger.info(f"*** Starting PyTurboWizard (Version {str(version)}) ***")

# If solver variable does not exist, Fluent has been started in external mode
external = "solver" not in globals()

# Get scriptpath
scriptPath = os.path.dirname(sys.argv[0])

# Load Json File
# Suggest Config File in python working Dir
config_filename = "turboSetupConfig.json"
# If arguments are passed take first argument as fullpath to the json file
if len(sys.argv) > 1:
    config_filename = sys.argv[1]
config_filename = os.path.normpath(config_filename)
logger.info("Opening ConfigFile: " + os.path.abspath(config_filename))
config_file = open(config_filename, "r")
turboData = dict()
# Load a yaml file if specified, otherwise json
if config_filename.endswith("yaml"):
    import yaml

    turboData = yaml.safe_load(config_file)
else:
    turboData = json.load(config_file)

#Copy dict from file
turboData_from_file = copy.deepcopy(turboData)

# Set Version to turboData
turboData["ptw_version"] = version
# Get or Set-Default Debug-Level
debug_level = turboData.setdefault("debug_level", debug_level)

# Get important Elements from json file
launchEl = turboData.get("launching")
glfunctionEl = turboData.get("functions")

# Use abs path of json-file-directory if 'workingDir' not specified in config-file
fl_workingDir = launchEl.get(
    "workingDir", os.path.dirname(os.path.abspath(config_filename))
)
fl_workingDir = os.path.normpath(fl_workingDir)
# Reset working dir in dict
launchEl["workingDir"] = fl_workingDir
logger.info("Used Fluent Working-Directory: " + fl_workingDir)

if external:
    # Fluent starts externally
    logger.info("Launching Fluent...")
    solver = launcher.launchFluent(launchEl)

# Set standard image output format to AVZ
go_format = '"AVZ"'
solver.tui.preferences.graphics.hardcopy_settings.hardcopy_driver(f'{go_format}')

# Set Batch options
solver.file.confirm_overwrite = False
#solver.tui.file.set_batch_options("no yes yes no") -> does not work

# Start Setup
caseDict = turboData.get("cases")
if caseDict is not None:
    for casename in caseDict:
        logger.info("Running Case: " + casename)
        caseEl = turboData["cases"][casename]
        # Basic Dict Stuff...
        # First: Copy data from reference if refCase is set
        if caseEl.get("refCase") is not None:
            dict_utils.merge_data_with_refDict(caseDict=caseEl, allCasesDict=caseDict)
        # Check if case should be executed
        if caseEl.setdefault("skip_execution", False):
            logger.info(
                f"Case '{casename}' is skipped: 'skip_execution' is set to 'True' in Case-Definition"
            )
            continue
        # Update initial case-function-dict
        caseFunctionEl = dict_utils.merge_functionDicts(
            caseDict=caseEl, glfunctionDict=glfunctionEl
        )
        # Check if material from lib should be used
        dict_utils.get_material_from_lib(caseDict=caseEl, scriptPath=scriptPath)
        # Basic Dict Stuff -> done

        # Get base caseFilename and update dict
        caseFilename = caseEl.setdefault("caseFilename", casename)

        # Start Transcript
        trnFileName = casename + ".trn"
        solver.file.start_transcript(file_name=trnFileName)

        # Mesh import, expressions, profiles
        result = meshimport.import_01(caseEl, solver)

        ### Expression Definition
        # Write ExpressionFile with specified Template
        expressions_utils.write_expression_file(
            data=caseEl, script_dir=scriptPath, working_dir=fl_workingDir
        )
        # Reading ExpressionFile into Fluent
        solver.tui.define.named_expressions.import_from_tsv(
            caseEl["expressionFilename"]
        )
        # Check if all inputParameters are valid
        expressions_utils.check_input_parameter_expressions(solver=solver)
        # Check if all outputParameters are set
        expressions_utils.check_output_parameter_expressions(caseEl=caseEl, solver=solver)
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
        fluent_utils.read_journals(
            data=caseEl, solver=solver, element_name="pre_init_journal_filenames"
        )

        # Initialization
        solve.init(data=caseEl, solver=solver, functionEl=caseFunctionEl)

        # Setup for Post Processing
        prepostproc.prepost(data=caseEl, solver=solver, functionEl=caseFunctionEl,launchEl=launchEl)

        # Write case and ini-data & settings file
        logger.info("Writing initial case & settings file")
        solver.file.write(file_type="case", file_name=caseFilename)

        # Writing additional setup info: settings & extsch file
        settingsFilename = '"' + caseFilename + '.set"'
        # Removing file manually, as batch options seem not to work
        if os.path.exists(settingsFilename):
            logger.info(f"Removing old existing settings-file {settingsFilename} ")
            os.remove(settingsFilename)
        logger.info(f"Writing settings-file {settingsFilename}")
        solver.tui.file.write_settings(settingsFilename)

        if caseEl.setdefault("run_extsch", False):
            misc_utils.run_extsch_script(scriptPath=scriptPath, workingDir=fl_workingDir, caseEl=caseEl)

        if solver.field_data.is_data_valid():
            logger.info("Writing initial dat file")
            solver.file.write(file_type="data", file_name=caseFilename)
        else:
            logger.info(
                "Skipping Writing of Initial Solution Data: No Solution Data available"
            )

        # Read Additional Journals, if specified
        fluent_utils.read_journals(
            data=caseEl, solver=solver, element_name="pre_solve_journal_filenames"
        )

        # Solve
        if caseEl["solution"].setdefault("runSolver", False):
            solve.solve_01(caseEl, solver)
            filename = caseFilename + "_fin"
            solver.file.write(file_type="case-data", file_name=filename)

        # Postprocessing
        if solver.field_data.is_data_valid():
            postproc.post(
                data=caseEl,
                solver=solver,
                functionEl=caseFunctionEl,
                launchEl=launchEl,
                trn_name=trnFileName,
            )
            # version 1.5.3: no alteration of case/data done in post processing, removed additonal saving
            #filename = caseFilename + "_fin"
            #solver.file.write(file_type="case-data", file_name=filename)
        else:
            logger.info("Skipping Postprocessing: No Solution Data available")

        # Read Additional Journals, if specified
        fluent_utils.read_journals(
            data=caseEl, solver=solver, element_name="pre_exit_journal_filenames"
        )

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
    # Post Process Studies
    parametricstudy_post.study_post(
        data=turboData, solver=solver, functionEl=glfunctionEl
    )

# Exit Solver
solver.exit()

# Write out Debug info
if debug_level > 0:
    #Compare turboData: final data vs file data --> check if some keywords have not been used
    logger.info("Detecting unused keywords of input-config-file")
    dict_utils.detect_unused_keywords(refDict=turboData, compareDict=turboData_from_file)

    import ntpath
    debug_filename = "ptw_" + ntpath.basename(config_filename)
    debug_file_path = os.path.join(fl_workingDir, debug_filename)
    jsonString = json.dumps(turboData, indent=4, sort_keys=True)
    with open(debug_file_path, "w") as jsonFile:
        logger.info(f"Writing ptw-json-File: {debug_file_path}")
        jsonFile.write(jsonString)

logger.info("Script successfully finished!")
