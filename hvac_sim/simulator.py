import numpy as np
from .parameters import Params
from .physics import rhs

class HVACSimulator:
    """
    Manages the state of the HVAC simulation and updates it step-by-step.
    """
    def __init__(self, initial_state: np.ndarray, params: Params, dt_s: int = 300):
        """
        Initializes the stateful simulator.

        Args:
            initial_state (np.ndarray): The starting state [T_z, T_w, CO2_z].
            params (Params): The model parameters.
            dt_s (int): The simulation time step in seconds.
        """
        self.state = np.array(initial_state, dtype=float)
        self.params = params
        self.dt_s = dt_s
        self.cumulative_energy_kwh = 0.0
        print(f"Simulator initialized with state: {self.state}")

    def step(self, inputs: dict) -> dict:
        """
        Performs a single simulation step using new sensor inputs.

        Args:
            inputs (dict): A dictionary of sensor readings, e.g.,
                           {'T_out': 25.0, 'N_occ': 5, 'T_set': 24.0}.

        Returns:
            dict: A dictionary containing the updated state and power usage.
        """
        # 1. Calculate the rates of change using the physics model
        deriv = rhs(self.state, inputs, self.params)

        # 2. Update the state variables (T_z, T_w, CO2) using Euler's method
        self.state += deriv[:3] * self.dt_s

        # 3. Get the electric power for this step and update cumulative energy
        power_kw = deriv[3]
        self.cumulative_energy_kwh += power_kw * self.dt_s / 3600.0

        # 4. Return the results for this step
        results = {
            "T_z": self.state[0],
            "T_w": self.state[1],
            "CO2_z": self.state[2],
            "P_e": power_kw,
            "E_KWh_cumulative": self.cumulative_energy_kwh,
        }
        return results