import os
import matplotlib.pyplot as plt

#Logger
from ptw_subroutines.utils import ptw_logger, utilities

logger = ptw_logger.getLogger()

def post(data, solver, functionEl, launchEl):
    # Get FunctionName & Update FunctionEl
    functionName = utilities.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="postproc",
        defaultName="post_01",
    )

    logger.info('\nRunning Postprocessing Function "' + functionName + '"...')
    if functionName == "post_01":
        post_01(data, solver, launchEl)
    else:
        logger.info(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Postprocessing!'
        )

    logger.info("\nRunning Postprocessing Function... finished!\n")


def post_01(data, solver, launchEl):
    fl_workingDir = launchEl.get("workingDir")
    caseFilename = data["caseFilename"]
    filename = (
        caseFilename
        + "_"
        + data["results"].setdefault("filename_outputParameter", "outParameters.out")
    )
    # solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
    tuicommand = (
        'define parameters output-parameters write-all-to-file "' + filename + '"'
    )
    solver.execute_tui(tuicommand)
    filename = (
        caseFilename + "_" + data["results"].setdefault("filename_summary", "report.sum")
    )
    solver.results.report.summary(write_to_file=True, file_name=filename)
    if data["locations"].get("tz_turbo_topology_names") is not None:
        try:
            spanPlots(data, solver)
        except Exception as e:
            logger.info(f"No span plots have been created: {e}")

    # Write out system time
    solver.report.system.time_statistics()

    ## write report table
    createReportTable(data=data, fl_workingDir=fl_workingDir, solver=solver)

    return


def createReportTable(data: dict, fl_workingDir, solver):
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
    reportFileName = caseFilename + "_report"
    report_file = os.path.join(fl_workingDir, reportFileName + ".out")
    file_names = os.listdir(fl_workingDir)
    filtered_files = [
        file
        for file in file_names
        if file.startswith(reportFileName) and file.endswith(".out")
    ]
    report_values = pd.DataFrame()
    cov_df = pd.DataFrame()
    mp_df = pd.DataFrame()

    if len(filtered_files) > 0:
        # Find the file name with the highest number
        report_file = max(
            filtered_files,
            key=lambda x: [int(num) for num in x.split("_") if num.isdigit()],
        )
        report_file = os.path.join(fl_workingDir, report_file)
        report_values,cov_df, mp_df = utilities.calcCov(report_file)
    
    else:
        logger.info("No Report File found: data not included in final report")

    # Write CoV and MP Plot
    plot_folder = os.path.join(fl_workingDir, f'plots_{caseFilename}')
    os.makedirs(plot_folder, exist_ok=True)  # Create the folder if it doesn't exist
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
            plt.title(f'{col} - {caseFilename}')
            plt.grid(True)

            # Save the plot in folder
            plot_filename = os.path.join(plot_folder,f'mp_plot_{col}.png')
            logger.info(f"Writing Monitor Plot to Directory: {plot_filename}")
            plt.savefig(plot_filename)
            plt.close()  # Close the figure to release memory
        else:
            logger.info("Missing Report File data: Monitor Plots not created")

        if not cov_df.empty:
            #Get CoV information
            covDict = solver.solution.monitor.convergence_conditions.convergence_reports()
            filtCovDict = {
                    key: value
                    for key, value in covDict.items()
                    if value.get("active", False) and value.get("cov", False)
                }
            
            cov_df.reset_index(inplace=True)

            # Get the list of columns excluding 'Iteration'
            y_columns = cov_df.columns[2:]
            filtered_y_columns = [col for col in y_columns if any(col.startswith(key[:-4]) for key in filtCovDict)]
        

            plt.figure(figsize=(10, 6))
            # Plot each column separately on the same plot
            for col in filtered_y_columns:
                plt.plot(cov_df['Iteration'], cov_df[col], label=col)
            
            plt.xlabel('Iteration')
            plt.ylabel('')
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.title(f'Coefficient of Variation (CoV)')
            plt.grid(True)
            plt.yscale('log')

            # Save the plot in folder
            plot_filename = os.path.join(plot_folder, f'cov_plot.png')
            plt.tight_layout()
            logger.info(f"Writing CoV Plot to Directory: {plot_filename}")
            plt.savefig(plot_filename)
            plt.close()  # Close the figure to release memory    
        else:
            logger.info("Missing Report File data: CoV Plot not created")

    # Read in transcript file
    trnFileName = caseFilename + ".trn"
    trnFileName = os.path.join(fl_workingDir, trnFileName)

    if os.path.isfile(trnFileName):
        with open(trnFileName, "r") as file:
            transcript = file.read()

        solver_trn_data_valid = False
        table_started = False
        lines = transcript.split("\n")
        wall_clock_tot = 0
        nodes = 0
        filtered_values = []
        filtered_headers = []

        for line in lines:
            if "Total wall-clock time" in line:
                wall_clock_tot = line.split(":")[1].strip()
                wall_clock_tot = wall_clock_tot.split(" ")[0].strip()
                logger.info("Detected Total Wall Clock Time:", wall_clock_tot)
            elif "compute nodes" in line:
                nodes = line.split(" ")[6].strip()
                logger.info("Detected Number of Nodes:", nodes)
            elif "iter  continuity  x-velocity" in line:
                headers = line.split()
                filtered_headers = headers[1:8]
                table_started = True
            elif table_started:
                values = line.split()
                if len(values) == 0:
                    table_started = False
                elif len(values[1:8]) == len(filtered_headers):
                    filtered_values = values[1:8]
                    solver_trn_data_valid = True
                else:
                    try:
                        values = int(values[0])
                    except ValueError:
                        table_started = False

        for i in range(len(filtered_headers)):
            filtered_headers[i] = "res-" + filtered_headers[i]

        if solver_trn_data_valid:
            filtered_values = [float(val) for val in filtered_values]
            res_columns = dict(zip(filtered_headers, filtered_values))
    else:
        logger.info('No trn-file found!: Skipping data')
        solver_trn_data_valid = False

    # get pseudo time step value
    time_step = solver.scheme_eval.string_eval("(rpgetvar 'pseudo-auto-time-step)")

    # write out flux reports
    massBalance = solver.report.fluxes.mass_flow()
    solveEnergy = solver.setup.models.energy.enabled()
    if solveEnergy:
        heatBalance = solver.report.fluxes.heat_transfer()

    ## write report table
    report_table = pd.DataFrame()
    report_table = pd.concat([report_table, report_values], axis=1)

    if solver_trn_data_valid:
        report_table = report_table.assign(**res_columns)
    else:
        logger.info(
            f"Reading Solver-Data from transcript file failed. Data not included in report table"
        )

    report_table.loc[0, "Mass Balance [kg/s]"] = massBalance
    if solveEnergy:
        report_table["Heat Balance [W]"] = heatBalance

    report_table.loc[0, "Total Wall Clock Time"] = wall_clock_tot
    report_table.loc[0, "Compute Nodes"] = nodes
    report_table.insert(0, "Case Name", caseFilename)
    report_table.insert(1, "Pseud Time Step [s]", time_step)

    # Report Table File-Name
    reportTableName = data["results"].setdefault("filename_reporttable", "reporttable.csv")
    reportTableFileName = os.path.join(
        fl_workingDir, caseFilename + "_" + reportTableName
    )
    logger.info("Writing Report Table to: " + reportTableFileName)
    report_table.to_csv(reportTableFileName, index=None)

    return


