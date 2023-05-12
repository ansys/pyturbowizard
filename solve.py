def init_01(data, solver):
    solver.tui.solve.initialize.compute_defaults.pressure_inlet(data["locations"]["bz_inlet_name"])
    solver.solution.initialization.standard_initialize()
    solver.solution.initialization.fmg_initialize()
    # Write initial data
    solver.file.write(file_type="data", file_name=data["caseFilename"])

def solve_01(data, solver):
    solver.solution.run_calculation.iterate(iter_count= data["solution"]["iter_count"])
    return


