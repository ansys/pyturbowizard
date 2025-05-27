# Logger
from ptw_subroutines.utils import ptw_logger, dict_utils

logger = ptw_logger.getLogger()


def numerics(data, solver, functionEl, gpu):
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
        "numerics_level1",
    ]

    defaultName = "numerics_bp_tn_2305"
    if gpu:
        defaultName = "numerics_defaults_pseudo_timestep"
        if tsn:
            logger.warning(
                "Turbomachinery specific numerics are not supported in GPU solver and will therefore not be used!"
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
    elif functionName == "numerics_level1":
        numerics_level1(data, solver)

    else:
        logger.info(
            f"Prescribed Function '{functionName}' not known. Skipping Specifying Numerics!"
        )

    logger.info("Specifying Numerics... finished!")


def numerics_defaults(data, solver):
    logger.info(
        "No changes of numerics-settings are made. Fluent defaults-settings are used..."
    )
    return


def numerics_bp_tn_2305(data, solver):
    solver.solution.methods.gradient_scheme = "green-gauss-node-based"
    logger.info(
        "Best Practice and turbo numerics with green-gauss-node-based will be used"
    )

    use_tsn = data["solution"].setdefault("tsn", True)
    if use_tsn:
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable("yes")
    return


def numerics_bp_tn_2305_lsq(data, solver):
    logger.info(
        "Best Practice and turbo numerics with least-sqaure-cell-based will be used"
    )
    solver.solution.methods.gradient_scheme = "least-square-cell-based"
    use_tsn = data["solution"].setdefault("tsn", True)
    if use_tsn:
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable("yes")
    return


def numerics_bp_all_2305(data, solver):
    discDict = solver.solution.methods.discretization_scheme
    for discKey in discDict:
        if discKey == "pressure":
            discDict[discKey] = "second-order"
        else:
            discDict[discKey] = "second-order-upwind"

    numerics_bp_tn_2305(data=data, solver=solver)
    return


def numerics_defaults_pseudo_timestep(data, solver):
    logger.info(
        "Setting pv-coupling using pseudo-time-step method, all other settings are fluent defaults..."
    )
    solver.solution.methods.p_v_coupling.flow_scheme = "Coupled"
    solver.solution.methods.pseudo_time_method.formulation.coupled_solver = (
        "global-time-step"
    )
    return


def numerics_level1(data ,solver):
    solver.tui.solve.set.numerics("no", "no", "no", "no", "no", 0.7)
    solver.solution.methods.gradient_scheme = "green-gauss-node-based"
    logger.info(
        "Best Practice and turbo numerics with green-gauss-node-based will be used"
    )

    use_tsn = data["solution"].setdefault("tsn", True)
    if use_tsn:
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable("yes")
    return

