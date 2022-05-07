import os
from math import floor
from adafruit_rplidar import RPLidar
from paho.mqtt import client
import json


# Setup the RPLidar
PORT_NAME = '/dev/ttyUSB0'
lidar = RPLidar(None, PORT_NAME, timeout=3)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)
client = client.Client("Rpi4")
client.on_connect = on_connect
client.connect("localhost")


def process_data(data):
    client.publish("lidar_data", json.dumps(data))

scan_data = [0]*360

try:
    for scan in lidar.iter_scans():
        for (_, angle, distance) in scan:
            scan_data[min([359, floor(angle)])] = distance
        process_data(scan_data)

except KeyboardInterrupt:
    print('Stopping.')

# except adafruit_rplidar.RPLidarException as e:
#     pass

lidar.stop()
lidar.disconnect()