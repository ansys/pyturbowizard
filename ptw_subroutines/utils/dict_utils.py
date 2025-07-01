import os
import json
import copy

# Logger
from ptw_subroutines.utils import ptw_logger

logger = ptw_logger.getLogger()


def get_funcname_and_upd_funcdict(
    parentDict: dict, functionDict: dict, funcDictName: str, defaultName: str
):
    functionName = None
    if functionDict is not None:
        functionName = functionDict.get(funcDictName)
    # Set Default if not already set
    if functionName is None:
        functionName = defaultName
        # If the element is not existing, create a new one, otherwise update the existing
        if functionDict is None:
            functionDict = {"functions": {funcDictName: functionName}}
        else:
            functionDict.update({funcDictName: functionName})

    # Update Parent Element
    parentDict.update({"functions": functionDict})
    return functionName


def merge_functionDicts(caseDict: dict, glfunctionDict: dict):
    # Merge function dicts
    caseFunctionDict = caseDict.get("functions")
    if glfunctionDict is not None and caseFunctionDict is not None:
        helpDict = glfunctionDict.copy()
        helpDict.update(caseFunctionDict)
        caseFunctionDict = helpDict
    elif caseFunctionDict is None:
        caseFunctionDict = glfunctionDict
    return caseFunctionDict


def merge_data_with_refDict(caseDict: dict, allCasesDict: dict):
    refCaseName = caseDict.get("refCase")
    refDict = allCasesDict.get(refCaseName)
    if refDict is None:
        logger.info(
            f"Specified Reference Case {refCaseName} not found in Config-File! --> Skipping CopyFunction..."
        )
        return caseDict
    helpCaseDict = copy.deepcopy(refDict)
    helpCaseDict.update(caseDict)
    caseDict.update(helpCaseDict)
    return


def get_material_from_lib(caseDict: dict, scriptPath: str):
    if isinstance(caseDict.get("fluid_properties"), str):
        materialStr = caseDict.get("fluid_properties")
        materialFileName = os.path.join(scriptPath, "ptw_misc", "material_lib.json")
        materialFile = open(materialFileName, "r")
        materialDict = json.load(materialFile)
        materialDict = materialDict.get(materialStr)
        if materialDict is not None:
            caseDict["fluid_properties"] = materialDict
        else:
            raise Exception(
                f"Specified material '{materialStr}' in config-file not found in material-lib: {materialFileName}"
            )
    return


def detect_unused_keywords(refDict: dict, compareDict: dict, path="root"):
    for item in compareDict:
        if item not in refDict:
            logger.warning(
                f"Element found in Config-File that is not known or used! Check keyword: '{item}' in '{path}'"
            )
        else:
            refEl = refDict.get(item)
            compareEl = compareDict.get(item)
            if isinstance(refEl, dict) and isinstance(compareEl, dict):
                newpath = f"{path} / {item}"
                detect_unused_keywords(
                    refDict=refEl, compareDict=compareEl, path=newpath
                )


def check_keys(case_dict: dict, case_name: str):
    # check if all basic elements exist
    check_list = [
        "expressions",
        "locations",
        "fluid_properties",
        "setup",
        "solution",
        "results",
    ]
    for check_item in check_list:
        if case_dict.get(check_item) is None:
            logger.warning(
                f"No key '{check_item}' found in case '{case_name}' ... "
                f"creating empty key in case-dict to avoid errors"
            )
            case_dict[check_item] = {}
