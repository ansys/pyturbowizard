# Logger
from ptw_subroutines.utils import ptw_logger

logger = ptw_logger.getLogger()


def import_01(data, solver):
    success = False
    meshFilename = data.get("meshFilename")
    if isinstance(meshFilename, str):
        logger.info(f"Importing mesh '{meshFilename}'")
        if meshFilename.endswith(".def"):
            solver.file.import_.read(file_type="cfx-definition", file_name=meshFilename)
            success = True
        elif meshFilename.endswith(".cgns"):
            solver.file.import_.read(file_type="cgns-mesh", file_name=meshFilename)
            success = True
        else:
            solver.file.read(file_type="mesh", file_name=meshFilename)
            success = True
    elif isinstance(meshFilename, list):
        logger.info(f"Importing multiple meshes...")
        import_mesh_type = False
        for fileName in meshFilename:
            if (
                fileName.endswith(".def")
                or fileName.endswith(".gtm")
                or fileName.endswith(".cgns")
            ):
                import_mesh_type = True
                break

        if import_mesh_type:
            if solver.version < "241":
                logger.error(
                    f"Import of multiple meshes only supported by version v241 or later"
                )
                return success
            else:
                logger.info(f"Importing multiple meshes '{meshFilename}'")
                multiple_mesh_import(solver=solver, meshnamelist=meshFilename)
        else:
            multiple_mesh_read(solver=solver, meshnamelist=meshFilename)

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


def multiple_mesh_read(solver, meshnamelist):
    meshIndex = 0
    for fileName in meshnamelist:
        if meshIndex == 0:
            logger.info(f"Importing mesh '{fileName}'")
            solver.file.read(file_type="mesh", file_name=fileName)
        else:
            logger.info(f"Appending mesh '{fileName}'")
            solver.tui.mesh.modify_zones.append_mesh(fileName)
        meshIndex += 1


def multiple_mesh_import(solver, meshnamelist):
    # using turbo-workflow to import multiple meshes
    solver.tui.turbo_workflow.workflow.enable()
    solver.workflow.InitializeWorkflow(WorkflowType=r"Turbo Workflow")
    solver.workflow.TaskObject["Describe Component"].Execute()
    solver.workflow.TaskObject["Define Blade Row Scope"].Execute()
    meshname_strings = ";".join(rf"{meshnamelist}")
    for meshname in meshnamelist:
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
