import argparse
import pathlib
import numpy
import json

from components.utils.type_aliases import RunConfiguration
import components.utils.config_keys as CONFIG

class ConfigurationLoader(argparse.ArgumentParser):
    run_configurations: list[RunConfiguration]
    configuration_name: str
    
    def __init__(self) -> None:
        json_data = self.load_config()
        self.validate_configuration(json_data)
    


    def load_config(self) -> list[RunConfiguration]:
        super().__init__(add_help=False)
        self.add_argument('config', type=str, help="Path to the input configuration json file")
        args = self.parse_args()
        
        json_path = pathlib.Path(args.config)
        if not json_path.exists():
            raise FileNotFoundError(f'configuration file does not exist at path "{json_path}"')
        
        self.run_configurations = list()
        with open(json_path, 'r') as json_file:
            self.configuration_name = json_path.stem
            return json.load(json_file)



    def validate_configuration(self, json_data: list[RunConfiguration]) -> None:
        if type(json_data) != list:
            raise TypeError('configuration file must begin with a list')
        
        for i, run_configuration in enumerate(json_data, 1):
            self.validate_run(run_configuration)
            self.run_configurations[-1]['index'] = i
    


    def validate_run(self, run_configuration: RunConfiguration) -> None:
        if type(run_configuration) != dict:
            raise TypeError(f'configuration file root list can only contain objects')
        
        RUN_CONFIGURATION_KEYS = set(run_configuration.keys())
        
        MISSING_KEYS = CONFIG.ALL_CONFIGURATION_KEYS - RUN_CONFIGURATION_KEYS
        if len(MISSING_KEYS) != 0:
            raise KeyError(f'configuration file missing configuration keys {MISSING_KEYS}')
        UNKNOWN_KEYS = RUN_CONFIGURATION_KEYS - CONFIG.ALL_CONFIGURATION_KEYS
        if len(UNKNOWN_KEYS) != 0:
            raise KeyError(f'configuration file unknown configuration keys {UNKNOWN_KEYS}')
        
        self.validate_current_limit(run_configuration)
        self.validate_setpoint(run_configuration)
        self.validate_pairings(run_configuration)

        self.run_configurations.append(run_configuration)
    


    def validate_current_limit(self, run_configuration: RunConfiguration) -> None:
        if type(run_configuration['current_limit']) not in {int, float}:
            raise ValueError(f'configuration file "current_limit" must point to a number')
        run_configuration['current_limit'] = numpy.float64(run_configuration['current_limit'])
    


    def validate_setpoint(self, run_configuration: RunConfiguration) -> None:
        if type(run_configuration['setpoint']) != dict:
            raise ValueError(f'configuration file "setpoint" must point to an object')

        RUN_SETPOINT_KEYS = set(run_configuration['setpoint'].keys())
        
        MISSING_KEYS = CONFIG.ALL_SETPOINT_KEYS - RUN_SETPOINT_KEYS
        for key in MISSING_KEYS:
            run_configuration['setpoint'][key] = 0
        UNKNOWN_KEYS = RUN_SETPOINT_KEYS - CONFIG.ALL_SETPOINT_KEYS
        if len(UNKNOWN_KEYS) != 0:
            raise KeyError(f'configuration file unknown setpoint keys {UNKNOWN_KEYS}')
        
        for key, value in run_configuration['setpoint'].items():
            if type(value) not in {int, float}:
                raise ValueError(f'configuration file setpoint "{key}" must point to a number')
            run_configuration['setpoint'][key] = numpy.float64(run_configuration['setpoint'][key])
    


    def validate_pairings(self, run_configuration: RunConfiguration) -> None:
        if type(run_configuration['pairings']) != list:
            raise ValueError(f'configuration file "pairings" must point to a list')

        for pairing in run_configuration['pairings']:
            if type(pairing) != dict:
                raise TypeError(f'configuration file pairing must be an object')

            RUN_PAIRING_KEYS = set(pairing.keys())
            
            MISSING_KEYS = CONFIG.ALL_PAIRING_KEYS - RUN_PAIRING_KEYS
            if len(MISSING_KEYS) != 0:
                raise KeyError(f'configuration file missing pairing keys {MISSING_KEYS}')
            UNKNOWN_KEYS = RUN_PAIRING_KEYS - CONFIG.ALL_PAIRING_KEYS
            if len(UNKNOWN_KEYS) != 0:
                raise KeyError(f'configuration file unknown pairing keys {UNKNOWN_KEYS}')

            for key, value in pairing.items():
                if type(value) != str:
                    raise ValueError(f'configuration file pairing "{key}" must point to a string')
                pairing[key] = pathlib.Path(value)
                if not pairing[key].exists():
                    raise FileNotFoundError(f'configuration file path to "{pairing[key]}" does not exist')
