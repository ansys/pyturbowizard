def init_01(data, solver):
    solver.tui.solve.initialize.compute_defaults.pressure_inlet(
        data["locations"]["bz_inlet_name"]
    )
    solver.solution.initialization.standard_initialize()

    solver.solution.initialization.hybrid_init_options.general_settings.reference_frame = (
        "absolute"
    )
    solver.solution.initialization.hybrid_init_options.general_settings.initial_pressure = (
        True
    )
    solver.solution.initialization.hybrid_initialize()
    # solver.solution.initialization.fmg_initialize()


def solve_01(data, solver):
    tsf = data["solution"].get("time_step_factor", 1)
    iter_count = data["solution"].get("iter_count", 0)
    print(
        "Solving " + str(iter_count) + " iterations with time scale factor " + str(tsf)
    )
    solver.solution.run_calculation.iterate(iter_count=iter_count)
    return
