import os.path
import json
import matplotlib.pyplot as plt

def write_expression_file(data: dict, script_dir: str, working_dir: str):
    fileName = data.get("expressionFilename")
    # if nothing is set for "expressionFilename" a default value ("expressions.tsv") is set and dict will be updated
    if fileName is None or fileName == "":
        fileName = "expressions.tsv"
        data["expressionFilename"] = fileName
    fileName = os.path.join(working_dir, fileName)
    with open(fileName, "w") as sf:
        expressionTemplatePath = os.path.join(
            script_dir, "tts_templates", data["expressionTemplate"]
        )
        with open(expressionTemplatePath, "r") as templateFile:
            tempData = templateFile.read()
            templateFile.close()
        helperDict = data["locations"]
        expressionEl = data.get("expressions")
        helperDict.update(expressionEl)
        # add rotation axis
        helperDict["rotation_axis_direction"] = tuple(
            data.get("rotation_axis_direction", [0.0, 0.0, 1.0])
        )
        helperDict["rotation_axis_origin"] = tuple(
            data.get("rotation_axis_origin", [0.0, 0.0, 0.0])
        )
        # add isentropic efficiency definition
        helperDict["isentropic_efficiency_ratio"] = data.get("isentropic_efficiency_ratio", 'TotalToTotal')
>>>>>>>>> Temporary merge branch 2
        tempData = cleanupInputExpressions(availableKeyEl=helperDict, fileData=tempData)
        for line in tempData.splitlines():
            try:
                sf.write(line.format(**helperDict))
                sf.write("\n")
            except KeyError as e:
                print(f"Expression not found in ConfigFile: {str(e)}")

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
    expDict = solver.setup.named_expressions()
    for expName in expDict:
        exp = expDict[expName]
        if exp.get("input_parameter"):
            expValue = solver.setup.named_expressions.get(expName).get_value()
            if type(expValue) is not float:
                print(
                    f"'{expName}' seems not to be valid: '{expValue}' \n "
                    f"Removing definition as Input Parameter..."
                )
                solver.setup.named_expressions.get(expName).input_parameter.set_state(
                    False
                )


def get_free_filename(dirname, base_filename):
    base_name, ext_name = os.path.splitext(base_filename)
    filename = base_filename
    filepath = os.path.join(dirname, filename)
    counter = 1
    while os.path.isfile(filepath):
        filename = base_name + "_" + str(counter) + ext_name
        filepath = os.path.join(dirname, filename)
        counter += 1
    return filename


