import os
import json
import sys
import copy
import ansys.fluent.core as pyfluent
from packaging.version import Version

# Load Script Modules
from ptw_subroutines import (
    numerics,
    parametricstudy,
    solve,
    meshimport,
    setupcfd,
    postproc,
    parametricstudy_post,
    prepostproc,
)
from ptw_subroutines.utils import (
    ptw_logger,
    launcher,
    dict_utils,
    expressions_utils,
    fluent_utils,
    misc_utils,
)


ptw_version = "1.9.1"

# Set Logger
logger = ptw_logger.init_logger()


class PTW_Run:
    """Object to setup & run the PyTurboWizard"""

    # Set Debug-Level
    debug_level = 1

    # input files
    mesh_file_name: str = ""
    config_file_name: str = ""

    script_path: str = ""
    fl_workingDir: str = ""

    # dicts
    turbo_data: dict = None
    turbo_data_from_file: dict = None
    launch_data: dict = None
    gl_function_data: dict = None

    solver: pyfluent.session_solver.Solver = None

    def load_config_file(self, script_path: str, config_filename: str):
        self.script_path = script_path
        self.config_file_name = config_filename
        logger.info(f"Reading ConfigFile: {os.path.abspath(config_filename)}")
        config_file = open(config_filename, "r")
        self.turbo_data = dict()
        # Load a yaml file if specified, otherwise json
        if config_filename.endswith("yaml"):
            import yaml

            self.turbo_data = yaml.safe_load(config_file)
        else:
            self.turbo_data = json.load(config_file)

        # Copy dict from file
        self.turbo_data_from_file = copy.deepcopy(self.turbo_data)

        # Set Version to turboData
        self.turbo_data["ptw_version"] = ptw_version
        # Get or Set-Default Debug-Level
        self.debug_level = self.turbo_data.setdefault("debug_level", self.debug_level)

        # Get important Elements from json file
        self.launch_data = self.turbo_data.get("launching")
        self.gl_function_data = self.turbo_data.get("functions")

        # Use abs path of json-file-directory if 'workingDir' not specified in config-file
        fl_workingDir = self.launch_data.get(
            "workingDir", os.path.dirname(os.path.abspath(config_filename))
        )
        fl_workingDir = os.path.normpath(fl_workingDir)
        # Reset working dir in dict
        self.launch_data["workingDir"] = fl_workingDir
        self.fl_workingDir = fl_workingDir
        logger.info(f"Used Fluent Working-Directory: {self.fl_workingDir}")

        logger.info(f"Reading ConfigFile: {os.path.abspath(config_filename)}... done!")

    def launch_fluent(self, solver=None):
        if solver is None:
            logger.info("Launching Fluent...")
            solver = launcher.launchFluent(self.launch_data)

        self.solver = solver

        return solver

    def ini_fluent_settings(self):
        solver = self.solver
        if solver is None:
            logger.warning(
                "No Fluent solver specified... Skipping PTW_Run-function 'ini_fluent_settings'!"
            )
            return

        logger.info("Initializing Fluent settings")

        # Set standard image output format to AVZ
        solver.execute_tui("/display/set/picture/driver avz")

        # Fluent Version Check
        if Version(solver._version) < Version("241"):
            # For version before 24.1, remove the streamhandler from the logger
            ptw_logger.remove_handlers(streamhandlers=True, filehandlers=False)
            # Set Batch options: Old API
            solver.file.confirm_overwrite = False
        else:
            # Set Batch options: API changes with v24.1
            solver.file.batch_options.confirm_overwrite = False
            solver.file.batch_options.exit_on_error = True
            solver.file.batch_options.hide_answer = True
            solver.file.batch_options.redisplay_question = False

        logger.info("Initializing Fluent settings... done!")

    def do_case_study(self):
        # Get Data from Class
        solver = self.solver
        if solver is None:
            logger.warning(
                "No Fluent solver specified... Skipping PTW_Run-function 'do_case_study'!"
            )
            return
        if self.turbo_data is None:
            logger.warning(
                "No Turbo-Dict loaded... Skipping PTW_Run-function 'do_case_study'!"
            )
            return

        logger.info("Running Case Study")
        # get data from class
        launchEl = self.launch_data
        fl_workingDir = self.fl_workingDir
        gl_function_data = self.gl_function_data
        turbo_data = self.turbo_data
        gpu = turbo_data.get("launching")["gpu"]

        caseDict = turbo_data.get("cases")
        if caseDict is not None:
            for casename in caseDict:
                logger.info(f"Running Case: {casename}")
                caseEl = turbo_data["cases"][casename]
                # Basic Dict Stuff...
                # First: Copy data from reference if refCase is set
                ref_case = caseEl.get("refCase")
                if ref_case is not None:
                    # Check if reference case is available
                    if caseDict.get(ref_case) is not None:
                        dict_utils.merge_data_with_refDict(
                            caseDict=caseEl, allCasesDict=caseDict
                        )
                    else:
                        logger.error(
                            f"Case '{casename}' is skipped: "
                            f"Specified Reference-Case: '{ref_case}' not available."
                        )
                        continue
                # Check if case should be executed
                if caseEl.setdefault("skip_execution", False):
                    logger.info(
                        f"Case '{casename}' is skipped: 'skip_execution' is set to 'True' in Case-Definition"
                    )
                    continue
                # Update initial case-function-dict
                caseFunctionEl = dict_utils.merge_functionDicts(
                    caseDict=caseEl, glfunctionDict=gl_function_data
                )
                # Check if material from lib should be used
                dict_utils.get_material_from_lib(
                    caseDict=caseEl, scriptPath=self.script_path
                )
                # Check if all important keys are available to avoid errors
                dict_utils.check_keys(case_dict=caseEl, case_name=casename)
                # Basic Dict Stuff -> done

                # Get base caseFilename and update dict
                caseFilename = caseEl.setdefault("caseFilename", casename)

                # Start Transcript
                caseOutPath = misc_utils.ptw_output(
                    fl_workingDir=fl_workingDir, case_name=caseFilename
                )
                trnName = f"{casename}.trn"
                trnFileName = os.path.join(caseOutPath, trnName)
                solver.file.start_transcript(file_name=trnFileName)

                # Mesh import, expressions, profiles
                meshimport.import_01(caseEl, solver)

                # Read Additional Journals, if specified
                fluent_utils.read_journals(
                    case_data=caseEl,
                    solver=solver,
                    element_name="post_meshimport_journal_filenames",
                    fluent_dir=fl_workingDir,
                    execution_dir=caseOutPath,
                )

                ### Expression Definition
                logger.info("Expression Definition... starting")
                # Write ExpressionFile with specified Template
                expressions_utils.write_expression_file(
                    data=caseEl, script_dir=self.script_path, working_dir=fl_workingDir
                )
                # Reading ExpressionFile into Fluent
                caseOutPath = misc_utils.ptw_output(
                    fl_workingDir=fl_workingDir, case_name=caseFilename
                )
                expressionFilename = os.path.join(
                    caseOutPath, caseEl["expressionFilename"]
                )
                solver.tui.define.named_expressions.import_from_tsv(expressionFilename)
                # Check if all inputParameters are valid
                expressions_utils.check_input_parameter_expressions(solver=solver)
                # Check if all outputParameters are set
                expressions_utils.check_output_parameter_expressions(
                    caseEl=caseEl, solver=solver
                )
                # Check if all expressions are valid for specific solver version
                expressions_utils.check_expression_versions(solver=solver)
                # Remove exp-file & write final expressions-file
                if os.path.exists(expressionFilename):
                    os.remove(expressionFilename)
                solver.tui.define.named_expressions.export_to_tsv(expressionFilename)
                logger.info("Expression Definition... done!")
                ### Expression Definition... done!

                # Enable Beta-Features
                solver.tui.define.beta_feature_access("yes ok")

                # Case Setup
                setupcfd.setup(
                    data=caseEl, solver=solver, functionEl=caseFunctionEl, gpu=gpu
                )
                setupcfd.set_reports(caseEl, solver, launchEl, gpu=gpu)

                # Solution
                # Set Solver Settings
                numerics.numerics(
                    data=caseEl, solver=solver, functionEl=caseFunctionEl, gpu=gpu
                )

                # Set "Run Calculation" properties
                setupcfd.set_run_calculation(caseEl, solver)

                # Read Additional Journals, if specified
                fluent_utils.read_journals(
                    case_data=caseEl,
                    solver=solver,
                    element_name="pre_init_journal_filenames",
                    fluent_dir=fl_workingDir,
                    execution_dir=caseOutPath,
                )

                # Initialization
                solve.init(
                    data=caseEl, solver=solver, functionEl=caseFunctionEl, gpu=gpu
                )

                # Setup for Post Processing
                prepostproc.prepost(
                    data=caseEl,
                    solver=solver,
                    functionEl=caseFunctionEl,
                    launchEl=launchEl,
                )

                # Write case and ini-data & settings file
                logger.info("Writing initial case & settings file")
                solver.file.write(file_type="case", file_name=caseFilename)
                settingsFilename = os.path.join(caseOutPath, "settings.set")
                # Removing file manually, as batch options seem not to work
                if os.path.exists(settingsFilename):
                    logger.info(
                        f"Removing old existing settings-file: {settingsFilename} "
                    )
                    os.remove(settingsFilename)
                logger.info(f"Writing settings-file: {settingsFilename}")
                solver.tui.file.write_settings(settingsFilename)
                # Writing additional setup info: extsch file
                if caseEl.setdefault("run_extsch", False):
                    misc_utils.run_extsch_script(
                        scriptPath=self.script_path,
                        workingDir=fl_workingDir,
                        caseEl=caseEl,
                    )

                if solver.field_data.is_data_valid():
                    logger.info("Writing initial dat file")
                    solver.file.write(file_type="data", file_name=caseFilename)
                else:
                    logger.info(
                        "Skipping Writing of Initial Solution Data: No Solution Data available"
                    )

                # Read Additional Journals, if specified
                fluent_utils.read_journals(
                    case_data=caseEl,
                    solver=solver,
                    element_name="pre_solve_journal_filenames",
                    fluent_dir=fl_workingDir,
                    execution_dir=caseOutPath,
                )

                # Solve
                if caseEl["solution"].setdefault("runSolver", False):
                    solve.solve_01(caseEl, solver)
                    filename = f"{caseFilename}_fin"
                    solver.file.write(file_type="case-data", file_name=filename)

                # Postprocessing
                if solver.field_data.is_data_valid():
                    postproc.post(
                        data=caseEl,
                        solver=solver,
                        functionEl=caseFunctionEl,
                        launchEl=launchEl,
                        trn_name=trnFileName,
                        gpu=gpu,
                    )
                    # version 1.5.3: no alteration of case/data done in post processing, removed additional saving
                    # filename = caseFilename + "_fin"
                    # solver.file.write(file_type="case-data", file_name=filename)
                else:
                    logger.info("Skipping Postprocessing: No Solution Data available")

                # Read Additional Journals, if specified
                fluent_utils.read_journals(
                    case_data=caseEl,
                    solver=solver,
                    element_name="pre_exit_journal_filenames",
                    fluent_dir=fl_workingDir,
                    execution_dir=caseOutPath,
                )

                # Finalize
                if "stop_transcript" in solver.file.get_active_command_names():
                    solver.file.stop_transcript()
                # End of Case-Loop

            # Merge if multiple cases are defined
            if len(caseDict) > 1:
                postproc.mergeReportTables(turboData=turbo_data, solver=solver)

        logger.info("Running Case Study... done!")

    def do_parametric_study(self):
        # Get Data from Class
        solver = self.solver
        if solver is None:
            logger.warning(
                "No Fluent solver specified... Skipping PTW_Run-function 'do_parametric_study'!"
            )
            return
        if self.turbo_data is None:
            logger.warning(
                "No Turbo-Dict loaded... Skipping PTW_Run-function 'do_parametric_study'!"
            )
            return

        logger.info("Running Parametric Study")
        turbo_data = self.turbo_data
        gl_function_data = self.gl_function_data
        gpu = turbo_data.get("launching")["gpu"]

        studyDict = turbo_data.get("studies")
        # Do Studies
        if studyDict is not None:
            parametricstudy.study(
                data=turbo_data, solver=solver, functionEl=gl_function_data, gpu=gpu
            )
            # Post Process Studies
            parametricstudy_post.study_post(
                data=turbo_data, solver=solver, functionEl=gl_function_data, gpu=gpu
            )

        logger.info("Running Parametric Study... done!")

    def finalize_session(self):
        # Get Data from Class
        solver = self.solver
        if solver is None:
            logger.warning(
                "No Fluent solver specified... Skipping PTW_Run-function 'finalize_session'!"
            )
            return
        if self.turbo_data is None:
            logger.warning(
                "No Turbo-Dict loaded... Skipping PTW_Run-function 'finalize_session'!"
            )
            return

        logger.info("Finalizing Fluent-Session")

        # Exit Solver
        solver.exit()

        # Do clean-up
        cleanup_data = self.launch_data.setdefault("ptw_cleanup", False)
        misc_utils.fluent_cleanup(
            working_dir=self.fl_workingDir, cleanup_data=cleanup_data
        )

        # Write out Debug info
        if self.debug_level > 0:
            # Compare turboData: final data vs file data --> check if some keywords have not been used
            logger.info("Searching for unused keywords in input-config-file...")
            dict_utils.detect_unused_keywords(
                refDict=self.turbo_data, compareDict=self.turbo_data_from_file
            )
            logger.info(
                "Searching for unused keywords in input-config-file... finished!"
            )

            import ntpath

            config_basename = os.path.splitext(ntpath.basename(self.config_file_name))[
                0
            ]
            debug_filename = f"ptw_{config_basename}.json"
            ptwOutPath = misc_utils.ptw_output(fl_workingDir=self.fl_workingDir)
            debug_file_path = os.path.join(ptwOutPath, debug_filename)
            jsonString = json.dumps(self.turbo_data, indent=4, sort_keys=True)
            with open(debug_file_path, "w") as jsonFile:
                logger.info(f"Writing ptw-json-File: {debug_file_path}")
                jsonFile.write(jsonString)

        logger.info("Finalizing Fluent-Session... done!")

    def do_full_run(self, script_path, config_filename, solver):
        logger.info(f"*** Starting PyTurboWizard (Version {ptw_version}) ***")
        # Start ptw_run
        self.load_config_file(script_path=script_path, config_filename=config_filename)
        self.launch_fluent(solver=solver)
        self.ini_fluent_settings()
        self.do_case_study()
        self.do_parametric_study()
        self.finalize_session()
        logger.info("PTW-Script successfully finished!")
        return


def ptw_main():
    # Get data from arguments
    # Get script_path (needed to get template-dir)
    script_path = os.path.dirname(sys.argv[0])
    # If arguments are passed take first argument as fullpath to the json file
    config_filename = "turboSetupConfig.json"
    if len(sys.argv) > 1:
        config_filename = sys.argv[1]
    config_filename = os.path.normpath(config_filename)
    ptw_run = PTW_Run()
    # Launch fluent
    solver_session = None
    if "solver" in globals():
        solver_session = globals()["solver"]
    ptw_run.do_full_run(
        script_path=script_path, config_filename=config_filename, solver=solver_session
    )


if __name__ == "__main__":
    ptw_main()
