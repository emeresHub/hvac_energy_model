import pandas as pd
import numpy as np
from .parameters import Params
from .physics import rhs # Import the physics equations from our package

def run_simulation(df_in: pd.DataFrame, p: Params, dt_s: int = 300) -> pd.DataFrame:
    """
    Runs the simulation over a given time-series of inputs.

    df_in: A pandas DataFrame with a datetime index and columns for T_out, N_occ, etc.
    p: The parameters for our model.
    dt_s: The time step in seconds (e.g., 300 seconds = 5 minutes).
    returns: A DataFrame with the simulation results (T_z, CO2_z, Power, Energy).
    """
    # Set the initial state of the system.
    T0 = df_in["T_set"].iloc[0]
    state = np.array([T0, T0, 600.0])    # Initial [T_z, T_w, CO₂_z]

    # Initialize variables to store results
    energy = 0.0
    rec = []

    # The main simulation loop
    for t, row in df_in.iterrows():
        # 1. Calculate the current rates of change using our ODE function.
        deriv = rhs(state, row, p)

        # 2. Apply the Euler method to update the state variables (T_z, T_w, CO₂).
        state[:3] += deriv[:3] * dt_s

        # 3. Get the electric power for this time step and accumulate energy.
        P_e = deriv[3]
        energy += P_e * dt_s / 3600.0

        # 4. Record the results for this time step.
        rec.append((t, state[0], state[1], state[2], P_e, energy))

    # After the loop, convert the list of results into a pandas DataFrame.
    out = pd.DataFrame(
        rec, columns=["time", "T_z", "T_w", "CO2_z", "P_e", "E_KWh"]
    ).set_index("time")


    # Can be removed if our use case does not require forecast
    # As a bonus, let's create a simple 1-hour-ahead forecast.
    # 1. 3600 seconds = 1 h.  Divide by the step length (dt_s) to find
    #    how many rows of data represent a one-hour horizon.
    hor = int(3600 / dt_s)          # e.g. dt_s=300 s  → hor = 12 rows

    # 2. .shift(-hor) moves each series upward by ‘hor’ rows,
    #    so the value stored at timestamp t now shows the model’s
    #    state at t + 1 hour.  (The tail rows shift past the index and become NaN.)
    out["T_z_h1"]  = out["T_z"].shift(-hor)   # 1-hour-ahead zone temperature (°C)
    out["CO2_h1"]  = out["CO2_z"].shift(-hor) # 1-hour-ahead CO₂ concentration (ppm)

    return out

