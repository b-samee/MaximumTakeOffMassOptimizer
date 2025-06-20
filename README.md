# Maximum Take-Off Mass Optimizer (MTOMO)

QPROP is an analysis program for predicting the performance of propeller-motor or windmill-generator combinations under a specific state setpoint, snapshot in time. This script takes a run configuration that represents a plane-environment-constraints scenario and performs an optimization over the Maximum Take-Off Mass (MTOM) by forking processes executing [Mark Drela's QPROP tool](https://web.mit.edu/drela/Public/web/qprop/). If the MTOM is found, plots for $x(t)$, $v(t)$, $a(t)$, $F_T(t)$, and $F_D(t)$ are generated for the successful run as well as a performance curve over the entire optimization. The optimization is achieved via a parallel interval search, where the worst-case number of epochs required to arrive at a solution is as follows, where $N$ is the number of processes forked for the optimization, $R$ is the mass range, and $\epsilon$ is the takeoff distance tolerance.

$$O\left(log_{N-1}\left(\frac{R}{\epsilon}\right)\right)$$

## Requirements and Running

This script was written in Python `3.13.3` and may require a version that is close to run. The script also requires that several packages be installed, which can be conveniently done by running `pip install -r requirements.txt`, assuming no virtual environment is being used for packages. By design, the script also requires a computer with at least 4 **logical processors**, which can be verified under `Task Manager > Performance > CPU`. The script is run using `python main.py -c <PATH_TO_CONFIG_JSON_FILE> [-p n_processes]`. The script was designed with the intention to reduce the need for modification. As such, a run configuration file provides all parameters that users may want to modify.

## Runs and Configurations

Each run configuration file represents a plane-environment-constraints scenario and thus the input to an optimization (run) over that scenario. The exact `json` structure of a run configuration file is shown below, where `|` delimits options. A run configuration file must consist of this exact structure.

```py
{
    "propeller_file": str,                                      # Path to propeller file
    "motor_file": str,                                          # Path to motor file
    "timestep_resolution": float | int,                         # Simulation time (s) step size
    "mass_range": [float | int, float | int],                   # Mass (kg) range to search
    "cutoff_displacement": [float | int, float | int],          # Cutoff distance (m) range
    "setpoint_parameters": {
        "velocity": None | float | int,                         # Initial velocity (m/s)
        "voltage": None | float | int,                          # Voltage (V)
        "dbeta": None | float | int,                            # Pitch-change angle (deg)
        "current": None | float | int,                          # Current (A)
        "torque": None | float | int,                           # Torque (N·m)
        "thrust": None | float | int,                           # Thrust (N)
        "pele": None | float | int,                             # Electrical Power (W)
        "rpm": None | float | int                               # RPM (rpm)
    },
    "aerodynamic_forces": {
        "fluid_density": None | float | int,                    # Fluid density (kg/m^3)
        "true_airspeed": None | float | int,                    # True airspeed (m/s)
        "drag_coefficient": None | float | int,                 # Drag coefficient
        "reference_area": None | float | int                    # Reference area (m^2)
        "acceleration_gravity": None | float | int              # Acceleration due to gravity (m/s^2)
        "lift_coefficient": None | float | int                  # Lift coefficient
    }
}
```

The `None` value is used to indicate to the optimizer that we don't want to provide a value ourselves, instead letting the optimizer figure it out. For `setpoint_parameters`, `None` means that the setpoint parameter should be initialized to 0. For `aerodynamic_forces`, `None` means that the parameter should be initialized to 0, except for three cases: for `acceleration_gravity` it is 9.81, for `lift_coefficient` it is 1.0, and for `true_airspeed` the optimizer should dynamically update the velocity to match the plane's current velocity at every step of the simulation.

## Project Structure

This section outlines the structure of the project for documentation purposes, in case future patches must be applied.

```bash
MaximumTakeOffMassOptimizer/                    # Project root
├── components/                                 # Python script components
│   ├── utils/                                  # Python script utilities
│   │   └── config_structure.py                 # Used to define and verify config structure
│   │   └── process_statuses.py                 # Used to define process status enums
│   ├── DynamicThrustModel.py                   # Represents the QPROP (slave) process
│   ├── ParallelBinaryOptimizer.py              # Represents the optimizer (master) process
│   └── RunConfiguration.py                     # Validates and encapsulates a run configuration
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
