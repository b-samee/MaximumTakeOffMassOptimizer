EXPECTED_CONFIGURATION_STRUCTURE = {
    'propeller_file': str,
    'motor_file': str,
    'timestep_size': (float, int),
    'mass_range': [(float, int), (float, int)],
    'arithmetic_precision': (None, int),
    'takeoff_displacement': (float, int),
    'setpoint_parameters': {
        'velocity': (None, float, int),
        'voltage': (None, float, int),
        'dbeta': (None, float, int),
        'current': (None, float, int),
        'torque': (None, float, int),
        'thrust': (None, float, int),
        'pele': (None, float, int),
        'rpm': (None, float, int)
    },
    'aerodynamic_forces': {
        'fluid_density': (None, float, int),
        'true_airspeed': (None, float, int),
        'drag_coefficient': (None, float, int),
        'reference_area': (None, float, int),
        'acceleration_gravity': (None, float, int),
        'lift_coefficient': (None, float, int)
    }
}

def get_config_structure(json: object) -> object:
    def get_json_structure(json: object, origin_keys: list[str] = list()) -> object:
        if isinstance(json, dict):
            result = {key: get_json_structure(value, origin_keys + [key]) for key, value in json.items()}
        elif isinstance(json, list):
            result = list()
            for i, value in enumerate(json):
                result.append(get_json_structure(value, [key for key in origin_keys] + [i]))
        elif json is None or isinstance(json, int) or isinstance(json, float):
            result = EXPECTED_CONFIGURATION_STRUCTURE
            try:
                for key in origin_keys:
                    result = result[key]
                if not (json is None and None in result or type(json) in result):
                    result = type(json)
            except Exception as e:
                result = type(json)
        else:
            result = type(json)
        
        return result
    
    return get_json_structure(json)
