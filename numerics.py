def numerics_01(data, solver):
    solver.solution.methods.gradient_scheme = "green-gauss-node-based"
    if data["solution"]["tsn"]:
        solver.tui.solve.set.advanced.turbomachinery_specific_numerics.enable('yes')
    return

