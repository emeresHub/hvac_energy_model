import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import os
from dotenv import load_dotenv
import threading
import time
from collections import deque
from num2words import num2words
import random

# Import our custom modules
from hvac_sim.parameters import Params
from hvac_sim.simulator import HVACSimulator
from mqtt_integration.client import MQTTClient, load_mqtt_config

# --- 1. INITIAL SETUP AND STATE MANAGEMENT ---

# Load environment variables from local.env
load_dotenv("local.env")

# Thread-safe data storage for communication between MQTT thread and Dash app
data_deque = deque(maxlen=288)  # Store last 24 hours at 5-min intervals
lock = threading.Lock()

# Global variable for the MQTT client so we can use it in callbacks
mqtt_client = None

# --- 2. HVAC SIMULATOR AND MQTT LOGIC ---

def on_sensor_data_received(msg_dict):
    """Callback triggered by MQTT client on new message."""
    global hvac_sim
    try:
        n_occ = int(msg_dict["N_occ"])
        inputs = {
            "T_out": float(msg_dict["T_out"]),
            "N_occ": n_occ,
            "T_set": float(msg_dict["T_set"]),
            "I_sol": float(msg_dict.get("I_sol", 0.0))
        }
        
        # Run one simulation step
        results = hvac_sim.step(inputs)
        
        # Add a timestamp and store the new data point
        results['timestamp'] = pd.to_datetime('now')
        results['N_occ'] = n_occ  # Add number of people
        results['T_set'] = float(msg_dict["T_set"])  # Store setpoint with results!
        with lock:
            data_deque.append(results)
            
    except (KeyError, ValueError) as e:
        print(f"Error processing message: {e}.")

def mqtt_service_thread():
    """Main function for the MQTT background thread."""
    global mqtt_client
    
    mqtt_config = load_mqtt_config()
    mqtt_config.client_id = f'{mqtt_config.client_id}-{random.randint(0, 1000)}'
    
    sensor_topic = os.getenv("BROKER_TOPIC")
    print("BROKER_TOPIC (env):", os.getenv("BROKER_TOPIC"))
    print("CONTROL_TOPIC (env):", os.getenv("CONTROL_TOPIC"))
    
    mqtt_client = MQTTClient(config=mqtt_config, topic=sensor_topic)
    mqtt_client.connect_mqtt()
    mqtt_client.subscribe(callback=on_sensor_data_received)
    
    # The Paho-MQTT loop_start() runs in a background thread itself,
    # but we'll keep this parent thread alive to be explicit.
    print(f"MQTT service running in background, subscribed to {sensor_topic}.")
    while True:
        time.sleep(1)

# --- 3. DASH APPLICATION LAYOUT ---

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
app.title = "HVAC Digital Twin"

app.layout = html.Div(style={'backgroundColor': '#F0F0F0', 'padding': '20px'}, children=[
    html.H1(
        "Live HVAC Digital Twin Dashboard",
        style={'textAlign': 'center', 'color': '#333'}
    ),
    html.Div(className='row', children=[
        html.Div(id='live-kpi-text', className='three columns', style={'padding': '20px'}),
        html.Div(className='nine columns', children=[
            dcc.Graph(id='live-graph')
        ])
    ]),
    html.Div(className='row', style={'padding': '20px', 'marginTop': '20px', 'backgroundColor': 'white', 'borderRadius': '5px'}, children=[
        html.H4("HVAC Control", style={'textAlign': 'center'}),
        html.Label("Target Temperature (°C)"),
        dcc.Slider(
            id='temp-setpoint-slider',
            min=18, max=28, step=0.5, value=24,
            marks={i: f'{i}°C' for i in range(18, 29, 2)}
        ),
        html.Button('Update Setpoint', id='update-setpoint-button', n_clicks=0, style={'marginTop': '15px'})
    ]),
    dcc.Interval(id='interval-component', interval=2*1000, n_intervals=0) # Update every 2 seconds
])

# --- 4. DASH CALLBACKS FOR INTERACTIVITY ---

