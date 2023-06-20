import os.path
import matplotlib.pyplot as plt
import pandas as pd


def writeExpressionFile(data: dict, script_dir: str, working_dir: str):
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
        #add rotation axis
        helperDict["rotation_axis_direction"] = tuple(data.get("rotation_axis_direction", [0., 0., 1.]))
        helperDict["rotation_axis_origin"] = tuple(data.get("rotation_axis_origin", [0., 0., 0.]))
        tempData = cleanupInputExpressions(availableKeyEl=helperDict, fileData=tempData)
        for line in tempData.splitlines():
            try:
                sf.write(line.format(**helperDict))
                sf.write("\n")
            except KeyError as e:
                print(f"Expression not found in ConfigFile: {str(e)}")

    return


def cleanupInputExpressions(availableKeyEl: dict, fileData: str):
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

        elif 'Torque' in line:
            if availableKeyEl.get("bz_walls_torque") is not None:
                cleanfiledata = cleanfiledata + "\n" + line
            else:
                continue

        elif 'Euler' in line:
            if (availableKeyEl.get("bz_ep1_Euler") and availableKeyEl.get("bz_ep2_Euler")) is not None:
                cleanfiledata = cleanfiledata + "\n" + line
            else:
                continue
        else:
            cleanfiledata = cleanfiledata + "\n" + line

    return cleanfiledata


def plotOperatingMap(design_point_table):
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
    parentEl: dict, functionEl: dict, funcElName: str, defaultName: str
):
    functionName = None
    if functionEl is not None:
        functionName = functionEl.get(funcElName)
    # Set Default if not already set
    if functionName is None:
        functionName = defaultName
        # If the element is not existing, create a new one, otherwise update the existing
        if functionEl is None:
            functionEl = {"functions": {funcElName: functionName}}
        else:
            functionEl.update({funcElName: functionName})

    # Update Parent Element
    parentEl.update({"functions": functionEl})
    return functionName


def merge_functionEls(caseEl: dict, glfunctionEl: dict):
    # Merge function dicts
    caseFunctionEl = caseEl.get("functions")
    if glfunctionEl is not None and caseFunctionEl is not None:
        helpDict = glfunctionEl.copy()
        helpDict.update(caseFunctionEl)
        caseFunctionEl = helpDict
    elif caseFunctionEl is None:
        caseFunctionEl = glfunctionEl
    return caseFunctionEl


def merge_data_with_refEl(caseEl: dict, allCasesEl: dict):
    refCaseName = caseEl.get("refCase")
    refEl = allCasesEl.get(refCaseName)
    if refEl is None:
        print(
            f"Specified Reference Case {refCaseName} not found in Config-File!\nSkipping CopyFunction..."
        )
        return caseEl
    helpCaseEl = refEl.copy()
    helpCaseEl.update(caseEl)
    caseEl.update(helpCaseEl)
    return

def CreateReportTable(reportFileName,trnFileName,caseFilename):

    # get report file
    # read in table of report-mp and get last row
    try:
        out_table = pd.read_csv(reportFileName, header=2, delimiter=" ")
        first_column = out_table.columns[0]
        last_column = out_table.columns[-1]

        # Remove brackets from first and last column names
        modified_columns = {
            first_column: first_column.replace('(', '').replace(')', '').replace('"',''),
            last_column: last_column.replace('(', '').replace(')', '')
        }
        out_table = out_table.rename(columns = modified_columns)
        report_values = out_table.iloc[[-1]]


        # Read in transcript file
        with open(trnFileName, "r") as file:
         transcript = file.read()

        table_started = False
        lines = transcript.split("\n")
        wall_clock_per_it = 0
        wall_clock_tot = 0
        nodes = 0
        filtered_values = []
        filtered_headers = []

        for line in lines:
            if "Average wall-clock time per iteration" in line:
                wall_clock_per_it = line.split(":")[1].strip()
                print("Average Wall Clock Time per Iteration:", wall_clock_per_it)
            elif "Total wall-clock time" in line:
                wall_clock_tot = line.split(":")[1].strip()
                print("Total Wall Clock Time:", wall_clock_tot)
            elif "iter" in line:
                headers = line.split()
                filtered_headers = headers[1:-1]
                table_started = True
            elif "Done." in line and table_started:
                # "Done." line encountered, indicating the end of the iteration table
                print("Done")
                table_started = False
            elif table_started:
                values = line.split()
                if len(values[1:-2]) == len(filtered_headers):
                    filtered_values = values[1:-2]

        for i in range(len(filtered_headers)):
            if filtered_headers[i].startswith('rep-'):
                filtered_headers[i] += '-cov'
            else:
                filtered_headers[i] = 'res-' + filtered_headers[i]

        filtered_values = [float(val) for val in filtered_values]
        res_columns = dict(zip(filtered_headers,filtered_values))


        ## write report table
        report_table = pd.DataFrame()
        report_table = pd.concat([report_table, report_values], axis=1)
        report_table = report_table.assign(**res_columns)
        report_table["Total Wall Clock Time"] = wall_clock_tot
        report_table["Ave Wall Clock Time per It"] = wall_clock_per_it
        report_table["Compute Nodes"] = nodes
        report_table.insert(0,"Case Name", caseFilename)

        reportTableFileName =  caseFilename + '_reporttable.csv'
        print("Writing Report Table to: "+ reportTableFileName)
        report_table.to_csv(reportTableFileName,index=None)
    except: print("Report File not found. Skipping Report Table.")
    return

def spanPlots(data,solver):
    # Create spanwise surfaces
    spansSurf = data["results"].get("span_plot_height")
    contVars = data["results"].get("span_plot_var")
    for spanVal in spansSurf:
        spanName = f"span-{spanVal}"
        print("Creating spanwise ISO-surface: " + spanName)
        solver.results.surfaces.iso_surface[spanName]= {}
        zones = solver.results.surfaces.iso_surface[spanName].zone.get_attr("allowed-values")
        solver.results.surfaces.iso_surface[spanName](
            field="spanwise-coordinate",
            zone = zones,
            iso_value = [spanVal]
        )

        for contVar in contVars:
            contName = spanName + "-" + contVar
            print("Creating spanwise contour-plot: " + contName)
            solver.results.graphics.contour[contName] = {}
            solver.results.graphics.contour[contName](
                field = contVar,
                contour_lines = True
            )
            solver.results.graphics.contour[contName].range_option.auto_range_on.global_range = False

