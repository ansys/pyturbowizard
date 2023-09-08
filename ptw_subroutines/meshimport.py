# Logger
from ptw_subroutines.utils import ptw_logger

logger = ptw_logger.getLogger()


def import_01(data, solver):
    success = False
    meshFilename = data.get("meshFilename")
    if type(meshFilename) is str:
        logger.info(f"Importing mesh '{meshFilename}'")
        if meshFilename.endswith(".def") or meshFilename.endswith(".cgns"):
            solver.file.import_.read(file_type="cfx-definition", file_name=meshFilename)
            success = True
        else:
            solver.file.read(file_type="mesh", file_name=meshFilename)
            success = True
    elif type(meshFilename) is list:
        logger.info(f"Importing multiple meshes...")
        meshIndex = 0
        for fileName in meshFilename:
            if meshIndex == 0:
                logger.info(f"Importing mesh '{fileName}'")
                solver.file.read(file_type="mesh", file_name=fileName)
            else:
                logger.info(f"Appending mesh '{fileName}'")
                solver.tui.mesh.modify_zones.append_mesh(fileName)
            meshIndex += 1
        success = True

    if not success:
        logger.error(f"No mesh file has been imported!")

    # BC Profiles
    profileName = data.get("profileName_In")
    if profileName is not None and profileName != "":
        logger.info(f"Importing profile '{profileName}'")
        solver.file.read_profile(file_name=profileName)

    profileName = data.get("profileName_Out")
    if profileName is not None and profileName != "":
        logger.info(f"Importing profile '{profileName}'")
        solver.file.read_profile(file_name=profileName)

    return success
