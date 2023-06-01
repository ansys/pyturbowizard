import utilities


def numerics(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = utilities.get_funcname_and_upd_funcdict(
        parentEl=data,
        functionEl=functionEl,
        funcElName="numerics",
        defaultName="numerics_01",
    )

    print('\nSpecifying Numerics: "' + functionName + '"...')
    if functionName == "numerics_01":
        numerics_01(data, solver)
    elif functionName == "numerics_bp_tn_2305":
        numerics_bp_tn_2305(data, solver)
    elif functionName == "numerics_bp_all_2305":
        numerics_bp_all_2305(data, solver)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Specifying Numerics!'
        )

    print("Specifying Numerics... finished.")


def numerics_01(data, solver):
    numerics_bp_all_2305(data=data, solver=solver)
    return


def numerics_bp_tn_2305(data, solver):
    solver.solution.methods.gradient_scheme = "green-gauss-node-based"
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
