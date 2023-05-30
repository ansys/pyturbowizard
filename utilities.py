import os.path
import matplotlib.pyplot as plt
import pandas as pd
import subprocess
import time


def writeExpressionFile(data, script_dir, working_dir):
    fileName = os.path.join(working_dir, data["expressionFilename"])
    if fileName is None:
        fileName = "expressions.tsv"

    with open(fileName, "w") as sf:
        expressionTemplatePath = os.path.join(script_dir, data["expressionTemplate"])
        with open(expressionTemplatePath, "r") as templateFile:
            tempData = templateFile.read()
            templateFile.close()
        helperDict = data["locations"]
        expressionEl = data.get("expressions")
        helperDict.update(expressionEl)
        tempData = cleanupInputExpressions(expressionEl=expressionEl, fileData=tempData)
        for line in tempData.splitlines():
            try:
                sf.write(line.format(**helperDict))
                sf.write("\n")
            except KeyError:
                # Skip the line if a key is missing
                continue

    return


def cleanupInputExpressions(expressionEl: dict, fileData: str):
    cleanfiledata = ""
    for line in fileData.splitlines():
        # write header line
        if cleanfiledata == "":
            cleanfiledata = line
        # check BCs and prescribed Expressions
        elif line.startswith('"BC'):
            for expKey in expressionEl:
                if expKey in line:
                    cleanfiledata = cleanfiledata + "\n" + line
                    break
        else:
            cleanfiledata = cleanfiledata + "\n" + line

    return cleanfiledata


def plotOperatingMap(design_point_table):
    # extract unit row and drop from table
    design_point_table = design_point_table.drop(0, axis=0)

    # filter out failed design points
    design_point_table = design_point_table.loc[
        design_point_table["Status"] != "Failed"
    ]

    # Filter out converged cases
    MP_MassFlow_conv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Converged", "MP_IN_MassFlow"
        ],
        errors="coerce",
    )
    MP_PRt_conv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Converged", "MP_PRt"
        ],
        errors="coerce",
    )
    MP_Isentropic_Efficiency_conv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Converged",
            "MP_Isentropic_Efficiency",
        ],
        errors="coerce",
    )

    # Filter out non converged cases
    MP_MassFlow_nconv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Not Converged", "MP_IN_MassFlow"
        ],
        errors="coerce",
    )
    MP_PRt_nconv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Not Converged", "MP_PRt"
        ],
        errors="coerce",
    )
    MP_Isentropic_Efficiency_nconv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Not Converged",
            "MP_Isentropic_Efficiency",
        ],
        errors="coerce",
    )

    # Merge
    MP_MassFlow = pd.concat([MP_MassFlow_conv, MP_MassFlow_nconv])
    MP_PRt = pd.concat([MP_PRt_conv, MP_PRt_nconv])
    MP_Isentropic_Efficiency = pd.concat(
        [MP_Isentropic_Efficiency_conv, MP_Isentropic_Efficiency_nconv]
    )

    # generate plots
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle("Operating Point Map")
    if (
        (len(MP_PRt) > 0)
        and (len(MP_MassFlow) > 0)
        and (len(MP_Isentropic_Efficiency) > 0)
    ):
        # Total Pressure Ratio
        axs[0].set_xlim([MP_MassFlow.min() * 0.99, MP_MassFlow.max() * 1.01])
        axs[0].set_ylim([MP_PRt.min() * 0.99, MP_PRt.max() * 1.01])
        axs[0].grid()
        axs[0].set_xlabel("inlet mass flow rate [kg/s]")
        axs[0].set_ylabel("total pressure ratio [-]")
        axs[0].scatter(MP_MassFlow_conv, MP_PRt_conv, marker="^")
        axs[0].scatter(MP_MassFlow_nconv, MP_PRt_nconv, marker="x")

        # Isentropic Efficiency
        axs[1].set_xlim([MP_MassFlow.min() * 0.99, MP_MassFlow.max() * 1.01])
        axs[1].set_ylim(
            [
                MP_Isentropic_Efficiency.min() * 0.99,
                MP_Isentropic_Efficiency.max() * 1.01,
            ]
        )
        axs[1].grid()
        axs[1].set_xlabel("inlet mass flow rate [kg/s]")
        axs[1].set_ylabel("isentropic efficiency [-]")
        axs[1].scatter(MP_MassFlow_conv, MP_Isentropic_Efficiency_conv, marker="^")
        axs[1].scatter(MP_MassFlow_nconv, MP_Isentropic_Efficiency_nconv, marker="x")
        fig.legend(["Converged", "Not Converged"])

    return fig


def launchFluent(launchEl):
    import ansys.fluent.core as pyfluent

    global solver

    fl_workingDir = launchEl["workingDir"]
    serverfilename = launchEl.get("serverfilename", None)
    queueEl = launchEl.get("queue_slurm", None)
    # open new session in queue
    if queueEl is not None:
        maxtime = float(launchEl.get("queue_waiting_time", 600.0))
        print("Trying to launching new Fluent Session on queue '" + queueEl + "'")
        print(
            "Max waiting time (launching-key: 'queue_waiting_time') set to: "
            + str(maxtime)
        )
        serverfilename = launchEl.get("serverfilename", "server-info.txt")
        commandlist = list()
        commandlist.append(
            pyfluent.launcher.launcher.get_fluent_exe_path(
                product_version=launchEl["fl_version"]
            )
        )
        precisionCommand = "3d"
        if launchEl.get("precision", True):
            precisionCommand = precisionCommand + "dp"
        batch_arguments = [
            precisionCommand,
            "-t%s" % (int(launchEl["noCore"])),
            "-scheduler=slurm",
            "-scheduler_queue=%s" % (launchEl["queue_slurm"]),
            "-sifile=%s" % (serverfilename),
        ]
        if not launchEl.get("show_gui", True):
            batch_arguments.extend(["-gu", "-driver opengl"])
        commandlist.extend(batch_arguments)
        process_files = subprocess.Popen(
            commandlist, cwd=fl_workingDir, stdout=subprocess.DEVNULL
        )
        # Check if Fluent started
        fullpathtosfname = os.path.join(fl_workingDir, serverfilename)
        current_time = 0
        while current_time <= maxtime:
            try:
                if os.path.isfile(fullpathtosfname):
                    time.sleep(5)
                    break
            except OSError:
                print("Witing to process start...")
                time.sleep(5)
                current_time += 5
        if current_time > maxtime:
            raise TimeoutError(
                "Maximum waiting time reached ("
                + str(maxtime)
                + "sec). Aborting script..."
            )
        # Start Session via hook
        solver = pyfluent.launch_fluent(
            start_instance=False, server_info_filepath=fullpathtosfname
        )
    # If no serverFilename is specified, a new session will be started
    elif serverfilename is None or serverfilename == "":
        solver = pyfluent.launch_fluent(
            precision=launchEl.get("precision", True),
            processor_count=int(launchEl["noCore"]),
            mode="solver",
            show_gui=launchEl.get("show_gui", True),
            product_version=launchEl["fl_version"],
            cwd=fl_workingDir,
        )
    # Hook to existing Session
    else:
        fullpathtosfname = os.path.join(fl_workingDir, serverfilename)
        print("Connecting to Fluent Session...")
        solver = pyfluent.launch_fluent(
            start_instance=False, server_info_filepath=fullpathtosfname
        )
    return solver