@app.callback(
    [Output('live-graph', 'figure'), Output('live-kpi-text', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_graph_live(n):
    with lock:
        if not data_deque:
            # Return empty state if no data yet
            empty_fig = go.Figure().update_layout(title="Waiting for sensor data...")
            return empty_fig, "No data yet."
        df = pd.DataFrame(list(data_deque))

    # Create the figure
    fig = go.Figure()
    # Add cumulative energy trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['E_KWh_cumulative'], name='Cumulative Energy (kWh)',
        mode='lines', line=dict(color='orange')
    ))
    # Add zone temperature trace
    fig.add_trace(go.Scatter(
        x=df['timestamp'], y=df['T_z'], name='Zone Temperature (°C)',
        mode='lines', line=dict(color='royalblue'), yaxis='y2'
    ))

    # Update layout for three axes (energy, temp, people)
    fig.update_layout(
        title='Live Simulation Data',
        xaxis_title='Time',
        yaxis=dict(title='Cumulative Energy (kWh)', color='orange'),
        yaxis2=dict(title='Zone Temperature (°C)', color='royalblue', overlaying='y', side='right'),
        yaxis3=dict(
            title='People Present', color='green',
            anchor="free", overlaying="y", side="left", position=0.05
        ),
        legend=dict(x=0, y=1.1, orientation='h'),
        margin=dict(l=60, r=60, t=60, b=60)
    )

    # Get latest data for KPIs
    latest_data = df.iloc[-1]
    total_energy_kwh = latest_data['E_KWh_cumulative']
    total_energy_words = num2words(round(total_energy_kwh, 1))
    n_people = latest_data.get('N_occ', 'N/A')
    current_setpoint = latest_data.get('T_set', 'N/A')

    # KPI text block with Setpoint line
    kpi_text = html.Div([
        html.H4("Current State"),
        html.P(f"Zone Temp: {latest_data['T_z']:.1f} °C"),
        html.P(f"Setpoint: {current_setpoint:.1f} °C"),   # <-- Current setpoint!
        html.P(f"CO₂ Level: {latest_data['CO2_z']:.0f} ppm"),
        html.P(f"Power Draw: {latest_data['P_e']:.2f} kW"),
        html.Hr(style={"borderTop": "1px solid #eee"}),
        html.Div([
            html.H4("People Present", style={"marginBottom": "0px", "color": "#2e8b57"}),
            html.H2(f"{n_people}", style={"marginTop": "0px", "fontWeight": "bold", "color": "#2e8b57"}),
        ], style={
            "padding": "10px 0", 
            "backgroundColor": "#f7fcf9", 
            "borderRadius": "7px", 
            "marginBottom": "18px",
            "textAlign": "center"
        }),
        html.Hr(style={"borderTop": "1px solid #eee"}),
        html.H4("Daily Summary"),
        html.P(f"Total Energy Today:"),
        html.H5(f"{total_energy_kwh:.2f} kWh"),
        html.P(f"({total_energy_words} kilowatt-hours)")
    ])

    return fig, kpi_text

@app.callback(
    Output('update-setpoint-button', 'style'), # Just to provide a dummy output
    [Input('update-setpoint-button', 'n_clicks')],
    [State('temp-setpoint-slider', 'value')]
)
def update_setpoint(n_clicks, temp_setpoint):
    if n_clicks > 0 and mqtt_client is not None:
        control_topic = os.getenv("CONTROL_TOPIC")
        payload = {'T_set': temp_setpoint}
        mqtt_client.mqtt_client.publish(control_topic, str(temp_setpoint))
        print(f"UI published new setpoint '{temp_setpoint}°C' to topic '{control_topic}'")
    
    # Return a default style, as a callback needs an output
    return {'marginTop': '15px'}

# --- 5. SCRIPT ENTRYPOINT ---
if __name__ == '__main__':
    # Initialize the HVAC simulator globally
    hvac_params = Params()
    initial_hvac_state = [18.0, 19.0, 600.0]
    hvac_sim = HVACSimulator(initial_state=initial_hvac_state, params=hvac_params, dt_s=300)
    
    # Start the MQTT client in a background thread
    mqtt_thread = threading.Thread(target=mqtt_service_thread)
    mqtt_thread.daemon = True
    mqtt_thread.start()
    
    # Start the Dash web server
    app.run(host="0.0.0.0", port=8050, debug=True)
