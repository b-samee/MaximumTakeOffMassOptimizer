import pathlib
import shutil
import numpy
import json

from components.utils.config_structure import get_config_structure, EXPECTED_CONFIGURATION_STRUCTURE

class RunConfiguration:
    identifier: str
    variable_drag: bool
    propeller_file: pathlib.Path
    motor_file: pathlib.Path
    timestep_size: numpy.float64
    mass_range: tuple[numpy.float64, numpy.float64]
    arithmetic_precision: int
    takeoff_displacement: numpy.float64
    setpoint_velocity: numpy.float64
    setpoint_voltage: numpy.float64
    setpoint_dbeta: numpy.float64
    setpoint_current: numpy.float64
    setpoint_torque: numpy.float64
    setpoint_thrust: numpy.float64
    setpoint_pele: numpy.float64
    setpoint_rpm: numpy.float64
    aerodynamic_forces_fluid_density: numpy.float64
    aerodynamic_forces_true_airspeed: numpy.float64
    aerodynamic_forces_drag_coefficient: numpy.float64
    aerodynamic_forces_reference_area: numpy.float64
    aerodynamic_forces_acceleration_gravity: numpy.float64
    aerodynamic_forces_lift_coefficient: numpy.float64
    
    def __init__(self, json_path: pathlib.Path) -> None:
        self.identifier = json_path.stem
        
        results_directory = pathlib.Path(self.identifier)
        if results_directory.exists():
            shutil.rmtree(results_directory)
        results_directory.mkdir()
        
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file)
        
        json_structure = get_config_structure(json_data)
        if json_structure != EXPECTED_CONFIGURATION_STRUCTURE:
            raise SyntaxError(
                f'structure of configuration file "{json_path}" is invalid\n'
                f'\nGOT:\n\n'
                f'{json_structure}\n'
                f'\nEXPECTED:\n\n'
                f'{EXPECTED_CONFIGURATION_STRUCTURE}\n'
            )
        
        self.variable_drag = json_data['aerodynamic_forces']['true_airspeed'] is None

        self.propeller_file = pathlib.Path(json_data['propeller_file'])
        if not self.propeller_file.exists():
            raise FileNotFoundError(f'propeller file "{self.propeller_file}" not found')
        
        self.motor_file = pathlib.Path(json_data['motor_file'])
        if not self.motor_file.exists():
            raise FileNotFoundError(f'motor file "{self.motor_file}" not found')
        
        self.timestep_size = numpy.float64(json_data['timestep_size'])

        self.mass_range = (numpy.float64(json_data['mass_range'][0]), numpy.float64(json_data['mass_range'][1]))
        if self.mass_range[0] > self.mass_range[1]:
            raise ValueError(f'minimum "mass_range" ({self.mass_range[0]}) cannot exceed maximum "mass_range" ({self.mass_range[1]})')
        if self.mass_range[0] == 0:
            raise ZeroDivisionError(f'mass cannot be 0')
        
        self.arithmetic_precision = json_data['arithmetic_precision']
        
        self.takeoff_displacement = numpy.float64(json_data['takeoff_displacement'])
        
        self.setpoint_velocity = numpy.float64(0) if json_data['setpoint_parameters']['velocity'] is None else numpy.float64(json_data['setpoint_parameters']['velocity'])
        
        self.setpoint_voltage = numpy.float64(0) if json_data['setpoint_parameters']['voltage'] is None else numpy.float64(json_data['setpoint_parameters']['voltage'])
        
        self.setpoint_dbeta = numpy.float64(0) if json_data['setpoint_parameters']['dbeta'] is None else numpy.float64(json_data['setpoint_parameters']['dbeta'])

        self.setpoint_current = numpy.float64(0) if json_data['setpoint_parameters']['current'] is None else numpy.float64(json_data['setpoint_parameters']['current'])

        self.setpoint_torque = numpy.float64(0) if json_data['setpoint_parameters']['torque'] is None else numpy.float64(json_data['setpoint_parameters']['torque'])

        self.setpoint_thrust = numpy.float64(0) if json_data['setpoint_parameters']['thrust'] is None else numpy.float64(json_data['setpoint_parameters']['thrust'])

        self.setpoint_pele = numpy.float64(0) if json_data['setpoint_parameters']['pele'] is None else numpy.float64(json_data['setpoint_parameters']['pele'])

        self.setpoint_rpm = numpy.float64(0) if json_data['setpoint_parameters']['rpm'] is None else numpy.float64(json_data['setpoint_parameters']['rpm'])
        
        self.aerodynamic_forces_fluid_density = numpy.float64(0) if json_data['aerodynamic_forces']['fluid_density'] is None else numpy.float64(json_data['aerodynamic_forces']['fluid_density'])
        
        self.aerodynamic_forces_true_airspeed = numpy.float64(0) if json_data['aerodynamic_forces']['true_airspeed'] is None else numpy.float64(json_data['aerodynamic_forces']['true_airspeed'])
        
        self.aerodynamic_forces_drag_coefficient = numpy.float64(0) if json_data['aerodynamic_forces']['drag_coefficient'] is None else numpy.float64(json_data['aerodynamic_forces']['drag_coefficient'])

        self.aerodynamic_forces_reference_area = numpy.float64(0) if json_data['aerodynamic_forces']['reference_area'] is None else numpy.float64(json_data['aerodynamic_forces']['reference_area'])
        
        self.aerodynamic_forces_acceleration_gravity = numpy.float64(9.81) if json_data['aerodynamic_forces']['acceleration_gravity'] is None else numpy.float64(json_data['aerodynamic_forces']['acceleration_gravity'])
        
        self.aerodynamic_forces_lift_coefficient = numpy.float64(1.0) if json_data['aerodynamic_forces']['lift_coefficient'] is None else numpy.float64(json_data['aerodynamic_forces']['lift_coefficient'])
        if self.aerodynamic_forces_lift_coefficient == 0:
            raise ZeroDivisionError(f'lift_coefficient cannot be 0')
    
    def get_run_string(self, velocity: numpy.float64) -> str:
        return f'qprop {self.propeller_file} {self.motor_file} {velocity} {self.setpoint_rpm} {self.setpoint_voltage} {self.setpoint_dbeta} {self.setpoint_thrust} {self.setpoint_torque} {self.setpoint_current} {self.setpoint_pele}'
    
    def get_drag_force(self, velocity: numpy.float64) -> numpy.float64:
        return numpy.float64(0.5) * self.aerodynamic_forces_fluid_density * numpy.power(velocity if self.variable_drag else self.aerodynamic_forces_true_airspeed, 2, dtype=numpy.float64) * self.aerodynamic_forces_drag_coefficient * self.aerodynamic_forces_reference_area
    
    def get_stall_velocity(self, mass: numpy.float64) -> numpy.float64:
        return numpy.sqrt(numpy.divide(2.0 * mass * self.aerodynamic_forces_acceleration_gravity, self.aerodynamic_forces_lift_coefficient * self.aerodynamic_forces_fluid_density * self.aerodynamic_forces_reference_area))
