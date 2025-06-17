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

```markdown
hvac_energy_model/
├─ hvac_sim/              # core simulation package
│   ├─ parameters.py      # all physical constants & defaults
│   ├─ physics.py         # 3R-2C heat + CO₂ ODEs
│   └─ simulator.py        # time-march driver (Euler v-1)
│
├─ mqtt_integration/      # MQTT client and integration code
├─ .gitignore
├─ dashboard.py           # Dash web dashboard
├─ local.env              # environment variables for config
├─ mosquitto.conf         # MQTT broker config
├─ publisher_test.py      # interactive MQTT sensor data publisher
├─ README.md
├─ requirements.txt
```


---

## Getting Started

### 1 · Install requirements

```bash
pip install -r requirements.txt
```

### 2 · Start the MQTT broker (if needed)

If you haven’t already got Mosquitto or another MQTT broker running locally, start it up:

```bash
# Example for Mosquitto (Docker, port 1883)
docker run -d --name mosquitto -p 1883:1883 -v "$PWD/mosquitto.conf:/mosquitto/config/mosquitto.conf" eclipse-mosquitto
```

### 3 · Start the interactive publisher

Open a new terminal:

```bash
python publisher_test.py
```

This will begin publishing random sensor data and will **listen for target temperature setpoints** from the dashboard UI.

### 4 · Run the live dashboard

Open another terminal:

```bash
python dashboard.py
```

This starts a web server.
Go to [http://127.0.0.1:8050](http://127.0.0.1:8050) in your browser.

### 5 · Use the Dashboard

* View live simulation data and KPIs.
* Adjust the target temperature using the slider and “Update Setpoint” button.
* The dashboard and publisher communicate via MQTT in real time.

---

