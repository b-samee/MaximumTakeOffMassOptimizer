import argparse
import pathlib
import numpy
import json

from components.utils.type_aliases import RunConfiguration

class ConfigurationLoader(argparse.ArgumentParser):
    run_configurations: list[RunConfiguration]
    
    def __init__(self) -> None:
        super().__init__(add_help=False)
        self.add_argument('config', type=str, help="Path to the input configuration json file")
        args = self.parse_args()
        
        json_path = pathlib.Path(args.config)
        if not json_path.exists():
            raise FileNotFoundError(f'ERROR: configuration file does not exist at path "{json_path}"')
        
        self.run_configurations = list()
        with open(json_path, 'r') as json_file:
            json_data = json.load(json_file)
        
        CONFIGURATION_KEYS = {'current_limit', 'setpoint', 'pairings'}
        
        SETPOINT_KEYS = {
            'velocity',
            'voltage',
            'dbeta',
            'current',
            'torque',
            'thrust',
            'pele',
            'rpm',
        }

        PAIRING_KEYS = {'propeller', 'motor'}
        
        error_prefix = 'ERROR: invalid configuration file format'
        
        if type(json_data) != list:
            raise TypeError(f'{error_prefix}, must begin with a list')
        
        for run_configuration in json_data:
            if type(run_configuration) != dict:
                raise TypeError(f'{error_prefix}, root list can only contain objects')
            
            RUN_CONFIGURATION_KEYS = set(run_configuration.keys())
            
            MISSING_KEYS = CONFIGURATION_KEYS - RUN_CONFIGURATION_KEYS
            if len(MISSING_KEYS) != 0:
                raise KeyError(f'{error_prefix}, missing configuration keys {MISSING_KEYS}')
            UNKNOWN_KEYS = RUN_CONFIGURATION_KEYS - CONFIGURATION_KEYS
            if len(UNKNOWN_KEYS) != 0:
                raise KeyError(f'{error_prefix}, unknown configuration keys {UNKNOWN_KEYS}')
            
            if type(run_configuration['current_limit']) not in {int, float}:
                raise ValueError(f'{error_prefix}, "current_limit" must point to a number')
            run_configuration['current_limit'] = numpy.float64(run_configuration['current_limit'])
            
            if type(run_configuration['setpoint']) != dict:
                raise ValueError(f'{error_prefix}, "setpoint" must point to an object')

            RUN_SETPOINT_KEYS = set(run_configuration['setpoint'].keys())
            
            MISSING_KEYS = SETPOINT_KEYS - RUN_SETPOINT_KEYS
            for key in MISSING_KEYS:
                run_configuration['setpoint'][key] = 0
            UNKNOWN_KEYS = RUN_SETPOINT_KEYS - SETPOINT_KEYS
            if len(UNKNOWN_KEYS) != 0:
                raise KeyError(f'{error_prefix}, unknown setpoint keys {UNKNOWN_KEYS}')
            
            for key, value in run_configuration['setpoint'].items():
                if type(value) not in {int, float}:
                    raise ValueError(f'{error_prefix}, setpoint "{key}" must point to a number')
                run_configuration['setpoint'][key] = numpy.float64(run_configuration['setpoint'][key])
            
            if type(run_configuration['pairings']) != list:
                raise ValueError(f'{error_prefix}, "pairings" must point to a list')

            for pairing in run_configuration['pairings']:
                if type(pairing) != dict:
                    raise TypeError(f'{error_prefix}, pairing must be an object')

                RUN_PAIRING_KEYS = set(pairing.keys())
                
                MISSING_KEYS = PAIRING_KEYS - RUN_PAIRING_KEYS
                if len(MISSING_KEYS) != 0:
                    raise KeyError(f'{error_prefix}, missing pairing keys {MISSING_KEYS}')
                UNKNOWN_KEYS = RUN_PAIRING_KEYS - PAIRING_KEYS
                if len(UNKNOWN_KEYS) != 0:
                    raise KeyError(f'{error_prefix}, unknown pairing keys {UNKNOWN_KEYS}')

                for key, value in pairing.items():
                    if type(value) != str:
                        raise ValueError(f'{error_prefix}, pairing "{key}" must point to a string')
                    pairing[key] = pathlib.Path(value)
                    if not pairing[key].exists():
                        raise FileNotFoundError(f'{error_prefix}, path to "{pairing[key]}" does not exist')
            
            self.run_configurations.append(run_configuration)
