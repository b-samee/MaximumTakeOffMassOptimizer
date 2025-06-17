# QProp Dispatcher

QPROP is an analysis program for predicting the performance of propeller-motor or windmill-generator combinations. This script wraps [Mark Drela's QPROP tool](https://web.mit.edu/drela/Public/web/qprop/), starting out as a port of [robjds' Qprop_Matlab script](https://github.com/robjds/Qprop_Matlab) where it was modified to its current state. The script reads a json configuration file and dispatches QPROP processes to generate analysis data over the full throttle range in steps of 10%. The generated analysis data is tested against a current limit and plotted.

## Requirements and Running

This script was written in Python `3.13.3` and requires at least Python `3.9.x` to run. The script also requires that several packages be installed. Users of this script can ensure the required packages are installed using `pip install -r requirements.txt`, assuming no virtual environment is being used for packages. It is highly recommended that the script is run on a processor that boasts at least 12 logical processors, as the script will fork 10 additional processes at a time to parallelize the throttle sweep. The number of logical processors can be verified in Task Manager, under the Performance tab, at the bottom right of the CPU section. This isn't a strict requirement, but the script will contend over the CPU when run on weaker systems. The script is run using `python main.py <PATH_TO_CONFIG_JSON_FILE>`. The script was designed with the intention to reduce the need for modification. As such, the configuration file provides all parameters that users may want to modify.

## Runs and Configurations

Each configuration file represents a set of runs, where each run is associated with specific parameters which apply to a set of pairing tests. The full structure of a typical configuration file is shown below. Runs and their tests are executed sequentially. Each test involves a sweep over 10 throttle steps to cover the full throttle range; this sweep is parallelized. The script was designed this way for future convenience. For most use cases, the configuration file will consist of a single run with a single pairing.

```json
// A CONFIGURATION REPRESENTS A SET OF RUNS
[
    // RUN_0
    {
        // EACH RUN IS ASSOCIATED WITH SPECIFIC PARAMETERS
        "current_limit": 16,
        "setpoint": {
            "velocity": 2.0,    // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
            "voltage": 8.4      // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
        },
        // AND THESE PARAMETERS APPLY TO A SET OF PAIRING TESTS
        "pairings": [
            { "propeller": "path/to/propeller/file", "motor": "path/to/motor/file" }
        ]
    },
    ...
    // RUN_N
    {
        // EACH RUN IS ASSOCIATED WITH SPECIFIC PARAMETERS
        "current_limit": 16,
        "setpoint": {
            "velocity": 2.0,    // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
            "voltage": 8.4,     // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
            "dbeta": 0.0,       // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
            "current": 0.0,     // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
            "torque": 0.0,      // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
            "thrust": 0.0,      // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
            "pele": 0.0,        // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
            "rpm": 0.0,         // OPTIONAL: WILL BE SET TO 0 IF NOT PROVIDED
        },
        // AND THESE PARAMETERS APPLY TO A SET OF PAIRING TESTS
        "pairings": [
            { "propeller": "path/to/propeller/file", "motor": "path/to/motor/file" },
            { "propeller": "path/to/propeller/file", "motor": "path/to/motor/file" }
        ]
    }
]
```

## Project Structure

This section outlines the structure of the project for documentation purposes, in case future patches must be applied.

```bash
QPROP-DISPATCHER/                               # Project root
├── components/                                 # Python script components
│   ├── ConfigurationLoader.py                  # Responsible for loading and validating configuration file
│   └── DynamicThrustModel.py                   # Responsible for preparing tasks, dispatching, and plotting
├── motor_files/                                # Motor files
│   └── ...
├── propeller_files/                            # Propeller files
│   └── ...
├── .gitignore                                  # Gitignore file
├── config.json                                 # Configuration file
├── LICENSE                                     # LICENSE file
├── main.py                                     # Main file of the script
├── qprop.exe                                   # QPROP executable dispatched by the script
├── README.md                                   # README file
└── requirements.txt                            # Package requirements file
```
