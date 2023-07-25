import os
from ptw_subroutines import utilities
import matplotlib.pyplot as plt
import json

def study(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = utilities.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="parametricstudy",
        defaultName="study_01",
    )

    print(f"Running ParamatricStudy-Function '{functionName}' ...")
    if functionName == "study_01":
        study01(data, solver)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Parametric Study!'
        )

    print(f"\nRunning ParamatricStudy-Function '{functionName}'...  finished!\n")


def study01(data, solver):
    studyDict = data.get("studies")
    flworking_Dir = data.get("launching")["workingDir"]

    # Init variables
    fluent_study = None
    studyIndex = 0

    for studyName in studyDict:
        studyEl = studyDict[studyName]
        print(f"\nRunning Study '{studyName}'...\n")
        # Check if study should be executed
        if studyEl.setdefault("skip_execution", False):
            print(
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
            refCaseFilePath = os.path.join(flworking_Dir, refCase)
            if studyIndex == 0:
                solver.file.read_case_data(
                    file_type="case-data", file_name=refCaseFilePath
                )
            else:
                tuicommand = 'file/rcd "' + refCaseFilePath + '" yes'
                solver.execute_tui(tuicommand)
                # solver.tui.file.read_case_data(refCaseFilePath, "yes")

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
                print("Using base case initialization method")
            elif initMethod == "baseDP":
                print("Using base DP data for Initialization")
                solver.tui.parametric_study.study.use_base_data("yes")
            elif initMethod == "prevDP":
                print("Using previous DP data for Initialization")
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

            initMethod = studyEl.setdefault("initMethod", "baseDP")
            if initMethod == "base_ini":
                print("Using base case initialization method")
            elif initMethod == "baseDP":
                print("Using base DP data for Initialization")
                solver.tui.parametric_study.study.use_base_data("yes")
            elif initMethod == "prevDP":
                print("Using previous DP data for Initialization")
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

        # Skipping after first study has been finished
        print(f"\nRunning Study '{studyName}' finished!\n")
        # break

        # Extract CoV information and store in temporary file for post processing
        covDict = solver.solution.monitor.convergence_conditions.convergence_reports()
        baseCaseName = studyDict[studyName].get('refCaseFilename')
        pathtostudy = os.path.join(
            flworking_Dir, f"{studyName}.cffdb", f"{baseCaseName}-Solve"
        )
        # Check if the folder exists
        if not os.path.exists(pathtostudy):
            print('No Study data has been found!\n')
            print('Skipping Post-Processing!')
        else:
            # Define the file path
            temp_data_path = os.path.join(pathtostudy, "temp_data.json")

            # Save the dictionary as a JSON file
            with open(temp_data_path, "w") as file:
                json.dump(covDict, file)

    print("All Studies finished")


def studyPlot(data):
    # Only working in external mode
    try:
        import pandas as pd
    except ImportError as e:
        print(f"ImportError! Could not import lib: {str(e)}")
        print(f"Skipping studyPlot function!")
        return

    print("Running Function StudyPlot ...")
    studyDict = data.get("studies")
    for studyName in studyDict:

        studyData = studyDict[studyName]
        runPostProc = studyData.setdefault("postProc", True)
        studyData["postProc"] = runPostProc
        
        if runPostProc:
            flworking_Dir = data.get("launching")["workingDir"]
            baseCaseName = studyDict[studyName].get('refCaseFilename')
            pathtostudy = os.path.join(flworking_Dir,f"{studyName}.cffdb",f"{baseCaseName}-Solve")
            baseCaseName = studyDict[studyName].get("refCaseFilename")
            pathtostudy = os.path.join(
                flworking_Dir, f"{studyName}.cffdb", f"{baseCaseName}-Solve"
            )

            # Define a Folder to store plots
            studyPlotFolder = os.path.join(flworking_Dir,f'{studyName}_study_plots')
            os.makedirs(studyPlotFolder, exist_ok=True)  # Create the folder if it doesn't exist
            
            # Get the study result table
            result_df, cov_df_list,residual_df_list, mp_df_list = utilities.getStudyReports(pathtostudy)

            # Extract CoV information for traffic light notation
            cov_data_exists = False
            temp_data_path = os.path.join(pathtostudy, "temp_data.json")
            if os.path.exists(temp_data_path):
                cov_data_exists = True
                with open(temp_data_path, "r") as file:
                    covDict = json.load(file)
                filtCovDict = {
                    key: value
                    for key, value in covDict.items()
                    if value.get("active", False) and value.get("cov", False)
                }
            else:
                print('No base case information for CoVs has been found!')
                cov_data_exists = False



            # Loop through each DataFrame in the list
            for idx, (cov_df, residual_df, mp_df) in enumerate(zip(cov_df_list, residual_df_list, mp_df_list), 1):  # Start index from 1
                # Create the subdirectory with the naming convention "DP<noOfEntry>"
                dp_name = result_df.iloc[idx-1]["Design Point"]
                dpdirectory_path = os.path.join(studyPlotFolder, dp_name)

                # Create the subdirectory if it doesn't exist
                if not os.path.exists(dpdirectory_path):
                    os.makedirs(dpdirectory_path
                )
                if not cov_df.empty:

                    cov_df.reset_index(inplace=True)

                    # Get the list of columns excluding 'Iteration'
                    y_columns = cov_df.columns[2:]
                    if cov_data_exists:
                        filtered_y_columns = [col for col in y_columns if any(col.startswith(key[:-4]) for key in filtCovDict)]
                    else:
                        filtered_y_columns = y_columns

                    plt.figure(figsize=(10, 6))
                    # Plot each column separately on the same plot
                    for col in filtered_y_columns:
                        plt.plot(cov_df['Iteration'], cov_df[col], label=col)
                    
                    plt.xlabel('Iteration')
                    plt.ylabel('')
                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                    plt.title(f'Coefficient of Variation (CoV) - {dp_name}')
                    plt.grid(True)
                    plt.yscale('log')

                    # Save the plot in the /test/[plot] folder
                    plot_filename = os.path.join(dpdirectory_path, f'cov_plot_{dp_name}.png')
                    plt.tight_layout()
                    plt.savefig(plot_filename)
                    plt.close()  # Close the figure to release memory

                if not mp_df.empty:
                    mp_df.reset_index(inplace=True)

                    # Get the list of columns excluding 'Iteration'
                    y_columns = mp_df.columns[2:]

                    # Plot each column separately and store them in separate plots
                    for col in y_columns:
                        plt.figure()  # Create a new figure for each plot
                        plt.plot(mp_df['Iteration'], mp_df[col])
                        plt.xlabel('Iteration')
                        plt.ylabel(col)
                        plt.title(f'{col} - {dp_name}')
                        plt.grid(True)

                        # Save the plot in the /test/[plot] folder
                        plot_filename = os.path.join(dpdirectory_path, f'mp_plot_{col}_{dp_name}.png')
                        plt.savefig(plot_filename)
                        plt.close()  # Close the figure to release memory

                if not residual_df.empty:
    
                    residual_df.reset_index(inplace=True)
                    # Get the list of columns excluding 'Iteration'
                    y_columns = residual_df.columns[2:]
                    plt.figure(figsize=(10, 6))
                    # Plot each column separately on the same plot
                    for col in y_columns:
                        plt.plot(residual_df['Iterations'], residual_df[col], label=col)

                    plt.xlabel('Iteration')
                    plt.ylabel('')
                    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                    plt.title(f'Residuals - {dp_name}')
                    plt.grid(True)
                    plt.yscale('log')

                    # Save the plot in the /test/[plot] folder
                    plot_filename = os.path.join(dpdirectory_path, f'residual_plot_{dp_name}.png')
                    plt.tight_layout()
                    plt.savefig(plot_filename)
                    plt.close()  # Close the figure to release memory

            # check if study data is available
            if result_df.empty:
                continue


            # Get the list of columns ending with '-cov'
            cov_columns = [col for col in result_df.columns if col.endswith("-cov")]

            # Initialize a list to store convergence results
            convergence_results = []

            # Check if Convergence is reached
            for _, row in result_df.iterrows():
                convergence = "good"
                for col in cov_columns:
                    cov_criterion = filtCovDict.get(col, {}).get("stop_criterion",1e-4)
                    if cov_criterion is not None:
                        if row[col] > 5 * cov_criterion:
                            convergence = 'poor'
                            break
                        elif row[col] > cov_criterion:
                            convergence = "ok"

                convergence_results.append(convergence)

            # Priority order to consider volume/massflow for plotting
            mf_fallback_columns = [
                "rep-mp-in-massflow-360",
                "rep-mp-out-massflow-360",
                "rep-mp-in-massflow",
                "rep-mp-out-massflow",
            ]
            vf_fallback_columns = [
                "rep-mp-in-volumeflow-360",
                "rep-mp-out-volumeflow-360",
                "rep-mp-in-volumeflow",
                "rep-mp-out-volumeflow",
            ]

            # Combine volume flow and mass flow columns
            fallback_columns = vf_fallback_columns + mf_fallback_columns

            # Sort the DataFrame using the first available definition in the fallback list
            sorted_df = None
            for column in fallback_columns:
                if column in result_df.columns:
                    sorted_df = result_df.sort_values(
                        by=column, ascending=True, ignore_index=True
                    )
                    break

            MP_MassFlow = None
            for column in mf_fallback_columns:
                if column in sorted_df.columns:
                    MP_MassFlow = sorted_df[column].values
                    break
            MP_VolumeFlow = None
            for column in vf_fallback_columns:
                if column in sorted_df.columns:
                    MP_VolumeFlow = sorted_df[column].values
                    break

            # Assign the convergence results to the 'convergence' column
            sorted_df["convergence"] = convergence_results
            # Filter out the dataframe to plot monitor points
            plot_df = sorted_df.iloc[:, 1:-1].drop(
                columns=[
                    col
                    for col in sorted_df.columns
                    if "-cov" in col or col in fallback_columns
                ]
            )
            # Generate traffic light notation for convergence
            color_map = {'good': 'green', 'ok': 'yellow', 'poor': 'red'}
            colors = sorted_df['convergence'].map(color_map)

            # Create Plots for monitor points with mass flow, volume flow or both
            if MP_MassFlow is not None and MP_VolumeFlow is not None:
                for column in plot_df.columns:
                    y_values = plot_df[column].values
                    # Create Plot with massflow
                    plt.figure()
                    figure_plot = utilities.plot_figure(
                        MP_MassFlow,
                        y_values,
                        "mass flow [kg/s]",
                        column,
                        colors,
                        cov_criterion,
                    )
                    plt.savefig(
                        os.path.join(studyPlotFolder + f"/plot_massflow_{column}.svg")
                    )
                    plt.close()
                    # Create Plot with massflow
                    plt.figure()
                    figure_plot = utilities.plot_figure(
                        MP_VolumeFlow, y_values, "volume flow", colors, cov_criterion
                    )
                    plt.savefig(
                        os.path.join(studyPlotFolder + f"/plot_volumeflow_{column}.svg")
                    )
                    plt.close()
            elif MP_MassFlow is not None and MP_VolumeFlow is None:
                for column in plot_df.columns:
                    y_values = plot_df[column].values
                    # Create Plot with massflow
                    plt.figure()
                    figure_plot = utilities.plot_figure(
                        MP_MassFlow, y_values, "mass flow", column, colors, cov_criterion
                    )
                    plt.savefig(
                        os.path.join(studyPlotFolder + f"/plot_massflow_{column}.svg")
                    )
                    plt.close()
            elif MP_VolumeFlow is not None and MP_MassFlow is None:
                for column in plot_df.columns:
                    y_values = plot_df[column].values
                    # Create Plot with volume flow
                    plt.figure()
                    figure_plot = utilities.plot_figure(
                        MP_VolumeFlow,
                        y_values,
                        "volume flow",
                        column,
                        colors,
                        cov_criterion,
                    )
                    plt.savefig(
                        os.path.join(studyPlotFolder + f"/plot_volumeflow_{column}.svg")
                    )
                    plt.close()
            
            sorted_df.to_csv(studyPlotFolder + f"/plot_table_{studyName}.csv", index=None)

    print("Running Function StudyPlot finished!")
