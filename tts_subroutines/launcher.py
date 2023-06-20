import os
import subprocess
import time


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
        # Check if serverfile already exists
        serverfilepath = os.path.join(fl_workingDir, serverfilename)
        if os.path.isfile(serverfilepath):
            raise FileExistsError(
                f"Serverfile already exits {serverfilepath}!"
                f"\nPlease remove this file or specify a different serverfilename (Key: 'serverfilename')!"
            )

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
                print("Waiting to process start...")
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
