from components.ConfigurationLoader import ConfigurationLoader
from components.DynamicThrustModel import DynamicThrustModel

import logging

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger()
    
    config = ConfigurationLoader()

    for run_configuration in config.run_configurations:
        logger.info(f'EXECUTING RUN {run_configuration["index"]}/{len(config.run_configurations)}')
        model = DynamicThrustModel(run_configuration, config.configuration_name)
        model.run()

if __name__ == '__main__':
    main()
