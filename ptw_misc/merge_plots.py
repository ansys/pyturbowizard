import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import matplotlib.colors as mcolors

def mergeStudyPlots(csv_legend_pairs, separate_plots=False, svg_filename=None):
    color_map = {'good': 'green', 'ok': 'orange', 'poor': 'red'}

    # Create a modified colormap with black replacing green, removing yellow/red
    modified_colormap = plt.cm.tab10
    colors = list(modified_colormap.colors)
    colors[2] = (0, 0, 0, 1)  # Replace green with black
    modified_colors = [color for i, color in enumerate(colors) if i not in [1, 3]]
    colormap = mcolors.ListedColormap(modified_colors)

    if separate_plots:
        # Initialize min/max values for both x and y axes
        x_min = y_min_pt = y_min_isen = float('inf')
        x_max = y_max_pt = y_max_isen = float('-inf')

        for csv_file, legend_label in csv_legend_pairs:
            data = pd.read_csv(csv_file)
            x_data = data["massflow"].values
            y_data_pt = data["pt_ratio"].values
            y_data_isen = data["isen_eff"].values

            # Update min/max values
            x_min = min(x_min, min(x_data))
            x_max = max(x_max, max(x_data))

            fig, axs = plt.subplots(1, 2, figsize=(15, 5))

            legend_colors = [
                mpatches.Patch(color='green', label='CoV < 1e-4'),
                mpatches.Patch(color='orange', label='CoV < 5e-4'),
                mpatches.Patch(color='red', label='CoV > 5e-4')
            ]
            legend_handles = legend_colors.copy()

            colors = data['convergence'].map(color_map)
            color = colormap(0)  # Use the first color for each plot


            axs[0].plot(x_data, y_data_pt, linestyle="-", color=color, label=legend_label)
            axs[0].scatter(x_data, y_data_pt, c=colors,zorder=2)
            

            legend_handles.append(Line2D([0], [0], linestyle='-', color=color, label=legend_label))

            axs[0].grid()
            axs[0].set_xlabel('inlet mass flow rate [kg/s]')
            axs[0].set_ylabel('total pressure ratio [-]')
            axs[0].set_xlim(0.99*x_min, 1.01*x_max)
            axs[0].set_ylim(0.99*y_min_pt, 1.01*y_max_pt)


            fig.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1, 1))
            plt.tight_layout()

            if svg_filename:
                plot_svg_filename = svg_filename.replace('.svg', f'_{legend_label.replace(" ", "_")}.svg')
                plt.savefig(plot_svg_filename, format='svg', bbox_inches='tight')
                print(f"Plot saved as {plot_svg_filename}")
            else:
                plt.show()
    else:
        fig, axs = plt.subplots(1, 2, figsize=(15, 5))

        legend_colors = [
                mpatches.Patch(color='green', label='CoV < 1e-4'),
                mpatches.Patch(color='orange', label='CoV < 5e-4'),
                mpatches.Patch(color='red', label='CoV > 5e-4')
        ]
        legend_handles = legend_colors.copy()

        for i, (csv_file, legend_label) in enumerate(csv_legend_pairs):
            data = pd.read_csv(csv_file)
            colors = data['convergence'].map(color_map)
            color = colormap(i)  # Use the odd indices for line colors


            axs[0].plot(data["massflow"].values, data["pt_ratio"].values, linestyle="-", color=color, label=legend_label)
            axs[0].scatter(data["massflow"].values, data["pt_ratio"].values, c=colors,zorder=2)       

            legend_handles.append(Line2D([0], [0], linestyle='-', color=color, label=legend_label))

        axs[0].grid()
        axs[0].set_xlabel('inlet mass flow rate [kg/s]')
        axs[0].set_ylabel('total pressure ratio [-]')

        fig.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1, 1))
        plt.tight_layout()

        if svg_filename:
            plt.savefig(svg_filename, format='svg', bbox_inches='tight')
            print(f"Plot saved as {svg_filename}")
        else:
            plt.show()