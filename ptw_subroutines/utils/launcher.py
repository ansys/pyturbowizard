import os
import subprocess
import time

# Logger
from ptw_subroutines.utils import ptw_logger, misc_utils

logger = ptw_logger.getLogger()


def launchFluent(launchEl: dict):
    import ansys.fluent.core as pyfluent

    global solver

    fl_workingDir = launchEl["workingDir"]
    serverfilename = launchEl.get("serverfilename")
    queueEl = launchEl.get("queue_slurm")
    get_launcher_defaults(launchEl=launchEl)

    # open new session in queue
    if queueEl is not None:
        maxtime = float(launchEl.setdefault("queue_waiting_time", 600.0))
        logger.info("Trying to launching new Fluent Session on queue '" + queueEl + "'")
        logger.info(
            "Max waiting time (launching-key: 'queue_waiting_time') set to: "
            + str(maxtime)
        )
        # Get a free server-filename
        serverfilename = launchEl.get("serverfilename", "server-info.txt")
        serverfilename = misc_utils.get_free_filename(
            dirname=fl_workingDir, base_filename=serverfilename
        )
        launchEl["serverfilename"] = serverfilename
        serverfilename = os.path.join(fl_workingDir, serverfilename)

        commandlist = list()
        commandlist.append(
            pyfluent.launcher.launcher.get_fluent_exe_path(
                product_version=launchEl["fl_version"]
            )
        )
        precisionCommand = "3d"
        if launchEl["precision"]:
            precisionCommand = precisionCommand + "dp"
        batch_arguments = [
            precisionCommand,
            "-t%s" % (int(launchEl["noCore"])),
            "-scheduler=slurm",
            "-scheduler_queue=%s" % (launchEl["queue_slurm"]),
            "-sifile=%s" % (serverfilename),
            "-py" if launchEl["py"] else "",
        ]
        if not launchEl["show_gui"]:
            batch_arguments.extend(["-gu", "-driver dx11"])
        commandlist.extend(batch_arguments)
        process_files = subprocess.Popen(
            commandlist, cwd=fl_workingDir, stdout=subprocess.DEVNULL
        )
        # Check if Fluent started
        fullpath_to_sf = os.path.join(fl_workingDir, serverfilename)
        current_time = 0
        while current_time <= maxtime:
            try:
                if os.path.isfile(fullpath_to_sf):
                    time.sleep(5)
                    break
            except OSError:
                logger.info("Waiting to process start...")
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
            start_instance=False,
            server_info_filepath=fullpath_to_sf,
            cleanup_on_exit=launchEl["exitatend"],
        )
    # If no serverFilename is specified, a new session will be started
    elif serverfilename is None or serverfilename == "":
        solver = pyfluent.launch_fluent(
            precision=launchEl["precision"],
            processor_count=int(launchEl["noCore"]),
            mode="solver",
            show_gui=launchEl["show_gui"],
            product_version=launchEl["fl_version"],
            cwd=fl_workingDir,
            cleanup_on_exit=launchEl["exitatend"],
            py=launchEl["py"],
        )
    # Hook to existing Session
    else:
        fullpath_to_sf = os.path.join(fl_workingDir, serverfilename)
        logger.info("Connecting to Fluent Session...")
        solver = pyfluent.launch_fluent(
            start_instance=False,
            server_info_filepath=fullpath_to_sf,
            cleanup_on_exit=launchEl["exitatend"],
        )
    return solver


def get_launcher_defaults(launchEl: dict):
    # Set defaults
    launchEl.setdefault("exitatend", True)
    launchEl.setdefault("show_gui", True)
    launchEl.setdefault("precision", True)
    launchEl.setdefault("py", False)
