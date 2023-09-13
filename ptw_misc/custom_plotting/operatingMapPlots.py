import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors
import json
import sys

def create_operating_map_plots(csv_legend_pairs, svg_filename=None,full_convergence=False):
    if full_convergence:
        color_map = {'converged': 'green','not converged': 'red'}
    else:
        color_map = {'good': 'green', 'ok': 'orange', 'poor': 'red'}

    modified_colormap = plt.cm.tab10
    colors = list(modified_colormap.colors)
    colors[2] = (0, 0, 0, 1)
    modified_colors = [color for i, color in enumerate(colors) if i not in [1, 3]]
    colormap = mcolors.ListedColormap(modified_colors)

    for y_col, y_label in zip(input_data['y_data'], input_data['y_labels']):
        fig, axs = plt.subplots(1, 1, figsize=(10, 6))
        cov_criterion = input_data['cov_criterion']
        legend_handles = []
        if full_convergence:
            legend_colors = [
                mpatches.Patch(color='green', label=f'converged'),
                mpatches.Patch(color='red', label=f'not converged')
            ]
        else:
            legend_colors = [
                mpatches.Patch(color='green', label=f'CoV < {"{:.0e}".format(cov_criterion)}'),
                mpatches.Patch(color='orange', label=f'CoV < {"{:.0e}".format(5*cov_criterion)}'),
                mpatches.Patch(color='red', label=f'CoV > {"{:.0e}".format(5*cov_criterion)}')
            ]
        legend_handles.extend(legend_colors)

        x_min, x_max = float('inf'), float('-inf')
        y_min, y_max = float('inf'), float('-inf')
        
        for csv_file, legend_label in csv_legend_pairs:
            data = pd.read_csv(csv_file)
            x_col = input_data['x_data'][0]

            if y_col in data.columns:
                x_data = data[x_col]
                y_data = data[y_col]
                cov_col = input_data['cov_data'][input_data['y_data'].index(y_col)]

                # Check if the column represents "rep-mp-isentropic-efficiency"
                if y_col == "rep-mp-isentropic-efficiency":
                    # Apply the inverse operation to values greater than 1 (Used because of FLuent Efficiency bug)
                    y_data = y_data.apply(lambda x: 1 / x if x > 1 else x)

                # Check if full convergence should be plotted (converged/not converged)
                if full_convergence:
                    if cov_col in data.columns:
                        cov_data = data[cov_col]
                        colors = [
                            color_map[convergence] if convergence in color_map else color_map['not converged']
                            for convergence in data['convergence']
                        ]
                        scatter_color = colors
                    else:
                        cov_data = None
                else:
                    # Plot CoV with traffic light notation
                    if cov_col in data.columns:
                        cov_data = data[cov_col]
                        colors = [
                            color_map['good'] if cov < 1.01*cov_criterion else
                            color_map['ok'] if cov < 5 * cov_criterion else
                            color_map['poor']
                            for cov in cov_data
                        ]
                        scatter_color = colors
                    else:
                        cov_data = None

                color = colormap(csv_legend_pairs.index((csv_file, legend_label)))

                axs.plot(x_data, y_data, linestyle="-", color=color, label=legend_label)
                axs.scatter(x_data, y_data, c=scatter_color if cov_data is not None else color, zorder=2, marker='x' if cov_data is None else None)

                x_min = min(x_min, min(x_data))
                x_max = max(x_max, max(x_data))
                y_min = min(y_min, min(y_data))
                y_max = max(y_max, max(y_data))
                
                legend_handles.append(Line2D([0], [0], linestyle='-', color=color, label=legend_label))

        axs.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1, 1))
        plt.tight_layout()

        #axs.set_xlim(0.99 * x_min, 1.01 * x_max)
        #axs.set_ylim(0.99 * y_min, 1.01 * y_max)
        axs.grid()
        axs.set_xlabel(input_data['x_label'][0] if 'x_label' in input_data else x_col)
        axs.set_ylabel(y_label if y_label else y_col)  # Use specified y_label or default to y_col name

        if svg_filename:
            plot_svg_filename = svg_filename.replace('.svg', f'_{y_col.replace(" ", "_")}.svg')
            plt.savefig(plot_svg_filename, format='svg', bbox_inches='tight')
            print(f"Plot saved as {plot_svg_filename}")
        else:
            plt.show()


# Check if a JSON file path is provided as a command-line argument
if len(sys.argv) < 2:
    print("Usage: operatingMapPlots.py <path_to_json_file.json>")
    sys.exit(1)


# Read the JSON input from the provided file
json_file_path = sys.argv[1]
with open(json_file_path, 'r') as json_file:
   input_data = json.load(json_file)

"""
input_data = {
    "filename" : "./plot.svg",
    "cov_criterion": 1e-4,
    "plot_full_convergence": True,
    "x_data": ["rep-mp-in-massflow-360"],
    "y_data": ["rep-mp-prt","rep-mp-isentropic-efficiency"],
    "x_label": ["inlet mass flow [kg/s]"],
    "y_labels": ["Total Pressure Ratio [-]","Isentropic Efficiency [-]"],
    "cov_data": ["rep-mp-prt-cov","rep-mp-isentropic-efficiency-cov"],
    "input_csv_data":{
        "GG-NB":{
            "csv_file": "./Catana/plot_table_Catana_SST.csv"
        },
        "LSQ-CB":{
            "csv_file": "./Catana/plot_table_Catana_LSQ.csv"
        },
        "EXP":{
            "csv_file": "./Catana/plot_table_Catana_exp.csv"
        }
    }
}
"""

# Check if a JSON file path is provided as a command-line argument
if len(sys.argv) < 2:
    print("Usage: operatingMapPlot.py <path_to_json_file.json>")
    sys.exit(1)

# Convert input data into pairs
csv_legend_pairs = [(data['csv_file'], legend_label) for legend_label, data in input_data['input_csv_data'].items()]

# Call the plot function
create_operating_map_plots(csv_legend_pairs, svg_filename=input_data['filename'],full_convergence=input_data["plot_full_convergence"])