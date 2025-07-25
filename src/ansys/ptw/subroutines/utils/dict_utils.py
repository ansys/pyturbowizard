# Copyright (C) 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""
Dictionary Utilities Module

This module provides utility functions for working with dictionaries in the PyTurboWizard
application.
"""

import copy
import json
import os

# Load Script Modules
from src.ansys.ptw.subroutines.utils import ptw_logger

logger = ptw_logger.get_logger()


def get_funcname_and_upd_funcdict(
    parentDict: dict, functionDict: dict, funcDictName: str, defaultName: str
):
    """
    Retrieve a function name from a dictionary and update the dictionary
    with a default value if necessary.

    Parameters:
        parentDict (dict): The parent dictionary containing function-related data.
        functionDict (dict): The dictionary to retrieve and update the function name.
        funcDictName (str): The key to look for in the function dictionary.
        defaultName (str): The default function name to use if the key is not found.

    Returns:
        str: The retrieved or default function name.
    """
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


def merge_function_dicts(caseDict: dict, glfunctionDict: dict):
    """merge function dictionaries"""
    # Merge function dicts
    caseFunctionDict = caseDict.get("functions")
    if glfunctionDict is not None and caseFunctionDict is not None:
        helpDict = glfunctionDict.copy()
        helpDict.update(caseFunctionDict)
        caseFunctionDict = helpDict
    elif caseFunctionDict is None:
        caseFunctionDict = glfunctionDict
    return caseFunctionDict


def merge_data_with_ref_dict(caseDict: dict, allCasesDict: dict):
    """merge data with reference dictionary"""
    refCaseName = caseDict.get("refCase")
    refDict = allCasesDict.get(refCaseName)
    if refDict is None:
        logger.info(
            f"Specified Reference Case {refCaseName} not found in Config-File! "
            f"--> Skipping CopyFunction..."
        )
        return caseDict
    helpCaseDict = copy.deepcopy(refDict)
    helpCaseDict.update(caseDict)
    caseDict.update(helpCaseDict)
    return


def get_material_from_lib(caseDict: dict, scriptPath: str):
    """get material from ptw-library"""
    if isinstance(caseDict.get("fluid_properties"), str):
        materialStr = caseDict.get("fluid_properties")
        materialFileName = os.path.join(scriptPath, "misc", "material_lib.json")
        materialFile = open(materialFileName, "r")
        materialDict = json.load(materialFile)
        materialDict = materialDict.get(materialStr)
        if materialDict is not None:
            caseDict["fluid_properties"] = materialDict
        else:
            raise Exception(
                f"Specified material '{materialStr}' in config-file not "
                f"found in material-lib: {materialFileName}"
            )
    return


def detect_unused_keywords(refDict: dict, compareDict: dict, path="root"):
    """detect unused keywords"""
    for item in compareDict:
        if item not in refDict:
            logger.warning(
                f"Element found in Config-File that is not known or used! "
                f"Check keyword: '{item}' in '{path}'"
            )
        else:
            refEl = refDict.get(item)
            compareEl = compareDict.get(item)
            if isinstance(refEl, dict) and isinstance(compareEl, dict):
                newpath = f"{path} / {item}"
                detect_unused_keywords(refDict=refEl, compareDict=compareEl, path=newpath)


def check_keys(case_dict: dict, case_name: str):
    """check if all basic elements exist"""
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
