# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Launcher Module

This module provides functionality for launching and managing ANSYS Fluent instances in the
PyTurboWizard application.
"""

import os
import platform

# Excluding low severity bandit warning as the validity of the inputs is enforced.
import subprocess  # nosec B404
import time

import ansys.fluent.core as pyfluent
from ansys.fluent.core import Dimension, UIMode
from packaging import version

# Load Script Modules
from . import misc_utils, ptw_logger

logger = ptw_logger.get_logger()


def launch_fluent(launchEl: dict):
    """Launch Fluent solver or connect to an existing session."""
    global solver

    fl_workingDir = launchEl["workingDir"]
    serverfilename = launchEl.get("serverfilename")
    queueEl = launchEl.get("queue_slurm")
    get_launcher_defaults(launchEl=launchEl)
    adjust_settings_to_version(launchEl=launchEl)

    # open new session in queue
    if queueEl is not None:
        solver = launch_queuing_session(launchEl=launchEl)
    # If no serverFilename is specified, a new session will be started
    elif serverfilename is None or serverfilename == "":
        if version.parse(pyfluent.__version__) < version.parse("0.29.0"):
            solver = pyfluent.launch_fluent(
                precision=launchEl["precision"],
                processor_count=int(launchEl["noCore"]),
                mode="solver",
                show_gui=launchEl["show_gui"],
                product_version=launchEl["fl_version"],
                cwd=fl_workingDir,
                cleanup_on_exit=launchEl["exitatend"],
                py=launchEl["py"],
                gpu=launchEl["gpu"],
                version=launchEl["version"],
            )
        else:
            solver = pyfluent.launch_fluent(
                precision=launchEl["precision"],
                processor_count=int(launchEl["noCore"]),
                mode="solver",
                ui_mode=launchEl["ui_mode"],
                product_version=launchEl["fl_version"],
                cwd=fl_workingDir,
                cleanup_on_exit=launchEl["exitatend"],
                py=launchEl["py"],
                gpu=launchEl["gpu"],
                dimension=launchEl["dimension"],
            )
    # Hook to existing Session
    else:
        solver = hook_to_existing_session(
            fl_workingDir=fl_workingDir,
            serverfilename=serverfilename,
            cleanup_on_exit=launchEl["exitatend"],
        )
    return solver


def hook_to_existing_session(fl_workingDir: str, serverfilename: str, cleanup_on_exit: bool):
    """Hook to an existing Fluent session using the server info file."""

    fullpath_to_sf = os.path.join(fl_workingDir, serverfilename)
    logger.info("Connecting to Fluent Session...")
    # Start Session via hook
    if version.parse(pyfluent.__version__) <= version.parse("0.17.1"):
        solver = pyfluent.launch_fluent(
            start_instance=False,
            server_info_filepath=fullpath_to_sf,
            cleanup_on_exit=cleanup_on_exit,
        )
    elif version.parse(pyfluent.__version__) <= version.parse("0.18.2"):
        solver = pyfluent.connect_to_fluent(
            server_info_filepath=fullpath_to_sf,
            cleanup_on_exit=cleanup_on_exit,
        )
    else:
        solver = pyfluent.connect_to_fluent(
            server_info_file_name=fullpath_to_sf,
            cleanup_on_exit=cleanup_on_exit,
        )

    return solver


def launch_queuing_session(launchEl: dict):
    """Launch Fluent solver in a queuing system (e.g., SLURM)."""
    solver = None
    queueEl = launchEl.get("queue_slurm")
    fl_workingDir = launchEl["workingDir"]
    additional_args = launchEl.get("additional_args", [])
    maxtime = int(launchEl.setdefault("queue_waiting_time", 600))

    logger.info("Trying to launching new Fluent Session on queue '" + queueEl + "'")
    logger.info("Max waiting time (launching-key: 'queue_waiting_time') set to: " + str(maxtime))
    if version.parse(pyfluent.__version__) < version.parse("0.19.0"):
        # Get a free server-filename
        serverfilename = launchEl.get("serverfilename", "server-info.txt")
        serverfilename = misc_utils.get_free_filename(
            dirname=fl_workingDir, base_filename=serverfilename
        )
        launchEl["serverfilename"] = serverfilename
        serverfilename = os.path.join(fl_workingDir, serverfilename)

        commandlist = list()

        # Get Fluent Executable
        fluent_path = get_fluent_exe_path(product_version=launchEl["fl_version"])
        if version.parse(pyfluent.__version__) < version.parse("0.19.0"):
            fluent_path = pyfluent.launcher.launcher.get_fluent_exe_path(
                product_version=launchEl["fl_version"]
            )
        logger.info("Used Fluent executable: '" + fluent_path + "'")
        commandlist.append(fluent_path)

        precisionCommand = launchEl["version"]
        if launchEl["precision"]:
            precisionCommand = precisionCommand + "dp"
        batch_arguments = [
            precisionCommand,
            "-t%s" % (int(launchEl["noCore"])),
            "-scheduler=slurm",
            "-scheduler_queue=%s" % (launchEl["queue_slurm"]),
            "-sifile=%s" % (serverfilename),
            "-py" if launchEl["py"] else "",
            "-gpu" if launchEl["gpu"] else "",
        ]
        if not launchEl["show_gui"]:
            batch_arguments.extend(["-gu", "-driver dx11"])
        batch_arguments.extend(additional_args)
        commandlist.extend(batch_arguments)
        # Excluding low severity bandit check as the validity of the inputs has been ensured.
        subprocess.Popen(commandlist, cwd=fl_workingDir, stdout=subprocess.DEVNULL)  # nosec B603
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
                "Maximum waiting time reached (" + str(maxtime) + "sec). Aborting script..."
            )
        # Start Session via hook
        solver = hook_to_existing_session(
            fl_workingDir=fl_workingDir,
            serverfilename=serverfilename,
            cleanup_on_exit=launchEl["exitatend"],
        )
    else:
        scheduler_options = {
            "scheduler": "slurm",
            "scheduler_queue": launchEl["queue_slurm"],
        }
        if version.parse(pyfluent.__version__) < version.parse("0.29.0"):
            solver = pyfluent.launch_fluent(
                precision=launchEl["precision"],
                processor_count=int(launchEl["noCore"]),
                mode="solver",
                show_gui=launchEl["show_gui"],
                product_version=launchEl["fl_version"],
                cwd=fl_workingDir,
                cleanup_on_exit=launchEl["exitatend"],
                py=launchEl["py"],
                gpu=launchEl["gpu"],
                scheduler_options=scheduler_options,
                additional_arguments=additional_args,
                version=launchEl["version"],
            ).result(timeout=maxtime)
        else:
            solver = pyfluent.launch_fluent(
                precision=launchEl["precision"],
                processor_count=int(launchEl["noCore"]),
                mode="solver",
                ui_mode=launchEl["ui_mode"],
                product_version=launchEl["fl_version"],
                cwd=fl_workingDir,
                cleanup_on_exit=launchEl["exitatend"],
                py=launchEl["py"],
                gpu=launchEl["gpu"],
                scheduler_options=scheduler_options,
                additional_arguments=additional_args,
                dimension=launchEl["dimension"],
                start_timeout=maxtime,
            ).result(timeout=maxtime)
    return solver


def get_fluent_exe_path(product_version: str):
    """Get the path to the Fluent executable based on the product version."""

    fluent_path = None
    product_version_split = product_version.split(".")
    root_env_name = "AWP_ROOT" + product_version_split[0] + product_version_split[1]
    ansys_root_path = os.getenv(root_env_name)
    if ansys_root_path is None:
        logger.error(f"Environment '{root_env_name}' not found on system")
        return fluent_path

    if platform.system() == "Windows":
        fluent_path = os.path.join(ansys_root_path, "fluent", "ntbin", "win64", "fluent.exe")
        if platform.architecture()[0] == "32bit":
            fluent_path = os.path.join(ansys_root_path, "fluent", "ntbin", "win32", "fluent.exe")
    elif platform.system() == "Linux":
        fluent_path = os.path.join(ansys_root_path, "fluent", "bin", "fluent")
    else:
        logger.error(f"System '{platform.system()}' not supported.")

    return fluent_path


def get_launcher_defaults(launchEl: dict):
    """Set default values for the launcher options."""
    # Set defaults
    launchEl.setdefault("exitatend", True)
    launchEl.setdefault("precision", True)
    launchEl.setdefault("py", True)
    launchEl.setdefault("gpu", False)
    if version.parse(pyfluent.__version__) < version.parse("0.29.0"):
        launchEl.setdefault("version", "3d")
        launchEl.setdefault("show_gui", True)
    else:
        launchEl.setdefault("dimension", Dimension.THREE.value)
        launchEl.setdefault("ui_mode", UIMode.GUI.value)


def adjust_settings_to_version(launchEl: dict):
    """Adjust launcher settings based on the version of PyFluent."""
    if version.parse(pyfluent.__version__) >= version.parse("0.29.0"):
        ui_mode = launchEl.get("show_gui")
        if isinstance(ui_mode, bool):
            if ui_mode:
                launchEl["ui_mode"] = UIMode.GUI.value
            else:
                launchEl["ui_mode"] = None
            logger.info(
                f"Updating launcher options: 'show_gui':{launchEl.get('show_gui')} "
                f"-> 'ui_mode':{launchEl.get('ui_mode')}"
            )
            # removing old definition
            launchEl.pop("show_gui")

        dimension = launchEl.get("version")
        if isinstance(dimension, str):
            if dimension == "2d":
                launchEl["dimension"] = Dimension.TWO.value
            else:
                launchEl["dimension"] = Dimension.THREE.value
            logger.info(
                f"Updating launcher options: 'version':{launchEl.get('version')} "
                f"-> 'dimension':{launchEl.get('dimension')}"
            )
            # removing old definition
            launchEl.pop("version")
