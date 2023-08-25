import pandas as pd
import matplotlib.pyplot as plt
import json
import sys
def plot_csv_data(csv_file_labels, x_column,x_label, y_column, y_label, max_iterations=None, filename=None):
    # Read CSV files and store data in a dictionary
    data_dict = {}
    for csv_file, label in csv_file_labels:
        data = pd.read_csv(csv_file, delimiter=',')
        data_dict[label] = data
    
    # Plotting Massflow vs Iteration for all CSV files
    plt.figure(figsize=(8, 6))
    for label, data in data_dict.items():
        plt.scatter(data[x_column], data[y_column], label=label)

    if max_iterations is not None:
        plt.axhline(y=max_iterations, color='g', linestyle='--', label='Max Iterations')

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.legend()
    plt.ylim(bottom=0)
    plt.grid(True)

    if filename:
        plt.savefig(filename)
    else:
        plt.show()


"""
# Example usage
input_data = {
    "csv_legend_pairs": {
        "GG-NB": {
            "./Catana/plot_table_Catana_SST.csv"
            },
        "LSQ-CB": {"./Catana/plot_table_Catana_LSQ.csv"
                   }
    },
    "x_column": "rep-mp-in-massflow-360",
    "y_column": "wallclock_time",
    "x_label": "inlet mass flow [kg/s]",
    "y_label": "Simulation Wall Clock Time [s]",
    "filename": "./Catana/performance_numerics.svg",
    "horizontal_line": None
}
"""

# Check if a JSON file path is provided as a command-line argument
if len(sys.argv) < 2:
    print("Usage: performancePlot.py <path_to_json_file.json>")
    sys.exit(1)


# Read the JSON input from the provided file
json_file_path = sys.argv[1]
with open(json_file_path, 'r') as json_file:
    input_data = json.load(json_file)


plot_csv_data(csv_legend_pairs=input_data["csv_legend_pairs"], 
              x_column=input_data["x_column"],
              x_label=input_data["x_label"],
                y_column=input_data["y_column"], 
                y_label=input_data["y_label"],
                max_iterations=input_data.get("horizontal_line",None), 
                filename=input_data["filename"])