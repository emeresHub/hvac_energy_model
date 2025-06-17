# -----------------------------------------------------------------------------
# Script Name: client.py
# Date Created: 2025-04-08
# Last Modified: 2025-06-16
# Author: Emere Ejor
# Description:
#   This script initializes an MQTT client with loaded condfigs, connects to an MQTT broker, and 
#   uses paho-MQTT to publish data and also subscribe to data to and from a specific topic respectively.
# -----------------------------------------------------------------------------

import logging
import json
from paho.mqtt import client as paho_mqtt_client
from dotenv import load_dotenv
import os

# Configure logging for MQTT Broker interactions
logging.basicConfig(
    level=logging.INFO,  # Minimum logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log format
    handlers=[logging.StreamHandler()]  # Output logs to terminal
)

class MQTTClientConfig:
    """
    Configuration class to handle MQTT client setup, including credentials.
    """

    def __init__(self, client_id, broker_address, port) -> None:
        """
        Initialize the MQTT client configuration.

        Args:
            client_id (str): Unique identifier for the MQTT client.
            broker_address (str): Address of the MQTT broker.
            port (int): Port to connect to the MQTT broker.
        """
        self.has_credentials = False
        self.client_id = client_id
        self.broker_address = broker_address
        self.port = port
        self.username = None
        self.password = None

    def set_credentials(self, username, password):
        """
        Set the username and password for the MQTT client.

        Args:
            username (str): The MQTT client's username.
            password (str): The MQTT client's password.
        """
        self.has_credentials = True
        self.username = username
        self.password = password


class MQTTClient:
    """
    MQTT client that handles connection, publishing, subscribing, and disconnection.
    """

    def __init__(self, config, topic) -> None:
        """
        Initialize the MQTT client with the configuration and topic.

        Args:
            config (MQTTClientConfig): Configuration for the MQTT client.
            topic (str): Topic to subscribe to or publish messages on.
        """
        self.logger = logging.getLogger("mqtt")
        self.mqtt_config = config
        self.topic = topic
        self.mqtt_client = paho_mqtt_client.Client(self.mqtt_config.client_id)

        # Set logging level to INFO and log client creation
        self.logger.setLevel(logging.INFO)
        self.logger.info("MQTT Client %s created", self.mqtt_config.client_id)

    def connect_mqtt(self):
        """
        Connect the MQTT client to the broker and start the MQTT loop.
        """

        def on_connect(client, userdata, flags, rc):
            """
            Callback function triggered on successful connection to the broker.

            Args:
                client: The MQTT client instance.
                userdata: User-defined data passed to the callback.
                flags: Response flags from the broker.
                rc: Connection result code.
            """
            if rc == 0:
                self.logger.info("Connected to MQTT Broker on topic %s successfully", self.topic)
            else:
                self.logger.info("Failed to connect to MQTT Broker on topic %s, return code %d", self.topic, rc)

        def on_disconnect(client, userdata, rc):
            """
            Callback function triggered on disconnection from the broker.

            Args:
                client: The MQTT client instance.
                userdata: User-defined data passed to the callback.
                rc: Disconnection result code.
            """
            if rc != 0:
                self.logger.info("Unexpected disconnection (return code %d). Reconnecting ......", rc)
            else:
                self.logger.info("Client disconnected successfully")

        # Assign callback functions for connection and disconnection
        self.mqtt_client.on_connect = on_connect
        self.mqtt_client.on_disconnect = on_disconnect

        # If credentials are provided, set them for the client
        if self.mqtt_config.has_credentials:
            self.mqtt_client.username_pw_set(self.mqtt_config.username, self.mqtt_config.password)

        # Connect to the MQTT broker and start the MQTT loop in the background
        self.mqtt_client.connect(self.mqtt_config.broker_address, self.mqtt_config.port)
        self.mqtt_client.loop_start()

    def disconnect_mqtt(self):
        """
        Disconnect the MQTT client from the broker and stop the loop.
        """
        self.logger.info("MQTT Broker Client disconnected successfully")
        self.mqtt_client.disconnect()
        self.mqtt_client.loop_stop()

    def publish(self, msg, callback):
        """
        Publish a message to the MQTT topic.

        Args:
            msg (str): The message to be published.
            callback (function): A callback function to modify or prepare the message.
        """
        self.logger.info("Published to topic %s", self.topic)

        # Process the message using the callback
        msg = callback(msg)
        
        # Publish the message to the specified topic
        self.mqtt_client.publish(self.topic, msg)

    def subscribe(self, callback=None):
        """
        Subscribe to the MQTT topic and handle incoming messages.

        Args:
            callback (function, optional): The callback function to handle incoming messages. Defaults to None.
        """
        self.logger.info("Subscribed to MQTT Broker topic %s", self.topic)

        def on_message(client, userdata, msg):
            """
            Callback function triggered when a message is received on the subscribed topic.

            Args:
                client: The MQTT client instance.
                userdata: User-defined data passed to the callback.
                msg: The message received from the broker.
            """
            msg_dict = json.loads(msg.payload)

            if callback is not None:
                callback(msg_dict)
        
        # Assign the callback function for message handling and subscribe to the topic
        self.mqtt_client.on_message = on_message
        self.mqtt_client.subscribe(self.topic)


