import os


def post(data, solver, functionName="post_01"):
    print('Running Postprocessing Function "' + functionName + '"...')
    if functionName == "post_01":
        post_01(data, solver)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Postprocessing!'
        )

    print("Postprocessing finished.")


def post_01(data, solver):
    caseFilename = data["caseFilename"]
    filename = caseFilename + "_" + data["results"]["filename_outputParameter_pf"]
    # solver.tui.define.parameters.output_parameters.write_all_to_file('filename')
    tuicommand = (
        'define parameters output-parameters write-all-to-file "' + filename + '"'
    )
    solver.execute_tui(tuicommand)
    filename = caseFilename + "_" + data["results"]["filename_summary_pf"]
    solver.results.report.summary(write_to_file=True, file_name=filename)

    #define span-wise surfaces for post processing
    if data["locations"].get("tz_turbo_topology_names") is not None:
        try:
            solver.tui.surface.iso_surface("spanwise-coordinate","span-20",[],[],"0.2",[])
            solver.tui.surface.iso_surface("spanwise-coordinate","span-50",[],[],"0.5",[])
            solver.tui.surface.iso_surface("spanwise-coordinate","span-90",[],[],"0.9",[])
        except Exception as e:
                print(f"No turbo surfaces have been created: {e}") 

    # Write out system time
    solver.report.system.time_statistics()

    return
