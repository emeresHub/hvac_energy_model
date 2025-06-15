# HVAC Energy Model

*A lightweight Python tool for simulating the thermal behaviour and energy use of a **single-zone** HVAC (Heating, Ventilation & Air-Conditioning) system.*

This model predicts:

* Indoor **air temperature**
* **Wall** (thermal-mass) temperature
* **CO₂** concentration  
* Instant **power draw (kW)** and cumulative **energy (kWh)**

based on building parameters plus time-series inputs such as outdoor weather and occupancy.

---

## ✨ Features

| Feature | What it does | Quick note |
|---------|--------------|------------|
| **Dynamic simulation** | Uses a **3R-2C** (three-resistance, two-capacitance) thermal network to track heat flows every time-step. | Captures both short-term spikes and wall-mass lag. |
| **HVAC control logic** | Simple on/off thermostat that holds a user-defined set-point. | Easy to swap in MPC later. |
| **Indoor-air-quality model** | Generates CO₂ from occupants and removes it via infiltration/ventilation. | One well-mixed box ODE. |
| **Energy accounting** | Logs instant power and integrates to kWh. | Compressor power = load ÷ COP; fan power follows the cube law. |

---

## 🗂 Project Structure

hvac_energy_model/
├─ data/ # input CSVs & saved result files
│
├─ hvac_sim/ # core simulation package
│ ├─ parameters.py # all physical constants & defaults
│ ├─ physics.py # 3R-2C heat + CO₂ ODEs
│ └─ simulate.py # time-march driver (Euler v-1)
│
└─ run.py # convenience script to launch a run



---

## 🚀 Getting Started

### 1 · Install requirements

```bash
pip install numpy pandas
```

### 2 · Run a 24-hour synthetic demo
```bash
python run.py
```
The script prints the first few rows to the console and writes a full
data/results/synthetic_run_results.csv.
