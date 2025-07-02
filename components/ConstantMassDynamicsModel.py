import matplotlib.pyplot
import numpy

class ConstantMassDynamicsModel:
    mass: numpy.float64
    stall_velocity: numpy.float64
    time: numpy.ndarray[numpy.float64]
    acceleration: numpy.ndarray[numpy.float64]
    velocity: numpy.ndarray[numpy.float64]
    position: numpy.ndarray[numpy.float64]
    thrust: numpy.ndarray[numpy.float64]
    drag: numpy.ndarray[numpy.float64]
    
    def __init__(self, mass: numpy.float64, stall_velocity: numpy.float64, time: list[numpy.float64], acceleration: list[numpy.float64], velocity: list[numpy.float64], position: list[numpy.float64], thrust: list[numpy.float64], drag: list[numpy.float64]) -> None:
        self.mass = mass
        self.stall_velocity = stall_velocity
        self.time = numpy.array(time, dtype=numpy.float64)
        self.acceleration = numpy.array(acceleration, dtype=numpy.float64)
        self.velocity = numpy.array(velocity, dtype=numpy.float64)
        self.position = numpy.array(position, dtype=numpy.float64)
        self.thrust = numpy.array(thrust, dtype=numpy.float64)
        self.drag = numpy.array(drag, dtype=numpy.float64)
    
    def get_position_takeoff(self) -> numpy.float64:
        return self.position[-2]
    
    def get_velocity_takeoff(self) -> numpy.float64:
        return self.velocity[-2]
    
    def plot_model(self, name: str, dynamics_models: dict[numpy.float64, object]) -> None:
        time = self.time[:-1]
        acceleration = self.acceleration
        velocity = self.velocity[:-1]
        position = self.position[:-1]
        thrust = self.thrust
        drag = self.drag
        
        performance_characteristics = list()
        for dynamics_model in dynamics_models.values():
            performance_characteristics.append((dynamics_model.mass, dynamics_model.stall_velocity, dynamics_model.get_velocity_takeoff()))
        
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
        axes[2, 1].set_title('Velocity vs Mass')
        axes[2, 1].set_xlabel('Mass (kg)')
        axes[2, 1].set_ylabel('Velocity (m/s)')
        axes[2, 1].set_xscale('log')
        axes[2, 1].grid(True)
        axes[2, 1].legend()
        
        matplotlib.pyplot.tight_layout()
        matplotlib.pyplot.savefig(f'{name}.png', dpi=300)
        matplotlib.pyplot.close()
