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

from packaging.version import Version

# Logger
from src.subroutines.utils import ptw_logger, dict_utils

logger = ptw_logger.getLogger()


def init(data, solver, functionEl, gpu):
    # Get FunctionName & Update FunctionEl
    defaultName = "init_fmg_01"
    if gpu:
        defaultName = "init_standard_01"

    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="initialization",
        defaultName=defaultName,
    )

    # Reordering Domain
    # Can have influence on convergence, but can lead to freeze on some cases
    reorder = data["solution"].setdefault("reorder_domain", True)
    if reorder:
        logger.info(
            "Reordering domain to reduce bandwidth according to the setup"
        )
        solver.settings.mesh.reorder.reorder_domain()

    supported_ini_gpu = ["init_standard_01", "init_hybrid_01"]

    supported_ini = [
        "init_standard_01",
        "init_standard_02",
        "init_hybrid_01",
        "init_fmg_01",
        "init_fmg_02",
        "init_fmg_03",
    ]

    if gpu:
        if (functionName not in supported_ini_gpu) and (
            functionName in supported_ini
        ):
            logger.warning(
                f"Prescribed Initialization Function '{functionName}' not supported in GPU solver. Using 'init_standard_01' instead!"
            )
            functionName = "init_standard_01"
        elif (functionName not in supported_ini_gpu) and (
            functionName not in supported_ini
        ):
            logger.warning(
                f"Prescribed Function '{functionName}' not known. Using 'init_standard_01' instead!"
            )
            functionName = "init_standard_01"

    logger.info(f"Running Initialization Function '{functionName}'")
    if functionName == "init_standard_01":
        init_standard_01(data, solver)
    elif functionName == "init_standard_02":
        init_standard_02(data, solver)
    elif functionName == "init_hybrid_01":
        init_hybrid_01(data, solver)
    elif functionName == "init_fmg_01":
        init_fmg_01(data, solver)
    elif functionName == "init_fmg_02":
        init_fmg_02(data, solver)
    elif functionName == "init_fmg_03":
        init_fmg_03(data, solver)
    else:
        logger.info(
            f"'Prescribed Function '{functionName}' not known. Skipping Initialization!"
        )

    logger.info("Initialization Function... finished.")


def init_standard_01(data, solver):
    logger.info(
        f'Using {data["locations"]["bz_inlet_names"][0]} pressure for initialization'
    )
    solver.settings.solution.initialization.reference_frame = "absolute"

    # if the boundary condition needs information from flow field
    # (e.g. density to convert volume-rate to massflow-rate),
    # we need to initialize first so that we have field data available
    logger.info(
        "Initializing flow field to get field data for flow field depended boundary conditions"
    )
    solver.settings.solution.initialization.standard_initialize()

    availableBCs = dir(solver.tui.solve.initialize.compute_defaults)
    if "mass_flow_inlet" in availableBCs:
        solver.tui.solve.initialize.compute_defaults.mass_flow_inlet(
            data["locations"]["bz_inlet_names"][0]
        )
    elif "pressure_inlet" in availableBCs:
        solver.tui.solve.initialize.compute_defaults.pressure_inlet(
            data["locations"]["bz_inlet_names"][0]
        )
    else:
        logger.info(f"No inlet BC specified. Initializing from 'all-zones'")
        solver.tui.solve.initialize.compute_defaults.all_zones()

    logger.info("Performing a standard initialization from inlet")
    solver.settings.solution.initialization.standard_initialize()


def init_standard_02(data, solver):
    # if the boundary condition needs information from flow field
    # (e.g. density to convert volume-rate to massflow-rate),
    # we need to initialize first so that we have field data available
    logger.info(
        "Initializing flow field to get field data for flow field depended boundary conditions"
    )
    solver.settings.solution.initialization.standard_initialize()

    solver.settings.solution.initialization.reference_frame = "relative"
    if "BC_IN_Tt" in data["expressions"]:
        myTemp = float(data["expressions"]["BC_IN_Tt"].split(" ")[0])
        solver.settings.solution.initialization.defaults = {
            "temperature": myTemp
        }
    if "BC_IN_p_gauge" in data["expressions"]:
        myPress = float(data["expressions"]["BC_IN_p_gauge"].split(" ")[0])
        solver.settings.solution.initialization.defaults = {
            "pressure": myPress
        }
    solver.settings.solution.initialization.defaults = {"k": 0.01}
    solver.settings.solution.initialization.defaults = {"omega": 0.01}
    solver.settings.solution.initialization.defaults = {"x-velocity": 0}
    solver.settings.solution.initialization.defaults = {"y-velocity": 0}
    solver.settings.solution.initialization.defaults = {"z-velocity": 0}
    logger.info("Performing a standard initialization from 0 values")
    solver.settings.solution.initialization.standard_initialize()


def init_hybrid_01(data, solver):
    init_hybrid_basic(data=data, solver=solver)


def init_fmg_01(data, solver):
    init_standard_01(data=data, solver=solver)
    init_fmg_basic(data=data, solver=solver)


def init_fmg_02(data, solver):
    init_standard_02(data=data, solver=solver)
    init_fmg_basic(data=data, solver=solver)


def init_fmg_03(data, solver):
    init_hybrid_01(data=data, solver=solver)
    init_fmg_basic(data=data, solver=solver)


def init_hybrid_basic(data, solver):
    # if the boundary condition needs information from flow field
    # (e.g. density to convert volume-rate to massflow-rate),
    # we need to initialize first so that we have field data available
    logger.info(
        "Initializing flow field to get field data for flow field depended boundary conditions"
    )
    solver.settings.solution.initialization.standard_initialize()

    if Version(solver._version) >= Version("241"):
        solver.settings.solution.initialization.initialization_type = "hybrid"
        solver.settings.solution.initialization.reference_frame = "absolute"
    else:
        solver.settings.solution.initialization.hybrid_init_options.general_settings.reference_frame = (
            "absolute"
        )

    solver.settings.solution.initialization.hybrid_init_options.general_settings.initial_pressure = (
        True
    )
    logger.info("Performing a hybrid initialization")
    solver.settings.solution.initialization.hybrid_initialize()


def init_fmg_basic(data, solver):
    logger.info("Performing a FMG initialization")
    if Version(solver._version) < Version("241"):
        # setting rp variable which is needed for version v232 when using gtis, may be obsolete in future versions
        solver.execute_tui(r"""(rpsetvar 'fmg-init/enable-with-gti? #t)""")
        solver.settings.solution.initialization.fmg_initialize()
    else:
        solver.settings.solution.initialization.fmg.fmg_initialize()


def solve_01(data, solver):
    iter_count = data["solution"].setdefault("iter_count", 500)
    logger.info(f"Solving max. {iter_count} iterations")
    solver.settings.solution.run_calculation.iterate(iter_count=iter_count)
    return
