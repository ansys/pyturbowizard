import os
import matplotlib.pyplot as plt
import json

# Logger
from ptw_subroutines.utils import ptw_logger, dict_utils, postproc_utils

logger = ptw_logger.getLogger()


def study_post(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="parametricstudy_post",
        defaultName="study_post_01",
    )

    logger.info(f"Running ParamatricStudy-Postprocessing Function '{functionName}' ...")
    if functionName == "study_post_01":
        study_post_01(data=data, solver=solver)
    else:
        logger.info(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Paramatric-Study-Postprocessing Function!'
        )

    logger.info(
        f"Running ParamatricStudy-Postprocessing Function '{functionName}'...  finished!"
    )


def study_post_01(data, solver):
    # Only working in external mode
    try:
        import pandas as pd
    except ImportError as e:
        logger.info(f"ImportError! Could not import lib: {str(e)}")
        logger.info(f"Skipping studyPlot function!")
        return

    logger.info("Running Function StudyPlot ...")
    studyDict = data.get("studies")
    for studyName in studyDict:
        studyData = studyDict[studyName]
        runPostProc = studyData.setdefault("postProc", True)
        studyData["postProc"] = runPostProc

        if runPostProc:
            flworking_Dir = data.get("launching")["workingDir"]
            baseCaseName = studyData.get("refCaseFilename")
            pathtostudy = os.path.join(
                flworking_Dir, f"{studyName}.cffdb", f"{baseCaseName}-Solve"
            )

            # Define a Folder to store plots
            studyPlotFolder = os.path.join(flworking_Dir, f"{studyName}_study_plots")
            os.makedirs(
                studyPlotFolder, exist_ok=True
            )  # Create the folder if it doesn't exist
            logger.info(f"Writing Study Plots to Directory: {studyPlotFolder}")
            # Get the study result table
            (
                result_df,
                cov_df_list,
                residual_df_list,
                mp_df_list,
            ) = postproc_utils.getStudyReports(pathtostudy)

            # check if study data is available
            if result_df.empty:
                continue

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
                logger.info("No base case information for CoVs has been found!")
                cov_data_exists = False

            # Loop through each DataFrame in the list
            for idx, (cov_df, residual_df, mp_df) in enumerate(
                zip(cov_df_list, residual_df_list, mp_df_list), 1
            ):  # Start index from 1
                # Create the subdirectory with the naming convention "DP<noOfEntry>"
                dp_name = result_df.iloc[idx - 1]["Design Point"]
                dpdirectory_path = os.path.join(studyPlotFolder, dp_name)

                # Create the subdirectory if it doesn't exist
                if not os.path.exists(dpdirectory_path):
                    os.makedirs(dpdirectory_path)
                if not cov_df.empty:
                    cov_df.reset_index(inplace=True)

                    # Get the list of columns excluding 'Iteration'
                    y_columns = cov_df.columns[2:]
                    if cov_data_exists:
                        filtered_y_columns = [
                            col
                            for col in y_columns
                            if any(col.startswith(key[:-4]) for key in filtCovDict)
                        ]
                    else:
                        filtered_y_columns = y_columns

                    plt.figure(figsize=(10, 6))
                    # Plot each column separately on the same plot
                    for col in filtered_y_columns:
                        plt.plot(cov_df["Iteration"], cov_df[col], label=col)

                    plt.xlabel("Iteration")
                    plt.ylabel("")
                    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
                    plt.title(f"Coefficient of Variation (CoV) - {dp_name}")
                    plt.grid(True)
                    plt.yscale("log")

                    # Save the plot in folder
                    plot_filename = os.path.join(
                        dpdirectory_path, f"cov_plot_{dp_name}.png"
                    )
                    plt.tight_layout()
                    logger.info(f"Writing CoV Plot to Directory: {plot_filename}")
                    plt.savefig(plot_filename)
                    plt.close()  # Close the figure to release memory

                if not mp_df.empty:
                    mp_df.reset_index(inplace=True)

                    # Get the list of columns excluding 'Iteration'
                    y_columns = mp_df.columns[2:]

                    # Plot each column separately and store them in separate plots
                    for col in y_columns:
                        plt.figure()  # Create a new figure for each plot
                        plt.plot(mp_df["Iteration"], mp_df[col])
                        plt.xlabel("Iteration")
                        plt.ylabel(col)
                        plt.title(f"{col} - {dp_name}")
                        plt.grid(True)

                        # Save the plot in the /test/[plot] folder
                        plot_filename = os.path.join(
                            dpdirectory_path, f"mp_plot_{col}_{dp_name}.png"
                        )
                        logger.info(
                            f"Writing Monitor Plot to Directory: {plot_filename}"
                        )
                        plt.savefig(plot_filename)
                        plt.close()  # Close the figure to release memory

                if not residual_df.empty:
                    residual_df.reset_index(inplace=True)
                    # Get the list of columns excluding 'Iteration'
                    y_columns = residual_df.columns[2:]
                    plt.figure(figsize=(10, 6))
                    # Plot each column separately on the same plot
                    for col in y_columns:
                        plt.plot(residual_df["Iterations"], residual_df[col], label=col)

                    plt.xlabel("Iteration")
                    plt.ylabel("")
                    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
                    plt.title(f"Residuals - {dp_name}")
                    plt.grid(True)
                    plt.yscale("log")

                    # Save the plot in the folder
                    plot_filename = os.path.join(
                        dpdirectory_path, f"residual_plot_{dp_name}.png"
                    )
                    plt.tight_layout()
                    logger.info(f"Writing Residual Plot to Directory: {plot_filename}")
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
                    cov_criterion = filtCovDict.get(col, {}).get("stop_criterion", 1e-4)
                    if cov_criterion is not None:
                        if row[col] > 5 * cov_criterion:
                            convergence = "poor"
                            break
                        elif row[col] > cov_criterion:
                            convergence = "ok"

                convergence_results.append(convergence)

            # Assign the convergence results to the 'convergence' column
            result_df["convergence"] = convergence_results

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

            # Filter out the dataframe to plot monitor points
            plot_df = sorted_df.iloc[:, 1:-1].drop(
                columns=[
                    col
                    for col in sorted_df.columns
                    if "-cov" in col or col in fallback_columns
                ]
            )
            # Generate traffic light notation for convergence
            color_map = {"good": "green", "ok": "yellow", "poor": "red"}
            colors = sorted_df["convergence"].map(color_map)

            # Create Plots for monitor points with mass flow, volume flow or both
            if MP_MassFlow is not None and MP_VolumeFlow is not None:
                for column in plot_df.columns:
                    y_values = plot_df[column].values
                    # Create Plot with massflow
                    plt.figure()
                    figure_plot = postproc_utils.plot_figure(
                        MP_MassFlow,
                        y_values,
                        "mass flow [kg/s]",
                        column,
                        colors,
                        cov_criterion,
                    )
                    plot_filename = os.path.join(
                        studyPlotFolder + f"/plot_massflow_{column}.svg"
                    )
                    logger.info(
                        f"Writing Operating Map Plot to Directory: {plot_filename}"
                    )
                    plt.savefig(plot_filename)
                    plt.close()
                    # Create Plot with volume flow
                    plt.figure()
                    figure_plot = postproc_utils.plot_figure(
                        MP_VolumeFlow, y_values, "volume flow", colors, cov_criterion
                    )

                    plot_filename = os.path.join(
                        studyPlotFolder + f"/plot_volumeflow_{column}.svg"
                    )
                    logger.info(
                        f"Writing Operating Map Plot to Directory: {plot_filename}"
                    )
                    plt.savefig(plot_filename)
                    plt.close()
            elif MP_MassFlow is not None and MP_VolumeFlow is None:
                for column in plot_df.columns:
                    y_values = plot_df[column].values
                    # Create Plot with massflow
                    plt.figure()
                    figure_plot = postproc_utils.plot_figure(
                        MP_MassFlow,
                        y_values,
                        "mass flow",
                        column,
                        colors,
                        cov_criterion,
                    )
                    plot_filename = os.path.join(
                        studyPlotFolder + f"/plot_massflow_{column}.svg"
                    )
                    logger.info(
                        f"Writing Operating Map Plot to Directory: {plot_filename}"
                    )
                    plt.savefig(plot_filename)
                    plt.close()
            elif MP_VolumeFlow is not None and MP_MassFlow is None:
                for column in plot_df.columns:
                    y_values = plot_df[column].values
                    # Create Plot with volume flow
                    plt.figure()
                    figure_plot = postproc_utils.plot_figure(
                        MP_VolumeFlow,
                        y_values,
                        "volume flow",
                        column,
                        colors,
                        cov_criterion,
                    )
                    plot_filename = os.path.join(
                        studyPlotFolder + f"/plot_volumeflow_{column}.svg"
                    )
                    logger.info(
                        f"Writing Operating Map Plot to Directory: {plot_filename}"
                    )
                    plt.savefig(plot_filename)
                    plt.close()
            sorted_df.to_csv(
                studyPlotFolder + f"/plot_table_{studyName}.csv", index=None
            )

    logger.info("Running Function StudyPlot finished!")
