# Logger
from ptw_subroutines.utils import ptw_logger, dict_utils

logger = ptw_logger.getLogger()


def init(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="initialization",
        defaultName="init_fmg_01",
    )

    logger.info('Running Initialization Function "' + functionName + '"...')
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
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Initialization!'
        )

    logger.info("Initialization Function... finished.")


def init_standard_01(data, solver):
    logger.info(
        f'Using {data["locations"]["bz_inlet_names"][0]} pressure for initialization'
    )
    solver.solution.initialization.reference_frame = "absolute"

    # if the boundary condition needs information from flow field
    # (e.g. density to convert volume-rate to massflow-rate),
    # we need to initialize first so that we have field data available
    solver.solution.initialization.standard_initialize()

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
        logger.info(f"No inlet BC specified. Initialing from 'all-zones'")
        solver.tui.solve.initialize.compute_defaults.all_zones()

    solver.solution.initialization.standard_initialize()


def init_standard_02(data, solver):

    # if the boundary condition needs information from flow field
    # (e.g. density to convert volume-rate to massflow-rate),
    # we need to initialize first so that we have field data available
    solver.solution.initialization.standard_initialize()
    
    solver.solution.initialization.reference_frame = "relative"
    if "BC_IN_Tt" in data["expressions"]:
        myTemp = float(data["expressions"]["BC_IN_Tt"].split(" ")[0])
        solver.solution.initialization.defaults = {"temperature": myTemp}
    if "BC_IN_p_gauge" in data["expressions"]:
          myPress = float(data["expressions"]["BC_IN_p_gauge"].split(" ")[0])
          solver.solution.initialization.defaults = {"pressure": myPress}
    solver.solution.initialization.defaults = {"k": 0.01}
    solver.solution.initialization.defaults = {"omega": 0.01}
    solver.solution.initialization.defaults = {"x-velocity": 0}
    solver.solution.initialization.defaults = {"y-velocity": 0}
    solver.solution.initialization.defaults = {"z-velocity": 0}

    solver.solution.initialization.standard_initialize()

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
    solver.solution.initialization.standard_initialize()
    solver.solution.initialization.hybrid_init_options.general_settings.reference_frame = (
        "absolute"
    )
    solver.solution.initialization.hybrid_init_options.general_settings.initial_pressure = (
        True
    )
    solver.solution.initialization.hybrid_initialize()

def init_fmg_basic(data, solver):
    # setting rp variable which is needed for version v232 when using gtis, may be obsolete in future versions
    solver.execute_tui(r"""(rpsetvar 'fmg-init/enable-with-gti? #t)""")
    solver.solution.initialization.fmg_initialize()

def solve_01(data, solver):
    iter_count = data["solution"].setdefault("iter_count", 500)
    logger.info("Solving " + str(iter_count) + " iterations")
    solver.solution.run_calculation.iterate(iter_count=iter_count)
    return
