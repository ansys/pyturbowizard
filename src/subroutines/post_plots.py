# -*- coding: utf-8 -*-
"""
Script for Post-processing Turbomachinery Cases

@author: dpons/mkaimasi
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os
import numpy as np
import pandas as pd
import re
from src.subroutines.utils import ptw_logger

# get logger
logger = ptw_logger.getLogger()


def Fplot(solver, file_name, work_dir, case_dict=None):

    if case_dict is None:
        import warnings

        warnings.warn(
            "[Fplot] case_dict is None. Empty plotting parameters will be used.",
            UserWarning,
        )
        case_dict = {}

    post_cfg = case_dict.get("post_processing")
    if post_cfg is None:
        logger.warning(
            f"No 'post_processing' element defined for case-dict '{case_dict}'...Skipping function 'Fplot'!"
        )
        return
    ref_cfg = case_dict.get("locations", {})

    def get_loading_data(surf, span=None):
        # Subroutine to extract loading data
        fields = [
            "x-coordinate",
            "pressure",
            "total-pressure",
            "rel-total-pressure",
            "mach-number",
            "rel-mach-number",
            "axial-coordinate",
            "meridional-coordinate",
            "spanwise-coordinate",
            "pitchwise-coordinate",
            "angular-coordinate",
        ]
        if span:
            # Update Span Location
            solver.settings.results.surfaces.iso_surface[surf].iso_values = [span]
        field_data = solver.fields.field_data
        loading_data = dict()
        loading_data["surf"] = surf
        loading_data["pct_span"] = span
        for ff in fields:
            data = field_data.get_scalar_field_data(field_name=ff, surfaces=[surf])
            # loading_data[ff] = [d.scalar_data for d in data]
            loading_data[ff] = data[surf]

        return loading_data

    def plot_loading(data, fields, SaveFig=True, w_dir=None):

        axial_coord = data["axial-coordinate"]
        bx = (axial_coord - np.min(axial_coord)) / (
            np.max(axial_coord) - np.min(axial_coord)
        )  # Axial Chord

        plot_folder = os.path.join(
            w_dir, "Airfoil_Loading_Plots"
        )  # Output Folder for the plots
        if SaveFig and not os.path.exists(plot_folder):
            os.makedirs(plot_folder)

        for field in fields:
            if field == "psopt":
                yvar = data["pressure"] / max(
                    data["total-pressure"]
                )  # Ps/Max(Pt)_along surface
                ylabel = "Ps/Pt"
            elif field == "psopt_r":
                yvar = data["pressure"] / max(
                    data["rel-total-pressure"]
                )  # Ps/Max(Pt)_along surface
                ylabel = "Ps/Pt"
            elif field == "mach-number":
                yvar = data[field]
                ylabel = "Mach Number"
            elif field == "rel-mach-number":
                yvar = data[field]
                ylabel = "Relative Mach Number"
            elif field == "pressure":
                yvar = data[field]
                ylabel = "Static Pressure"
            else:
                yvar = data[field]
                ylabel = field  # fallback label

            fig, ax = plt.subplots()
            ax.scatter(bx, yvar, s=2)
            title = "{af} Loading ({fld}) at {span:.0f}% Span".format(
                af=data["surf"].upper(),
                fld=field.replace("-", " ").title(),
                span=data["pct_span"] * 100,
            )
            ax.set_title(title)
            # ax.set_ylim(0, 1)
            ax.grid(visible=True)
            ax.set_xlabel("% Bx")
            ax.set_ylabel(ylabel)

            if SaveFig:
                filename = title.replace(" ", "_").replace("%", "pct") + ".png"
                fig.savefig(os.path.join(plot_folder, filename), dpi=400)
                plt.close(fig)

    def write_loading_csv(data, filename):
        f = open(filename, "w")

        f.write("## Ansys Fluent Profile\n")
        f.write("##\n")
        f.write("## Generated from Fluent .prof file using\n")
        f.write("## Python transfer utility\n")
        f.write("##\n")
        f.write("\n")

        f.write("[Name]\n")
        f.write(data["surf"] + "\n\n")

        f.write("[Pct Span]\n")
        f.write(str(data["pct_span"]) + "\n\n")

        field_names = list(data.keys())[2:]
        f.write("[Data]\n")
        f.write(",".join(field_names))
        f.write("\n")
        for i in range(0, len(data[field_names[0]])):
            f.write(",".join([r"{:1.10f}".format(data[k][i]) for k in field_names]))
            f.write("\n")
        f.write('#-- End of profile --"\n\n')
        f.close()

    def plot_row_radial_profile(prof, SaveFig=False, fig_dir="Radial_Profile_Figures"):
        if SaveFig and not os.path.exists(fig_dir):
            os.makedirs(fig_dir)
        for af in list(prof.keys()):
            for zone in list(prof[af].keys()):
                data = prof[af][zone]
                for vv in list(prof[af][zone].keys())[1:]:
                    fig, ax = plt.subplots()

                    ax.plot(data["Hub to Shroud Distance"], data[vv], color="r")
                    clean_af = af.split("-", 1)[1].replace("-", "")
                    title = (
                        clean_af.title()
                        + " "
                        + zone.title()
                        + " "
                        + vv.title().replace("-", " ")
                        + " Radial Profile"
                    )
                    ax.set_title(title)
                    ax.set_xlim(0, 1.0)
                    ax.grid(visible=True)
                    ax.set_xlabel("% Span")
                    ax.set_ylabel(vv.title().replace("-", " "))
                    if SaveFig:
                        fig_path = os.path.join(
                            fig_dir, title.replace(" ", "_") + ".png"
                        )
                        fig.savefig(fig_path, dpi=400)
                        plt.close(fig)

    def Read_Fluent_xy(file):
        with open(file, "r") as f:
            lines = f.readlines()
        Title = re.findall('"([^"]*)"', lines[0])[0]
        Labels = re.findall('"([^"]*)"', lines[1])
        var = {key: [] for key in Labels}
        data = lines[4:-1]

        for d in data:
            vals = d.strip().split()
            for i in range(0, len(Labels)):

                var[Labels[i]].append(float(vals[i]))

        return var

    def parse_mass_avg_report(filepath):
        with open(filepath, "r") as f:
            lines = f.readlines()

        data = {}
        current_var = None
        for i, line in enumerate(lines):
            # Find the variable name
            if "Mass-Weighted Average" in line or "Mass Flow Rate" in line:
                current_var = lines[i + 1].strip()
                data[current_var] = {}
                continue

            # Skip lines with just dashes or headers
            if set(line.strip()) <= {"-", " "} or "Net" in line:
                continue

            # Match surface-value lines
            match = re.match(r"\s*(.+?)\s+([-\d\.Ee+]+)\s*$", line)
            if match and current_var:
                surface = match.group(1).strip()
                try:
                    value = float(match.group(2))
                    data[current_var][surface] = value
                except ValueError:
                    continue  # ignore bad values

        df = pd.DataFrame.from_dict(data, orient="index")
        return df

    #####################
    #                   #
    #  AIRFOIL LOADING  #
    #                   #
    #####################

    def airfoil_loading_analysis(solver, work_dir, case_dict):

        if not case_dict.get("airfoil_zones") or not case_dict.get("loading_span_cuts"):
            logger.warning(
                "[airfoil_loading_analysis] No airfoil zones or span cuts defined — skipping airfoil loading plot creation."
            )
            return  # Graceful exit

        af_surf = case_dict["airfoil_zones"]
        pct_spans = case_dict["loading_span_cuts"]
        plot_types = case_dict.get("plot_types", [])

        wall_list = [
            s
            for s in list(
                solver.settings.setup.boundary_conditions.wall.get_state().keys()
            )
            if "bld" in s
        ]
        field = "spanwise-coordinate"

        for af in af_surf:
            clip_name = af.replace("-", "_") + "_clip"
            for pct_span in pct_spans:
                if clip_name not in list(
                    solver.settings.results.surfaces.iso_surface.keys()
                ):
                    solver.settings.results.surfaces.iso_surface.create(clip_name)

                solver.settings.results.surfaces.iso_surface[clip_name] = {
                    "surfaces": wall_list,
                    "field": field,
                    "iso_values": [pct_span],
                    "zones": af,
                }

                loading_data = get_loading_data(clip_name, span=pct_span)
                plot_loading(loading_data, plot_types, SaveFig=True, w_dir=work_dir)

                output_filename = (
                    f"{clip_name.title()}_{int(pct_span * 100)}Pct_Span_loading.csv"
                )
                csv_folder = os.path.join(work_dir, "Airfoil_Loading_CSVs")
                os.makedirs(csv_folder, exist_ok=True)
                write_loading_csv(
                    loading_data, os.path.join(csv_folder, output_filename)
                )

    ####################
    #                  #
    #  INTEGRAL VALUES #
    #                  #
    ####################

    def generate_integral_values(solver, work_dir, config, basename):
        fields = config.get("fields", [])
        if not fields:
            logger.warning(
                "[Integral Values] No fields defined — nothing will be calculated."
            )
            return

        bc_types = solver.settings.setup.boundary_conditions.get_state().keys()
        target_bc_types = [
            bc
            for bc in bc_types
            if any(key in bc.lower() for key in ["interface", "inlet", "outlet"])
        ]
        faces = []
        for bc_type in target_bc_types:
            faces += list(
                getattr(solver.settings.setup.boundary_conditions, bc_type)
                .get_state()
                .keys()
            )

        surface = [s for s in faces if "inflow" in s.lower() or "outflow" in s.lower()]

        mass_avg_filename = os.path.join(work_dir, f"Mass_Ave_Integrals_{basename}.txt")
        mass_flow_filename = os.path.join(work_dir, f"Mass_flow_{basename}.txt")

        for field in fields:
            solver.settings.results.report.surface_integrals.mass_weighted_avg(
                surface_names=surface,
                report_of=field,
                write_to_file=True,
                file_name=mass_avg_filename,
            )

        solver.settings.results.report.surface_integrals.mass_flow_rate(
            surface_names=surface, write_to_file=True, file_name=mass_flow_filename
        )

        df_mass_avg = parse_mass_avg_report(mass_avg_filename)
        df_mass_flow = parse_mass_avg_report(mass_flow_filename)

        df_mass_avg.to_csv(os.path.join(work_dir, f"Mass_Ave_Processed_{basename}.csv"))
        df_mass_flow.to_csv(
            os.path.join(work_dir, f"Mass_flow_Processed_{basename}.csv")
        )

    # ###############################
    # #                             #
    # #  ROW-BY-ROW RADIAL PROFILE  #
    # #                             #
    # ###############################

    def generate_radial_profiles(solver, work_dir, config):
        variables = config.get("variables", [])
        rows = config.get("rows", {})

        profile_dir = os.path.join(work_dir, "Radial_Profile_XY")
        os.makedirs(profile_dir, exist_ok=True)

        prof_data = dict()

        for row_name, settings in rows.items():
            topo = row_name + "-topology"
            inlet_axial = settings.get("inlet_axial", 0.0)
            outlet_axial = settings.get("outlet_axial", 1.0)

            prof_data[row_name] = {"Inlet": {}, "Outlet": {}}

            for var in variables:
                fname_inlet = os.path.join(
                    profile_dir,
                    f"{row_name}_inlet_{var.replace('-','_')}_radial_profile.xy",
                )
                fname_outlet = os.path.join(
                    profile_dir,
                    f"{row_name}_outlet_{var.replace('-','_')}_radial_profile.xy",
                )

                solver.tui.turbo_post.xy_plot_avg(
                    topo,
                    "hub-to-casing-distance",
                    var,
                    str(inlet_axial),
                    "0",
                    "0",
                    "yes",
                    f'"{fname_inlet}"',
                )
                solver.tui.turbo_post.xy_plot_avg(
                    topo,
                    "hub-to-casing-distance",
                    var,
                    str(outlet_axial),
                    "0",
                    "0",
                    "yes",
                    f'"{fname_outlet}"',
                )

                prof_data[row_name]["Inlet"].update(Read_Fluent_xy(fname_inlet))
                prof_data[row_name]["Outlet"].update(Read_Fluent_xy(fname_outlet))

        # Save plots
        plot_row_radial_profile(
            prof_data,
            SaveFig=True,
            fig_dir=os.path.join(work_dir, "Radial_Profile_Figures"),
        )

    input_filename = os.path.join(work_dir, file_name)
    basename = os.path.splitext(os.path.basename(input_filename))[0]

    ref_zone = ref_cfg.get("cz_rotating_names", [None])[0]
    solver.settings.setup.reference_values.zone = ref_zone
    solver.tui.define.custom_field_functions.define(
        '"swirl-angle"', '"atan(tangential_velocity/axial_velocity)"'
    )
    solver.tui.define.custom_field_functions.define(
        '"rel-swirl-angle"', '"atan(rel_tangential_velocity/rel_axial_velocity)"'
    )

    airfoil_cfg = post_cfg.get("airfoil_loading")
    radial_cfg = post_cfg.get("radial_profiles", {})
    integral_cfg = post_cfg.get("integral_values", {})

    if airfoil_cfg:
        logger.info("[Fplot] Starting airfoil loading post-processing...")
        airfoil_loading_analysis(
            solver=solver, work_dir=work_dir, case_dict=airfoil_cfg
        )
    else:
        logger.info(
            "[Fplot] No 'airfoil_loading' config found. Skipping airfoil plots."
        )

    if radial_cfg:
        logger.info("[Fplot] Starting radial profile post-processing...")
        generate_radial_profiles(solver, work_dir, radial_cfg)
    else:
        logger.info("[Fplot] No 'radial_profiles' config found. Skipping radial plots.")

    if integral_cfg:
        logger.info("[Fplot] Starting integral value post-processing...")
        generate_integral_values(solver, work_dir, integral_cfg, basename)
    else:
        logger.info(
            "[Fplot] No 'integral_values' config found. Skipping integral reports."
        )
