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
    use_python_command = solver.version >= "24.1.0"

    # Set output for time statistics in transcript
    command_name = "print-time-statistics"
    command = "solver.tui.parallel.timer.usage"
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

    solver.tui.results.graphics.mesh.display('"Mesh"')
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

                plot_filename = "./" + f"{contName}_plot"
                if use_python_command:
                    # Python commands
                    contour_display_command = f"solver.results.graphics.contour.display(object_name={contName})"
                    contour_save_command = f"solver.results.graphics.picture.save_picture(file_name={plot_filename})"
                else:
                    # TUI commands
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
