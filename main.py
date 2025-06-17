from components.ConfigurationLoader import ConfigurationLoader
from components.DynamicThrustModel import DynamicThrustModel

import logging

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    logger = logging.getLogger()
    
    config = ConfigurationLoader()

    for i, run_configuration in enumerate(config.run_configurations, 1):
        logger.info(f'EXECUTING RUN {i}/{len(config.run_configurations)}')
        model = DynamicThrustModel(run_configuration)
        model.run(i)

if __name__ == '__main__':
    main()
