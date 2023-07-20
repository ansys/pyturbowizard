import os.path
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def write_expression_file(data: dict, script_dir: str, working_dir: str):
    fileName = data.get("expressionFilename")
    # if nothing is set for "expressionFilename" a default value ("expressions.tsv") is set and dict will be updated
    if fileName is None or fileName == "":
        fileName = "expressions.tsv"
        data["expressionFilename"] = fileName
    fileName = os.path.join(working_dir, fileName)
    with open(fileName, "w") as sf:
        expressionTemplatePath = os.path.join(
            script_dir, "ptw_templates", data["expressionTemplate"]
        )
        with open(expressionTemplatePath, "r") as templateFile:
            tempData = templateFile.read()
            templateFile.close()
        helperDict = data["locations"]
        expressionEl = data.get("expressions")
        helperDict.update(expressionEl)
        # add rotation axis
        helperDict["rotation_axis_direction"] = tuple(
            data.setdefault("rotation_axis_direction", [0.0, 0.0, 1.0])
        )
        helperDict["rotation_axis_origin"] = tuple(
            data.setdefault("rotation_axis_origin", [0.0, 0.0, 0.0])
        )
        # add isentropic efficiency definition
        helperDict["isentropic_efficiency_ratio"] = data.setdefault(
            "isentropic_efficiency_ratio", "TotalToTotal"
        )
        tempData = cleanup_input_expressions(
            availableKeyEl=helperDict, fileData=tempData
        )
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
    for expName in solver.setup.named_expressions():
        exp = solver.setup.named_expressions.get(expName)
        if expName.startswith("BC_"):
            expValue = exp.get_value()
            if type(expValue) is not float:
                print(
                    f"'{expName}' seems not to be valid: '{expValue}' \n "
                    f"Removing definition as Input Parameter..."
                )
                exp.set_state({"input_parameter": False})
    return


def check_output_parameter_expressions(solutionDict: dict, solver):
    reportlist = solutionDict.get("reportlist")
    if reportlist is None:
        return

    for expName in solver.setup.named_expressions():
        exp = solver.setup.named_expressions.get(expName)
        if expName in reportlist:
            print(
                f"Expression '{expName}' found in Config-File: 'Case/Solution/reportlist'"
                f"Setting expression '{expName}' as output-parameter"
            )
            exp.set_state({"output_parameter": True})
    return


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


def plot_figure(x_values, y_values, x_label, y_label, colors, criterion):
    try:
        import pandas as pd
    except ImportError as e:
        print(f"ImportError! Could not import lib: {str(e)}")
        print(f"Skipping 'plotOperatingMap' function!")
        return

    # Create the figure and axis
    fig, ax = plt.subplots()

    if (len(x_values) > 0) and (len(y_values) > 0):
        ax.set_xlim([x_values.min() * 0.99, x_values.max() * 1.01])
        ax.set_ylim([y_values.min() * 0.99, y_values.max() * 1.01])
        ax.grid()
        ax.set_xlabel(x_label)  # Set x-axis label dynamically
        ax.set_ylabel(y_label)  # Set y-axis label as DataFrame column header

        # plot values
        ax.scatter(x_values, y_values, marker="o", c=colors, edgecolor="black")
        ax.plot(x_values, y_values)

        # Create legend handles for color coding
        legend_colors = [
            mpatches.Patch(color="green", label=f'CoV < {"{:.0e}".format(criterion)}'),
            mpatches.Patch(
                color="yellow", label=f'CoV < {"{:.0e}".format(5*criterion)}'
            ),
            mpatches.Patch(color="red", label=f'CoV > {"{:.0e}".format(5*criterion)}'),
        ]
        ax.legend(handles=legend_colors, loc="best")
    return fig


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


def read_journals(data: dict, solver, element_name: str):
    journal_list = data.get(element_name)
    if journal_list is not None and len(journal_list) > 0:
        print(
            f"Reading specified journal files specified in ConfigFile '{element_name}': {journal_list}"
        )
        solver.file.read_journal(file_name_list=journal_list)
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


def getStudyReports(pathtostudy):
    try:
        import pandas as pd
    except ImportError as e:
        print(f"ImportError! Could not import lib: {str(e)}")
        print(f"Skipping 'getStudyReports' function!")
        return

    # Filter and get only the subdirectories within pathtostudy
    subdirectories = [
        name
        for name in os.listdir(pathtostudy)
        if os.path.isdir(os.path.join(pathtostudy, name))
    ]
    result_dfs = []  # List to store result report files
    for dpname in subdirectories:
        folder_path = os.path.join(pathtostudy, dpname)

        # Check if the folder_path contains a .out file
        out_files = [file for file in os.listdir(folder_path) if file.endswith(".out")]

        # Check if any .out file exists in the folder_path
        if out_files:
            # Take the first .out file as the csv_file_path
            report_file_path = os.path.join(folder_path, out_files[0])
            report_table = calcCov(report_file_path)
            result_dfs.append(report_table)

        else:
            continue
    # Concatenate the list of result DataFrames into a single DataFrame
    result_df = pd.DataFrame
    if len(result_dfs) > 0:
        result_df = pd.concat(result_dfs, ignore_index=True)
    return result_df