def plot_operating_map(design_point_table):
    try:
        import pandas as pd
    except ImportError as e:
        print(f"ImportError! Could not import lib: {str(e)}")
        print(f"Skipping 'plotOperatingMap' function!")
        return

    # extract unit row and drop from table
    design_point_table = design_point_table.drop(0, axis=0)

    # filter out failed design points
    design_point_table = design_point_table.loc[
        design_point_table["Status"] != "Failed"
    ]

    # Filter out converged cases
    MP_MassFlow_conv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Converged", "MP_IN_MassFlow"
        ],
        errors="coerce",
    )
    MP_PRt_conv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Converged", "MP_PRt"
        ],
        errors="coerce",
    )
    MP_Isentropic_Efficiency_conv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Converged",
            "MP_Isentropic_Efficiency",
        ],
        errors="coerce",
    )

    # Filter out non converged cases
    MP_MassFlow_nconv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Not Converged", "MP_IN_MassFlow"
        ],
        errors="coerce",
    )
    MP_PRt_nconv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Not Converged", "MP_PRt"
        ],
        errors="coerce",
    )
    MP_Isentropic_Efficiency_nconv = pd.to_numeric(
        design_point_table.loc[
            design_point_table["Status"] == "Updated : Not Converged",
            "MP_Isentropic_Efficiency",
        ],
        errors="coerce",
    )

    # Merge
    MP_MassFlow = pd.concat([MP_MassFlow_conv, MP_MassFlow_nconv])
    MP_PRt = pd.concat([MP_PRt_conv, MP_PRt_nconv])
    MP_Isentropic_Efficiency = pd.concat(
        [MP_Isentropic_Efficiency_conv, MP_Isentropic_Efficiency_nconv]
    )

    # generate plots
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    fig.suptitle("Operating Point Map")
    if (
        (len(MP_PRt) > 0)
        and (len(MP_MassFlow) > 0)
        and (len(MP_Isentropic_Efficiency) > 0)
    ):
        # Total Pressure Ratio
        axs[0].set_xlim([MP_MassFlow.min() * 0.99, MP_MassFlow.max() * 1.01])
        axs[0].set_ylim([MP_PRt.min() * 0.99, MP_PRt.max() * 1.01])
        axs[0].grid()
        axs[0].set_xlabel("inlet mass flow rate [kg/s]")
        axs[0].set_ylabel("total pressure ratio [-]")
        axs[0].scatter(MP_MassFlow_conv, MP_PRt_conv, marker="^")
        axs[0].scatter(MP_MassFlow_nconv, MP_PRt_nconv, marker="x")

        # Isentropic Efficiency
        axs[1].set_xlim([MP_MassFlow.min() * 0.99, MP_MassFlow.max() * 1.01])
        axs[1].set_ylim(
            [
                MP_Isentropic_Efficiency.min() * 0.99,
                MP_Isentropic_Efficiency.max() * 1.01,
            ]
        )
        axs[1].grid()
        axs[1].set_xlabel("inlet mass flow rate [kg/s]")
        axs[1].set_ylabel("isentropic efficiency [-]")
        axs[1].scatter(MP_MassFlow_conv, MP_Isentropic_Efficiency_conv, marker="^")
        axs[1].scatter(MP_MassFlow_nconv, MP_Isentropic_Efficiency_nconv, marker="x")
        fig.legend(["Converged", "Not Converged"])

    return fig


def get_funcname_and_upd_funcdict(
    parentDict: dict, functionDict: dict, funcElName: str, defaultName: str
):
    functionName = None
    if functionDict is not None:
        functionName = functionDict.get(funcElName)
    # Set Default if not already set
    if functionName is None:
        functionName = defaultName
        # If the element is not existing, create a new one, otherwise update the existing
        if functionDict is None:
            functionDict = {"functions": {funcElName: functionName}}
        else:
            functionDict.update({funcElName: functionName})

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
        print(
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
        materialFileName = os.path.join(scriptPath, "tts_misc", "material_lib.json")
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

def calcCov(reportOut):
    try:
        import pandas as pd
    except ImportError as e:
        print(f"ImportError! Could not import lib: {str(e)}")
        print(f"Skipping Function 'calcCov'!")
        return

    data = pd.read_csv(reportOut, skiprows=2, delim_whitespace=True)
    data.columns = data.columns.str.strip('()"')

    # Initialize lists to store mean and COV values
    mean_values = []
    cov_values = []

    # Calculate mean and COV for each column
    for column in data.columns[1:]:
        last_50_rows = data[column].tail(50)  # Select the last 50 rows of the column
        std = last_50_rows.std()
        mean = last_50_rows.mean()  # Calculate mean
        cov = std / mean  # Calculate COV
        mean_values.append(mean)
        cov_values.append(cov)

    # Create a DataFrame with mean and COV values
    result_dict = {}
    result_dict[data.columns[0]] = data.iloc[
        -1, 0
    ]  # Add first column header and last row value

    # format dataframe
    for i, column in enumerate(data.columns[1:]):
        result_dict[column] = mean_values[i]

    for i, column in enumerate(data.columns[1:]):
        result_dict[column + "-cov"] = cov_values[i]

    result_df = pd.DataFrame(result_dict, index=[0])

    return result_df