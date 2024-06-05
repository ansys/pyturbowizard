import os
import matplotlib.pyplot as plt

# Logger
from ptw_subroutines.utils import (
    ptw_logger,
    postproc_utils,
    dict_utils,
    fluent_utils,
    misc_utils,
)

logger = ptw_logger.getLogger()


def post(data, solver, functionEl, launchEl, trn_name, gpu):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="postproc",
        defaultName="post_01",
    )

    logger.info(f"Running Postprocessing Function '{functionName}' ...")
    if functionName == "post_01":
        post_01(data, solver, launchEl, trn_name, gpu)
    else:
        logger.info(
            f"Prescribed Function '{functionName}' not known. Skipping Postprocessing!"
        )

    logger.info("Running Postprocessing Function... finished!")


def post_01(data, solver, launchEl, trn_name, gpu):
    fl_workingDir = launchEl.get("workingDir")
    caseFilename = data["caseFilename"]
    caseOutPath = misc_utils.ptw_output(
        fl_workingDir=fl_workingDir, case_name=caseFilename
    )
    filename = os.path.join(
        caseOutPath,
        data["results"].setdefault("filename_outputParameter", "outParameters.out"),
    )

    # solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
    tuicommand = (
        'define parameters output-parameters write-all-to-file "' + filename + '"'
    )
    solver.execute_tui(tuicommand)
    filename = os.path.join(
        caseOutPath, data["results"].setdefault("filename_summary", "report.sum")
    )
    solver.results.report.summary(write_to_file=True, file_name=filename)

    # Write out system time
    solver.tui.report.system.time_stats()
    # solver.report.system.time_statistics()

    # Save Residual Plot
    # plot_folder = os.path.join(caseOutPath, f"plots")
    # os.makedirs(plot_folder, exist_ok=True)  # Create the folder if it doesn't exist
    # residualFileName = os.path.join(plot_folder, "residuals.png")

    # Scaling does not work (set resolution)
    # solver.tui.plot.residuals()
    # solver.execute_tui("/display/set/picture/driver png")
    # solver.tui.display.set_window_by_name("residuals")
    # solver.tui.display.set.picture.x_resolution(1200)
    # solver.tui.display.set.picture.y_resolution(800)
    # solver.tui.display.save_picture(residualFileName,"ok")
    # solver.execute_tui("/display/set/picture/driver avz")

    ## write report table
    createReportTable(
        data=data,
        fl_workingDir=fl_workingDir,
        solver=solver,
        trn_filename=trn_name,
        gpu=gpu,
    )

    ## move case span-plots to case output folder
    spansSurf = data["results"].get("span_plot_height")
    contVars = data["results"].get("span_plot_var")
    if (spansSurf is not None) and (contVars is not None):
        misc_utils.move_files(
            source_dir=fl_workingDir,
            target_dir=caseOutPath,
            filename_wildcard="span*plot.avz",
        )

    return


