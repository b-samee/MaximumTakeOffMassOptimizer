import multiprocessing.sharedctypes
import multiprocessing
import logging
import ctypes
import numpy
import tqdm

from components.RunConfiguration import RunConfiguration
from components.utils.process_statuses import ProcessStatus
from components.ConstantMassDynamicsSimulation import ConstantMassDynamicsSimulation
from components.utils.result_states import ResultState
from components.ConstantMassDynamicsModel import ConstantMassDynamicsModel

class MaximumTakeOffMassOptimizer:
    n_processes: int
    
    status_counters: list[multiprocessing.sharedctypes.Synchronized]
    position_counters: list[multiprocessing.sharedctypes.Synchronized]
    velocity_counters: list[multiprocessing.sharedctypes.Synchronized]
    acceleration_counters: list[multiprocessing.sharedctypes.Synchronized]
    time_counters: list[multiprocessing.sharedctypes.Synchronized]
    thrust_counters: list[multiprocessing.sharedctypes.Synchronized]
    drag_counters: list[multiprocessing.sharedctypes.Synchronized]
    
    progress_bars: list[tqdm.tqdm]

    results: dict[numpy.float64, ConstantMassDynamicsModel] | None
    
    def __init__(self, n_processes: int) -> None:
        self.n_processes = n_processes
        
        self.status_counters = list()
        self.position_counters = list()
        self.velocity_counters = list()
        self.acceleration_counters = list()
        self.time_counters = list()
        self.thrust_counters = list()
        self.drag_counters = list()

        self.main_progress_indicator = tqdm.tqdm(bar_format='{desc} | Elapsed: {elapsed} | Epoch: {n}', desc=f'Optimizing for MTOW | Config: -', position=0, initial=1, leave=True)
        self.progress_bars = list()

        self.results = None
        
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
        config_masses = f'[{", ".join(f"{mass_bound:.{run_configuration.arithmetic_precision}f}" for mass_bound in run_configuration.mass_range)}]'
        config_displacements = run_configuration.takeoff_displacement
        
        self.main_progress_indicator.set_description_str(
            f'Optimizing for MTOW | Config[{config_identifier}]: m={config_masses} kg ~ x={config_displacements} m'
        )
        
        self.results = dict()
        results_queue = multiprocessing.Queue(maxsize=self.n_processes)
        
        backup_minimum = numpy.round(numpy.float64(minimum), run_configuration.arithmetic_precision)
        backup_maximum = numpy.round(numpy.float64(maximum), run_configuration.arithmetic_precision)

        PRECISION_MULTIPLIER = 10**run_configuration.arithmetic_precision
        
        MASS_SPACE = numpy.linspace(minimum, maximum, self.n_processes)
        while True:
            MASS_SPACE = numpy.round(MASS_SPACE, run_configuration.arithmetic_precision)
            if int(MASS_SPACE[-1]*PRECISION_MULTIPLIER)-int(MASS_SPACE[0]*PRECISION_MULTIPLIER) <= 1:
                return self.cleanup_return(ResultState.MTOM_FOUND, MASS_SPACE[0], run_configuration)
            
            processes: list[multiprocessing.Process] = list()

            PROCESS_PADDING = len(str(self.n_processes-1))
            MASS_PADDING = max([len(f'{mass:.{run_configuration.arithmetic_precision}f}') for mass in MASS_SPACE])
            
            for i in range(self.n_processes):
                self.status_counters[i].value = 0
                self.position_counters[i].value = 0
                self.velocity_counters[i].value = 0
                self.acceleration_counters[i].value = 0
                self.time_counters[i].value = 0
                self.thrust_counters[i].value = 0
                self.drag_counters[i].value = 0
                
                self.progress_bars[i].total = run_configuration.takeoff_displacement
                self.progress_bars[i].set_description_str(f'Process {i:>{PROCESS_PADDING}} | m = {MASS_SPACE[i]:>{MASS_PADDING}.{run_configuration.arithmetic_precision}f} kg | [{ProcessStatus.FORKING_PROCESS}]')
                self.progress_bars[i].set_postfix_str(f't = 0 s | x = 0 m | v = 0 m/s | a = 0 m/s^2 | T = 0 N | D = 0 N')
                
                processes.append(
                    multiprocessing.Process(
                        target=ConstantMassDynamicsSimulation.simulate_dynamics_given_mass,
                        args=(
                            run_configuration,
                            MASS_SPACE[i],
                            results_queue,
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
                        self.progress_bars[i].set_description_str(f'Process {i:>{PROCESS_PADDING}} | m = {MASS_SPACE[i]:>{MASS_PADDING}.{run_configuration.arithmetic_precision}f} kg | [{ProcessStatus.get(self.status_counters[i].value)}]')
                    with self.position_counters[i].get_lock():
                        self.progress_bars[i].n = min(self.position_counters[i].value, run_configuration.takeoff_displacement)
                        self.progress_bars[i].last_print_n = min(self.position_counters[i].value, run_configuration.takeoff_displacement)
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
            
                while not results_queue.empty():
                    dynamics_model: ConstantMassDynamicsModel = results_queue.get()
                    if dynamics_model.mass not in self.results:
                        self.results[dynamics_model.mass] = dynamics_model
            
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
                if backup_minimum < MASS_SPACE[0]:
                    MASS_SPACE = numpy.linspace(backup_minimum, MASS_SPACE[0], self.n_processes+2)[1:-1]
                    backup_maximum = MASS_SPACE[0]
                else:
                    return self.cleanup_return(ResultState.MASS_LOWERBOUND_BEYOND_MTOM)
            if process_with_maximum_accepted_mass == self.n_processes-1:
                if backup_maximum > MASS_SPACE[-1]:
                    MASS_SPACE = numpy.linspace(MASS_SPACE[-1], backup_maximum, self.n_processes+2)[1:-1]
                    backup_minimum = MASS_SPACE[-1]
                else:
                    return self.cleanup_return(ResultState.MASS_UPPERBOUND_BELOW_MTOM, MASS_SPACE[process_with_maximum_accepted_mass], run_configuration)
            else:
                MASS_SPACE = numpy.linspace(minimum, maximum, self.n_processes+2)[1:-1]
                backup_minimum = minimum
                backup_maximum = maximum
            
            self.main_progress_indicator.update(1)
    
    def cleanup_return(self, result_state: ResultState, mass: numpy.float64 | None = None, run_configuration: RunConfiguration | None = None) -> None:
        self.main_progress_indicator.close()
        for progress_bar in self.progress_bars:
            progress_bar.close()
        
        if result_state == ResultState.MASS_LOWERBOUND_BEYOND_MTOM:
            logging.error(f'MTOM cannot be found within the given range: the minimum mass provided is too high.')
            return
        elif result_state == ResultState.MASS_UPPERBOUND_BELOW_MTOM:
            logging.warning(f'MTOM was only found locally: the maximum mass provided is too low.')
        
        optimal_dynamics_model = self.results[mass]
        
        if optimal_dynamics_model.get_position_takeoff() > run_configuration.takeoff_displacement:
            logging.warning(f'MTOM found may not be accurate: simulation timestep size ({run_configuration.timestep_size}) may be too large.')
        
        logging.info(f'STALL_VELOCITY = {optimal_dynamics_model.stall_velocity:.{run_configuration.arithmetic_precision}f} m/s | MTOM = {mass:.{run_configuration.arithmetic_precision}f} kg | LIFTOFF_DISTANCE = {optimal_dynamics_model.get_position_takeoff()} m')
        
        optimal_dynamics_model.plot_model(f'{run_configuration.identifier}-dt={run_configuration.timestep_size}-xf={optimal_dynamics_model.get_position_takeoff()}-m={mass:.{run_configuration.arithmetic_precision}f}-vf={optimal_dynamics_model.get_velocity_takeoff():.{run_configuration.arithmetic_precision}f}', self.results)
