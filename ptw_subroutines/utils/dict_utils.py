import os
import json

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
            f"Specified Reference Case {refCaseName} not found in Config-File!\nSkipping CopyFunction..."
        )
        return caseDict
    helpCaseDict = refDict.copy()
    helpCaseDict.update(caseDict)
    caseDict.update(helpCaseDict)
    return


def get_material_from_lib(caseDict: dict, scriptPath: str):
    if type(caseDict.get("fluid_properties")) is str:
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