def load_mqtt_config() -> MQTTClientConfig:
    """
    Load MQTT client configuration from environment variables and dotenv files.

    Returns:
        MQTTClientConfig: The loaded MQTT client configuration object.
    """
    if os.getenv("ENV") == "publish-local":
        load_dotenv("publisher-local.env")
    
    if os.getenv("ENV") == "subscribe-local":
        load_dotenv("subscriber-local.env")

    # Retrieve configuration values from environment variables
    broker_address = os.getenv("BROKER_ADDRESS")
    broker_port = int(os.getenv("BROKER_PORT"))
    client_id = os.getenv("CLIENT_ID")
    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    # Initialize and return the MQTTClientConfig object
    mqtt_client_config = MQTTClientConfig(client_id=client_id, broker_address=broker_address, port=broker_port)

    # Set credentials if provided
    if username is not None and password is not None:
        mqtt_client_config.set_credentials(username=username, password=password)

    return mqtt_client_config


def load_mqtt_client(config: MQTTClientConfig) -> MQTTClient:
    """
    Initialize the MQTT client with the provided configuration.

    Args:
        config (MQTTClientConfig): The configuration for the MQTT client.

    Returns:
        MQTTClient: The initialized MQTT client instance.
    """
    broker_topic = os.getenv("BROKER_TOPIC")

    # Create and return the MQTT client instance
    mqtt_client = MQTTClient(config=config, topic=broker_topic)

    return mqtt_client


def load_mqtt_config_with_parameters(broker_address=str, broker_port=int, client_id=str, username=str, password=str) -> MQTTClientConfig:
    """
    Load MQTT client configuration using explicit parameters.

    Args:
        broker_address (str): Address of the MQTT broker.
        broker_port (int): Port number for the MQTT broker.
        client_id (str): MQTT client identifier.
        username (str): MQTT client username.
        password (str): MQTT client password.

    Returns:
        MQTTClientConfig: The configured MQTTClientConfig object.
    """
    # Initialize configuration with provided parameters
    mqtt_client_config = MQTTClientConfig(broker_address=broker_address, broker_port=broker_port, client_id=client_id, username=username, password=password)

    # Set credentials if provided
    if username is not None and password is not None:
        mqtt_client_config.set_credentials(username=username, password=password)

    return mqtt_client_config


def load_mqtt_client_with_parameters(config: MQTTClientConfig, broker_topic=str) -> MQTTClient:
    """
    Initialize the MQTT client with the provided configuration and topic.

    Args:
        config (MQTTClientConfig): The configuration for the MQTT client.
        broker_topic (str): The topic to be used for subscribing/publishing.

    Returns:
        MQTTClient: The initialized MQTT client instance.
    """
    # Create and return the MQTT client instance
    mqtt_client = MQTTClient(config=config, topic=broker_topic)

    return mqtt_client