def createReportTable(data: dict, fl_workingDir, solver, trn_filename, gpu):
    try:
        import pandas as pd
    except ImportError as e:
        logger.info(f"ImportError! Could not import lib: {str(e)}")
        logger.info(f"Skipping writing custom reporttable!")
        return
    caseFilename = data["caseFilename"]
    logger.info(f"Creating a report table for {caseFilename}")
    # get report file
    # read in table of report-mp and get last row

    # Filter for file names starting with "report"
    caseOutPath = misc_utils.ptw_output(
        fl_workingDir=fl_workingDir, case_name=caseFilename
    )
    reportFileName = "report"
    report_file = os.path.join(caseOutPath, "report.out")
    file_names = os.listdir(caseOutPath)
    filtered_files = [
        file
        for file in file_names
        if file.startswith(reportFileName) and file.endswith(".out")
    ]
    report_values = pd.DataFrame()
    cov_df = pd.DataFrame()
    mp_df = pd.DataFrame()

    if len(filtered_files) > 0:
        if len(filtered_files) > 1:
            logger.warning(f"Multiple .out-files found: {filtered_files}")
        # Find the file name with the highest number
        report_file = max(
            filtered_files,
            key=lambda x: [int(num) for num in x.split("_") if num.isdigit()],
        )
        report_file = os.path.join(caseOutPath, report_file)
        report_values, cov_df, mp_df = postproc_utils.calcCov(report_file)
        logger.info(f"Using: {report_file} for Evaluation.")

    else:
        logger.info("No Report File found: data not included in final report")

    # Write CoV and MP Plot
    plot_folder = os.path.join(caseOutPath, f"plots")
    os.makedirs(plot_folder, exist_ok=True)  # Create the folder if it doesn't exist
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
            plt.title(f"{col} - {caseFilename}")
            plt.grid(True)

            # Save the plot in folder
            plot_filename = os.path.join(plot_folder, f"mp_plot_{col}.png")
            logger.info(f"Writing Monitor Plot to Directory: {plot_filename}")
            plt.savefig(plot_filename)
            plt.close()  # Close the figure to release memory
    else:
        logger.info("Missing Report File data: Monitor Plots not created")

    if (not cov_df.empty) and (not gpu):
        # Get CoV information
        covDict = solver.solution.monitor.convergence_conditions.convergence_reports()
        if covDict is not None:
            filtCovDict = {
                key: value
                for key, value in covDict.items()
                if value.get("active", False) and value.get("cov", False)
            }

            cov_df.reset_index(inplace=True)

            # Get the list of columns excluding 'Iteration'
            y_columns = cov_df.columns[2:]
            filtered_y_columns = [
                col
                for col in y_columns
                if any(col.startswith(key[:-4]) for key in filtCovDict)
            ]

            plt.figure(figsize=(10, 6))
            # Plot each column separately on the same plot
            for col in filtered_y_columns:
                plt.plot(cov_df["Iteration"], cov_df[col], label=col)

            plt.xlabel("Iteration")
            plt.ylabel("")
            plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
            plt.title(f"Coefficient of Variation (CoV 50) - {caseFilename}")
            plt.grid(True)
            plt.yscale("log")

            # Save the plot in folder
            plot_filename = os.path.join(plot_folder, f"cov_plot.png")
            plt.tight_layout()
            logger.info(f"Writing CoV Plot to Directory: {plot_filename}")
            plt.savefig(plot_filename)
            plt.close()  # Close the figure to release memory
        else:
            logger.info("No CoVs have been specified: CoV Plot not created")
    elif (not cov_df.empty) and gpu:
        logger.info("CoVs are not supported in GPU solver: CoV Plot not created")
    else:
        logger.info("Missing Report File data: CoV Plot not created")

    # Read in transcript file
    caseOutPath = misc_utils.ptw_output(
        fl_workingDir=fl_workingDir, case_name=caseFilename
    )
    trnFilePath = os.path.join(caseOutPath, trn_filename)
    report_table, res_df = postproc_utils.evaluateTranscript(
        trnFilePath=trnFilePath, caseFilename=caseFilename, solver=solver
    )

    # Select columns from report_table
    columns_before_report_values = report_table.iloc[:, :2]
    columns_after_report_values = report_table.iloc[:, 2:]

    # Concatenate DataFrames
    result_table = pd.concat(
        [columns_before_report_values, report_values, columns_after_report_values],
        axis=1,
    )

    # Report Table File-Name to csv
    resultTableName = data["results"].setdefault(
        "filename_reporttable", "reporttable.csv"
    )
    reportTableFileName = os.path.join(caseOutPath, resultTableName)
    logger.info("Writing Report Table to: " + reportTableFileName)
    result_table.to_csv(reportTableFileName, index=None)

    # Residual Dataframe to csv
    resiudalFileName = "residuals.csv"
    resiudalFileName = os.path.join(caseOutPath, resiudalFileName)
    res_df.to_csv(resiudalFileName)

    # Plot Resiuduals
    # Get the list of columns excluding 'Iteration'
    y_columns = res_df.columns[2:]
    plt.figure(figsize=(10, 6))
    # Plot each column separately on the same plot
    for col in y_columns:
        plt.plot(res_df["iter"], res_df[col], label=col)

    plt.xlabel("Iteration")
    plt.ylabel("")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.title(f"Residuals - {caseFilename}")
    plt.grid(True)
    plt.yscale("log")

    # Save the plot in the folder
    plot_filename = os.path.join(caseOutPath, "plots/residual_plot.png")
    plt.tight_layout()
    logger.info(f"Writing Residual Plot to Directory: {plot_filename}")
    plt.savefig(plot_filename)
    plt.close()  # Close the figure to release memory
    return


def mergeReportTables(turboData, solver):
    # Only working with pandas lib
    try:
        import pandas as pd
    except ImportError as e:
        logger.info(f"ImportError! Could not import lib: {str(e)}")
        logger.info("Skipping mergeReportTables function!")
        return

    logger.info("Merging Report-Tables of all defined cases")

    fl_workingDir = turboData["launching"].get("workingDir")
    caseDict = turboData.get("cases")
    ptwOutPath = misc_utils.ptw_output(fl_workingDir=fl_workingDir)
    if caseDict is not None:
        reportFiles = []
        for casename in caseDict:
            caseEl = turboData["cases"][casename]
            caseFilename = caseEl["caseFilename"]
            resultEl = caseEl.get("results")
            if resultEl is not None:
                reportTableName = resultEl.setdefault(
                    "filename_reporttable", "reporttable.csv"
                )
                reportTableName = caseFilename + "_" + reportTableName
                caseOutPath = misc_utils.ptw_output(
                    fl_workingDir=fl_workingDir, case_name=caseFilename
                )
                reportTableFilePath = os.path.join(caseOutPath, reportTableName)
                if os.path.isfile(reportTableFilePath):
                    reportFiles.append(reportTableFilePath)

        if len(reportFiles) > 1:
            df = pd.concat((pd.read_csv(f, header=0) for f in reportFiles))
            merged_file_name = os.path.join(ptwOutPath, "merged_reporttable.csv")
            logger.info(f"Writing merged report-file: {merged_file_name}")
            df.to_csv(merged_file_name)

    return
