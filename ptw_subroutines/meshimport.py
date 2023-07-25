#Logger
from ptw_subroutines import ptw_logger
logger = ptw_logger.getLogger()

def import_01(data, solver):
    success = False
    meshFilename = data["meshFilename"]
    if meshFilename.endswith(".def") or meshFilename.endswith(".cgns"):
        solver.file.import_.read(file_type="cfx-definition", file_name=meshFilename)
        success = True
    else:
        solver.file.read(file_type="mesh", file_name=meshFilename)
        success = True

    # BC Profiles
    profileName = data.get("profileName_In")
    if profileName is not None and profileName != "":
        solver.file.read_profile(file_name=profileName)

    profileName = data.get("profileName_Out")
    if profileName is not None and profileName != "":
        solver.file.read_profile(file_name=profileName)

    return success
