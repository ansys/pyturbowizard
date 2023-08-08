import os
import json

# Logger
from ptw_subroutines.utils import ptw_logger, dict_utils

logger = ptw_logger.getLogger()


def study(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="parametricstudy",
        defaultName="study_01",
    )

    logger.info(f"Running ParamatricStudy-Function '{functionName}' ...")
    if functionName == "study_01":
        study01(data, solver)
    else:
        logger.info(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Parametric Study!'
        )

    logger.info(f"\nRunning ParamatricStudy-Function '{functionName}'...  finished!\n")


def study01(data, solver):
    studyDict = data.get("studies")
    flworking_Dir = data.get("launching")["workingDir"]

    # Init variables
    fluent_study = None
    studyIndex = 0

    for studyName in studyDict:
        studyEl = studyDict[studyName]
        logger.info(f"\nRunning Study '{studyName}'...\n")
        # Check if study should be executed
        if studyEl.setdefault("skip_execution", False):
            logger.info(
                f"Study '{studyName}' is skipped: 'skip_execution' is set to 'True' in Study-Definition\n"
            )
            continue

        # Getting all input data from json file
        # datapath = studyEl.get("datapath")
        refCase = studyEl.get("refCaseFilename")
        runExisting = studyEl.setdefault("runExistingProject", False)

        # Do some checks to skip if a run is not possible
        studyFileName = studyName + ".flprj"
        studyFileName = os.path.join(flworking_Dir, studyFileName)
        studyFolderPath = studyName + ".cffdb"
        studyFolderPath = os.path.join(flworking_Dir, studyFolderPath)
        if os.path.isfile(studyFileName) or os.path.isdir(studyFolderPath):
            if not studyEl.setdefault("overwriteExisting", False):
                logger.info("Fluent-Project already exists " + studyFileName)
                logger.info(
                    'and "overwriteExisting"-flag is set to False or not existing in Config-File'
                )
                logger.info('Skipping Parametric Study "' + studyName + '"\n')
                break
        else:
            if runExisting:
                logger.info("Specified Fluent-Project does not exist " + studyFileName)
                logger.info('Skipping Parametric Study "' + studyName + '"\n')
                break

        # Check if a new Project should be created or an existing is executed
        if not runExisting:
            # Read Ref Case
            refCaseFilePath = os.path.join(flworking_Dir, refCase)
            if studyIndex == 0:
                solver.file.read_case_data(
                    file_name=refCaseFilePath
                )
            else:
                tuicommand = 'file/rcd "' + refCaseFilePath + '" yes'
                solver.execute_tui(tuicommand)
                #solver.tui.file.read_case_data(refCaseFilePath)
                #solver.file.read_case_data(file_name=refCaseFilePath)

            # Initialize a new parametric study
            solver.parametric_studies.initialize(project_filename=studyName)
            psname = refCase + "-Solve"
            fluent_study = solver.parametric_studies[psname]

            designPointCounter = 1
            definitionList = studyEl.get("definition")

            for studyDef in definitionList:
                ipList = studyDef.get("inputparameters")
                numIPs = len(ipList)
                useScaleFactor = studyDef.get("useScaleFactor")
                # if a single value is prescribed (old code), we automatically transfer it to a list
                if type(useScaleFactor) is not list:
                    glSFValue = useScaleFactor
                    useScaleFactor = []
                    for ipIndex in range(numIPs):
                        useScaleFactor.append(glSFValue)

                valueListArray = studyDef.get("valueList")
                numDPs = len(valueListArray[0])
                for dpIndex in range(numDPs):
                    # new_dp = fluent_study.add_design_point()
                    fluent_study.design_points.duplicate(design_point="Base DP")
                    designPointName = "DP" + str(designPointCounter)
                    # new_dp = {"BC_P_Out": 0.}
                    new_dp = fluent_study.design_points[designPointName]
                    for ipIndex in range(numIPs):
                        ipName = ipList[ipIndex]
                        modValue = valueListArray[ipIndex][dpIndex]
                        if useScaleFactor[ipIndex]:
                            ref_dp = fluent_study.design_points[
                                "Base DP"
                            ].input_parameters()
                            # ref_dp = {"ip1": 2.0, "BC_P_Out": 1.0, "ip3": 3.0}
                            refValue = ref_dp[ipName]
                            modValue = refValue * modValue

                        # new_dp[ipName] = modValue
                        new_dp.input_parameters = {ipName: modValue}
                        write_data_flag = studyEl.setdefault("write_data", False)
                        new_dp.write_data = write_data_flag
                        studyEl["write_data"] = write_data_flag

                    # fluent_study.design_points[designPointName].input_parameters = new_dp
                    designPointCounter = designPointCounter + 1

            # Set Initialization Method
            # convert oldkeyword definition (pre v1.4.7)
            updateFromBaseDP = studyEl.get("updateFromBaseDP")
            if (studyEl.get("initMethod") is None) and (updateFromBaseDP is not None):
                if updateFromBaseDP:
                    studyEl["initMethod"] = "baseDP"
                else:
                    studyEl["initMethod"] = "prevDP"

            initMethod = studyEl.setdefault("initMethod", "baseDP")
            if initMethod == "base_ini":
                logger.info("Using base case initialization method")
            elif initMethod == "baseDP":
                logger.info("Using base DP data for Initialization")
                solver.tui.parametric_study.study.use_base_data("yes")
            elif initMethod == "prevDP":
                logger.info("Using previous DP data for Initialization")
                solver.tui.parametric_study.study.use_data_of_previous_dp("yes")

            # Run all Design Points
            if studyEl.setdefault("updateAllDPs", False):
                fluent_study.design_points.update_all()

            # Export results to table
            design_point_table_filepath = (
                flworking_Dir + "/" + studyName + "_dp_table.csv"
            )
            design_point_table_filepath = os.path.normpath(design_point_table_filepath)
            solver.parametric_studies.export_design_table(
                filepath=design_point_table_filepath
            )

            # Save Study
            # solver.tui.file.parametric_project.save_as(studyName)
            solver.file.parametric_project.save()

            # Increasing study index
            studyIndex = studyIndex + 1

        else:
            # Load Existing Project
            flworking_Dir = data.get("launching")["workingDir"]
            solver.file.parametric_project.open(project_filename=studyFileName)
            psname = refCase + "-Solve"
            fluent_study = solver.parametric_studies[psname]

            # Set Initialization Method
            # convert oldkeyword definition (pre v1.4.7)
            updateFromBaseDP = studyEl.get("updateFromBaseDP")
            if (studyEl.get("initMethod") is None) and (updateFromBaseDP is not None):
                if updateFromBaseDP:
                    studyEl["initMethod"] = "baseDP"
                else:
                    studyEl["initMethod"] = "prevDP"

            initMethod = studyEl.setdefault("initMethod", "base_ini")
            if initMethod == "base_ini":
                logger.info("Using base case initialization method")
            elif initMethod == "baseDP":
                logger.info("Using base DP data for Initialization")
                solver.tui.parametric_study.study.use_base_data("yes")
            elif initMethod == "prevDP":
                logger.info("Using previous DP data for Initialization")
                solver.tui.parametric_study.study.use_data_of_previous_dp("yes")

            # Run all Design Points
            if studyEl.setdefault("updateAllDPs", False):
                fluent_study.design_points.update_all()

            # Export results to table
            design_point_table_filepath = (
                flworking_Dir + "/" + studyName + "_dp_table.csv"
            )
            design_point_table_filepath = os.path.normpath(design_point_table_filepath)
            solver.parametric_studies.export_design_table(
                filepath=design_point_table_filepath
            )

            # Save Study
            solver.file.parametric_project.save()

            # Increasing study index
            studyIndex = studyIndex + 1

        logger.info(f"\nRunning Study '{studyName}' finished!\n")
        # break

        # Extract CoV information and store in temporary file for post processing
        covDict = solver.solution.monitor.convergence_conditions.convergence_reports()
        baseCaseName = studyDict[studyName].get("refCaseFilename")
        pathtostudy = os.path.join(
            flworking_Dir, f"{studyName}.cffdb", f"{baseCaseName}-Solve"
        )
        # Check if the folder exists
        if not os.path.exists(pathtostudy):
            logger.info("No Study data has been found!\n")
            logger.info("Skipping Post-Processing!")
        else:
            # Define the file path
            temp_data_path = os.path.join(pathtostudy, "temp_data.json")

            # Save the dictionary as a JSON file
            with open(temp_data_path, "w") as file:
                json.dump(covDict, file)

    logger.info("All Studies finished")
