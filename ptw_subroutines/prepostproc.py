import os

from ptw_subroutines.utils import (
    ptw_logger,
    postproc_utils,
    dict_utils,
    fluent_utils,
    misc_utils,
)

# Logger
logger = ptw_logger.getLogger()


def prepost(data, solver, functionEl, launchEl):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="prepostproc",
        defaultName="prepost_01",
    )

    logger.info(f"Running Pre-Postprocessing Function '{functionName}' ...")
    if functionName == "prepost_01":
        prepost_01(data, solver, launchEl)
    else:
        logger.info(
            f"Prescribed Function '{functionName}' not known. Skipping Pre-Postprocessing!"
        )

    logger.info("Running Pre-Postprocessing Function... finished!")


def prepost_01(data, solver, launchEl):
    fl_WorkingDir = launchEl.get("workingDir")
    # Check version -> for version 24.1 use python command
    use_python_command = False
    #use_python_command = solver.version >= "24.1.0"

    # Set output for time statistics in transcript
    command_name = "print-time-statistics"
    command = "solver.tui.parallel.timer.usage()"
    if not use_python_command:
        command = "/report/system/time-stats"
    fluent_utils.addExecuteCommand(
        command_name=command_name,
        command=command,
        solver=solver,
        pythonCommand=use_python_command,
    )

    # Save 3D file of the mesh and domain

    # Get walls of domain
    surfaces = solver.field_info.get_surfaces_info()
    wall_surfaces = [
        key for key, value in surfaces.items() if value.get("zone_type") == "wall"
    ]

    solver.results.graphics.mesh["Mesh"] = {}
    solver.results.graphics.mesh["Mesh"].surfaces_list = wall_surfaces
    solver.results.graphics.mesh["Mesh"].options.edges = True

    solver.results.graphics.mesh.display(object_name="Mesh")
    caseOutPath = misc_utils.ptw_output(
        fl_workingDir=fl_WorkingDir, case_name=data["caseFilename"]
    )
    MeshPicFilename = os.path.join(caseOutPath, "Mesh.avz")
    solver.tui.display.save_picture(f"{MeshPicFilename}")

    # Create Spanwise Plots if specified by user
    if data["locations"].get("tz_turbo_topology_names") is not None:
        try:
            spanPlots(data, solver, launchEl)
        except Exception as e:
            logger.info(f"No span plots have been created: {e}")

    # Create Oil Flow Pathlines if specified by user
    if solver.version >= "24.1.0" and data["results"].get("oilflow_pathlines_surfaces") is not None and data["results"].get("oilflow_pathlines_var") is not None:
        try:
            oilflow_pathlines(data, solver, launchEl)
        except Exception as e:
            logger.info(f"No oil flow pathlines have been created: {e}")

    # Create Pathlines if specified by user
    if solver.version >= "24.1.0" and data["results"].get("pathlines_releaseSurfaces") is not None and data["results"].get("pathlines_var") is not None:
        try:
            pathlines(data, solver, launchEl)
        except Exception as e:
            logger.info(f"No pathlines have been created: {e}")


def spanPlots(data, solver, launchEl):
    # Check version -> for version 24.1 use python command
    use_python_command = solver.version >= "24.1.0"

    # Create spanwise surfaces
    spansSurf = data["results"].get("span_plot_height")
    contVars = data["results"].get("span_plot_var")

    # Declare a string to store all the commands
    all_commands_str = ""

    # Set AVZ is bugged since "" get recognized as terminator by pyFluent in every case
    # Set picture format for output to AVZ (Python and TUI)
    # solver.tui.display.set.picture.driver.avz
    # AVZvar = '"AVZ"'
    # setAVZ = f'/preferences/graphics/hardcopy-settings/hardcopy-driver {AVZvar}'
    # all_commands_str = setAVZ

    availableFieldDataNames = (
        solver.field_data.get_scalar_field_data.field_name.allowed_values()
    )
    for contVar in contVars:
        if contVar not in availableFieldDataNames:
            logger.info(f"FieldVariable: '{contVar}' not available in Solution-Data!")
            logger.info(f"Available Scalar Values are: '{availableFieldDataNames}'")

    # Create Contour Plots for every surface
    for spanVal in spansSurf:
        spanName = f"span-{int(spanVal*100)}"
        logger.info(f"Creating spanwise ISO-surface: {spanName}")
        solver.results.surfaces.iso_surface[spanName] = {}

        if solver.version >= "24.1.0":
            zones = solver.results.surfaces.iso_surface[spanName].zones.get_attr(
                "allowed-values"
            )
            solver.results.surfaces.iso_surface[spanName](
                field="spanwise-coordinate", zones=zones, iso_values=[spanVal]
            )
        else:
            zones = solver.results.surfaces.iso_surface[spanName].zone.get_attr(
                "allowed-values"
            )
            solver.results.surfaces.iso_surface[spanName](
                field="spanwise-coordinate", zone=zones, iso_value=[spanVal]
            )


        for contVar in contVars:
            if contVar in availableFieldDataNames:
                contName = spanName + "-" + contVar
                logger.info(f"Creating spanwise contour-plot: {contName}")
                solver.results.graphics.contour[contName] = {}
                solver.results.graphics.contour[contName](
                    field=contVar,
                    contour_lines=True,
                    surfaces_list=spanName,
                )
                # set range to local range
                solver.results.graphics.contour[
                    contName
                ].range_option.auto_range_on.global_range = False

                # Set color map to banded and reduce size
                solver.results.graphics.contour[contName].color_map(size=20)
                solver.results.graphics.contour[contName].coloring(option="banded")
                solver.results.graphics.contour[contName].display()

                fl_workingDir = launchEl.get("workingDir")
                # Save contour plos as avz files
                # Python commands (not supported yet):
                # plot_folder = os.path.join(fl_workingDir, f'plots_{caseFilename}')
                # os.makedirs(plot_folder, exist_ok=True)  # Create the folder if it doesn't exist
                # plot_filename = os.path.join(plot_folder, f'{contName}_plot')
                # solver.tui.display.save_picture(plot_filename)

                
                if use_python_command:
                    # Python commands
                    plot_filename = f"{contName}_plot"
                    contour_display_command = f"solver.results.graphics.contour['{contName}'].display()"
                    contour_save_command = f"solver.results.graphics.picture.save_picture(file_name='{plot_filename}')"
                else:
                    # TUI commands
                    plot_filename = "./" + f"{contName}_plot"
                    contour_display_command = (
                        f"/results/graphics/contour/display {contName}"
                    )
                    contour_save_command = f"/display/save-picture {plot_filename} ok"

                command_str = (
                    contour_display_command + "\n" + contour_save_command + "\n"
                )
                all_commands_str += command_str

    command_name = "save-contour-plots"
    logger.info(f"Adding execute command: {command_name}")
    fluent_utils.addExecuteCommand(
        solver=solver,
        command_name=command_name,
        command=all_commands_str,
        pythonCommand=use_python_command,
    )

    return

