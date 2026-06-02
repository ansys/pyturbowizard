import numpy as np
import os

version = "1.4"

def calculate_stddev(numbers):
    if len(numbers) == 0:
        return None  # Return None if the array is empty

    # Calculate the standard deviation
    std_dev = np.std(numbers)

    return std_dev


def calculate_mean(numbers):
    if len(numbers) == 0:
        return None  # Return None if the array is empty

    # Calculate the mean
    mean = np.mean(numbers)

    return mean


def compute_surface_report(def_name: str):
    if (
            def_name
            not in solver.settings.solution.report_definitions.surface.get_object_names()
    ):
        return None

    compute_object = solver.settings.solution.report_definitions.compute(
        report_defs=def_name
    )[0]
    value = float(compute_object[def_name][0])
    return value

def do_convergence_check(value, conv_crit):
    if isinstance(value, float) and value <= conv_crit:
        print(
            f"Convergence reached! |{value}| <= Convergence Criterion: {conv_crit}"
        )
        solver.settings.solution.run_calculation.interrupt()
        return True
    else:
        return False

class MCoV:
    def __init__(
            self, def_name: str, avg_interval=5, mcov_interval=None, conv_crit=1.0e-5, log_file: str = None
    ):
        self.value_array = np.array([])
        self.mean_array = np.array([])
        self.avg_interval = avg_interval
        self.mcov_interval = mcov_interval
        if mcov_interval is None:
            self.mcov_interval = avg_interval
        self.def_name = def_name
        self.conv_crit = conv_crit
        self.log_file = log_file
        self.init_log_file()

    def init_log_file(self, delete_existing=True):
        # Remove the old log file if it exists
        if delete_existing and self.log_file and os.path.exists(self.log_file):
            os.remove(self.log_file)
        # Write header if log_file is specified and it doesn't exist
        if self.log_file and not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                f.write(
                    "update_index, current_value, mean_value, mcov\n")

    def update_data(self, current_value=None,check_convergence=True):
        mean = None
        if current_value is None:
            current_value = compute_surface_report(def_name=self.def_name)
        if current_value is not None:
            # Removing the first element of the array if it's equal/bigger than the specified avg_interval
            if len(self.value_array) >= self.avg_interval:
                self.value_array = self.value_array[1:]
            # Removing the first element of the array if it's equal/bigger than the specified mcov_interval
            if len(self.mean_array) >= self.mcov_interval:
                self.mean_array = self.mean_array[1:]
            self.value_array = np.append(self.value_array, current_value)
            if len(self.value_array) == self.avg_interval:
                mean = calculate_mean(self.value_array)
                self.mean_array = np.append(self.mean_array, mean)

        # Calc mcov-value
        mcov = self.calc_mcov()

        # Log the process if log_file is specified
        if self.log_file:
            with open(self.log_file, 'a') as f:
                index = sum(1 for line in open(self.log_file))
                f.write(f"{index}, {current_value}, {mean}, {mcov}\n")

        # Check Convergence
        if check_convergence:
            do_convergence_check(value=mcov,conv_crit=self.conv_crit)

        return mean

    def calc_deri(self, abs_value=True):
        mean_deri = None
        if len(self.value_array) == self.avg_interval and len(self.mean_array) > 2:
            curr_mean = calculate_mean(self.value_array)
            prev_mean = self.mean_array[-2]
            mean_deri = (
                (curr_mean - prev_mean) / abs(curr_mean)
                if curr_mean != 0
                else float("inf")
            )  # Handle division by zero
            # if check_convergence and (abs(mean_deri) <= self.conv_crit):
            #     print(
            #         f"Convergence reached! Mean-Gradient: |{mean_deri}| <= Convergence Criterion: {self.conv_crit}"
            #     )
            #     solver.settings.solution.run_calculation.interrupt()
        if mean_deri is not None and abs_value:
            return abs(mean_deri)
        return mean_deri

    def calc_mcov(self):
        cov = None
        if len(self.mean_array) == self.mcov_interval:
            mean = calculate_mean(self.mean_array)
            std = calculate_stddev(self.mean_array)
            if std is not None and mean != 0:
                cov = std / abs(mean)
            else:
                cov = float("inf")  # Handle division by zero or None std_dev
        return cov


# Example usage
# mcov_def_name = "my_report_definition"
# mcov_avg_interval = 5
# mcov_con_crit = 1e-4
# mcov_log_file = "mcov.log"
# rm = MCoV(def_name=mcov_def_name, conv_crit=mcov_con_crit, avg_interval=mcov_avg_interval,
#                   log_file=mcov_log_file)
# Include a python execute-command (repeat)
# command_name = "mcov_update"
# mcov_update_freq = 1000
# mcov_update_method = "time-step"
# command = "rm.update_data()"
# solver.tui.solve.execute_commands.add_edit(
#     command_name, "no", mcov_update_freq, mcov_update_method, "yes", f'"{command}"'
# )

