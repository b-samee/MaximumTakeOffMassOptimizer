import multiprocessing
import argparse
import pathlib
import logging
import json

from components.utils.config_structure import get_config_structure, EXPECTED_CONFIGURATION_STRUCTURE

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
        raise ValueError(f'amount of processes to be forked ({args.processes}) exceed the number of logical processors remaining for forking ({n_processes})')
    
    with open(json_path, 'r') as json_file:
        json_data = json.load(json_file)
    
    json_structure = get_config_structure(json_data)
    if json_structure != EXPECTED_CONFIGURATION_STRUCTURE:
        raise SyntaxError(
            f'structure of configuration file "{json_path}" is invalid\n'
            f'GOT:\n'
            f'{json_structure}\n'
            f'EXPECTED:\n'
            f'{EXPECTED_CONFIGURATION_STRUCTURE}\n'
        )

if __name__ == '__main__':
    main()
