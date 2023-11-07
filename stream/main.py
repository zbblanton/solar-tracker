import json
import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

# InfluxDB settings
INFLUXDB_URL = 'http://10.0.0.21:8086'
INFLUXDB_TOKEN = 'fmKFpdZxgqvsTJHrFBQpq2NtEWASfi4PTCsdDBve_1e8ign8lzfX0TiwpTL-hksgcyetRWNh5desSa-yEMO2Gw==' # Just a development token
INFLUXDB_ORG = 'org'
INFLUXDB_BUCKET = 'solar-tracker'

# MQTT settings
MQTT_BROKER_URL = '10.0.0.21'
MQTT_BROKER_PORT = 1883
MQTT_TOPIC = 'solar/controlunit/1/status'

# Initialize InfluxDB Client
client = InfluxDBClient(url=INFLUXDB_URL, token=INFLUXDB_TOKEN, org=INFLUXDB_ORG)
write_api = client.write_api(write_options=SYNCHRONOUS)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    client.subscribe(MQTT_TOPIC)

def on_message(client, userdata, msg):
    print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")

    # Format from mqtt
    # {"position": 90, "supply-voltage": 4.73, "internal_temp": 28, "battery-voltage": 0.12}

    # Write data to InfluxDB
    try:
        data = json.loads(msg.payload.decode())
        suppy_voltage = data.get("supply-voltage")
        internal_temp = data.get("internal_temp")
        battery_voltage = data.get("battery-voltage")
        position = data.get("position")
        point = Point("status").tag("topic", msg.topic).field("position", position).field("supply-voltage", suppy_voltage).field("internal_temp", internal_temp).field("battery-voltage", battery_voltage)

        # write_api.write(write_options=SYNCHRONOUS).write(bucket=INFLUXDB_BUCKET, org=org_id, record=point)
        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
        print("Data written to InfluxDB")
    except Exception as e:
        print(f"Failed to write to InfluxDB: {e}")

# Initialize and configure MQTT client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

# Connect to MQTT broker
mqtt_client.connect(MQTT_BROKER_URL, MQTT_BROKER_PORT, 60)

# Start the loop
mqtt_client.loop_start()

try:
    # Loop forever
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting...")
finally:
    mqtt_client.loop_stop()
    mqtt_client.disconnect()
    client.close()