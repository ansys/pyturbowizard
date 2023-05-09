def init_01(data, solver):
    solver.tui.solve.initialize.compute_defaults.pressure_inlet(bz_inlet_name)
    solver.solution.initialization.standard_initialize()
    solver.solution.initialization.fmg_initialize()

def solve_01(data, solver):
    solver.solution.run_calculation.iterate(iter_count=iter_count)
    return


