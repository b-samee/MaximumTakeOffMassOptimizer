import pathlib
import numpy
import json

from components.utils.config_structure import get_config_structure, EXPECTED_CONFIGURATION_STRUCTURE

class RunConfiguration:
    variable_drag: bool
    propeller_file: pathlib.Path
    motor_file: pathlib.Path
    timestep_resolution: numpy.float64
    mass_range: tuple[numpy.float64, numpy.float64]
    cutoff_displacement: tuple[numpy.float64, numpy.float64]
    setpoint_velocity: numpy.float64
    setpoint_voltage: numpy.float64
    setpoint_dbeta: numpy.float64
    setpoint_current: numpy.float64
    setpoint_torque: numpy.float64
    setpoint_thrust: numpy.float64
    setpoint_pele: numpy.float64
    setpoint_rpm: numpy.float64
    drag_force_fluid_density: numpy.float64
    drag_force_true_airspeed: numpy.float64
    drag_force_drag_coefficient: numpy.float64
    drag_force_reference_area: numpy.float64

    def __init__(self, json_path: str) -> None:
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
        
        self.variable_drag = json_data['drag_force']['true_airspeed'] is None

        self.propeller_file = pathlib.Path(json_data['propeller_file'])
        if not self.propeller_file.exists():
            raise FileNotFoundError(f'propeller file "{self.propeller_file}" not found')
        
        self.motor_file = pathlib.Path(json_data['motor_file'])
        if not self.motor_file.exists():
            raise FileNotFoundError(f'motor file "{self.motor_file}" not found')
        
        self.timestep_resolution = numpy.float64(json_data['timestep_resolution'])

        self.mass_range = (numpy.float64(json_data['mass_range'][0]), numpy.float64(json_data['mass_range'][1]))
        
        self.cutoff_displacement = (numpy.float64(json_data['cutoff_displacement'][0]), numpy.float64(json_data['cutoff_displacement'][1]))
        
        self.setpoint_velocity = numpy.float64(0) if json_data['setpoint_parameters']['velocity'] is None else numpy.float64(json_data['setpoint_parameters']['velocity'])
        
        self.setpoint_voltage = numpy.float64(0) if json_data['setpoint_parameters']['voltage'] is None else numpy.float64(json_data['setpoint_parameters']['voltage'])
        
        self.setpoint_dbeta = numpy.float64(0) if json_data['setpoint_parameters']['dbeta'] is None else numpy.float64(json_data['setpoint_parameters']['dbeta'])

        self.setpoint_current = numpy.float64(0) if json_data['setpoint_parameters']['current'] is None else numpy.float64(json_data['setpoint_parameters']['current'])

        self.setpoint_torque = numpy.float64(0) if json_data['setpoint_parameters']['torque'] is None else numpy.float64(json_data['setpoint_parameters']['torque'])

        self.setpoint_thrust = numpy.float64(0) if json_data['setpoint_parameters']['thrust'] is None else numpy.float64(json_data['setpoint_parameters']['thrust'])

        self.setpoint_pele = numpy.float64(0) if json_data['setpoint_parameters']['pele'] is None else numpy.float64(json_data['setpoint_parameters']['pele'])

        self.setpoint_rpm = numpy.float64(0) if json_data['setpoint_parameters']['rpm'] is None else numpy.float64(json_data['setpoint_parameters']['rpm'])
        
        self.drag_force_fluid_density = numpy.float64(0) if json_data['drag_force']['fluid_density'] is None else numpy.float64(json_data['drag_force']['fluid_density'])
        
        self.drag_force_true_airspeed = numpy.float64(0) if json_data['drag_force']['true_airspeed'] is None else numpy.float64(json_data['drag_force']['true_airspeed'])
        
        self.drag_force_drag_coefficient = numpy.float64(0) if json_data['drag_force']['drag_coefficient'] is None else numpy.float64(json_data['drag_force']['drag_coefficient'])

        self.drag_force_reference_area = numpy.float64(0) if json_data['drag_force']['reference_area'] is None else numpy.float64(json_data['drag_force']['reference_area'])
    
    def get_run_string(self, velocity: numpy.float64) -> str:
        return f'qprop {self.propeller_file} {self.motor_file} {velocity} {self.setpoint_rpm} {self.setpoint_voltage} {self.setpoint_dbeta} {self.setpoint_thrust} {self.setpoint_torque} {self.setpoint_current} {self.setpoint_pele}'
    
    def get_drag_force(self, velocity: numpy.float64) -> numpy.float64:
        return numpy.float64(0.5) * self.drag_force_fluid_density * numpy.power(velocity if self.variable_drag else self.drag_force_true_airspeed, 2, dtype=numpy.float64) * self.drag_force_drag_coefficient * self.drag_force_reference_area
