# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Parametric Study Module

This module provides functionality setting and running parametric studies
conducted in the PyTurboWizard application.
"""

import json
import os

from packaging.version import Version

# Load Script Modules
from src.ansys.ptw.subroutines.utils import dict_utils, fluent_utils, misc_utils, ptw_logger

# Logger


logger = ptw_logger.get_logger()


def study(data, solver, functionEl, gpu):
    """Run a parametric study based on the provided data and function element."""
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="parametricstudy",
        defaultName="study_01",
    )

    logger.info(f"Running ParametricStudy-Function '{functionName}' ...")
    if functionName == "study_01":
        study_01(data, solver, gpu)
    else:
        logger.info(f"Prescribed Function '{functionName}' not known. Skipping Parametric Study!")

    logger.info(f"Running ParametricStudy-Function '{functionName}'...  finished!")


def study_01(data, solver, gpu):
    """Run a parametric study based on the provided data and solver, version 1.0."""
    studyDict = data.get("studies")
    flworking_Dir = data.get("launching")["workingDir"]

    # Init variables
    fluent_study = None
    studyIndex = 0

    for studyName in studyDict:
        studyEl = studyDict[studyName]
        logger.info(f"Running Study '{studyName}'...")
        # Check if study should be executed
        if studyEl.setdefault("skip_execution", False):
            logger.info(
                f"Study '{studyName}' is skipped: 'skip_execution' is set "
                f"to 'True' in Study-Definition"
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
                logger.info(
                    f"Fluent-Project '{studyFileName}' already exists and "
                    f"'overwriteExisting'-flag is set to 'False' or "
                    f"not existing in Config-File \nSkipping Parametric Study '{studyName}'"
                )
                break
        else:
            if runExisting:
                logger.info(
                    f"Specified Fluent-Project '{studyFileName}' does not exist"
                    f"\nSkipping Parametric Study '{studyName}"
                )
                break

        # Check if a new Project should be created or an existing is executed
        if not runExisting:
            # Read Ref Case
            refCaseFilePath = os.path.join(flworking_Dir, refCase)
            if Version(solver._version) >= Version("241"):
                solver.settings.file.read_case_data(file_name=refCaseFilePath)
            else:
                if studyIndex == 0:
                    solver.settings.file.read_case_data(file_name=refCaseFilePath)
                else:
                    tuicommand = 'file/rcd "' + refCaseFilePath + '" yes'
                    solver.execute_tui(tuicommand)

            # Initialize a new parametric study
            projectFilename = os.path.join(flworking_Dir, studyName)
            solver.settings.parametric_studies.initialize(project_filename=projectFilename)
            psname = refCase + "-Solve"
            fluent_study = solver.settings.parametric_studies[psname]

            # Set standard image output format to AVZ
            solver.execute_tui("/display/set/picture/driver avz")

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
                    fluent_study.design_points.duplicate(design_point="Base DP")
                    designPointName = list(fluent_study.design_points)[-1]
                    new_dp = fluent_study.design_points[designPointName]
                    for ipIndex in range(numIPs):
                        ipName = ipList[ipIndex]
                        modValue = valueListArray[ipIndex][dpIndex]
                        if useScaleFactor[ipIndex]:
                            ref_dp = fluent_study.design_points["Base DP"].input_parameters()
                            # ref_dp = {"ip1": 2.0, "BC_P_Out": 1.0, "ip3": 3.0}
                            refValue = ref_dp[ipName]
                            modValue = refValue * modValue

                        new_dp.input_parameters = {ipName: modValue}
                        new_dp.write_data = studyEl.setdefault("write_data", False)
                        simulation_report_flag = studyEl.setdefault("simulation_report", False)
                        new_dp.capture_simulation_report_data = simulation_report_flag

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
                logger.info("Using previous updated data for Initialization")
                solver.tui.parametric_study.study.use_data_of_previous_dp("yes")

            if Version(solver._version) >= Version("241"):
                if not studyEl.setdefault("reread_case", False):
                    solver.tui.parametric_study.study.read_case_before_each_dp_update("no")
                else:
                    solver.tui.parametric_study.study.read_case_before_each_dp_update("yes")

            # Run all Design Points
            if studyEl.setdefault("updateAllDPs", False):
                fluent_study.design_points.update_all()

            # Export results to table

            studyOutPath = misc_utils.ptw_output(fl_workingDir=flworking_Dir, study_name=studyName)

            design_point_table_filepath = os.path.join(studyOutPath, "dp_table.csv")
            solver.settings.parametric_studies.export_design_table(
                filepath=design_point_table_filepath
            )

            # Save Study
            if studyIndex == 0:
                solver.settings.file.parametric_project.save()
            else:
                projectFilename = os.path.join(flworking_Dir, studyName)
                solver.tui.file.parametric_project.save_as(projectFilename)

            # Increasing study index
            studyIndex = studyIndex + 1

        else:
            # Load Existing Project
            flworking_Dir = data.get("launching")["workingDir"]
            solver.settings.file.parametric_project.open(project_filename=studyFileName)
            psname = refCase + "-Solve"
            fluent_study = solver.settings.parametric_studies[psname]

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
                logger.info("Using previous updated data for Initialization")
                solver.tui.parametric_study.study.use_data_of_previous_dp("yes")

            if Version(solver._version) >= Version("241"):
                if not studyEl.setdefault("reread_case", False):
                    solver.tui.parametric_study.study.read_case_before_each_dp_update("no")
                else:
                    solver.tui.parametric_study.study.read_case_before_each_dp_update("yes")

            # Run all Design Points
            if studyEl.setdefault("updateAllDPs", False):
                fluent_study.design_points.update_all()

            # Export results to table
            studyOutPath = misc_utils.ptw_output(fl_workingDir=flworking_Dir, study_name=studyName)

            design_point_table_filepath = os.path.join(studyOutPath, "dp_table.csv")
            solver.settings.parametric_studies.export_design_table(
                filepath=design_point_table_filepath
            )

            # Save Study
            if studyIndex == 0:
                solver.settings.file.parametric_project.save()
            else:
                projectFilename = os.path.join(flworking_Dir, studyName)
                solver.tui.file.parametric_project.save_as(projectFilename)

            # Increasing study index
            studyIndex = studyIndex + 1

        logger.info(f"Running Study '{studyName}' finished!")
        # break

        # Extract CoV information and store in temporary file for postprocessing
        # (CoV not available with GPU solver at the moment)
        if gpu:
            tempDataDict = {"num_eqs": 0}
        else:
            tempDataDict = (
                solver.settings.solution.monitor.convergence_conditions.convergence_reports()
            )
        number_eqs = fluent_utils.get_number_of_equations(solver=solver)
        tempDataDict["num_eqs"] = number_eqs

        baseCaseName = studyDict[studyName].get("refCaseFilename")
        pathtostudy = os.path.join(flworking_Dir, f"{studyName}.cffdb", f"{baseCaseName}-Solve")
        # Check if the folder exists
        if not os.path.exists(pathtostudy):
            logger.info("No Study data has been found!")
            logger.info("Skipping Post-Processing!")
        else:
            # Define the file path
            temp_data_path = os.path.join(pathtostudy, "temp_data.json")

            # Save the dictionary as a JSON file
            with open(temp_data_path, "w") as file:
                json.dump(tempDataDict, file)

    logger.info("All Studies finished")
