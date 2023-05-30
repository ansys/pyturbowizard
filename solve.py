def init(data, solver, functionName="init_01_hybrid"):
    print('Running Initialization Function "' + functionName + '"...')
    if functionName == "init_01_hybrid":
        init_01_hybrid(data, solver)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Initialization!'
        )

    print("Initialization finished.")


def init_01_standard(data, solver):
    print(f'Using {data["locations"]["bz_inlet_names"][0]} pressure for initialization')
    solver.tui.solve.initialize.compute_defaults.pressure_inlet(
        data["locations"]["bz_inlet_names"][0]
    )
    solver.solution.initialization.standard_initialize()

    solver.solution.initialization.hybrid_init_options.general_settings.reference_frame = (
        "absolute"
    )


def init_01_hybrid(data, solver):
    init_01_standard(data=data, solver=solver)
    solver.solution.initialization.hybrid_init_options.general_settings.reference_frame = (
        "absolute"
    )
    solver.solution.initialization.hybrid_init_options.general_settings.initial_pressure = (
        True
    )
    solver.solution.initialization.hybrid_initialize()


def init_01_fmg(data, solver):
    init_01_standard(data=data, solver=solver)
    solver.solution.initialization.fmg_initialize()


def solve_01(data, solver):
    tsf = data["solution"].get("time_step_factor", 1)
    iter_count = data["solution"].get("iter_count", 0)
    print(
        "Solving " + str(iter_count) + " iterations with time scale factor " + str(tsf)
    )
    solver.solution.run_calculation.iterate(iter_count=iter_count)
    return
