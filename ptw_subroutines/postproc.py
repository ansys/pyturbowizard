import os
import matplotlib.pyplot as plt

# Logger
from ptw_subroutines.utils import ptw_logger, postproc_utils, dict_utils, fluent_utils, misc_utils

logger = ptw_logger.getLogger()


def post(data, solver, functionEl, launchEl, trn_name):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="postproc",
        defaultName="post_01",
    )

    logger.info('Running Postprocessing Function "' + functionName + '"...')
    if functionName == "post_01":
        post_01(data, solver, launchEl, trn_name)
    else:
        logger.info(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Postprocessing!'
        )

    logger.info("Running Postprocessing Function... finished!")


def post_01(data, solver, launchEl, trn_name):
    fl_workingDir = launchEl.get("workingDir")
    caseFilename = data["caseFilename"]
    caseOutPath = misc_utils.ptw_output(fl_workingDir=fl_workingDir,case_name=caseFilename)
    filename = os.path.join(caseOutPath, data["results"].setdefault("filename_outputParameter", "outParameters.out"))
    
    # solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
    tuicommand = (
        'define parameters output-parameters write-all-to-file "' + filename + '"'
    )
    solver.execute_tui(tuicommand)
    filename = os.path.join(caseOutPath, data["results"].setdefault("filename_summary", "report.sum"))
    solver.results.report.summary(write_to_file=True, file_name=filename)

    # Write out system time
    solver.tui.report.system.time_stats()
    #solver.report.system.time_statistics()

    ## write report table
    createReportTable(
        data=data, fl_workingDir=fl_workingDir, solver=solver, trn_filename=trn_name
    )

    return


def createReportTable(data: dict, fl_workingDir, solver, trn_filename):
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
    caseOutPath = misc_utils.ptw_output(fl_workingDir=fl_workingDir,case_name=caseFilename)
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

        if not cov_df.empty:
            # Get CoV information
            covDict = (
                solver.solution.monitor.convergence_conditions.convergence_reports()
            )
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
            plt.title(f"Coefficient of Variation (CoV)")
            plt.grid(True)
            plt.yscale("log")

            # Save the plot in folder
            plot_filename = os.path.join(plot_folder, f"cov_plot.png")
            plt.tight_layout()
            logger.info(f"Writing CoV Plot to Directory: {plot_filename}")
            plt.savefig(plot_filename)
            plt.close()  # Close the figure to release memory
        else:
            logger.info("Missing Report File data: CoV Plot not created")

    # Read in transcript file
    caseOutPath = misc_utils.ptw_output(fl_workingDir=fl_workingDir,case_name=caseFilename)
    trnFilePath = os.path.join(caseOutPath, trn_filename)

    report_table = postproc_utils.evaluateTranscript(trnFilePath=trnFilePath,caseFilename=caseFilename,solver=solver)

    # Select columns from report_table
    columns_before_report_values = report_table.iloc[:, :2]
    columns_after_report_values = report_table.iloc[:, 2:]

    # Concatenate DataFrames
    result_table = pd.concat([columns_before_report_values, report_values, columns_after_report_values], axis=1)

    # Report Table File-Name
    resultTableName = data["results"].setdefault(
        "filename_reporttable", "reporttable.csv"
    )
    reportTableFileName = os.path.join(
        caseOutPath, resultTableName
    )
    logger.info("Writing Report Table to: " + reportTableFileName)
    result_table.to_csv(reportTableFileName, index=None)

    return


def mergeReportTables(turboData, solver):
    # Only working with pandas lib
    try:
        import pandas as pd
    except ImportError as e:
        logger.info(f"ImportError! Could not import lib: {str(e)}")
        logger.info(f"Skipping mergeReportTables function!")
        return

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
                caseOutPath=misc_utils.ptw_output(fl_workingDir=fl_workingDir,case_name=caseFilename)
                reportTableFilePath = os.path.join(caseOutPath, reportTableName)
                if os.path.isfile(reportTableFilePath):
                    reportFiles.append(reportTableFilePath)

        if len(reportFiles) > 1:
            df = pd.concat((pd.read_csv(f, header=0) for f in reportFiles))
            mergedFileName = os.path.join(ptwOutPath, "mergedReporttable.csv")
            df.to_csv(mergedFileName)

    return
