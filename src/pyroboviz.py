from roboviz import MapVisualizer
import config
from paho.mqtt import client
import json

pos = None

# Initialize empty map
mapbytes = bytearray(config.map_size_pixels * config.map_size_pixels)

# Set up a SLAM display
viz = MapVisualizer(config.map_size_pixels, config.map_size_m, 'SLAM')

def disp():
    x, y, theta, = pos[0], pos[1], pos[2]
    viz.display(x/1000., y/1000., theta, mapbytes)


def subscribe(client):
    def on_message(client, userdata, msg):
        global pos
        global mapbytes

        payload = msg.payload
        if msg.topic == "map":
            mapbytes = bytearray(payload)
            if not pos is None:
                disp()
        elif msg.topic == "pos":
            pos = json.loads(msg.payload.decode())
            
    client.subscribe("map")
    client.subscribe("pos")
    client.on_message = on_message

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)


client = client.Client("pyroboviz")
client.on_connect = on_connect
client.connect(config.mqtt_broker)

subscribe(client)
print("pyroboviz started")
client.loop_forever()