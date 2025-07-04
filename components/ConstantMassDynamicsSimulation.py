import multiprocessing.sharedctypes
import multiprocessing
import numpy
import subprocess
import io

from components.RunConfiguration import RunConfiguration
from components.utils.process_statuses import ProcessStatus
from components.ConstantMassDynamicsModel import ConstantMassDynamicsModel

class ConstantMassDynamicsSimulation:
    @classmethod
    def simulate_dynamics_given_mass(
        cls,
        run_configuration: RunConfiguration,
        mass: numpy.float64,
        run_results: multiprocessing.Queue,
        status_counter: multiprocessing.sharedctypes.Synchronized,
        position_counter: multiprocessing.sharedctypes.Synchronized,
        velocity_counter: multiprocessing.sharedctypes.Synchronized,
        acceleration_counter: multiprocessing.sharedctypes.Synchronized,
        time_counter: multiprocessing.sharedctypes.Synchronized,
        thrust_counter: multiprocessing.sharedctypes.Synchronized,
        drag_counter: multiprocessing.sharedctypes.Synchronized
    ) -> None:
        duration = [numpy.float64(0.0)]
        acceleration = list()
        velocity = [run_configuration.setpoint_velocity]
        position = [numpy.float64(0.0)]
        thrust = list()
        drag = list()
        
        stall_velocity = run_configuration.get_stall_velocity(mass)
        
        while True:
            with status_counter.get_lock():
                status_counter.value = ProcessStatus.EXECUTING_QPROP.value
            
            completed_process = subprocess.run(run_configuration.get_run_string(velocity[-1]), capture_output=True, text=True)
            
            with status_counter.get_lock():
                status_counter.value = ProcessStatus.EXTRACTING_DATA.value
            
            data_stream = io.StringIO(completed_process.stdout)
            data = numpy.loadtxt(data_stream, skiprows=17)
            
            thrust.append(data[:, 3][0])
            drag.append(run_configuration.get_drag_force(velocity[-1]))
            
            with status_counter.get_lock():
                status_counter.value = ProcessStatus.ITERATING_STATE.value
            
            acceleration.append((thrust[-1]-drag[-1]) / mass)
            velocity.append(velocity[-1] + acceleration[-1] * run_configuration.timestep_size)
            position.append(position[-1] + velocity[-1] * run_configuration.timestep_size)
            duration.append(duration[-1] + run_configuration.timestep_size)
            
            with status_counter.get_lock():
                status_counter.value = ProcessStatus.UPDATING_COUNTS.value

            with position_counter.get_lock():
                with velocity_counter.get_lock():
                    with acceleration_counter.get_lock():
                        with time_counter.get_lock():
                            with thrust_counter.get_lock():
                                with drag_counter.get_lock():
                                    position_counter.value = position[-1]
                                    velocity_counter.value = velocity[-1]
                                    acceleration_counter.value = acceleration[-1]
                                    time_counter.value = duration[-1]
                                    thrust_counter.value = thrust[-1]
                                    drag_counter.value = drag[-1]
            
            with status_counter.get_lock():
                status_counter.value = ProcessStatus.CHECKING_LIMITS.value
            
            if position[-1] > run_configuration.takeoff_displacement:
                with status_counter.get_lock():
                    status_counter.value = ProcessStatus.FAILED_VELOCITY.value if velocity[-1] <= stall_velocity else ProcessStatus.SUCCESS_TAKEOFF.value
                break
        
        run_results.put(ConstantMassDynamicsModel(
            mass=mass,
            stall_velocity=stall_velocity,
            time=duration,
            acceleration=acceleration,
            velocity=velocity,
            position=position,
            thrust=thrust,
            drag=drag
        ))
