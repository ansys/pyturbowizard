from packaging import version

# Logger
from ptw_subroutines.utils import ptw_logger

logger = ptw_logger.getLogger()


def read_journals(data: dict, solver, element_name: str):
    journal_list = data.get(element_name)
    if journal_list is not None and len(journal_list) > 0:
        logger.info(
            f"Reading specified journal files specified in ConfigFile '{element_name}': {journal_list}"
        )
        solver.file.read_journal(file_name_list=journal_list)
    return


def getNumberOfEquations(solver):
    # Check active number of equations
    equDict = solver.solution.controls.equations()
    number_eqs = 0
    for equ in equDict:
        if equ == "flow":
            number_eqs += 4
        if equ == "kw":
            number_eqs += 2
        if equ == "temperature":
            number_eqs += 1

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

