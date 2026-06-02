import csv, json
import logging
import math
import os
from packaging.version import Version

# Load Script Modules
from .utils import ptw_logger, mcov

__version__ = "1.0.6"

logger = ptw_logger.get_logger()

####################################### Trn Configuration Class ##########################################################

class TrnSimulationConfig:
    """Configuration class for the simulation settings."""
    def __init__(self):
        """Initialize the simulation configuration with default values."""
        # Basic User Input
        self.base_filename = "BaseCase"  # Base name for case files, report files, etc.
        self.mesh_filename = f"{self.base_filename}.msh.h5"
        self.restart_filename = ""
       
        # RANS simulation   
        self.rans_iterations = 5000 # Number of RANS iterations     
        self.rans_settings_file = f"{self.base_filename}_RANS.set"   
        self.bc_file = ""  # JSON file containing BC adjustments for different phases, can be empty if not needed
        self.rans_postprocessing = []
        self.rans_write_data = True

        # Reference Time: Through Flow Time / Blade-Passing Period
        self.reference_time = 0.0282

        # Phase 1 -> periodic-signal
        self.skip_p1 = False
        self.time_step_size_p1 = 1.0e-05
        self.num_ref_times_p1 = 20
        self.write_data_p1 = True
        self.read_journal_p1 = [] # Read journal before starting solver for Phase 1, can be empty if not needed
        self.ramp_up_p1 = {}  # Dictionary with time_step_size: time_step_count for ramp-up phase

        # Phase 2 -> trn-sampling run
        self.time_step_size_p2 = 1.0e-05
        self.num_ref_times_p2 = 10
        self.ramp_up_p2 = {}  # Dictionary with time_step_size: time_step_count for ramp-up phase

        # Postprocessing settings
        self.do_postprocessing = []
        self.write_case_after_pp = False
        self.export_cfdpost = False

        # General settings        
        self.max_iter_per_step = 5
        self.auto_save_frequency = 0
        self.residual_convergence = False
        self.copy_frame_to_mesh_motion = False
        self.disable_temp_sec_grad = False

        # SRS-options
        self.les_model = "sbes"        
        self.central_scheme_pure = False  # Setting Central Scheme with zero diffusion coefficient
        self.wall_use_second_cell = False  # Use second cell off a wall quantities for near-wall treatment
        self.near_wall_rans_layer = False
        self.turb_generator_option = "No Perturbations"  # Available options: ['No Perturbations', 'Vortex Method', 'Spectral Synthesizer', 'Synthetic Turbulence Generator']
        self.use_pyUDFs = []
        self.use_zone_sampling = False
        self.skip_srs_settings = False  # Skip SRS-settings, directly jump to solution process
        self.create_setup_only = False  # Only creates the setup and writes cas&dat-file
        self.time_discretization = "unsteady-2nd-order-bounded" # Time discretization scheme for unsteady solver settings
        self.use_limiter_time = True  # Use limiter in time for 2nd order unsteady scheme

        # MCOV definition
        #self.mcov_journal_name = ""
        self.mcov_def_names = ["my_report_definition"]
        self.mcov_updates_per_rt = 20  # Number of updates per reference time
        self.mcov_avg_interval = 2 * self.mcov_updates_per_rt
        self.mcov_con_crit = 5.e-5
        self.mcov_command_name = "mcov_update"

        # Logger file-name
        self.logger_file_name = 'srs_solution.log'
        self.solver_monitor = False  # Useful to extract residuals for batch runs (without graphics)

    def log_settings(self,logger): 
        """Log the configuration settings to the provided logger."""       
        logger.info(f"SimulationConfig: {vars(self)}")
    
    def update_from_dict(self, config_dict: dict):
        """Update the configuration settings from a dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_dict(self):
        """Get the configuration settings as a dictionary."""
        return vars(self)

    def write_to_json(self, file_path: str):
        """Write the configuration to a JSON file."""
        try:
            with open(file_path, 'w') as json_file:
                json.dump(self.get_dict(), json_file, indent=4)
            logger.info(f"Configuration successfully written to {file_path}")
        except Exception as e:
            logger.error(f"Error writing configuration to JSON: {e}")

    def read_from_json(self, file_path: str):
        """Read the configuration from a JSON file."""
        try:
            with open(file_path, 'r') as json_file:
                data = json.load(json_file)
                self.update_from_dict(data)
            logger.info(f"Configuration successfully loaded from {file_path}")
        except Exception as e:
            logger.error(f"Error reading configuration from JSON: {e}")

  
def get_valid_filepath(file_path:str):
    """Get a valid file path for the solver report files."""
    if not file_path:
        raise ValueError("Invalid file path provided.")

    folder_path = os.path.dirname(file_path)
    if folder_path:
        if os.path.exists(folder_path):
            return file_path
        else:
            return os.path.basename(file_path)
    else:
        return file_path


def export_solver_monitor(solver, filepath: str = "residual.csv", monitor_set_name: str = "residual"):
    """Export the solver monitor data to a CSV file."""
    mp = solver.monitors.get_monitor_set_data(monitor_set_name=monitor_set_name)
    indices = mp[0]
    data_dict = mp[1]
    with open(filepath, 'w', newline='') as file:
        writer = csv.writer(file)
        # Write header
        header = ['Index'] + list(data_dict.keys())
        writer.writerow(header)
        # Write data rows
        for i in range(len(indices)):
            row = [indices[i]] + [data_dict[key][i] for key in data_dict]
            writer.writerow(row)

def initialize_logger(logger_file_path: str = None):
    """Initialize the logger based on the configuration."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    logger = logging.getLogger(__name__)
    if logger_file_path:
        # Create a file handler -> overwrite if existing
        file_handler = logging.FileHandler(logger_file_path, mode='w')
        file_handler.setLevel(logging.INFO)
        # Create a formatter and set it for the file handler
        formatter = logging.Formatter(fmt='%(asctime)s - {%(filename)s:%(lineno)d} - %(levelname)s -  %(message)s',
                                    datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        # Add the file handler to the logger
        logger.addHandler(file_handler)

    return logger


def save_source_with_addons(source_file: str, addons: str, output_file: str = None):
    """Save a copy of source_file with a '#sym:<symbol_name>' marker appended."""
    if not source_file:
        raise ValueError("source_file must be provided")

    if output_file is None:
        source_dir = os.path.dirname(source_file)
        source_name = os.path.basename(source_file)
        base_name, ext = os.path.splitext(source_name)
        output_file = os.path.join(source_dir, f"{base_name}_with_symbol{ext}")

    with open(source_file, "r", encoding="utf-8") as src:
        source_content = src.read().rstrip("\n")

    source_content = f"{source_content}\n{addons}"

    with open(output_file, "w", encoding="utf-8") as dst:
        dst.write(f"{source_content}\n")

    return output_file

###################################### Trn Solution Class ##########################################################

class TrnSimulationRun:
    
    """Class to run the simulation based on the provided configuration."""
    def __init__(self, solver, config: TrnSimulationConfig, gpu:bool=False):
        self.solver = solver
        self.config = config
        self.gpu = gpu
        if logger is None:           
            self.logger = initialize_logger(config.logger_file_name)
        else:
            self.logger = logger

    def initialize_run(self, solver=None, config: TrnSimulationConfig = None, logger=None):
        '""Initialize the solver run with basic settings."""'
        if solver is None:
            solver = self.solver
        if config is None:
            config = self.config
        if logger is None:
            logger = self.logger
        logger.info("Initializing basic-settings...")  
        # Set batch options
        solver.settings.file.batch_options.confirm_overwrite = False
        solver.settings.file.batch_options.exit_on_error = True
        solver.settings.file.batch_options.hide_answer = True
        solver.settings.file.batch_options.redisplay_question = False

        # Check if an old transcript file is active
        if 'stop_transcript' in solver.settings.file.get_active_command_names():
            solver.settings.file.stop_transcript()
        # Start new Transcript & read cas/dat file
        solver.settings.file.start_transcript(file_name=f"{config.base_filename}.trn")

        logger.info("Initializing basic-settings... done")

    def run_rans(self, solver=None, config: TrnSimulationConfig = None, logger=None):
        """Run the RANS solution phase."""
        if solver is None:
            solver = self.solver
        if config is None:
            config = self.config
        if logger is None:
            logger = self.logger
        logger.info("Starting RANS Phase ...")    
        if config.mesh_filename and not config.restart_filename:
            # Search for existing mesh file    
            logger.info(f"Reading mesh file: {config.mesh_filename}")     
            solver.settings.file.read(file_type="mesh", file_name=config.mesh_filename)        
        
        # Read RANS settings file
        if config.rans_settings_file:
            logger.info(f"Reading RANS settings file: {config.rans_settings_file}")
            solver.settings.file.read_settings(file_name=config.rans_settings_file)

        if not solver.settings.setup.general.solver.time() == "steady":
            logger.error("RANS Phase requires steady solver settings!")
            return 
        
        if config.bc_file:
            if os.path.exists(config.bc_file):
                bc_dict = {}
                with open(config.bc_file, 'r') as f:
                    bc_dict = json.load(f)
                logger.info(f"Adjusting boundary conditions based on file: {config.bc_file}")
                self.adjust_bcs(solver=solver, bc_dict=bc_dict, logger=logger)
            else:
                logger.info(f"Boundary condition file '{config.bc_file}' not found, skipping BC adjustments.")

        if not config.restart_filename:
            # Initialize solution using standard initialize
            logger.info("Initializing RANS solution...")       
            solver.settings.solution.initialization.standard_initialize()
            logger.info("RANS solution initialized")      

        # Reset Timer
        logger.info("Resetting parallel timer...")
        solver.settings.parallel.timer.reset()
        if config.solver_monitor:
            logger.info("RANS: Starting Solver-Monitor...")
            solver.monitors.start

        # Write setup to json-file
        setup_json_file = f"{config.base_filename}_setup_rans.json"
        logger.info(f"Exporting RANS-setup to JSON file: {setup_json_file}")
        setup_dict = solver.settings.setup()
        with open(setup_json_file, 'w') as json_file:
            json.dump(setup_dict, json_file, indent=4)

        # Start RANS Solver
        logger.info(f"Starting RANS Solver for {config.rans_iterations} iterations...")
        solver.settings.solution.run_calculation.iterate(iter_count=config.rans_iterations)
        logger.info("RANS Solver finished")
        solver.settings.parallel.timer.usage()
        solver.settings.results.report.system.print_system_statistics()
        if config.solver_monitor:
            logger.info("RANS: Exporting & Stopping Solver-Monitor...")
            export_solver_monitor(solver=solver, filepath="residuals-rans.csv")
            solver.monitors.stop
        else:
            solver.execute_tui(r"""(write-residuals-to-file 'residuals-rans.xy)""")   
        # Write final cas- & dat-file
        if config.rans_write_data:
            file_name = f"{config.base_filename}_rans_fin"
            logger.info(f"Writing RANS case- & dat-file: {file_name}")
            solver.settings.file.write(file_type="case-data", file_name=file_name)
        # Run RANS Postprocessing
        if len(config.rans_postprocessing) > 0:
            logger.info(f"RANS: Run Fluent Postprocessing: {config.rans_postprocessing}")
            solver.settings.file.read_journal(file_name_list=config.rans_postprocessing)
    
    def adjust_bcs(self, solver=None, bc_dict: dict = {}, logger=None):
        """Adjust CFD named expressions based on provided dictionary."""
        if solver is None:
            solver = self.solver
        if logger is None:
            logger = self.logger
        logger.info(f"Adjusting CFD named expressions based on provided dictionary: {bc_dict}")
        for bc_name, bc_value in bc_dict.items():            
            # if bc_name in solver.settings.parameters.input_parameters.expression():
            #     solver.settings.parameters.input_parameters.expression[bc_name].value = float(bc_value)               
            # else:
            #     logger.warning(f"Boundary condition '{bc_name}' not found in input parameters of setup...skipping this parameter adjustment.")
            if bc_name in solver.settings.setup.named_expressions():
                old_def = solver.settings.setup.named_expressions[bc_name].definition()
                unit = old_def.split("[")[1].split("]")[0] if "[" in old_def and "]" in old_def else "" 
                new_def = f"{bc_value} [{unit}]" if unit else str(bc_value)
                solver.settings.setup.named_expressions[bc_name].definition = new_def
            else:
                logger.warning(f"Boundary condition '{bc_name}' not found in named expressions of setup...skipping this parameter adjustment.")
            # special handling for angle of attack (aoa) if present in settings
            if bc_name == "BC_aoa":
                aoa = float(bc_value)  
                # adjust force vector for drag and lift reports based on new aoa value
                for report_name in solver.settings.solution.report_definitions.drag():
                    solver.settings.solution.report_definitions.drag[report_name].force_vector = [math.cos(math.radians(aoa)), 0., math.sin(math.radians(aoa))]                
                for report_name in solver.settings.solution.report_definitions.lift():
                    solver.settings.solution.report_definitions.lift[report_name].force_vector = [-math.sin(math.radians(aoa)), 0., math.cos(math.radians(aoa))]                
    
    def create_mcov_controller(self, solver=None, config: TrnSimulationConfig = None, time_step_per_rt_p1=1.0, logger=None):
        """Create MCoV controller for transient solution phase 1."""
        if solver is None:
            solver = self.solver
        if config is None:
            config = self.config
        if logger is None:
            logger = self.logger
        if mcov.__file__ and config.mcov_def_names:
            logger.info("Applying MCOV-criterium")
            # Calc mcov update-frequency
            mcov_update_freq = math.ceil(time_step_per_rt_p1 / config.mcov_updates_per_rt)
            mcov_update_method = "time-step"
            # Load basic mcov-definition class via journal: Running_Mean
            #solver.settings.file.read_journal(file_name_list=[config.mcov_journal_name])            
            logger.info(f"Loading MCoV class from file: {mcov.__file__}") 
            # Create a command string to define MCoV objects for each definition name specified in the config, with the specific settings for this case
            mcov_command_str = ""
            for mcov_def_name in config.mcov_def_names:
                # Include a python execute-command (repeat)
                mcov_log_file = f"mcov_{mcov_def_name}.log" 
                mcov_command_str += f"mcov_{mcov_def_name} = MCoV(def_name='{mcov_def_name}', conv_crit={config.mcov_con_crit}, avg_interval={config.mcov_avg_interval},log_file='{mcov_log_file}')\n"
            # writing a copy of the mcov source with the specific command for the current case, to ensure that the MCoV class is available in the solver with the specific settings for this case
            mcov_file_name = f"{os.path.splitext(os.path.basename(mcov.__file__))[0]}_control.py"
            try:
                mcov_source_copy = save_source_with_addons(
                    source_file=mcov.__file__, addons=mcov_command_str, output_file=mcov_file_name
                )
                logger.info(f"Saved MCOV source with addons to: {mcov_source_copy}")
            except Exception as e:
                logger.warning(f"Could not save MCOV source with addons: {e}")
            solver.settings.file.read_journal(file_name_list=[mcov_file_name])
            # Add execute command to solver settings
            for mcov_def_name in config.mcov_def_names:
                command = f"mcov_{mcov_def_name}.update_data()"
                solver.tui.solve.execute_commands.add_edit(
                    config.mcov_command_name, "no", mcov_update_freq, mcov_update_method, "yes", f'"{command}"'
                )

    def adjust_transient_settings(self, solver=None, config: TrnSimulationConfig = None, logger=None):
        '""Adjust the transient settings for the solver."""'
        if solver is None:
            solver = self.solver
        if config is None:
            config = self.config
        if logger is None:
            logger = self.logger
        logger.info("Adjust transient-settings...")
        # Change transient-scheme and LES-model settings
        logger.info(f"Setting time discretization scheme to '{config.time_discretization}' and limiter in time to '{config.use_limiter_time}'")
        solver.settings.setup.general.solver.time = config.time_discretization

        # Adjust interfaces
        # Copy frame-motion to mesh-motion
        if config.copy_frame_to_mesh_motion:
            for cz_name in solver.settings.setup.cell_zone_conditions.fluid():
                if isinstance(config.copy_frame_to_mesh_motion,
                              list) and cz_name not in config.copy_frame_to_mesh_motion:
                    continue
                cell_zone = solver.settings.setup.cell_zone_conditions.fluid[cz_name]
                if cell_zone.reference_frame.frame_motion():
                    cell_zone.reference_frame.mrf_toggle_mrf_mgrid_ui()

        if self.gpu:
            solver.settings.solution.methods.use_limiter_in_time = config.use_limiter_time
        if config.les_model:                       
            if config.les_model == "sbes":            
                # Setting SBES model
                logger.info("Setting up solver settings for SBES model...")
                solver.settings.setup.models.viscous.model = "k-omega"            
                solver.settings.setup.models.viscous.hybrid_rans_les = ("stress-blended-eddy-simulation")
                solver.settings.setup.models.viscous.sbes_options.hybrid_model = "sbes"
                solver.settings.setup.models.viscous.sbes_options.les_subgrid_scale_model = "wale"
            else:
                # Setting LES model
                logger.info("Setting up solver settings for LES model...")
                solver.settings.setup.models.viscous.model = "large-eddy-simulation"
                
                # Setting subgrid scale model
                supported_sg_models = solver.settings.setup.models.viscous.subgrid_scale_model.allowed_values()
                if f"les-subgrid-{config.les_model}" in supported_sg_models:
                    logger.info(f"Setting up subgrid model 'les-subgrid-{config.les_model}'")
                    solver.settings.setup.models.viscous.subgrid_scale_model = f"les-subgrid-{config.les_model}"
                else:
                    logger.warning(f"Subgrid model 'les-subgrid-{config.les_model}' not supported, using 'les-subgrid-wale' instead")                    
                    solver.settings.setup.models.viscous.subgrid_scale_model = "les-subgrid-wale"              

                if config.near_wall_rans_layer:
                    logger.info(f"Setting near_wall_rans_layer = {config.near_wall_rans_layer}")
                    solver.settings.setup.models.viscous.les_model_options.near_wall_rans_layer = config.near_wall_rans_layer

                if self.gpu:
                    if config.wall_use_second_cell:
                        logger.info("Setting second_cell_off_a_wall_quantities")
                        solver.settings.setup.models.viscous.near_wall_treatment.use_second_cell_off_a_wall_quantities = True

                    logger.info("Setting optimized LES numerics...")
                    solver.settings.solution.methods.set_optimized_les_numerics()
                    if config.central_scheme_pure:
                        logger.info("Setting Central Scheme with zero diffusion coefficient...")
                        solver.settings.solution.methods.spatial_discretization_parameters.low_diffusion_central.diffusion_coefficient = 0.

        # Setting solver methods
        logger.info("Setting up solver methods...")
        if "SIMPLEC" in solver.settings.solution.methods.p_v_coupling.flow_scheme.allowed_values():
            solver.settings.solution.methods.p_v_coupling.flow_scheme = "SIMPLEC"
        else:
            flow_scheme = solver.settings.solution.methods.p_v_coupling.flow_scheme()
            logger.info(f"'SIMPLEC' flow scheme not available, keeping original flow scheme: {flow_scheme}")
        solver.settings.solution.methods.gradient_scheme = "least-square-cell-based"
       
        if config.disable_temp_sec_grad:
            solver.execute_tui(r'''(rpsetvar 'temperature/secondary-gradient? #f)''')

        # Additional solver settings
        if config.auto_save_frequency > 0:
            # solver.settings.file.auto_save.root_name = "./jsm_case01_WB_F_ANSA_AOA-18.58-SST-URANS"
            solver.settings.file.auto_save.data_frequency = config.auto_save_frequency
            solver.settings.file.auto_save.retain_most_recent_files = True
            solver.settings.file.auto_save.max_files = 1

        # Adjust Convergence Criterium
        if not config.residual_convergence:
            logger.info("Setting up convergence criterium to 'none'...")
            solver.settings.solution.monitor.residual.options.criterion_type = 'none'
            #solver.settings.solution.monitor.convergence_conditions.convergence_reports.clear()
            for cr in solver.settings.solution.monitor.convergence_conditions.convergence_reports:
                solver.settings.solution.monitor.convergence_conditions.convergence_reports[cr].active = False

        # Adjust report-file
        logger.info("Adjusting report-file-names...")
        report_files = solver.settings.solution.monitor.report_files
        for rfile_name in report_files:
            rfile = report_files[rfile_name]
            org_file_name = rfile.file_name()
            file_path = get_valid_filepath(org_file_name)
            base_name, ext = os.path.splitext(file_path)
            rfile.file_name = f"{base_name}_p1{ext}"
            logger.info(f"Report-File changed: {org_file_name} to {rfile.file_name()}")
            rfile.frequency_of = 'time-step'
            old_defintion_list = rfile.report_defs()
            if 'flow-time' not in old_defintion_list:
                defintion_list = ['flow-time']
                defintion_list.extend(old_defintion_list)
                rfile.report_defs = defintion_list

        # if no report-file is available we create one
        if len(report_files) == 0:
            logger.info("No Report-File defined, creating a default report-file...")
            rfile_name = "report-file"
            solver.settings.solution.monitor.report_files[rfile_name] = {}
            rfile = report_files[rfile_name]
            rfile.file_name = "report_p1.out"
            rfile.report_defs = rfile.report_defs.allowed_values()

        # Adjust report definition plots
        logger.info("Adjusting report-definition plots...")
        report_plots = solver.settings.solution.monitor.report_plots
        for plot_name in report_plots:
            plot = report_plots[plot_name]
            plot.frequency_of = 'time-step'
            plot.x_label = 'flow-time'

        # Specify turbulence algorithm for all inlets
        if config.les_model:
            for bc_type in solver.settings.setup.boundary_conditions.get_active_child_names():
                if "inlet" in bc_type:
                    logger.info(f"Changing turbulent BCs of type '{bc_type}'")
                    bc_object = solver.settings.setup.boundary_conditions.find_object(bc_type)
                    for inlet_bc_name in bc_object.keys():
                        inlet_bc = bc_object[inlet_bc_name]
                        inlet_bc.turbulence.fluctuating_velocity_algorithm = config.turb_generator_option

        # Load PyUDFs
        if config.use_pyUDFs:
            logger.info("Loading specified PyUDFs...")
            pyUDF_string = ' '.join(f'"{pyUDF}"' for pyUDF in config.use_pyUDFs)
            solver.execute_tui(f'(gpuapp-add-udf {pyUDF_string})')
            solver.execute_tui(f'(gpuapp-list-udf)')
            logger.info("Loading specified PyUDFs... done!")

        logger.info("Adjust transient-settings...done")

    def run_phase_1(self, solver=None, config: TrnSimulationConfig = None, logger=None):
        """Run the first solution phase."""
        if solver is None:
            solver = self.solver
        if config is None:
            config = self.config
        if logger is None:
            logger = self.logger
        # Reset Timer
        logger.info("Resetting parallel timer...")
        solver.settings.parallel.timer.reset()
        # Calc timesteps per reference time
        time_step_per_rt_p1 = math.ceil(config.reference_time / config.time_step_size_p1)
        self.create_mcov_controller(solver=solver, config=config, time_step_per_rt_p1=time_step_per_rt_p1)
        solver.settings.solution.run_calculation.transient_controls.type = "Fixed"
        solver.settings.solution.run_calculation.transient_controls.method = "User-Specified"
        time_step_count = math.ceil(time_step_per_rt_p1 * config.num_ref_times_p1)
        logger.info(f"SP1: Number of Reference-Times (RT) = {config.num_ref_times_p1}")
        logger.info(f"SP1: Time-Steps per RT = {time_step_per_rt_p1}")
        logger.info(f"SP1: time-step-size = {config.time_step_size_p1}")
        logger.info(f"SP1: max time-step-count = {time_step_count}")
        solver.settings.solution.run_calculation.transient_controls.time_step_size = config.time_step_size_p1
        solver.settings.solution.run_calculation.transient_controls.time_step_count = time_step_count

        # Write setup to json-file
        setup_json_file = f"{config.base_filename}_setup_p1.json"
        logger.info(f"Exporting p1-setup to JSON file: {setup_json_file}")
        setup_dict = solver.settings.setup()
        with open(setup_json_file, 'w') as json_file:
            json.dump(setup_dict, json_file, indent=4)

        if config.create_setup_only:
            logger.warning(f"Only creating setup-file ('create_setup_only'=True), then exiting solver...")
            file_name = f"{config.base_filename}_p1"
            logger.info(f"SP1: Writing case- & dat-file: {file_name}")
            solver.settings.file.write(file_type="case-data", file_name=file_name)
            solver.exit()
            return 1
        if config.solver_monitor:
            logger.info("SP1: Starting Solver-Monitor...")
            solver.monitors.start
        if len(config.read_journal_p1) > 0:
            logger.info(f"SP1: Run Journals before solving: {config.read_journal_p1}")
            solver.settings.file.read_journal(file_name_list=config.read_journal_p1)
        # do ramp-up, if specified
        if isinstance(config.ramp_up_p1, dict):
            for rampup_time_step, rampup_time_step_count in config.ramp_up_p1.items(): 
                logger.info(f"SP1: Starting Ramp-up (time-step-size {rampup_time_step}s for {rampup_time_step_count} time-steps)")
                solver.settings.solution.run_calculation.transient_controls.time_step_size = rampup_time_step
                solver.settings.solution.run_calculation.dual_time_iterate(time_step_count=rampup_time_step_count,
                                                                    max_iter_per_step=config.max_iter_per_step) 
            logger.info("SP1: Ramp-ups finished")    
            solver.settings.solution.run_calculation.transient_controls.time_step_size = config.time_step_size_p1
            solver.settings.solution.run_calculation.transient_controls.time_step_count = time_step_count   
        
        # start solver    
        logger.info("SP1: Starting Solver...")
        solver.settings.solution.run_calculation.dual_time_iterate(time_step_count=time_step_count,
                                                                max_iter_per_step=config.max_iter_per_step)
        logger.info("SP1: Solver finished")
        solver.settings.parallel.timer.usage()
        solver.settings.results.report.system.print_system_statistics()
        if config.solver_monitor:
            logger.info("SP1: Exporting & Stopping Solver-Monitor...")
            export_solver_monitor(solver,filepath="residuals-p1.csv")
            solver.monitors.stop
        else:
            solver.execute_tui(r"""(write-residuals-to-file 'residuals-p1.xy)""")

        if config.write_data_p1:
            file_name = f"{config.base_filename}_p1_fin"
            logger.info(f"SP1: Writing case- & dat-file: {file_name}")
            solver.settings.file.write(file_type="case-data", file_name=file_name)

        logger.info("Solution Phase 1 (SP1)...done")

    def run_phase_2(self, solver=None, config: TrnSimulationConfig = None, logger=None):
        """Run the second solution phase."""
        if solver is None:
            solver = self.solver
        if config is None:
            config = self.config
        if logger is None:
            logger = self.logger
        logger.info("Starting Solution Phase 2 (SP2)...")
        # Reset Timer
        logger.info("Resetting parallel timer...")
        solver.settings.parallel.timer.reset()
        # Calc timesteps per reference time   
        time_step_per_rt_p2 = math.ceil(config.reference_time / config.time_step_size_p2)
        ## Adjust report-file-name
        logger.info("Adjusting report-file-names")
        report_files = solver.settings.solution.monitor.report_files
        for rfile_name in report_files:
            rfile = report_files[rfile_name]
            org_file_name = rfile.file_name()
            file_path = get_valid_filepath(org_file_name)
            base_name, ext = os.path.splitext(file_path)
            if "_p1" in base_name:
                base_name = base_name.replace("_p1", "_p2")
            else:
                base_name = f"{base_name}_p2"
            rfile.file_name = f"{base_name}{ext}"
            logger.info(f"Report-File changed: {org_file_name} to {rfile.file_name()}")
            rfile.frequency_of = 'time-step'
            old_defintion_list = rfile.report_defs()
            if 'flow-time' not in old_defintion_list:
                defintion_list = ['flow-time']
                defintion_list.extend(old_defintion_list)
                rfile.report_defs = defintion_list

        ## Disable MCOV criterium if specified
        if config.mcov_def_names:
            logger.info("Disable MCOV criterium")
            if Version(solver._version) < Version("252"):
                solver.settings.solution.calculation_activity.execute_commands.disable(command_name=config.mcov_command_name)
            else:
                mcov_exec_command = solver.settings.solution.calculation_activity.execute_commands[config.mcov_command_name]
                if mcov_exec_command is not None:
                    mcov_exec_command.enable = False

        ## Define Sampling
        logger.info("Enable sampling...")
        solver.settings.solution.run_calculation.data_sampling.enabled = True
        solver.settings.solution.run_calculation.data_sampling = {"force_statistics": False}    
        solver.settings.solution.run_calculation.data_sampling = {'flow_shear_stresses' : False, 'flow_heat_fluxes' : False}
        logger.info("Enable sampling...done")
        ## Define Sampling... done!

        time_step_count = math.ceil(time_step_per_rt_p2 * config.num_ref_times_p2)
        logger.info(f"SP2: Number of Reference-Times (RT) = {config.num_ref_times_p2}")
        logger.info(f"SP2: Time-Steps per RT = {time_step_per_rt_p2}")
        logger.info(f"SP2: time-step-size = {config.time_step_size_p2}")
        logger.info(f"SP2: max time-step-count = {time_step_count}")
        solver.settings.solution.run_calculation.transient_controls.time_step_size = config.time_step_size_p2

        # Write setup to json-file
        setup_json_file = f"{config.base_filename}_setup_p2.json"
        logger.info(f"Exporting p2-setup to JSON file: {setup_json_file}")
        setup_dict = solver.settings.setup()
        with open(setup_json_file, 'w') as json_file:
            json.dump(setup_dict, json_file, indent=4)

        if config.solver_monitor:
            logger.info("SP2: Starting Solver-Monitor...")
            solver.monitors.start
            
        # do ramp-up, if specified
        if isinstance(config.ramp_up_p2, dict):
            for rampup_time_step, rampup_time_step_count in config.ramp_up_p2.items(): 
                logger.info(f"SP2: Starting Ramp-up (time-step-size {rampup_time_step}s for {rampup_time_step_count} time-steps)")
                solver.settings.solution.run_calculation.transient_controls.time_step_size = rampup_time_step
                solver.settings.solution.run_calculation.dual_time_iterate(time_step_count=rampup_time_step_count,
                                                                    max_iter_per_step=config.max_iter_per_step) 
            logger.info("SP2: Ramp-ups finished")
            solver.settings.solution.run_calculation.transient_controls.time_step_size = config.time_step_size_p2
            solver.settings.solution.run_calculation.transient_controls.time_step_count = time_step_count   

        logger.info("SP2: Starting Solver...")
        solver.settings.solution.run_calculation.dual_time_iterate(
            time_step_count=time_step_count, max_iter_per_step=config.max_iter_per_step
        )
        logger.info("SP2: Solver finished")
        solver.settings.parallel.timer.usage()  
        solver.settings.results.report.system.print_system_statistics()      
        if config.solver_monitor:
            logger.info("SP2: Exporting & Stopping Solver-Monitor...")
            export_solver_monitor(solver=solver, filepath="residuals-p2.csv")
            solver.monitors.stop
        else:
            solver.execute_tui(r"""(write-residuals-to-file 'residuals-p2.xy)""")       
        
        # Write final cas- & dat-file
        file_name = f"{config.base_filename}_p2_fin"
        logger.info(f"SP2: Writing case- & dat-file: {file_name}")
        solver.settings.file.write(file_type="case-data", file_name=file_name)
        logger.info("Solution Phase 2 (SP2)...done")

    def run_postprocessing(self, solver=None, config: TrnSimulationConfig = None, logger=None):
        """Run the postprocessing phase."""     
        if solver is None:
            solver = self.solver
        if config is None:
            config = self.config
        if logger is None:
            logger = self.logger
        # Solution export of statistical data to cfdpost
        if config.export_cfdpost:
            cfdpost_filename = f"{config.base_filename}_p2_fin_cfdpost"
            logger.info(f"SP2: Exporting of statistical data to CFDPost: {cfdpost_filename}")
            availableFieldDataNames = (
                solver.fields.field_data.get_scalar_field_data.field_name.allowed_values()
            )
            statistics_fields = [s for s in availableFieldDataNames if s.startswith("mean") or s.startswith("rsme")]
            solver.tui.file.export.cdat_for_cfd_post__and__ensight(cfdpost_filename, '()', '*', '()', *statistics_fields)

        # Run Fluent Postprocessing
        if len(config.do_postprocessing) > 0:
            logger.info(f"SP2: Run Fluent Postprocessing: {config.do_postprocessing}")
            solver.settings.file.read_journal(file_name_list=config.do_postprocessing)
            # Save case with pp-settings
            if config.write_case_after_pp:
                file_name = f"{config.base_filename}_p2_fin_postprocessed"
                logger.info(f"SP2: Writing case-file with pp-settings: {file_name}")
                solver.settings.file.write(file_type="case", file_name=file_name)

    def run_solution(self, solver=None, config: TrnSimulationConfig = None, logger=None):
        """Run the solution process."""
        if solver is None:
            solver = self.solver
        if config is None:
            config = self.config
        if logger is None:
            logger = self.logger
        if solver is None:
            logger.error("solver variable not set... exiting script")
            return 0

        # Initialize run
        self.initialize_run()
        
        if config.restart_filename:
            logger.info(f"Reading restart-file: {config.restart_filename}")
            solver.settings.file.read_case_data(file_name=config.restart_filename)

        # Activate Beta Features
        logger.info("Enabling Beta Features...")
        solver.settings.file.beta_settings(enable=True)

        # RANS Phase
        if config.rans_iterations > 0:
            self.run_rans()

        if config.skip_srs_settings:
            logger.warning("Skipping srs-settings, directly going to solution phase!")
        else:
            self.adjust_transient_settings()

        # Solution Phase 1
        if config.skip_p1:
            logger.info("Skipping Solution Phase 1 (SP1)...")
        else:
            self.run_phase_1()
            
        # Solution Phase 2
        self.run_phase_2()   
        
        # Postprocessing
        self.run_postprocessing()
                
        logger.info(f"Script 'srs_solution' successfully finished")
        # Exit Solver
        # solver.exit()
        return 1
