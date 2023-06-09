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
    caseFilename = data["caseFilename"]
    filename = caseFilename + "_" + data["results"]["filename_outputParameter_pf"]
    # solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
    tuicommand = (
        'define parameters output-parameters write-all-to-file "' + filename + '"'
    )
    solver.execute_tui(tuicommand)
    filename = caseFilename + "_" + data["results"]["filename_summary_pf"]
    solver.results.report.summary(write_to_file=True, file_name=filename)

    # define span-wise surfaces for post processing
    if data["locations"].get("tz_turbo_topology_names") is not None:
        try:
            print("Creating spanwise ISO-surfaces @20,50,90 span")
            solver.tui.surface.iso_surface(
                "spanwise-coordinate", "span-20", [], [], "0.2", []
            )
            solver.tui.surface.iso_surface(
                "spanwise-coordinate", "span-50", [], [], "0.5", []
            )
            solver.tui.surface.iso_surface(
                "spanwise-coordinate", "span-90", [], [], "0.9", []
            )
        except Exception as e:
            print(f"No turbo surfaces have been created: {e}")

    ## read read in the results of the simulation

    # get correct report file from fluent
    file_names = os.listdir(launchEl.get("workingDir"))
    # Filter for file names starting with "report"
    filtered_files = [file for file in file_names if file.startswith("report")]
    # Find the file name with the highest number
    report_file = max(filtered_files, key=lambda x: [int(num) for num in x.split("_") if num.isdigit()])

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
    report_values = out_table.iloc[[-1]]

    ## get wall clock time
    # Write out system time
    solver.report.system.time_statistics()

    trnFileName = caseFilename + ".trn"
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
    report_table = report_values
    
    report_table["Total Wall Clock Time"] = wall_clock_tot
    report_table["Ave Wall Clock Time per It"] = wall_clock_per_it
    report_table["Compute Nodes"] = nodes
    report_table["Case Name"] = caseFilename

    reportTableFileName =  caseFilename + '_reporttable.csv'
    report_table.to_csv(reportTableFileName,index=None)
    
    return
