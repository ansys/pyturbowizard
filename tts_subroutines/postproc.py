from tts_subroutines import utilities
import pandas as pd
import os

def post(data, solver, functionEl, launchEl):
    # Get FunctionName & Update FunctionEl
    functionName = utilities.get_funcname_and_upd_funcdict(
        parentEl=data,
        functionEl=functionEl,
        funcElName="postproc",
        defaultName="post_01",
    )

    print('\nRunning Postprocessing Function "' + functionName + '"...')
    if functionName == "post_01":
        post_01(data, solver, launchEl)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Postprocessing!'
        )

    print("\nRunning Postprocessing Function... finished!\n")


def post_01(data, solver, launchEl):
    fl_workingDir = launchEl.get("workingDir")
    caseFilename = data["caseFilename"]
    filename = caseFilename + "_" + data["results"].get("filename_outputParameter", "outParameters.out")
    # solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
    tuicommand = (
        'define parameters output-parameters write-all-to-file "' + filename + '"'
    )
    solver.execute_tui(tuicommand)
    filename = caseFilename + "_" + data["results"].get("filename_summary", "report.sum")
    solver.results.report.summary(write_to_file=True, file_name=filename)
    if data["locations"].get("tz_turbo_topology_names") is not None:
        try:
            utilities.spanPlots(data,solver)
        except Exception as e:
            print(f"No span plots have been created: {e}")

    ## get wall clock time
    # Write out system time
    solver.report.system.time_statistics()
    ## read read in the results of the simulation
    trnFileName = caseFilename + ".trn"
    # get correct report file from fluent
    reportFileName = caseFilename + "_report.out"
            print(f"No turbo surfaces have been created: {e}")

    ## read in the results of the simulation
    # Only working in external mode
    try:
        import pandas as pd
        # get correct report file from fluent
        file_names = os.listdir(fl_workingDir)
        # Filter for file names starting with "report"
        reportFileName = caseFilename + "_report"
        filtered_files = [file for file in file_names if file.startswith(reportFileName) and file.endswith(".out")]
        report_table = pd.DataFrame()
        if len(filtered_files) > 0:
            # Find the file name with the highest number
            report_file = max(filtered_files, key=lambda x: [int(num) for num in x.split("_") if num.isdigit()])
            report_file = os.path.join(fl_workingDir, report_file)

            # read in table of report-mp and get last row
            out_table = pd.read_csv(report_file, header=2, delimiter=" ")
            first_column = out_table.columns[0]
            last_column = out_table.columns[-1]

            # Remove brackets from first and last column names
            modified_columns = {
                first_column: first_column.replace('(', '').replace(')', '').replace('"',''),
                last_column: last_column.replace('(', '').replace(')', '')
            }
            out_table = out_table.rename(columns = modified_columns)
            report_table = out_table.iloc[[-1]].copy()
            print(f"No Monitor Report File '{reportFileName}*.out' found... No Data will be added to Case Report Table!")

        ## get wall clock time
        # Write out system time
        solver.report.system.time_statistics()

        trnFileName = caseFilename + ".trn"
        trnFileName = os.path.join(fl_workingDir, trnFileName)
        with open(trnFileName, "r") as file:
            transcript = file.read()

        lines = transcript.split("\n")
        wall_clock_per_it = 0
        wall_clock_tot = 0
        nodes = 0
        for line in lines:
            if "Average wall-clock time per iteration" in line:
                wall_clock_per_it = line.split(":")[1].strip()
                print("Average Wall Clock Time per Iteration:", wall_clock_per_it)
            if "Total wall-clock time" in line:
                wall_clock_tot = line.split(":")[1].strip()
                print("Total Wall Clock Time:", wall_clock_tot)
            if "iterations on " in line:
                nodes = line.split(" ")[-3]

        ## write report table
        #report_table = report_values
        report_table["Case Name"] = [caseFilename]
        report_table["Total Wall Clock Time"] = [wall_clock_tot]
        report_table["Ave Wall Clock Time per It"] = [wall_clock_per_it]
        report_table["Compute Nodes"] = [nodes]

        #Reorder Table to get Case Name as first column
        report_table = report_table[['Case Name'] + [col for col in report_table.columns if col != 'Case Name']]

        #Save Report Table
        reportTableName = data["results"].get("filename_reporttable", "reporttable.csv")
        data["results"]["filename_reporttable"] = reportTableName
        reportTableFileName = caseFilename + '_' + reportTableName
        reportTableFileName = os.path.join(fl_workingDir, reportTableFileName)
        report_table.to_csv(reportTableFileName, index=None)

    except ImportError as e:
        print(f"ImportError! Could not import lib: {str(e)}")
        print(f"Skipping writing custom reporttable!")
        # Write out system time
        solver.report.system.time_statistics()
        return

    return

def mergeReportTables(turboData, solver):
    # Only working with pandas lib
    try:
        import pandas as pd
    except ImportError as e:
        print(f"ImportError! Could not import lib: {str(e)}")
        print(f"Skipping mergeReportTables function!")
        return

    fl_workingDir = turboData["launching"].get("workingDir")
    caseDict = turboData.get("cases")
    if caseDict is not None:
        reportFiles =  []
        for casename in caseDict:
            caseEl = turboData["cases"][casename]
            caseFilename = caseEl["caseFilename"]
            reportTableName = caseEl["results"].get("filename_reporttable", "reporttable.csv")
            reportTableName = caseFilename + "_" + reportTableName
            reportTableFilePath = os.path.join(fl_workingDir, reportTableName)
            if os.path.isfile(reportTableFilePath):
                reportFiles.append(reportTableFilePath)
        df = pd.concat((pd.read_csv(f, header=0) for f in reportFiles))
        mergedFileName = os.path.join(fl_workingDir, "mergedReporttable.csv")
        df.to_csv(mergedFileName)

    utilities.CreateReportTable(reportFileName,trnFileName,caseFilename)


    return