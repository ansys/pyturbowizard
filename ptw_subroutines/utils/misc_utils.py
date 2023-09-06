import os.path
import ntpath
import subprocess

# Logger
from ptw_subroutines.utils import ptw_logger

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

def run_extsch_script(scriptPath:str, workingDir:str, caseEl:dict):
    from sys import platform
    if platform == "linux" or platform == "linux2":
        logger.info(f"Running 'extsch' script...")
        caseFilename = caseEl.get("caseFilename")
        output_filename = f"{caseFilename}.extsch"
        commandlist = list()
        exec_path = os.path.join(scriptPath, "ptw_misc", "extsch_script", "extsch")
        commandlist.append(exec_path)
        commandlist.append(f"{caseFilename}.cas.h5")
        commandlist.append("| uniq")
        commandlist.append(f"> {output_filename}")
        process_files = subprocess.Popen(
            commandlist, cwd=workingDir, stdout=subprocess.DEVNULL
        )
        logger.info(f"'extsch' output written to: {output_filename}")
    else:
        logger.info(f"Script 'extsch' only available for linux platforms (current platform: {platform}): Skipping function!")

def ptw_output(fl_workingDir, study_name=None, case_name=None):
    # Define a PTW output folder in Fluent working directory
    ptw_output_path = ""
    if os.path.exists(fl_workingDir):
        ptw_output_path = os.path.join(fl_workingDir, "PTW_output")
        if not os.path.exists(ptw_output_path):
            os.makedirs(ptw_output_path)
    
    # Get the Path to a seprate case folder
    if study_name is not None:
        study_name = 'study_'+study_name
        study_path = os.path.join(ptw_output_path, study_name)
        if not os.path.exists(study_path):
            os.makedirs(study_path)
        return study_path
    
    # Get the Path to a seprate study folder
    if case_name is not None:
        case_name = 'case_' + case_name
        case_path = os.path.join(ptw_output_path, case_name)
        if not os.path.exists(case_path):
            os.makedirs(case_path)
        return case_path
    
    return ptw_output_path



def can_convert_to_number(value):
    try:
        float_value = float(value)
        int_value = int(float_value)
        return float_value == int_value
    except ValueError:
        return False






