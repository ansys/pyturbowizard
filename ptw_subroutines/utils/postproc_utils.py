import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Logger
from ptw_subroutines.utils import ptw_logger

logger = ptw_logger.getLogger()

def calcCov(reportOut, window_size=50):
    try:
        import pandas as pd
    except ImportError as e:
        logger.info(f"ImportError! Could not import lib: {str(e)}")
        logger.info(f"Skipping Function 'calcCov'!")
        return

    mp_df = pd.read_csv(reportOut, skiprows=2, delim_whitespace=True)
    mp_df.columns = mp_df.columns.str.strip('()"')

    # Subtract the first entry in the 'Iteration' column from all other entries
    mp_df["Iteration"] = mp_df["Iteration"] - mp_df["Iteration"].iloc[0]

    # Initialize lists to store mean and COV values
    mean_values = []
    cov_values = []
    
    # calculate the Coefficient of Variation over the window size
    cov_df = mp_df.copy()
    cov_df.iloc[:, 1:] = (
        mp_df.iloc[:, 1:].rolling(window=window_size).std()
        / mp_df.iloc[:, 1:].rolling(window=window_size).mean()
    )

    mean_values = mp_df.iloc[:, 1:].rolling(window=window_size).mean().iloc[-1]
    cov_values = cov_df.iloc[-1]

    formatted_report_df = pd.DataFrame(
        {mp_df.columns[0]: [mp_df[mp_df.columns[0]].iloc[-1]]}, index=[0]
    )  # format the headers of the dataframe

    # Add mean values to the DataFrame
    for column in mp_df.columns[1:]:
        col_name_mean = column
        formatted_report_df[col_name_mean] = mean_values[column]

    # Add COV values to the DataFrame with modified column headers
    for column in mp_df.columns[1:]:
        col_name_cov = column + "-cov"
        formatted_report_df[col_name_cov] = cov_values[column]

    return formatted_report_df, cov_df, mp_df


def getStudyReports(pathtostudy):
    try:
        import pandas as pd
    except ImportError as e:
        logger.info(f"ImportError! Could not import lib: {str(e)}")
        logger.info(f"Skipping 'getStudyReports' function!")
        return

    # Filter the Design Points Subdirectories in the study folder
    subdirectories = [
        name
        for name in os.listdir(pathtostudy)
        if os.path.isdir(os.path.join(pathtostudy, name))
    ]

    # Initialize the lists to store result DataFrames
    repot_df = []  # List to store report_table DataFrames
    cov_df_list = []  # List to store cov_df DataFrames
    mp_df_list = []  # List to store mp_df DataFrames
    residual_df_list = []  # List to store residual_df DataFrames

    for dpname in subdirectories:
        folder_path = os.path.join(pathtostudy, dpname)

        # Check if the folder_path contains a .out file
        out_files = [file for file in os.listdir(folder_path) if file.endswith(".out")]
        # Check if any .out file exists in the folder_path
        if out_files:
            # Take the first .out file as the csv_file_path
            report_file_path = os.path.join(folder_path, out_files[0])
            report_table, cov_df, mp_df = calcCov(report_file_path)
            report_table.insert(0, "Design Point", dpname)
        else:
            continue

        # Check if the file 'Auto-generated-residuals-data-static.csv' exists in the folder
        csv_file_path = os.path.join(
            folder_path, "Auto-generated-residuals-data-static.csv"
        )
        if os.path.exists(csv_file_path):
            # If the file exists, read it into a pandas DataFrame
            residual_df = pd.read_csv(csv_file_path)
        else:
            continue

        # Append the DataFrames to their respective lists
        repot_df.append(report_table)
        cov_df_list.append(cov_df)
        mp_df_list.append(mp_df)
        residual_df_list.append(residual_df)

    # Concatenate the list of designpoints into a single DataFrame
    result_df = pd.DataFrame
    if len(repot_df) > 0:
        result_df = pd.concat(repot_df, ignore_index=True)

    # Return dataframes of operating map, residuals
    return result_df, cov_df_list, residual_df_list, mp_df_list



def plot_figure(x_values, y_values, x_label, y_label, colors, criterion):

    # Create the figure and axis
    fig, ax = plt.subplots()

    if (len(x_values) > 0) and (len(y_values) > 0):
        ax.set_xlim([x_values.min() * 0.95, x_values.max() * 1.05])
        ax.set_ylim([y_values.min() * 0.95, y_values.max() * 1.05])
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