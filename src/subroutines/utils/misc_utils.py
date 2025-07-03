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

import glob
import ntpath
import os.path
import shutil
import subprocess
import time

# Logger
from src.subroutines.utils import ptw_logger

logger = ptw_logger.getLogger()


def get_free_filename(dirname, base_filename):
    base_name, ext_name = os.path.splitext(base_filename)
    filename = base_filename
    filepath = os.path.join(dirname, filename)
    counter = 1
    while os.path.isfile(filepath):
        filename = base_name + "_" + str(counter) + ext_name
        filepath = os.path.join(dirname, filename)
        counter += 1
    return filename


def get_free_filename_maxIndex(dirname, base_filename):
    base_name, ext_name = os.path.splitext(base_filename)
    filename = base_filename
    file_list = os.listdir(dirname)
    maxCount = None
    for file in file_list:
        checkfile, checkExt = os.path.splitext(ntpath.basename(file))
        checkfile_parts = checkfile.split("_")
        if (checkfile_parts[0] == base_name) and (checkExt == ext_name):
            try:
                count = int(checkfile_parts[-1])
            except ValueError:
                count = 0
            if maxCount is None:
                maxCount = count
            else:
                maxCount = max(maxCount, count)

    if maxCount is not None:
        filename = base_name + "_" + str(maxCount + 1) + ext_name

    return filename


def run_extsch_script(path_to_script: str, workingDir: str, caseEl: dict):
    import platform

    if platform.system() == "Linux":
        logger.info(f"Running 'extsch' script...")
        # Check if the script exists
        if not os.path.exists(path_to_script):
            logger.warning(
                f"Script 'extsch' not found at: {path_to_script}. Skipping function!"
            )
            return

        caseFilename = caseEl.get("caseFilename")
        output_filename = f"{caseFilename}.extsch"
        commandlist = list()
        commandlist.append(path_to_script)
        commandlist.append(f"{caseFilename}.cas.h5")
        commandlist.append("| uniq")
        commandlist.append(f"> {output_filename}")
        process_files = subprocess.Popen(
            commandlist, cwd=workingDir, stdout=subprocess.DEVNULL
        )
        logger.info(f"'extsch' output written to: {output_filename}")
    else:
        logger.info(
            f"Script 'extsch' only available for linux platforms (current platform: {platform}): Skipping function!"
        )


def ptw_output(fl_workingDir, study_name=None, case_name=None):
    # Define a PTW output folder in Fluent working directory
    ptw_output_path = ""
    if os.path.exists(fl_workingDir):
        ptw_output_path = os.path.join(fl_workingDir, "PTW_output")
        if not os.path.exists(ptw_output_path):
            os.makedirs(ptw_output_path)

    # Get the Path to a separate case folder
    if study_name is not None:
        study_name = "study_" + study_name
        study_path = os.path.join(ptw_output_path, study_name)
        if not os.path.exists(study_path):
            os.makedirs(study_path)
        return study_path

    # Get the Path to a separate study folder
    if case_name is not None:
        case_name = "case_" + case_name
        case_path = os.path.join(ptw_output_path, case_name)
        if not os.path.exists(case_path):
            os.makedirs(case_path)
        return case_path

    return ptw_output_path


def can_convert_to_number(value):
    try:
        float_value = float(value)
        return True
    except ValueError:
        return False


def move_files(
    source_dir: str,
    target_dir: str,
    filename_wildcard: str,
    overwrite: bool = True,
):
    filenames = glob.glob(os.path.join(source_dir, filename_wildcard))
    for source_file in filenames:
        target_file = ntpath.basename(source_file)
        logger.info(
            f"Moving file '{target_file}' from '{source_dir}' to '{target_dir}'"
        )
        target_file = os.path.join(target_dir, target_file)
        if overwrite:
            shutil.move(source_file, target_file)
        else:
            try:
                shutil.move(source_file, target_dir)
            except shutil.Error as e:
                logger.exception(
                    f"Moving file '{source_file}' failed: {str(e)}"
                )


def remove_files(working_dir: str, filename_wildcard):
    import glob

    if isinstance(filename_wildcard, list):
        for wc in filename_wildcard:
            remove_files(working_dir=working_dir, filename_wildcard=wc)
    if isinstance(filename_wildcard, str):
        filenames = glob.glob(os.path.join(working_dir, filename_wildcard))
        for file_name in filenames:
            logger.info(f"Removing file '{file_name}'")
            try:
                os.remove(file_name)
            except PermissionError as e:
                logger.exception(f"Remove file '{file_name}' failed: {str(e)}")


def fluent_cleanup(working_dir: str, cleanup_data):
    if cleanup_data:
        # Wait some time, till the fluent session is closed to avoid any file-locks
        time.sleep(5)
        logger.info("Doing standard clean-up...")
        remove_files(working_dir=working_dir, filename_wildcard="fluent*.trn")
        remove_files(working_dir=working_dir, filename_wildcard="*slurm*")
        logger.info("Doing standard clean-up... finished!")
    elif isinstance(cleanup_data, list):
        # Wait some time, till the fluent session is closed to avoid any file-locks
        time.sleep(5)
        logger.info("Doing user-adjusted clean-up...")
        remove_files(working_dir=working_dir, filename_wildcard=cleanup_data)
        logger.info("Doing user-adjusted clean-up...  finished!")
