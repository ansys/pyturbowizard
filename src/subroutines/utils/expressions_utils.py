import os
import re
from packaging.version import Version

# Logger
from src.subroutines.utils import ptw_logger, misc_utils

logger = ptw_logger.getLogger()


def write_expression_file(data: dict, script_dir: str, working_dir: str):
    fileName = data.get("expressionFilename")
    # if nothing is set for "expressionFilename" a default value ("expressions.tsv") is set and dict will be updated
    if fileName is None or fileName == "":
        fileName = "expressions.tsv"
        data["expressionFilename"] = fileName

    case_output_path = misc_utils.ptw_output(
        fl_workingDir=working_dir, case_name=data.get("caseFilename")
    )
    fileName = os.path.join(case_output_path, fileName)
    # Remove exp-file
    if os.path.exists(fileName):
        os.remove(fileName)
    # Write new file
    with open(fileName, "w") as sf:
        expressionTemplatePath = os.path.join(
            script_dir, "templates", data["expressionTemplate"]
        )
        with open(expressionTemplatePath, "r") as templateFile:
            tempData = templateFile.read()
            templateFile.close()
        helperDict = data["locations"]
        expressionEl = data.get("expressions")
        helperDict.update(expressionEl)
        helperDict.update(data["fluid_properties"])
        # add rotation axis
        helperDict["rotation_axis_direction"] = tuple(
            data.setdefault("rotation_axis_direction", [0.0, 0.0, 1.0])
        )
        helperDict["rotation_axis_origin"] = tuple(
            data.setdefault("rotation_axis_origin", [0.0, 0.0, 0.0])
        )
        # add efficiency definition
        helperDict["efficiency_ratio"] = data.setdefault(
            "efficiency_ratio", "TotalToTotal"
        )
        tempData = cleanup_input_expressions(
            availableKeyEl=helperDict, fileData=tempData
        )
        for line in tempData.splitlines():
            try:
                sf.write(line.format(**helperDict))
                sf.write("\n")
            except KeyError as e:
                logger.info(f"Expression not found in ConfigFile: {str(e)}")

    return


def cleanup_input_expressions(availableKeyEl: dict, fileData: str):
    cleanfiledata = ""

    for line in fileData.splitlines():
        # write header line
        if cleanfiledata == "":
            cleanfiledata = line
        # check BCs and prescribed Expressions
        elif line.startswith('"BC'):
            columns = line.split("\t")
            expKey = columns[1].replace('"{', "").replace('}"', "")
            if availableKeyEl.get(expKey) is not None:
                cleanfiledata = cleanfiledata + "\n" + line
            else:
                continue
        elif line.startswith('"GEO'):
            columns = line.split("\t")
            expKey = columns[1].replace('"{', "").replace('}"', "")
            if availableKeyEl.get(expKey) is not None:
                cleanfiledata = cleanfiledata + "\n" + line
            elif line.startswith('"GEO_NPSHa"'):
                columns[1] = columns[1].replace("{" + expKey + "}", "0 [m]")
                line = "\t".join(columns)
                cleanfiledata = cleanfiledata + "\n" + line
            else:
                columns[1] = columns[1].replace("{" + expKey + "}", "1")
                line = "\t".join(columns)
                cleanfiledata = cleanfiledata + "\n" + line

        elif "Torque" in line:
            if availableKeyEl.get("bz_walls_torque") is not None:
                cleanfiledata = cleanfiledata + "\n" + line
            else:
                continue

        elif "Euler" in line:
            if (
                availableKeyEl.get("bz_ep1_Euler")
                and availableKeyEl.get("bz_ep2_Euler")
            ) is not None:
                cleanfiledata = cleanfiledata + "\n" + line
            else:
                continue
        else:
            cleanfiledata = cleanfiledata + "\n" + line

    return cleanfiledata


def check_input_parameter_expressions(solver):
    for exp_name in solver.settings.setup.named_expressions():
        exp = solver.settings.setup.named_expressions.get(exp_name)
        if exp_name.startswith("BC_"):
            # First check
            expValue = exp.get_value()
            if not isinstance(expValue, float):
                logger.info(
                    f"'{exp_name}' seems not to be valid: '{expValue}' "
                    f"--> Removing definition as Input Parameter..."
                )
                exp.set_state({"input_parameter": False})
            else:
                # Second check:
                # if any strings in the expression except units or brackets, it's probably not valid
                exp_def = exp.definition()
                cleaned_def = re.sub(r"[\[].*?[\]]", "", exp_def)
                cleaned_def = cleaned_def.replace("(", "").replace(")", "")
                try:
                    float(cleaned_def)
                    exp.set_state({"input_parameter": True})
                except ValueError:
                    logger.info(
                        f"'{exp_name}' seems not to be const. value and "
                        f"may depend on another expression or function: {exp_def} "
                        f"--> Removing definition as Input Parameter..."
                    )
                    exp.set_state({"input_parameter": False})

    return


def check_output_parameter_expressions(caseEl: dict, solver):
    solutionDict = caseEl.get("solution")
    if solutionDict is None:
        return
    reportlist = solutionDict.get("reportlist")
    if reportlist is None:
        return

    for expName in solver.settings.setup.named_expressions():
        exp = solver.settings.setup.named_expressions.get(expName)
        if expName in reportlist:
            logger.info(
                f"Expression '{expName}' found in Config-File: 'Case/Solution/reportlist'"
                f"Setting expression '{expName}' as output-parameter"
            )
            exp.set_state({"output_parameter": True})
    return


def check_expression_versions(solver):
    import re

    if Version(solver._version) < Version("241"):
        for expName in solver.settings.setup.named_expressions():
            if (
                expName == "MP_Isentropic_Efficiency"
                or expName == "MP_Polytropic_Efficiency"
            ):
                exp = solver.settings.setup.named_expressions.get(expName)
                logger.info(
                    f"Checking & updating expression '{expName}' to latest version"
                )
                definition = exp.get_state()["definition"]
                definition_new = re.sub(r",Process='\w+'", "", definition)
                exp.set_state({"definition": definition_new})

    return


def create_and_evaluate_expression(
    exp_name: str, definition: str, overwrite_definition=True, evaluate_value=True
):
    if exp_name not in solver.settings.setup.named_expressions.get_object_names():
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
        else:
            value = float(value)
    return value
