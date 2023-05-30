import os
import utilities
import matplotlib.pyplot as plt
import pandas as pd

def study(data, solver, functionName="study_01"):
    print('Running ParamatricStudy Function "' + functionName + '"...')
    if functionName == "study_01":
        study01(data, solver)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Parametric Study!'
        )

    print("ParamatricStudy finished.")


def study01(data, solver):
    studyDict = data.get("studies")
    flworking_Dir = data.get("launching")["workingDir"]

    # Init variables
    fluent_study = None
    studyIndex = 0

    for studyName in studyDict:
        studyEl = studyDict[studyName]
        # Getting all input data from json file
        # datapath = studyEl.get("datapath")
        refCase = studyEl.get("refCaseFilename")
        runExisting = studyEl.get("runExistingProject", False)

        # Do some checks to skip if a run is not possible
        studyFileName = flworking_Dir + "/" + studyName + ".flprj"
        studyFileName = os.path.normpath(studyFileName)
        if os.path.isfile(studyFileName):
            if not studyEl.get("overwriteExisting", False):
                print("Fluent-Project already exists " + studyFileName)
                print(
                    'and "overwriteExisting"-flag is set to False or not existing in Config-File'
                )
                print('Skipping Parametric Study "' + studyName + '"\n')
                break
        else:
            if runExisting:
                print("Specified Fluent-Project does not exist " + studyFileName)
                print('Skipping Parametric Study "' + studyName + '"\n')
                break

        # Check if a new Project should be created or an existing is executed
        if not runExisting:
            # Read Ref Case
            # solver.file.read_case_data(file_type="case-data", file_name=refCase)
            solver.tui.file.read_case_data(refCase)

            # Initialize a new parametric study
            if fluent_study is None:
                # fluent_study = ParametricStudy(solver.parametric_studies).initialize()
                solver.parametric_studies.initialize(project_filename=studyName)
                psname = refCase + "-Solve"
                fluent_study = solver.parametric_studies[psname]

            designPointCounter = 1
            definitionList = studyEl.get("definition")

            for studyDef in definitionList:
                useScaleFactor = studyDef.get("useScaleFactor")
                ipList = studyDef.get("inputparameters")
                valueListArray = studyDef.get("valueList")
                numDPs = len(valueListArray[0])
                for dpIndex in range(numDPs):
                    # new_dp = fluent_study.add_design_point()
                    fluent_study.design_points.duplicate(design_point="Base DP")
                    designPointName = "DP" + str(designPointCounter)
                    # new_dp = {"BC_P_Out": 0.}
                    new_dp = fluent_study.design_points[designPointName]
                    numIPs = len(ipList)
                    for ipIndex in range(numIPs):
                        ipName = ipList[ipIndex]
                        modValue = valueListArray[ipIndex][dpIndex]
                        if useScaleFactor:
                            ref_dp = fluent_study.design_points[
                                "Base DP"
                            ].input_parameters()
                            # ref_dp = {"ip1": 2.0, "BC_P_Out": 1.0, "ip3": 3.0}
                            refValue = ref_dp[ipName]
                            modValue = refValue * modValue

                        # new_dp[ipName] = modValue
                        new_dp.input_parameters = {ipName: modValue}
                        new_dp.write_data = studyEl.get("write_data")

                    # fluent_study.design_points[designPointName].input_parameters = new_dp
                    designPointCounter = designPointCounter + 1

            # Set Update Method
            updateFromBaseDP = studyEl.get("updateFromBaseDP", False)
            if updateFromBaseDP:
                solver.tui.parametric_study.study.use_base_data("yes")
            else:
                solver.tui.parametric_study.study.use_data_of_previous_dp("yes")

            # Run all Design Points
            if studyEl.get("updateAllDPs", False):
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
            if studyIndex == 0:
                solver.file.parametric_project.save()
            else:
                solver.file.parametric_project.save_as(project_filename=studyName)
            #

            if studyIndex < (len(studyDict) - 1):
                # Delete DesignPoints Current Study
                # fluent_study = fluent_study.duplicate()
                for dpIndex in range(designPointCounter - 1):
                    designPointName = "DP" + str(dpIndex + 1)
                    fluent_study.design_points.delete_design_points(
                        design_points=designPointName
                    )
            studyIndex = studyIndex + 1

        else:
            # Load Existing Project
            flworking_Dir = data.get("launching")["workingDir"]
            # studyFileName = studyName + ".flprj"
            solver.file.parametric_project.open(project_filename=studyFileName)
            psname = refCase + "-Solve"
            fluent_study = solver.parametric_studies[psname]

            # Set Update Method
            updateFromBaseDP = studyEl.get("updateFromBaseDP", False)
            if updateFromBaseDP:
                solver.tui.parametric_study.study.use_base_data("yes")

            else:
                solver.tui.parametric_study.study.use_data_of_previous_dp("yes")

            # Run all Design Points
            if studyEl.get("updateAllDPs", False):
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

    print("All Studies finished")


def studyPlot(data):

    print("Running Function StudyPlot ...")
    studyDict = data.get("studies")
    for studyName in studyDict:
        
        flworking_Dir = data.get("launching")["workingDir"]
        design_point_table_path = flworking_Dir + "/" + studyName + "_dp_table.csv"
        design_point_table_path = os.path.normpath(design_point_table_path)
        if os.path.isfile(design_point_table_path):
            # read in design point table csv
            design_point_table = pd.read_csv(
                design_point_table_path, delimiter=",", header=0
            )

            fig = utilities.plotOperatingMap(design_point_table)
            fig
            study_plot_name = (
                flworking_Dir + "/" + studyName + "_operating_point_map.svg"
            )
            print("generating figure: " + study_plot_name)
            plt.savefig(study_plot_name)
        else:
            print("No designpoint table CSV-file found")

    print("Running Function StudyPlot finished!")
