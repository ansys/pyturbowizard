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

    ## read in the results of the simulation
    utilities.createReportTable(data=data, fl_workingDir=fl_workingDir)

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

    return