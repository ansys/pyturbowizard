import os, csv
from packaging.version import Version

# Logger
from ptw_subroutines.utils import ptw_logger

logger = ptw_logger.getLogger()


def read_journals(
    case_data: dict,
    solver,
    element_name: str,
    fluent_dir: str = "",
    execution_dir: str = "",
):
    journal_list = case_data.get(element_name)
    if journal_list is not None and len(journal_list) > 0:
        logger.info(
            f"Reading specified journal files specified in ConfigFile '{element_name}': {journal_list}"
        )
        if os.path.exists(fluent_dir) and os.path.exists(execution_dir):
            # Change working dir
            chdir_command = rf"""(chdir "{execution_dir}")"""
            solver.execute_tui(chdir_command)
            # Create adjusted list with absolute paths, if not already set
            adjusted_journal_list = []
            for journal_file in journal_list:
                new_journal_file = journal_file
                if not os.path.isabs(journal_file):
                    new_journal_file = os.path.join(fluent_dir, journal_file)
                    logger.info(
                        f"Changing specified journal-file '{journal_file}' to absolute path : {new_journal_file}"
                    )
                adjusted_journal_list.append(new_journal_file)
            solver.settings.file.read_journal(file_name_list=adjusted_journal_list)
            # Change back working dir
            chdir_command = rf"""(chdir "{fluent_dir}")"""
            solver.execute_tui(chdir_command)
        else:
            # default procedure if no execution-folder has been specified
            solver.settings.file.read_journal(file_name_list=journal_list)

    return


def getNumberOfEquations(solver):
    number_eqs = 0
    # Check active number of equations
    if Version(solver._version) < Version("241"):
        equDict = solver.settings.solution.controls.equations()
        for equ in equDict:
            if equ == "flow":
                number_eqs += 4
            if equ == "kw":
                number_eqs += 2
            if equ == "temperature":
                number_eqs += 1
    else:
        number_eqs = len(solver.settings.solution.monitor.residual.equations.keys())
    return number_eqs


def addExecuteCommand(solver, command_name, command, pythonCommand: bool = False):
    # Add a command to execute after solving is finished
    if Version(solver._version) < Version("251"):
        if pythonCommand:
                solver.tui.solve.execute_commands.add_edit(
                    f"{command_name}", "yes", "yes", "yes", f'"{command}"'
                )
        else:
            solver.tui.solve.execute_commands.add_edit(
                f"{command_name}", "yes", "yes", "no", f'"{command}"'
            )
    else:
        solver.settings.solution.calculation_activity.execute_commands.create(name=command_name)
        solver.settings.solution.calculation_activity.execute_commands[command_name].execution_command = command
        solver.settings.solution.calculation_activity.execute_commands[command_name].enable = True
        solver.settings.solution.calculation_activity.execute_commands[command_name].execution_type = 'execute-at-end'
        solver.settings.solution.calculation_activity.execute_commands[command_name].python_cmd = pythonCommand

def check_version(solver):

    fluent_version = solver.get_fluent_version()
    if isinstance(fluent_version, str):
        return fluent_version
    else:
        return str(fluent_version.number)

def create_iso_surface(solver,name:str,field_name:str,iso_values:list,zones:list=None,surfaces:list=None):
    if (
            name
            not in solver.settings.results.surfaces.iso_surface.get_object_names()
    ):
        solver.settings.results.surfaces.iso_surface.create(name=name)

    if zones is None:
        zones = []
        if surfaces is None:
            zones = solver.settings.setup.cell_zone_conditions.get_active_child_names()

    if surfaces is None:
        surfaces = []

    solver.settings.results.surfaces.iso_surface[name] = {
        "field": field_name,
        "zones": zones,
        "surfaces": surfaces,
        "iso_values": iso_values,
    }

def create_iso_clip(solver,name:str,field_name:str,min_value:float,max_value:float,surfaces:list=None):
    if (
            name
            not in solver.settings.results.surfaces.iso_clip.get_object_names()
    ):
        solver.settings.results.surfaces.iso_clip.create(name=name)

    if surfaces is None:
        surfaces = []

    solver.settings.results.surfaces.iso_clip[name] = {
        "field": field_name,
        "range": {"minimum": min_value, "maximum": max_value},
        "surfaces": surfaces,
    }

def create_point_surface(solver,name:str,point:list,snap_method:str="nearest"):
    if (
            name
            not in solver.settings.results.surfaces.point_surface.get_object_names()
    ):
        solver.settings.results.surfaces.point_surface.create(name=name)
    allowed_values = solver.settings.results.surfaces.point_surface[name].snap_method.allowed_values()
    if snap_method in allowed_values:
        solver.settings.results.surfaces.point_surface[name] = {
            "points": point,
            "snap_method": snap_method,
        }
    else:
        logger.warning(f"Could not specify prescribed snap_method '{snap_method}' when creating point_surface '{name}'. Allowed methods are: {allowed_values}")

def create_plane_surface(solver,name:str,value:float,method:str='xy-plane'):
    if (
            name
            not in solver.settings.results.surfaces.plane_surface.get_object_names()
    ):
        solver.settings.results.surfaces.plane_surface.create(name=name)

    if method == 'xy-plane':
        solver.settings.results.surfaces.plane_surface[name] = {
            "method": method,
            "z": value,
        }
    elif method == 'zx-plane':
        solver.settings.results.surfaces.plane_surface[name] = {
            "method": method,
            "y": value,
        }
    elif method == 'yz-plane':
        solver.settings.results.surfaces.plane_surface[name] = {
            "method": method,
            "x": value,
        }
    else:
        allowed_methods = solver.settings.results.surfaces.plane_surface["bla"].method.allowed_values()
        logger.warning(f"Could not specify prescribed method '{method}' when creating plane_surface '{name}'. Allowed methods are: {allowed_methods}")


def export_solver_monitor(solver, filepath: str = "residual.csv", monitor_set_name: str = "residual"):
    mp = solver.monitors.get_monitor_set_data(monitor_set_name=monitor_set_name)
    indices = mp[0]
    data_dict = mp[1]
    with open(filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        header = ['Index'] + list(data_dict.keys())
        writer.writerow(header)
        # Write data rows
        for i in range(len(indices)):
            row = [indices[i]] + [data_dict[key][i] for key in data_dict]
            writer.writerow(row)

def create_and_evaluate_expression(solver, exp_name: str, definition: str, overwrite_definition=True, evaluate_value=False):
    if (exp_name not in solver.settings.setup.named_expressions.get_object_names()):
        solver.settings.setup.named_expressions.create(name=exp_name)
        solver.settings.setup.named_expressions[exp_name] = {"definition": definition}
    if overwrite_definition:
        solver.settings.setup.named_expressions[exp_name] = {"definition": definition}
    value = None
    if evaluate_value:
        value = solver.settings.setup.named_expressions[exp_name].get_value()
    if isinstance(value, str):
        str_value = value.split()[0]
        value = float(str_value)
    return value

