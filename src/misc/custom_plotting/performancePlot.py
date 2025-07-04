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
Performance Plot Module

This module provides functionality for generating performance plots in the PyTurboWizard
application.
"""

import json
import sys

import matplotlib.pyplot as plt
import pandas as pd


def plot_csv_data(
    csv_legend_pairs,
    x_column,
    x_label,
    y_column,
    y_label,
    max_iterations=None,
    filename=None,
):
    """Plot data from multiple CSV files with specified x and y columns."""
    # Read CSV files and store data in a dictionary
    data_dict = {}
    for csv_file, label in csv_legend_pairs:
        data = pd.read_csv(csv_file, delimiter=",")
        data_dict[label] = data

    # Plotting Massflow vs Iteration for all CSV files
    plt.figure(figsize=(8, 6))
    for label, data in data_dict.items():
        plt.scatter(data[x_column], data[y_column], label=label)

    if max_iterations is not None:
        plt.axhline(y=max_iterations, color="g", linestyle="--", label="Max Iterations")

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
        "prev DP": "./hannover/plot_table_Hannover_1p5stage_SST.csv",
        "base DP": "./hannover/plot_table_Hannover_1p5stage_basedp.csv",
        "init Hybrid": "./hannover/plot_table_Hannover_1p5stage_hybrid.csv"
    },
    "x_column": "rep-mp-in-massflow-360",
    "y_column": "wallclock_time",
    "x_label": "inlet mass flow [kg/s]",
    "y_label": "Simulation Wall Clock Time [s]",
    "filename": "./hannover/performance_init.svg",
    "horizontal_line": None
}
"""

# Check if a JSON file path is provided as a command-line argument
if len(sys.argv) < 2:
    print("Usage: performancePlot.py <path_to_json_file.json>")
    sys.exit(1)


# Read the JSON input from the provided file
json_file_path = sys.argv[1]
with open(json_file_path, "r") as json_file:
    input_data = json.load(json_file)


plot_csv_data(
    csv_legend_pairs=input_data["csv_legend_pairs"],
    x_column=input_data["x_column"],
    x_label=input_data["x_label"],
    y_column=input_data["y_column"],
    y_label=input_data["y_label"],
    max_iterations=input_data.get("horizontal_line", None),
    filename=input_data["filename"],
)
