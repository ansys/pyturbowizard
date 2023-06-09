from tts_subroutines import utilities


def numerics(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = utilities.get_funcname_and_upd_funcdict(
        parentEl=data,
        functionEl=functionEl,
        funcElName="numerics",
        defaultName="numerics_bp_all_2305",
    )

    print('\nSpecifying Numerics: "' + functionName + '"...')
    if functionName == "numerics_defaults":
        numerics_defaults(data, solver)
    elif functionName == "numerics_bp_tn_2305":
        numerics_bp_tn_2305(data, solver)
    elif functionName == "numerics_bp_tn_2305_lsq":
        numerics_bp_tn_2305_lsq(data, solver)
    elif functionName == "numerics_bp_all_2305":
        numerics_bp_all_2305(data, solver)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Specifying Numerics!'
        )

    print("\nSpecifying Numerics... finished!\n")


def numerics_defaults(data, solver):
    print(
        "No changes of numerics-settings are made. Fluent defaults-settings are used..."
    )
    return


def numerics_bp_tn_2305(data, solver):
    solver.solution.methods.gradient_scheme = "green-gauss-node-based"
    print("Best Practice and turbo numerics with green-gauss-node-based will be used")

    if data["solution"]["tsn"]:
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable("yes")
    return

def numerics_bp_tn_2305_lsq(data, solver):
    print("Best Practice and turbo numerics with least-sqaure-cell-based will be used")
    solver.solution.methods.gradient_scheme = "least-square-cell-based"
    if data["solution"]["tsn"]:
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