def spanPlots(data, solver):
    # Create spanwise surfaces
    spansSurf = data["results"].get("span_plot_height")
    contVars = data["results"].get("span_plot_var")
    availableFieldDataNames = (
        solver.field_data.get_scalar_field_data.field_name.allowed_values()
    )
    for contVar in contVars:
        if contVar not in availableFieldDataNames:
            logger.info(f"FieldVariable: '{contVar}' not available in Solution-Data!")
            logger.info(f"Available Scalar Values are: '{availableFieldDataNames}'")

    for spanVal in spansSurf:
        spanName = f"span-{spanVal}"
        logger.info("Creating spanwise ISO-surface: " + spanName)
        solver.results.surfaces.iso_surface[spanName] = {}
        zones = solver.results.surfaces.iso_surface[spanName].zone.get_attr(
            "allowed-values"
        )
        solver.results.surfaces.iso_surface[spanName](
            field="spanwise-coordinate", zone=zones, iso_value=[spanVal]
        )

        for contVar in contVars:
            if contVar in availableFieldDataNames:
                contName = spanName + "-" + contVar
                logger.info("Creating spanwise contour-plot: " + contName)
                solver.results.graphics.contour[contName] = {}
                solver.results.graphics.contour[contName](
                    field=contVar, contour_lines=True, surfaces_list=spanName
                )
                solver.results.graphics.contour[
                    contName
                ].range_option.auto_range_on.global_range = False


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
                reportTableFilePath = os.path.join(fl_workingDir, reportTableName)
                if os.path.isfile(reportTableFilePath):
                    reportFiles.append(reportTableFilePath)

        if len(reportFiles) > 1:
            df = pd.concat((pd.read_csv(f, header=0) for f in reportFiles))
            mergedFileName = os.path.join(fl_workingDir, "mergedReporttable.csv")
            df.to_csv(mergedFileName)

    return
