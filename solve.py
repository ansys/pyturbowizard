def init_01(data, solver):
    solver.tui.solve.initialize.compute_defaults.pressure_inlet(
        data["locations"]["bz_inlet_name"]
    )
    solver.solution.initialization.standard_initialize()
    solver.tui.solve.initialize.set_hyb_initialization.general_settings('10', '1', '1', 'absolute', 'yes', 'no', 'no')
    solver.solution.initialization.hybrid_initialize()
    # solver.solution.initialization.fmg_initialize()


def solve_01(data, solver):
    print("Solving " + str(data["solution"]["iter_count"]) + " iterations with time scale factor " + str(
        data["solution"]["time_step_factor"]))
    solver.solution.run_calculation.iterate(iter_count=data["solution"]["iter_count"])
    return
