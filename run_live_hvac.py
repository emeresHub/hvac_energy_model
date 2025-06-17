import time
import json
import os
from dotenv import load_dotenv

# Import our custom modules
from hvac_sim.parameters import Params
from hvac_sim.simulator import HVACSimulator
from mqtt_integration.client import MQTTClient, load_mqtt_config

# --- Global Simulator Instance ---
# Initialize model parameters with defaults
hvac_params = Params()

# Set initial state: [Zone Temp, Wall Temp, CO2 concentration]
# We'll start with values that might be typical for an occupied space.
initial_hvac_state = [24.0, 24.0, 600.0]

# Create a single, stateful instance of our simulator
# The time step (dt_s) should match how often you expect new sensor data
hvac_sim = HVACSimulator(initial_state=initial_hvac_state, params=hvac_params, dt_s=300) # 300s = 5 mins

def on_sensor_data_received(msg_dict):
    """
    This is the core callback function. It gets triggered by the MQTT client
    whenever a new message arrives on the subscribed topic.
    """
    print(f"\nReceived sensor data: {msg_dict}")

    try:
        # We expect the message payload to be a JSON string with these keys
        inputs = {
            "T_out": float(msg_dict["T_out"]),
            "N_occ": int(msg_dict["N_occ"]),
            "T_set": float(msg_dict["T_set"]),
            "I_sol": float(msg_dict.get("I_sol", 0.0)) # Optional solar gain
        }

        # Run one step of the simulation with the new inputs
        results = hvac_sim.step(inputs)

        # Print the results
        print("--- HVAC Model Updated ---")
        print(f"  Zone Temperature: {results['T_z']:.2f} °C")
        print(f"  CO2 Level: {results['CO2_z']:.0f} ppm")
        print(f"  Current Power Draw: {results['P_e']:.3f} kW")
        print(f"  Cumulative Energy: {results['E_KWh_cumulative']:.3f} kWh")
        print("--------------------------")

    except (KeyError, ValueError) as e:
        print(f"Error processing message: {e}. Ensure payload is valid JSON with required keys.")

def main():
    """Main function to set up MQTT client and run the application."""
    print("--- Starting Live HVAC Simulation ---")

    # Load MQTT configuration from the .env file
    load_dotenv("local.env")
    mqtt_config = load_mqtt_config()

    # Get the topic from environment variables
    topic = os.getenv("BROKER_TOPIC")
    if not topic:
        raise ValueError("BROKER_TOPIC not set in environment file!")

    # Initialize the MQTT Client
    mqtt_client = MQTTClient(config=mqtt_config, topic=topic)

    # Connect to the MQTT broker
    mqtt_client.connect_mqtt()

    # Subscribe to the topic and link our callback function
    # This tells the client: "When a message comes in, run on_sensor_data_received"
    mqtt_client.subscribe(callback=on_sensor_data_received)

    print(f"MQTT client connected. Subscribed to topic '{topic}'. Waiting for sensor data...")
    print("Press Ctrl+C to exit.")

    # Keep the script running indefinitely to listen for messages
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        mqtt_client.disconnect_mqtt()
        print("Application stopped.")

if __name__ == "__main__":
    main()