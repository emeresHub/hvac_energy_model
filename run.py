import pandas as pd
import numpy as np
from hvac_sim import Params, run_simulation # Import from our new package

def main():
    """Main function to set up and run the HVAC simulation."""
    print("Setting up simulation inputs...")
    # Create a time range for our simulation: 24 hours, with a data point every 5 minutes.
    rng = pd.date_range("2025-06-01", periods=288, freq="5min")
    df = pd.DataFrame(index=rng)

    # Create synthetic data:
    df["T_out"] = 25 + 5 * np.sin(np.linspace(0, 2 * np.pi, len(rng)))
    df["N_occ"] = (np.sin(np.linspace(-1, 3 * np.pi, len(rng))).clip(0) * 20).astype(int)
    df["T_set"] = 24.0

    # Initialize model parameters with defaults
    params = Params()

    print("Running simulation...")
    # Run the simulation with the synthetic data and default parameters.
    results = run_simulation(df, params)

    # --- Print Results ---
    print("--- Simulation Results (First 5 Steps) ---")
    print(results.head())

    print("\n--- Hourly Energy Consumption (kWh) ---")
    print(results["E_KWh"].resample("1H").last().diff().dropna())

if __name__ == "__main__":
    main()

