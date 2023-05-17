import matplotlib.pyplot as plt
import os
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

    # Init variables
    fluent_study = None
    studyIndex = 0

    for studyName in studyDict:
        studyEl = studyDict[studyName]
        # Getting all input data from json file
        #datapath = studyEl.get("datapath")
        refCase = studyEl.get("refCaseFilename")
        runExisting = studyEl.get("runExistingProject", False)

        # Do some checks to skip if a run is not possible
        studyFileName = data.get("launching")["workingDir"] + "/" + studyName + ".flprj"
        studyFileName = os.path.normpath(studyFileName)
        if os.path.isfile(studyFileName):
            if not studyEl.get("overwriteExisting", False):
                print("Fluent-Project already exists " + studyFileName)
                print(
                    'and "overwriteExisting"-flag is set to False or not existing in Config-File'
                )
                print('Skipping Parametric Study "' + studyName + '"')
                break
        else:
            if runExisting:
                print("Specified Fluent-Project does not exist " + studyFileName)
                print('Skipping Parametric Study "' + studyName + '"')
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
            solver.tui.parametric_study.study.use_data_of_previous_dp("yes")
            # solver.tui.parametric_study.study.use_base_data('yes')

            # Run all Design Points
            if studyEl.get("updateAllDPs", False):
                fluent_study.design_points.update_all()

            # Export results to table
            design_point_table = studyName + "_dp_table.csv"
            solver.parametric_studies.export_design_table(filepath=design_point_table)

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
            # studyFileName = studyName + ".flprj"
            solver.file.parametric_project.open(project_filename=studyFileName)
            psname = refCase + "-Solve"
            fluent_study = solver.parametric_studies[psname]

            # Set Update Method
            solver.tui.parametric_study.study.use_data_of_previous_dp("yes")

            # Run all Design Points
            if studyEl.get("updateAllDPs", False):
                fluent_study.design_points.update_all()

            # Export results to table
            design_point_table = studyName + "_dp_table.csv"
            solver.parametric_studies.export_design_table(filepath=design_point_table)

            # Save Study
            solver.file.parametric_project.save()

    print("All Studies finished")


def studyPlot(data):
    print('Running Function StudyPlot ...')
    studyDict = data.get("studies")
    for studyName in studyDict:
        flworking_Dir = data.get("launching")["workingDir"]
        design_point_table_path = flworking_Dir + "/" + studyName + "_dp_table.csv"
        design_point_table_path = os.path.normpath(design_point_table_path)
        if os.path.isfile(design_point_table_path):
            design_point_table = pd.read_csv(
                design_point_table_path, delimiter=",", header=0
            )

            # extract unit row and drop from table
            units = design_point_table.iloc[0, :]
            design_point_table = design_point_table.drop(0, axis=0)

            # clear out NaN values for plot data
            MP_MassFlow = pd.to_numeric(
                design_point_table.loc[:, "MP_IN_MassFlow"], errors="coerce"
            )
            MP_PRt = pd.to_numeric(
                design_point_table.loc[:, "MP_PRt"], errors="coerce"
            )
            MP_Isentropic_Efficiency = pd.to_numeric(
                design_point_table.loc[:, "MP_Isentropic_Efficiency"], errors="coerce"
            )

            # generate plots
            fig, axs = plt.subplots(1, 2, figsize=(12, 6))
            fig.suptitle("Compressor Map")
            # Total Pressure Ratio
            axs[0].set_xlim(
                [MP_MassFlow.min() * 0.99, MP_MassFlow.max() * 1.01]
            )
            axs[0].set_ylim([MP_PRt.min() * 0.99, MP_PRt.max() * 1.01])
            axs[0].grid()
            axs[0].set_xlabel("reduced mass flow rate [kg/s]")
            axs[0].set_ylabel("total pressure ratio [-]")
            axs[0].plot(MP_MassFlow, MP_PRt, marker="^")

            # Isentropic Efficiency
            axs[1].set_xlim(
                [MP_MassFlow.min() * 0.99, MP_MassFlow.max() * 1.01]
            )
            axs[1].set_ylim(
                [
                    MP_Isentropic_Efficiency.min() * 0.99,
                    MP_Isentropic_Efficiency.max() * 1.01,
                ]
            )
            axs[1].grid()
            axs[1].plot(MP_MassFlow, MP_Isentropic_Efficiency, marker="^")
            axs[1].set_xlabel("reduced mass flow rate [kg/s]")
            axs[1].set_ylabel("isentropic efficiency [-]")

            study_plot_name = flworking_Dir + "/" + studyName + "_compressor_map.svg"
            study_plot_name = os.path.normpath(study_plot_name)
            print("generating figure: " + study_plot_name)
            plt.savefig(study_plot_name)
        else:
            print("No designpoint table CSV-file found")

    print('Running Function StudyPlot finished!')
