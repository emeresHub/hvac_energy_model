import paho.mqtt.client as mqtt
import time
import json
import random
import os
from dotenv import load_dotenv

# --- Configuration ---
load_dotenv("local.env")
BROKER_ADDRESS = os.getenv("BROKER_ADDRESS")
PORT = int(os.getenv("BROKER_PORT"))
SENSOR_TOPIC = os.getenv("BROKER_TOPIC")
CONTROL_TOPIC = os.getenv("CONTROL_TOPIC")
CLIENT_ID = "interactive_sensor_publisher"

# Global variable to hold the current setpoint, with a default
current_setpoint = 24.0

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Publisher connected successfully.")
        # Subscribe to the control topic upon connection
        client.subscribe(CONTROL_TOPIC)
        print(f"Subscribed to control topic: {CONTROL_TOPIC}")
    else:
        print(f"Failed to connect, return code {rc}\n")

def on_message(client, userdata, msg):
    """Callback for when a message is received on the control topic."""
    global current_setpoint
    try:
        new_setpoint = float(msg.payload.decode())
        current_setpoint = new_setpoint
        print(f"\nReceived new setpoint from GUI: {current_setpoint}°C\n")
    except ValueError:
        print(f"Could not parse setpoint from payload: {msg.payload}")

def run():
    client = mqtt.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER_ADDRESS, PORT)
    client.loop_start() # Handles reconnects and processes messages automatically

    while True:
        # Simulate changing sensor data
        temp_outside = round(25 + random.uniform(-2, 2), 2)
        occupants =  random.randint(0, 15)
        
        # This data structure must match what the subscriber expects
        # CRUCIALLY, it now uses the 'current_setpoint' updated by the GUI
        data = {
            "T_out": temp_outside,
            "N_occ": occupants,
            "T_set": current_setpoint 
        }
        
        msg = json.dumps(data)
        result = client.publish(SENSOR_TOPIC, msg)
        status = result[0]
        
        if status == 0:
            print(f"Sent `{msg}` to topic `{SENSOR_TOPIC}`")
        else:
            print(f"Failed to send message to topic {SENSOR_TOPIC}")
        
        time.sleep(10) # Publish new data every 10 seconds

if __name__ == '__main__':
    run()