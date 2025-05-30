# Logger
from ptw_subroutines.utils import ptw_logger, fluent_utils

from packaging.version import Version

logger = ptw_logger.getLogger()


def import_01(data, solver):
    success = False
    meshFilename = data.get("meshFilename")
    if isinstance(meshFilename, str):
        logger.info(f"Importing mesh '{meshFilename}'")
        if meshFilename.endswith(".def"):
            solver.settings.file.import_.read(file_type="cfx-definition", file_name=meshFilename)
            success = True
        elif meshFilename.endswith(".cgns"):
            solver.settings.file.import_.read(file_type="cgns-mesh", file_name=meshFilename)
            success = True
        elif meshFilename.endswith(".gtm"):
            if Version(solver._version) < Version("241"):
                logger.error(
                    f"Import of multiple meshes only supported by version v241 or later"
                )
            else:
                meshnamelist = [meshFilename]
                multiple_mesh_import(solver=solver, meshname_list=meshnamelist)
                success = True
        else:
            solver.settings.file.read(file_type="mesh", file_name=meshFilename)
            success = True
    elif isinstance(meshFilename, list):
        logger.info(f"Importing multiple meshes...")
        supported_import_mesh_type = False
        for fileName in meshFilename:
            if (
                fileName.endswith(".def")
                or fileName.endswith(".gtm")
                or fileName.endswith(".cgns")
            ):
                supported_import_mesh_type = True
                break

        if supported_import_mesh_type:
            if Version(solver._version) < Version("241"):
                logger.error(
                    f"Import of multiple meshes only supported by version v241 or later"
                )
                return success
            else:
                logger.info(f"Importing multiple meshes '{meshFilename}'")
                multiple_mesh_import(solver=solver, meshname_list=meshFilename)
        else:
            multiple_mesh_read(solver=solver, meshnamelist=meshFilename)

        success = True

    if not success:
        logger.error(f"No mesh file has been imported!")

    # BC Profiles
    profileName = data.get("profileName_In")
    if profileName is not None and profileName != "":
        logger.info(f"Importing profile '{profileName}'")
        solver.settings.file.read_profile(file_name=profileName)

    profileName = data.get("profileName_Out")
    if profileName is not None and profileName != "":
        logger.info(f"Importing profile '{profileName}'")
        solver.settings.file.read_profile(file_name=profileName)

    return success


def multiple_mesh_read(solver, meshnamelist):
    meshIndex = 0
    for fileName in meshnamelist:
        if meshIndex == 0:
            logger.info(f"Importing mesh '{fileName}'")
            solver.settings.file.read(file_type="mesh", file_name=fileName)
        else:
            logger.info(f"Appending mesh '{fileName}'")
            solver.tui.mesh.modify_zones.append_mesh(fileName)
        meshIndex += 1


def multiple_mesh_import(solver, meshname_list:list):
    # using turbo-workflow to import multiple meshes
    solver.tui.turbo_workflow.workflow.enable()
    solver.workflow.InitializeWorkflow(WorkflowType=r"Turbo Workflow")
    solver.workflow.TaskObject["Describe Component"].Execute()
    solver.workflow.TaskObject["Define Blade Row Scope"].Execute()
    meshname_strings = ";".join(rf"{meshname_list}")
    for meshname in meshname_list:
        meshname_formatted = rf"{meshname}"
        solver.workflow.TaskObject["Import Mesh"].Arguments.set_state(
            {
                r"MeshFilePath": meshname_strings,
                r"MeshName": meshname_formatted,
            }
        )
        solver.workflow.TaskObject["Import Mesh"].InsertCompoundChildTask()
        solver.workflow.TaskObject[meshname_formatted].Arguments.set_state(
            {
                r"MeshFilePath": meshname_formatted,
                r"MeshName": meshname_formatted,
            }
        )
        solver.workflow.TaskObject[meshname_formatted].Execute()
    # Clean-up
    # for meshname in meshnamelist:
    #     solver.workflow.TaskObject["Import Mesh"].Arguments.set_state(
    #         {
    #             r"MeshFilePath": r"",
    #             r"MeshName": rf"{meshname}",
    #         }
    #     )
    # Turn off Turbo-Workflow
    solver.tui.turbo_workflow.workflow.disable("yes")
    return
