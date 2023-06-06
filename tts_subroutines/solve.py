from tts_subroutines import utilities


def init(data, solver, functionEl):
    # Get FunctionName & Update FunctionEl
    functionName = utilities.get_funcname_and_upd_funcdict(
        parentEl=data,
        functionEl=functionEl,
        funcElName="initialization",
        defaultName="init_hybrid_01",
    )

    print('\nRunning Initialization Function "' + functionName + '"...')
    if functionName == "init_standard_01":
        init_standard_01(data, solver)
    if functionName == "init_hybrid_01":
        init_hybrid_01(data, solver)
    if functionName == "init_fmg_01":
        init_fmg_01(data, solver)
    else:
        print(
            'Prescribed Function "'
            + functionName
            + '" not known. Skipping Initialization!'
        )

    print("Running Initialization Function... finished.")


def init_standard_01(data, solver):
    print(f'Using {data["locations"]["bz_inlet_names"][0]} pressure for initialization')
    solver.tui.solve.initialize.compute_defaults.pressure_inlet(
        data["locations"]["bz_inlet_names"][0]
    )
    solver.solution.initialization.standard_initialize()

    solver.solution.initialization.hybrid_init_options.general_settings.reference_frame = (
        "absolute"
    )


def init_hybrid_01(data, solver):
    init_standard_01(data=data, solver=solver)
    solver.solution.initialization.hybrid_init_options.general_settings.reference_frame = (
        "absolute"
    )
    solver.solution.initialization.hybrid_init_options.general_settings.initial_pressure = (
        True
    )
    solver.solution.initialization.hybrid_initialize()


def init_fmg_01(data, solver):
    init_standard_01(data=data, solver=solver)
    solver.solution.initialization.fmg_initialize()


def solve_01(data, solver):
    iter_count = data["solution"].get("iter_count", 0)
    print(
        "Solving " + str(iter_count) + " iterations"
    )
    solver.solution.run_calculation.iterate(iter_count=iter_count)
    return
