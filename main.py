import multiprocessing
import argparse
import pathlib
import logging

from components.RunConfiguration import RunConfiguration
from components.MaxTakeOffMassOptimizer import MaxTakeOffMassOptimizer

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    
    if multiprocessing.cpu_count() < 4:
        raise SystemError(f'system requirements not met: number of logical processors ({multiprocessing.cpu_count()}) falls below 4')
    
    argparser = argparse.ArgumentParser(add_help=False)
    argparser.add_argument('-c', '--config', required=True, type=str, help='Path to the input configuration json file')
    argparser.add_argument('-p', '--processes', type=int, default=multiprocessing.cpu_count(), help='Amount of processes forked to speedup optimization')
    args = argparser.parse_args()
    
    json_path = pathlib.Path(args.config)
    if not json_path.exists():
        raise FileNotFoundError(f'configuration file does not exist at path "{json_path}"')
    
    n_processes = max(3, min(args.processes, multiprocessing.cpu_count()-1))
    optimizer = MaxTakeOffMassOptimizer(n_processes)
    
    run_configuration = RunConfiguration(json_path)
    optimizer.run(run_configuration)

if __name__ == '__main__':
    main()