def oilflow_pathlines(data, solver, launchEl):

    oilflowPL_vars = data["results"].get("oilflow_pathlines_var")

    availableFieldDataNames = (
        solver.field_data.get_scalar_field_data.field_name.allowed_values()
    )
    for oilflowPL_var in oilflowPL_vars:
        if oilflowPL_var not in availableFieldDataNames:
            logger.info(f"FieldVariable: '{oilflowPL_var}' not available in Solution-Data!")
            logger.info(f"Available Scalar Values are: '{availableFieldDataNames}'")

    oilflowPL_surfaces = data["results"]["oilflow_pathlines_surfaces"]
    
    # Create oil flow pathlines on specified surfaces colorized by the specified variables
    oilflowPL_objects = []
    for oilflowPL_var in oilflowPL_vars:
        oilflowPL_name = f"oilflow-pathlines-{oilflowPL_var}"
        logger.info(f"Creating oil flow pathlines: {oilflowPL_name}")
        solver.results.graphics.pathline[oilflowPL_name] = {}
        solver.results.graphics.pathline[oilflowPL_name].options(oil_flow=True)
        solver.results.graphics.pathline[oilflowPL_name](
            onzone = oilflowPL_surfaces,
            release_from_surfaces = oilflowPL_surfaces,
            field = oilflowPL_var,
            step = 3000,
            skip = 15)
        solver.results.graphics.pathline[oilflowPL_name].color_map(size=20)
        oilflowPL_objects.append(oilflowPL_name)

    # Create mesh object with oil flow surfaces
    meshName = "oilflowPL-surfaces"
    logger.info(f"Creating mesh object: {meshName}")
    solver.results.graphics.mesh[meshName] = {}
    solver.results.graphics.mesh[meshName](
        surfaces_list = oilflowPL_surfaces
    )

    # Create scenes including the pathlines and the blade mesh object
    for oilflowPL_object in oilflowPL_objects:
        sceneName = f"sc-{oilflowPL_object}"
        logger.info(f"Creating scene: {sceneName}")
        scene_inputs = [oilflowPL_object,meshName]
        for scene_input in scene_inputs:     
            solver.results.scene[sceneName] = {}
            solver.results.scene[sceneName].graphics_objects[scene_input] = {
            "name": scene_input
            }


    return


def pathlines(data, solver, launchEl):

    pathlineVars = data["results"].get("pathlines_var")

    availableFieldDataNames = (
        solver.field_data.get_scalar_field_data.field_name.allowed_values()
    )
    for pathlineVar in pathlineVars:
        if pathlineVar not in availableFieldDataNames:
            logger.info(f"FieldVariable: '{pathlineVar}' not available in Solution-Data!")
            logger.info(f"Available Scalar Values are: '{availableFieldDataNames}'")

    pathlinesRelSurf = data["results"]["pathlines_releaseSurfaces"]
    
    # Create pathlines from specified surfaces colorized by the specified variables
    for pathlineVar in pathlineVars:
        pathlineName = f"pathlines-{pathlineVar}"
        logger.info(f"Creating pathlines: {pathlineName}")
        solver.results.graphics.pathline[pathlineName] = {}
        solver.results.graphics.pathline[pathlineName](
            release_from_surfaces = pathlinesRelSurf,
            field = pathlineVar,
            step = 3000,
            skip = 5)
        solver.results.graphics.pathline[pathlineName].color_map(size=20)

    return
