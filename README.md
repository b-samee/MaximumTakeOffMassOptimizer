# Maximum Take-Off Mass Optimizer (MTOMO)

QPROP is an analysis program for predicting the performance of propeller-motor or windmill-generator combinations under a specific state setpoint, snapshot in time. This script takes a run configuration that represents a plane-environment-constraints scenario and performs an optimization over the Maximum Take-Off Mass (MTOM) by forking processes executing [Mark Drela's QPROP tool](https://web.mit.edu/drela/Public/web/qprop/). If the MTOM is found, plots for $x(t)$, $v(t)$, $a(t)$, $F_T(t)$, and $F_D(t)$ are generated for the successful run as well as a performance curve over the entire optimization. The optimization is achieved via a parallel interval search, where the worst-case number of epochs required to arrive at a solution is as follows, where $N$ is the number of processes forked for the optimization, $R$ is the mass range, and $\epsilon$ is the takeoff distance tolerance.

$$O\left(log_{N-1}\left(\frac{R}{\epsilon}\right)\right)$$

## Requirements and Running

This script was written in Python `3.13.3` and may require a version that is close to run. The script also requires that several packages be installed, which can be conveniently done by running `pip install -r requirements.txt`, assuming no virtual environment is being used for packages. By design, the script also requires a computer with at least 4 **logical processors**, which can be verified under `Task Manager > Performance > CPU`. The script is run using `python main.py -c <PATH_TO_CONFIG_JSON_FILE> [-p n_processes]`. The script was designed with the intention to reduce the need for modification. As such, a run configuration file provides all parameters that users may want to modify.

## Runs and Configurations

Each configuration file represents a set of runs, where each run is associated with specific parameters which apply to a set of pairing tests. The full structure of a typical configuration file is shown below. Runs and their tests are executed sequentially. Each test involves a sweep over 10 throttle steps to cover the full throttle range; this sweep is parallelized. The script was designed this way for future convenience. For most use cases, the configuration file will consist of a single run with a single pairing.

```py
{
    "propeller_file": str,
    "motor_file": str,
    "timestep_resolution": float | int,
    "mass_range": [float | int, float | int],
    "cutoff_displacement": [float | int, float | int],
    "discard_conditions": {
        "velocity": None | float | int,
        "time": None | float | int
    },
    "setpoint_parameters": {
        "velocity": None | float | int,
        "voltage": None | float | int,
        "dbeta": None | float | int,
        "current": None | float | int,
        "torque": None | float | int,
        "thrust": None | float | int,
        "pele": None | float | int,
        "rpm": None | float | int
    },
    "drag_force": {
        "fluid_density": None | float | int,
        "true_airspeed": None | float | int,
        "drag_coefficient": None | float | int,
        "reference_area": None | float | int
    }
}
```

## Project Structure

This section outlines the structure of the project for documentation purposes, in case future patches must be applied.

```bash
QPROP-DISPATCHER/                               # Project root
├── components/                                 # Python script components
│   ├── utils/                                  # Python script utilities
│   │   └── type_aliases.py                     # Defines type aliases for readability
│   │   └── config_keys.py                      # Defines config keys for readability
│   ├── ConfigurationLoader.py                  # Loads and validates configuration file
│   └── DynamicThrustModel.py                   # Prepares and dispatches tasks, plots data
├── motor_files/                                # Motor files
│   └── ...
├── propeller_files/                            # Propeller files
│   └── ...
├── .gitignore                                  # Gitignore file
├── LICENSE                                     # LICENSE file
├── main.py                                     # Main file of the script
├── qprop.exe                                   # QPROP executable dispatched by the script
├── README.md                                   # README file
└── requirements.txt                            # Package requirements file
```
