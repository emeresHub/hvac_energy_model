from dataclasses import dataclass

@dataclass
class Params:
    """
    Tool-Box to hold all our model's physical parameters.
    Each parameter is a 'float'.
    """
    # Thermal Properties: How heat moves around
    R_oa: float = 3.0      # K per kW  (Thermal resistance between outdoor air and zone air)
    R_wz: float = 1.6      # K per kW  (Thermal resistance between the wall's mass and zone air)
    R_ow: float = 2.0      # K per kW  (Thermal resistance between outdoor air and the wall's mass)
    C_z:  float = 3_000.0  # kJ / K    (Thermal capacitance of the zone's air and furniture)
    C_w:  float = 15_000.0 # kJ / K    (Thermal capacitance of the building's inner wall mass)

    # HVAC System Properties
    COP:  float = 3.5      # –         (Coefficient of Performance: cooling efficiency)
    P_fan_des: float = 1.2 # kW        (The power consumed by the fan when the system is on)
    m_air_des: float = 2.5 # kg/s      (The mass of air the HVAC system moves per second)

    # Building & Occupant Properties
    V:    float = 240.0    # m³        (The total volume of the room or zone)
    ACH:  float = 0.4      # h⁻¹       (Air Changes per Hour: how much fresh air leaks in)
    E_occ: float = 0.005   # L·s⁻¹·person⁻¹ (The rate of CO₂ generated per person)
    c_p:  float = 1.006    # kJ·kg⁻¹·K⁻¹ (Specific heat of air: energy to raise its temperature)

    COP_cool: float = 3.5  # Cooling efficiency
    COP_heat: float = 3.0  # Heating efficiency

    @property
    def C_z_kW(self):
        """Converts the zone capacitance from kilojoules (kJ) to kilowatt-seconds (kW·s)."""
        return self.C_z

    @property
    def C_w_kW(self):
        """Converts the wall capacitance from kilojoules (kJ) to kilowatt-seconds (kW·s)."""
        return self.C_w

