import multiprocessing
import argparse
import pathlib
import logging

from components.RunConfiguration import RunConfiguration
from components.MaxTakeOffMassOptimizer import ParallelBinaryOptimizer

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    
    argparser = argparse.ArgumentParser(add_help=False)
    argparser.add_argument('-c', '--config', required=True, type=str, help='Path to the input configuration json file')
    argparser.add_argument('-p', '--processes', type=int, default=3, help='Amount of processes forked in an attempt to speedup optimization')
    args = argparser.parse_args()
    
    json_path = pathlib.Path(args.config)
    if not json_path.exists():
        raise FileNotFoundError(f'configuration file does not exist at path "{json_path}"')
    
    n_processes = min(args.processes, multiprocessing.cpu_count()-1)
    if args.processes > n_processes:
        raise ValueError(f'number of processes forked ({args.processes}) exceed the number of logical processors remaining for forking ({n_processes})')
    elif args.processes < 3:
        raise ValueError(f'number of processes forked ({args.processes}) must be at least 3')
    
    optimizer = ParallelBinaryOptimizer(args.processes)
    
    run_configuration = RunConfiguration(json_path)
    optimizer.run(run_configuration)

if __name__ == '__main__':
    main()
