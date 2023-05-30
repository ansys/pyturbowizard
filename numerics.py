def numerics(data, solver, functionName="numerics_01"):
    print('\nSpecifying Numerics: "' + functionName + '"...')
    if functionName == "numerics_01":
        numerics_01(data, solver)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Specifying Numerics!'
        )

    print("Specifying Numerics... finished.")


def numerics_01(data, solver):
    # Fluent Defaults in v232
    # solver.solution.methods.discretization_scheme["pressure"] = "second-order"
    # solver.solution.methods.discretization_scheme["temperature"] = "second-order-upwind"
    # solver.solution.methods.discretization_scheme["mom"] = "second-order-upwind"
    # solver.solution.methods.discretization_scheme["k"] = "second-order-upwind"
    # solver.solution.methods.discretization_scheme["omega"] = "second-order-upwind"

    discDict = solver.solution.methods.discretization_scheme
    for discKey in discDict:
        if discKey == "pressure":
            discDict[discKey] = "second-order"
        else:
            discDict[discKey] = "second-order-upwind"

    solver.solution.methods.gradient_scheme = "green-gauss-node-based"
    if data["solution"]["tsn"]:
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable("yes")
    return
