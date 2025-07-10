import argparse
import pathlib
import logging
import psutil

from components.RunConfiguration import RunConfiguration
from components.MaximumTakeOffMassOptimizer import MaximumTakeOffMassOptimizer

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    
    MINIMUM_CORES_REQUIRED_BY_ALGORITHM_DESIGN = 4
    
    system_cores = psutil.cpu_count(logical=False)
    if system_cores < 4:
        raise SystemError(f'system requirements not met: number of cores ({system_cores}) must be at least 4')
    
    argparser = argparse.ArgumentParser(add_help=False)
    argparser.add_argument('-c', '--config', required=True, type=str, help='Path to the input configuration json file')
    argparser.add_argument('-p', '--processes', type=int, default=MINIMUM_CORES_REQUIRED_BY_ALGORITHM_DESIGN-1, help='Amount of processes forked to speedup optimization')
    args = argparser.parse_args()
    
    json_path = pathlib.Path(args.config)
    if not json_path.exists():
        raise FileNotFoundError(f'configuration file does not exist at path "{json_path}"')
    
    n_processes = max(MINIMUM_CORES_REQUIRED_BY_ALGORITHM_DESIGN-1, min(args.processes, system_cores-1))
    if n_processes != args.processes:
        logging.warning(f'Supplied number of processes ({args.processes}) is beyond the allowable [{MINIMUM_CORES_REQUIRED_BY_ALGORITHM_DESIGN-1}, {system_cores-1}]. Clamping to {n_processes}...')
    
    optimizer = MaximumTakeOffMassOptimizer(n_processes)
    
    run_configuration = RunConfiguration(json_path)
    optimizer.run(run_configuration)

if __name__ == '__main__':
    main()
