from roboviz import MapVisualizer
import config
from paho.mqtt import client
import json
from datetime import datetime
import time

pos = None
n = 0
time_start_s = time.time()

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
        global n
        global time_start_s

        payload = msg.payload
        if msg.topic == "map":
            n+=1
            if n % 10 == 0:
                print(f"{datetime.now()}: Recive map frequency: {n/(time.time() - time_start_s)} hz")
                time_start_s = time.time()
                n = 0

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
