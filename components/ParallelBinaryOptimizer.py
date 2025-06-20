import multiprocessing.sharedctypes
import matplotlib.pyplot
import multiprocessing
import pathlib
import logging
import ctypes
import numpy
import tqdm
import math

from components.RunConfiguration import RunConfiguration
from components.utils.process_statuses import ProcessStatus
from components.DynamicThrustModel import DynamicThrustModel

class ParallelBinaryOptimizer:
    n_processes: int
    
    status_counters: list[multiprocessing.sharedctypes.Synchronized]
    position_counters: list[multiprocessing.sharedctypes.Synchronized]
    velocity_counters: list[multiprocessing.sharedctypes.Synchronized]
    acceleration_counters: list[multiprocessing.sharedctypes.Synchronized]
    time_counters: list[multiprocessing.sharedctypes.Synchronized]
    thrust_counters: list[multiprocessing.sharedctypes.Synchronized]
    drag_counters: list[multiprocessing.sharedctypes.Synchronized]
    
    progress_bars: list[tqdm.tqdm]
    
    def __init__(self, n_processes: int) -> None:
        self.n_processes = n_processes
        
        self.status_counters = list()
        self.position_counters = list()
        self.velocity_counters = list()
        self.acceleration_counters = list()
        self.time_counters = list()
        self.thrust_counters = list()
        self.drag_counters = list()

        self.main_progress_indicator = tqdm.tqdm(bar_format='{desc} | Elapsed: {elapsed} | Epoch: {n} / ~{total}', desc=f'Optimizing for MTOW | Config: -', position=0, leave=True)
        self.progress_bars = list()
        
        for i in range(self.n_processes):
            self.status_counters.append(multiprocessing.Value(ctypes.c_byte, 0))
            self.position_counters.append(multiprocessing.Value(ctypes.c_double, 0))
            self.velocity_counters.append(multiprocessing.Value(ctypes.c_double, 0))
            self.acceleration_counters.append(multiprocessing.Value(ctypes.c_double, 0))
            self.time_counters.append(multiprocessing.Value(ctypes.c_double, 0))
            self.thrust_counters.append(multiprocessing.Value(ctypes.c_double, 0))
            self.drag_counters.append(multiprocessing.Value(ctypes.c_double, 0))
            
            self.progress_bars.append(
                tqdm.tqdm(
                    total=0,
                    position=i+1,
                    desc=f'Process {i} | m = - kg |  [{ProcessStatus.OPTIMIZER_SETUP}]',
                    leave=True,
                    postfix=f't = 0 s | x = 0 m | v = 0 m/s | a = 0 m/s^2 | T = 0 N | D = 0 N'
                )
            )
    
    def run(self, run_configuration: RunConfiguration) -> None:
        process_with_maximum_accepted_mass = None

        minimum = run_configuration.mass_range[0]
        maximum = run_configuration.mass_range[1]

        config_identifier = run_configuration.identifier
        config_masses = f'({", ".join(f"{mass_bound:.2f}" for mass_bound in run_configuration.mass_range)})'
        config_displacements = f'({", ".join(f"{displacement_bound:.2f}" for displacement_bound in run_configuration.cutoff_displacement)})'
        
        mass_range = run_configuration.mass_range[1] - run_configuration.mass_range[0]
        tolerance = run_configuration.cutoff_displacement[1] - run_configuration.cutoff_displacement[0]
        intervals = self.n_processes-1
        
        self.main_progress_indicator.total = int(math.ceil(math.log((mass_range) / (tolerance), intervals)))
        
        self.main_progress_indicator.set_description_str(
            f'Optimizing for MTOW | Config[{config_identifier}]: m={config_masses} kg ~ x={config_displacements} m'
        )
        
        while True:
            MASS_SPACE = numpy.linspace(minimum, maximum, self.n_processes)
            processes: list[multiprocessing.Process] = list()

            PROCESS_PADDING = len(str(self.n_processes-1))
            MASS_PADDING = max([len(f'{mass:.2f}') for mass in MASS_SPACE])
            
            for i in range(self.n_processes):
                self.status_counters[i].value = 0
                self.position_counters[i].value = 0
                self.velocity_counters[i].value = 0
                self.acceleration_counters[i].value = 0
                self.time_counters[i].value = 0
                self.thrust_counters[i].value = 0
                self.drag_counters[i].value = 0
                
                self.progress_bars[i].total = run_configuration.cutoff_displacement[0]
                self.progress_bars[i].set_description_str(f'Process {i:>{PROCESS_PADDING}} | m = {MASS_SPACE[i]:>{MASS_PADDING}.2f} kg | [{ProcessStatus.FORKING_PROCESS}]')
                self.progress_bars[i].set_postfix_str(f't = 0 s | x = 0 m | v = 0 m/s | a = 0 m/s^2 | T = 0 N | D = 0 N')
                
                processes.append(
                    multiprocessing.Process(
                        target=DynamicThrustModel.simulate_dynamics_given_mass,
                        args=(
                            run_configuration,
                            MASS_SPACE[i],
                            self.status_counters[i],
                            self.position_counters[i],
                            self.velocity_counters[i],
                            self.acceleration_counters[i],
                            self.time_counters[i],
                            self.thrust_counters[i],
                            self.drag_counters[i],
                        )
                    )
                )
            
            for process in processes:
                process.start()
            
            while any(process.is_alive() for process in processes):
                self.main_progress_indicator.refresh()
                
                local_time_counters = list()
                local_position_counters = list()
                local_velocity_counters = list()
                local_acceleration_counters = list()
                local_thrust_counters = list()
                local_drag_counters = list()
                
                for i in range(self.n_processes):
                    with self.status_counters[i].get_lock():
                        self.progress_bars[i].set_description_str(f'Process {i:>{PROCESS_PADDING}} | m = {MASS_SPACE[i]:>{MASS_PADDING}.2f} kg | [{ProcessStatus.get(self.status_counters[i].value)}]')
                    with self.position_counters[i].get_lock():
                        self.progress_bars[i].n = int(min(self.position_counters[i].value, run_configuration.cutoff_displacement[0]))
                        self.progress_bars[i].last_print_n = int(min(self.position_counters[i].value, run_configuration.cutoff_displacement[0]))
                        with self.velocity_counters[i].get_lock():
                            with self.acceleration_counters[i].get_lock():
                                with self.time_counters[i].get_lock():
                                    with self.thrust_counters[i].get_lock():
                                        with self.drag_counters[i].get_lock():
                                            local_time_counters.append(f'{self.time_counters[i].value:.2f}')
                                            local_position_counters.append(f'{self.position_counters[i].value:.2f}')
                                            local_velocity_counters.append(f'{self.velocity_counters[i].value:.2f}')
                                            local_acceleration_counters.append(f'{self.acceleration_counters[i].value:.2f}')
                                            local_thrust_counters.append(f'{self.thrust_counters[i].value:.2f}')
                                            local_drag_counters.append(f'{self.drag_counters[i].value:.2f}')
                
                TIME_COUNTER_PADDING = max([len(string) for string in local_time_counters])
                POSITION_COUNTER_PADDING = max([len(string) for string in local_position_counters])
                VELOCITY_COUNTER_PADDING = max([len(string) for string in local_velocity_counters])
                ACCELERATION_COUNTER_PADDING = max([len(string) for string in local_acceleration_counters])
                THRUST_COUNTER_PADDING = max([len(string) for string in local_thrust_counters])
                DRAG_COUNTER_PADDING = max([len(string) for string in local_drag_counters])
                
                for i in range(self.n_processes):
                    self.progress_bars[i].set_postfix_str(
                        f't = {local_time_counters[i]:>{TIME_COUNTER_PADDING}} s'
                        f' | '
                        f'x = {local_position_counters[i]:>{POSITION_COUNTER_PADDING}} m'
                        f' | '
                        f'v = {local_velocity_counters[i]:>{VELOCITY_COUNTER_PADDING}} m/s'
                        f' | '
                        f'a = {local_acceleration_counters[i]:>{ACCELERATION_COUNTER_PADDING}} m/s^2'
                        f' | '
                        f'T = {local_thrust_counters[i]:>{THRUST_COUNTER_PADDING}} N'
                        f' | '
                        f'D = {local_drag_counters[i]:>{DRAG_COUNTER_PADDING}} N'
                    )
            
            for process in processes:
                process.join()
            
            for i in range(self.n_processes):
                if self.status_counters[i].value == ProcessStatus.SUCCESS_TAKEOFF.value and MASS_SPACE[i] >= minimum:
                    minimum = MASS_SPACE[i]
                    process_with_maximum_accepted_mass = i
                
                j = self.n_processes-1-i
                if self.status_counters[j].value > ProcessStatus.SUCCESS_TAKEOFF.value and MASS_SPACE[j] <= maximum:
                    maximum = MASS_SPACE[j]
            
            if process_with_maximum_accepted_mass is None:
                return self.cleanup_return()
            else:
                takeoff_above_cutoff_lowerbound = self.position_counters[process_with_maximum_accepted_mass].value > run_configuration.cutoff_displacement[0]
                takeoff_below_cutoff_upperbound = self.position_counters[process_with_maximum_accepted_mass].value < run_configuration.cutoff_displacement[1]
            
            if process_with_maximum_accepted_mass == self.n_processes-1:
                return self.cleanup_return(-MASS_SPACE[process_with_maximum_accepted_mass], run_configuration)
            elif takeoff_above_cutoff_lowerbound and takeoff_below_cutoff_upperbound:
                return self.cleanup_return(MASS_SPACE[process_with_maximum_accepted_mass], run_configuration)
            
            self.main_progress_indicator.update(1)
    
    def cleanup_return(self, mass: numpy.float64 | None = None, run_configuration: RunConfiguration | None = None) -> None:
        self.main_progress_indicator.close()
        for progress_bar in self.progress_bars:
            progress_bar.close()
        
        if mass is None:
            logging.error(f'MTOM cannot be found within the given range: the minimum mass provided is too high.')
        else:
            local_solution = mass < 0
            if local_solution: mass = -mass
            
            stall_velocity = run_configuration.get_stall_velocity(mass)
            
            logging.info(f'STALL_VELOCITY = {stall_velocity:.2f} m/s | MTOM = {mass:.3f} kg')
            
            if local_solution:
                logging.warning(f'* MTOM was only found locally: the maximum mass provided is too low.')
            
            best_run_data = numpy.load(f'{run_configuration.identifier}/{run_configuration.identifier}-{mass:.16f}.npz')
            time = best_run_data['t'][:-1]
            acceleration = best_run_data['a']
            velocity = best_run_data['v'][:-1]
            position = best_run_data['x'][:-1]
            thrust = best_run_data['T']
            drag = best_run_data['D']
            
            run_file_paths = list(pathlib.Path(run_configuration.identifier).rglob('*.npz'))
            
            performance_characteristics = list()
            for run_file_path in run_file_paths:
                run_data = numpy.load(run_file_path)
                performance_characteristics.append((run_data['mass'], run_data['stall_velocity'], run_data['v'][-2]))
            
            performance_characteristics.sort(key=lambda e: e[0])
            masses, stall_velocities, velocities = zip(*performance_characteristics)
            stall_velocities = numpy.array(stall_velocities, dtype=numpy.float64)
            velocities = numpy.array(velocities, dtype=numpy.float64)
            masses = numpy.array(masses, dtype=numpy.float64)
            
            _, axes = matplotlib.pyplot.subplots(3, 2, figsize=(10, 8))
            
            axes[0, 0].plot(time, position, label='Position', color='black')
            axes[0, 0].set_title('Position vs Time')
            axes[0, 0].set_xlabel('Time (s)')
            axes[0, 0].set_ylabel('Position (m)')
            axes[0, 0].grid(True)

            axes[0, 1].plot(time, velocity, label='Velocity', color='black')
            axes[0, 1].set_title('Velocity vs Time')
            axes[0, 1].set_xlabel('Time (s)')
            axes[0, 1].set_ylabel('Velocity (m/s)')
            axes[0, 1].grid(True)

            axes[1, 0].plot(time, acceleration, label='Acceleration', color='black')
            axes[1, 0].set_title('Acceleration vs Time')
            axes[1, 0].set_xlabel('Time (s)')
            axes[1, 0].set_ylabel('Acceleration (m/s^2)')
            axes[1, 0].grid(True)

            axes[1, 1].plot(time, thrust, label='Thrust', color='black')
            axes[1, 1].set_title('Thrust vs Time')
            axes[1, 1].set_xlabel('Time (s)')
            axes[1, 1].set_ylabel('Thrust (N)')
            axes[1, 1].grid(True)

            axes[2, 0].plot(time, drag, label='Drag', color='black')
            axes[2, 0].set_title('Drag vs Time')
            axes[2, 0].set_xlabel('Time (s)')
            axes[2, 0].set_ylabel('Drag (N)')
            axes[2, 0].grid(True)

            axes[2, 1].plot(masses, velocities, label='Final Velocity', color='black')
            axes[2, 1].plot(masses, stall_velocities, label='Stall Velocity', color='red', linestyle='--')
            axes[2, 1].set_title('Performance Curve')
            axes[2, 1].set_xlabel('Mass (kg)')
            axes[2, 1].set_ylabel('Velocity (m/s)')
            axes[2, 1].set_xscale('log')
            axes[2, 1].grid(True)
            axes[2, 1].legend()
            
            matplotlib.pyplot.tight_layout()
            matplotlib.pyplot.savefig(f'{run_configuration.identifier}/{run_configuration.identifier}-{mass:.3f}kg-{stall_velocity:.2f}mps.png', dpi=300)
            matplotlib.pyplot.close()
