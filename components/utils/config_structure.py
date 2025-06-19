EXPECTED_CONFIGURATION_STRUCTURE = {
    'propeller_file': str,
    'motor_file': str,
    'timestep_resolution': (float, int),
    'mass_range': [(float, int), (float, int)],
    'cutoff_displacement': [(float, int), (float, int)],
    'setpoint_parameters': {
        'velocity': (float, int),
        'voltage': (float, int),
        'dbeta': (float, int),
        'current': (float, int),
        'torque': (float, int),
        'thrust': (float, int),
        'pele': (float, int),
        'rpm': (float, int)
    },
    'drag_force': {
        'fluid_density': (float, int),
        'true_airspeed': (None, float, int),
        'drag_coefficient': (float, int),
        'reference_area': (float, int)
    }
}

def get_config_structure(json: object) -> object:
    def get_json_structure(json: object, origin_keys: list[str] = list()) -> object:
        if isinstance(json, dict):
            result = {key: get_json_structure(value, [key]) for key, value in json.items()}
        elif isinstance(json, list):
            result = list()
            for value in json: result.append(get_json_structure(value, origin_keys))
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
