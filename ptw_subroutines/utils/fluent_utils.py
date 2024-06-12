import os.path

from packaging import version

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
            solver.file.read_journal(file_name_list=adjusted_journal_list)
            # Change back working dir
            chdir_command = rf"""(chdir "{fluent_dir}")"""
            solver.execute_tui(chdir_command)
        else:
            # default procedure if no execution-folder has been specified
            solver.file.read_journal(file_name_list=journal_list)

    return


def getNumberOfEquations(solver):
    number_eqs = 0
    # Check active number of equations
    if solver.version < "241":
        equDict = solver.solution.controls.equations()
        for equ in equDict:
            if equ == "flow":
                number_eqs += 4
            if equ == "kw":
                number_eqs += 2
            if equ == "temperature":
                number_eqs += 1
    else:
        number_eqs = len(solver.solution.monitor.residual.equations.keys())
    return number_eqs


def addExecuteCommand(solver, command_name, command, pythonCommand: bool = False):
    # Add a command to execute after solving is finished
    if pythonCommand:
        solver.tui.solve.execute_commands.add_edit(
            f"{command_name}", "yes", "yes", "yes", f'"{command}"'
        )
    else:
        solver.tui.solve.execute_commands.add_edit(
            f"{command_name}", "yes", "yes", "no", f'"{command}"'
        )
