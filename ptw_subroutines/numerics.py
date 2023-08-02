# Logger
from ptw_subroutines.utils import ptw_logger, dict_utils

logger = ptw_logger.getLogger()


def numerics(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = dict_utils.get_funcname_and_upd_funcdict(
        parentDict=data,
        functionDict=functionEl,
        funcDictName="numerics",
        defaultName="numerics_bp_tn_2305",
    )

    logger.info('\nSpecifying Numerics: "' + functionName + '"...')
    if functionName == "numerics_defaults":
        numerics_defaults(data, solver)
    elif functionName == "numerics_bp_tn_2305":
        numerics_bp_tn_2305(data, solver)
    elif functionName == "numerics_bp_tn_2305_lsq":
        numerics_bp_tn_2305_lsq(data, solver)
    elif functionName == "numerics_bp_all_2305":
        numerics_bp_all_2305(data, solver)
    else:
        logger.info(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Specifying Numerics!'
        )

    logger.info("\nSpecifying Numerics... finished!\n")


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
