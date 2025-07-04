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
Numerics Module

This module is setting the numerical methods and utilities in the PyTurboWizard application.
"""

# Logger
from src.subroutines.utils import dict_utils, ptw_logger

logger = ptw_logger.getLogger()


def numerics(data, solver, functionEl, gpu):
    """Set numerics for the solver based on the provided data and function element."""
    # Get FunctionName & Update FunctionEl
    if "tsn" not in data.get("solution"):
        tsn = False
    else:
        tsn = data.get("solution")["tsn"]

    supported_num = [
        "numerics_defaults",
        "numerics_bp_tn_2305",
        "numerics_bp_tn_2305_lsq",
        "numerics_bp_all_2305",
        "numerics_defaults_pseudo_timestep",
    ]

    defaultName = "numerics_bp_tn_2305"
    if gpu:
        defaultName = "numerics_defaults_pseudo_timestep"
        if tsn:
            logger.warning(
                "Turbomachinery specific numerics are not supported in GPU solver "
                "and will therefore not be used!"
            )
            data.get("solution")["tsn"] = False

    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="numerics",
        defaultName=defaultName,
    )

    logger.info(f"Specifying Numerics '{functionName}' ...")
    if functionName == "numerics_defaults":
        numerics_defaults(data, solver)
    elif functionName == "numerics_bp_tn_2305":
        numerics_bp_tn_2305(data, solver)
    elif functionName == "numerics_bp_tn_2305_lsq":
        numerics_bp_tn_2305_lsq(data, solver)
    elif functionName == "numerics_bp_all_2305":
        numerics_bp_all_2305(data, solver)
    elif functionName == "numerics_defaults_pseudo_timestep":
        numerics_defaults_pseudo_timestep(data, solver)
    else:
        logger.info(
            f"Prescribed Function '{functionName}' not known. Skipping Specifying Numerics!"
        )

    logger.info("Specifying Numerics... finished!")


def numerics_defaults(data, solver):
    """Set numerics to default values."""
    logger.info("No changes of numerics-settings are made. Fluent defaults-settings are used...")
    return


def numerics_bp_tn_2305(data, solver):
    """Set numerics to Best Practice and turbo numerics with green-gauss-node-based scheme."""
    solver.settings.solution.methods.gradient_scheme = "green-gauss-node-based"
    logger.info("Best Practice and turbo numerics with green-gauss-node-based will be used")

    use_tsn = data["solution"].setdefault("tsn", True)
    if use_tsn:
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable("yes")
    return


def numerics_bp_tn_2305_lsq(data, solver):
    """Set numerics to Best Practice and turbo numerics with least-square-cell-based scheme."""
    logger.info("Best Practice and turbo numerics with least-square-cell-based will be used")
    solver.settings.solution.methods.gradient_scheme = "least-square-cell-based"
    use_tsn = data["solution"].setdefault("tsn", True)
    if use_tsn:
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable("yes")
    return


def numerics_bp_all_2305(data, solver):
    """Set numerics to Best Practice and turbo numerics with second-order upwind scheme."""
    discDict = solver.settings.solution.methods.discretization_scheme
    for discKey in discDict:
        if discKey == "pressure":
            discDict[discKey] = "second-order"
        else:
            discDict[discKey] = "second-order-upwind"

    numerics_bp_tn_2305(data=data, solver=solver)
    return


def numerics_defaults_pseudo_timestep(data, solver):
    """Set numerics to pseudo-time-step method."""
    logger.info(
        "Setting pv-coupling using pseudo-time-step method, "
        "all other settings are fluent defaults..."
    )
    solver.settings.solution.methods.p_v_coupling.flow_scheme = "Coupled"
    solver.settings.solution.methods.pseudo_time_method.formulation.coupled_solver = (
        "global-time-step"
    )
    return
