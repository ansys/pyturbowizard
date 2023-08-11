import os.path
import ntpath

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












