import multiprocessing.sharedctypes
import multiprocessing
import ctypes
import numpy
import tqdm

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
                    initial=0,
                    position=i,
                    desc=f'Process {i} | m = - kg |  [{ProcessStatus.SLEEPING}]',
                    leave=True,
                    postfix=f't = 0 s | x = 0 m | v = 0 m/s | a = 0 m/s^2 | T = 0 N | D = 0 N'
                )
            )
    
    def run(self, run_configuration: RunConfiguration) -> None:
        process_with_maximum_accepted_mass = None

        minimum = run_configuration.mass_range[0]
        maximum = run_configuration.mass_range[1]
        
        while True:
            MASS_SPACE = numpy.linspace(minimum, maximum, self.n_processes)
            processes: list[multiprocessing.Process] = list()
            
            for i in range(self.n_processes):
                self.status_counters[i].value = 0
                self.position_counters[i].value = 0
                self.velocity_counters[i].value = 0
                self.acceleration_counters[i].value = 0
                self.time_counters[i].value = 0
                self.thrust_counters[i].value = 0
                self.drag_counters[i].value = 0
                
                self.progress_bars[i].total = run_configuration.cutoff_displacement[0]
                self.progress_bars[i].set_description_str(f'Process {i} | m = {MASS_SPACE[i]:.2f} kg |  [{ProcessStatus.STARTING}]')
                self.progress_bars[i].set_postfix_str(f't = 0 s | x = 0 m | v = 0 m/s | a = 0 m/s^2 | T = 0 N | D = 0 N')
                
                processes.append(
                    multiprocessing.Process(
                        target=DynamicThrustModel.thrust_vs_time_given_mass,
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
                for i in range(self.n_processes):
                    with self.status_counters[i].get_lock():
                        self.progress_bars[i].set_description_str(f'Process {i} | m = {MASS_SPACE[i]:.2f} kg |  [{ProcessStatus.get(self.status_counters[i].value)}]')
                    with self.position_counters[i].get_lock():
                        self.progress_bars[i].n = int(min(self.position_counters[i].value, run_configuration.cutoff_displacement[0]))
                        self.progress_bars[i].last_print_n = int(min(self.position_counters[i].value, run_configuration.cutoff_displacement[0]))
                        with self.velocity_counters[i].get_lock():
                            with self.acceleration_counters[i].get_lock():
                                with self.time_counters[i].get_lock():
                                    with self.thrust_counters[i].get_lock():
                                        with self.drag_counters[i].get_lock():
                                            self.progress_bars[i].set_postfix_str(
                                                f't = {self.time_counters[i].value:.2f} s'
                                                f' | '
                                                f'x = {self.position_counters[i].value:.2f} m'
                                                f' | '
                                                f'v = {self.velocity_counters[i].value:.2f} m/s'
                                                f' | '
                                                f'a = {self.acceleration_counters[i].value:.2f} m/s^2'
                                                f' | '
                                                f'T = {self.thrust_counters[i].value:.2f} N'
                                                f' | '
                                                f'D = {self.drag_counters[i].value:.2f} N'
                                            )
            
            for process in processes:
                process.join()
            
            for i in range(self.n_processes):
                if ProcessStatus.get(self.status_counters[i].value) == ProcessStatus.ACCEPTED and MASS_SPACE[i] > minimum:
                    minimum = MASS_SPACE[i]
                    process_with_maximum_accepted_mass = i
                if ProcessStatus.get(self.status_counters[self.n_processes-1-i].value) == ProcessStatus.REJECTED and MASS_SPACE[i] < maximum:
                    maximum = MASS_SPACE[i]
            
            takeoff_position_within_spec = self.position_counters[i].value > run_configuration.cutoff_displacement[0] and self.position_counters[i].value < run_configuration.cutoff_displacement[1]
            if process_with_maximum_accepted_mass is None:
                for progress_bar in self.progress_bars:
                    progress_bar.close()
                print('MINIMUM IS ABOVE MAXIMUM ALLOWABLE MASS')
                return#! MINIMUM IS ABOVE MAXIMUM ALLOWABLE MASS
            elif process_with_maximum_accepted_mass == self.n_processes-1:
                for progress_bar in self.progress_bars:
                    progress_bar.close()
                print('MAXIMUM IS BELOW MAXIMUM ALLOWABLE MASS')
                return#! MAXIMUM IS BELOW MAXIMUM ALLOWABLE MASS
            elif takeoff_position_within_spec:
                for progress_bar in self.progress_bars:
                    progress_bar.close()
                print('SUCCESS')
                return#! SUCCESS!
