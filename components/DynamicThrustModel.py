import multiprocessing.sharedctypes
import matplotlib.pyplot
import multiprocessing
import numpy
import pathlib
import subprocess
import copy
import tqdm
import ctypes
import logging
import io

from components.utils.type_aliases import RunConfiguration, Pairing

class DynamicThrustModel:
    run_configuration: RunConfiguration
    configuration_designation: str
    
    def __init__(self, run_configuration: RunConfiguration, configuration_designation: str) -> None:
        self.run_configuration = run_configuration
        self.configuration_designation = configuration_designation
    
    
    
    def qprop_task(self, counter: multiprocessing.sharedctypes.Synchronized, pairing: Pairing, throttle: numpy.float64) -> None:
        with counter.get_lock():
            counter.value = 1
        
        setpoint_copy = copy.deepcopy(self.run_configuration['setpoint'])
        setpoint_copy['voltage'] = numpy.multiply(setpoint_copy['voltage'], throttle)
        setpoint_string = ' '.join([str(value) for value in setpoint_copy.values()])
        
        propeller_file = pairing['propeller']
        motor_file = pairing['motor']
        
        with counter.get_lock():
            counter.value = 2
        
        completed_process = subprocess.run(f'qprop {propeller_file} {motor_file} {setpoint_string}', capture_output=True, text=True)
        data_stream = io.StringIO(completed_process.stdout)
        data = numpy.loadtxt(data_stream, skiprows=17)

        output = {
            'freestream': data[:, 0],
            'rpm':        data[:, 1],
            'thrust':     data[:, 3],
            'torque':     data[:, 4],
            'voltage':    data[:, 6],
            'current':    data[:, 7],
        }
        
        throttle_limit = None
        for current in output['current']:
            if current >= self.run_configuration['current_limit'] and throttle_limit is None:
                throttle_limit = throttle
        
        with counter.get_lock():
            counter.value = 3
        
        self.plot(output, throttle_limit, propeller_file.stem, motor_file.stem)
        
        with counter.get_lock():
            counter.value = 4
    
    
    
    def run(self) -> None:
        STATE_MESSAGES = ["Preparing Task", "Started Task", "Executing QPROP", "Generating Plots", "Finished Task"]
        
        logger = logging.getLogger()
        
        n_pairing_tests = len(self.run_configuration['pairings'])
        for test_n in range(n_pairing_tests):
            pairing = self.run_configuration['pairings'][test_n]
            logger.info(f'Executing run {self.run_configuration["index"]} pairing {test_n+1}/{n_pairing_tests} ({pairing["propeller"].stem} x {pairing["motor"].stem})')
            
            throttle = numpy.linspace(0.1, 1.0, 10)
            
            counters: list[multiprocessing.sharedctypes.Synchronized[ctypes.c_int64]] = list()
            for i in range(throttle.size):
                counters.append(multiprocessing.Value(ctypes.c_int64, 0))
            
            progress_bars: list[tqdm.tqdm] = list()
            for i in range(throttle.size):
                progress_bars.append(tqdm.tqdm(total=4, initial=0, position=i, desc=f'Process {i}: {STATE_MESSAGES[counters[i].value]}', leave=True))
            
            processes: list[multiprocessing.Process] = list()
            for i in range(throttle.size):
                processes.append(multiprocessing.Process(target=self.qprop_task, args=(counters[i], pairing, throttle[i])))
            
            for i in range(throttle.size):
                processes[i].start()
            
            while any(process.is_alive() for process in processes):
                for i, counter in enumerate(counters):
                    with counter.get_lock():
                        progress_bars[i].n = counter.value
                        progress_bars[i].last_print_n = counter.value
                        progress_bars[i].set_description(f'Process {i}: {STATE_MESSAGES[counter.value]}')
            
            for process in processes:
                process.join()
            
            for progress_bar in progress_bars:
                progress_bar.close()
    
    
    
    def plot(self, output: dict[str: numpy.ndarray], throttle_limit: numpy.float64, propeller: str, motor: str) -> None:
        pass
