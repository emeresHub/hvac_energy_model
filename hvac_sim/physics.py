import numpy as np
from typing import Sequence, Dict, Tuple
from .parameters import Params 

def hvac_power(T_z: float, T_set: float, p: Params) -> Tuple[float, float]:
    m_air = p.m_air_des
    delta = T_z - T_set

    if delta > 0:
        # Cooling needed
        Q = m_air * p.c_p * delta  # positive, cooling load
        P = Q / p.COP + p.P_fan_des
    elif delta < 0:
        # Heating needed
        Q = m_air * p.c_p * delta  # negative, heating load
        P = abs(Q) / p.COP + p.P_fan_des  # COP for heating, or you can set a different COP
    else:
        Q = 0.0
        P = 0.0

    return Q, P




def rhs(state: Sequence[float], inp: Dict[str, float], p: Params) -> np.ndarray:
    """
    Calculates the rate of change for each state variable.
    'state' is a list or array: [Zone Temperature, Wall Temperature, Zone CO₂]
    'inp' is a dictionary of external inputs: {'Outside Temp', 'Num Occupants', ...}
    It returns these rates of change, plus the current electric power use.
    """
    T_z, T_w, CO2_z = state

    # Unpack external inputs
    T_out = inp["T_out"]
    N_occ = inp["N_occ"]
    T_set = inp["T_set"]
    I_sol = inp.get("I_sol", 0.0)
    Q_int = inp.get("Q_int", 100.0 * N_occ)

    # Calculate HVAC cooling and power
    Q_HVAC, P_e = hvac_power(T_z, T_set, p)

    # Calculate temperature derivatives (rates of change)
    dTz = ((T_out - T_z) / p.R_oa +
           (T_w - T_z) / p.R_wz +
           Q_int / 1000.0 -  # convert internal gains from **W** to **kW**
           Q_HVAC) / p.C_z_kW

    dTw = ((T_z - T_w) / p.R_wz +
           (T_out - T_w) / p.R_ow +
           I_sol / 1000.0) / p.C_w_kW  # solar gains: W ➜ kW

    # Calculate CO₂ derivative
    Vdot_inf = p.ACH * p.V / 3600.0
    # ACH (air-changes-per-hour) × volume (m³) gives m³ / h
    # divide by 3600 to express that infiltration flow in m³ / s

    C_out = 400.0   # baseline outdoor CO₂ concentration in ppm (≈ current global average)

    E_m3s = p.E_occ * N_occ / 1000.0
    # occupant CO₂ generation rate:
    # per-person (L/s) × number of people, then /1000 to convert L → m³

    dCO2 = (Vdot_inf * (C_out - CO2_z) + E_m3s * 1e6) / p.V

    # Return all the calculated rates of change, plus the power usage.
    return np.array([dTz, dTw, dCO2, P_e])

