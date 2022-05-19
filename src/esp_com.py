# Handles communication with esp and publishes received encoder values, also listens for velocities to write to the esp
import time
from paho.mqtt import client
from datetime import datetime
import config
import serial
import serial.tools.list_ports
import os
import json

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def vel_msg_received(msg):
    payload = msg.payload
    byte_array = bytearray(payload)
    vel_to_esp(byte_array[0], byte_array[1])

def subscribe(client):
    def on_message(client, userdata, msg):
        # print(f"Received `{msg.payload}` from `{msg.topic}` topic")

        if msg.topic == "vel":
            vel_msg_received(msg)
        

    client.subscribe("vel")
    client.on_message = on_message


def open_serial():
    while True:
        for p in [comport.device for comport in serial.tools.list_ports.comports()]:
            if '/dev/ttyUSB' not in p:
                continue

            os.system(f"sudo chmod 666 {p}")
            ser = serial.Serial(p, 115200, timeout=1)
            time.sleep(3)
            ser.write(b'?')
            data = ser.read_until(b'<esp>')
            print(data)
            if not b'esp' in data:
                continue
            
            return ser

        print("Failed to find an esp. Please restart esp")


def vel_to_esp(vel_r, vel_l):
    ser.write(bytearray([33, vel_r, vel_l])), # 33 is '!'
    print(f"sending vel_r: {vel_r}, vel_l: {vel_l}")


nn = 0
time_startt = time.time()
ser = open_serial()

client = client.Client("esp_com")
client.on_connect = on_connect
client.connect(config.mqtt_broker)
subscribe(client)

print("Esp communicator started")

while True:
    ser.read_until(b'#')
    d = ser.read(8) # Read two uint_32
    encoder_right = int.from_bytes(d[:4], "little")
    encoder_left = int.from_bytes(d[4:], "little")

    nn += 1
    if nn%250 == 0:
        print(f"{datetime.now().strftime('%H:%M:%S')}: encoder recive frequency: {nn/(time.time()-time_startt)} hz")
        time_startt = time.time()
        nn = 0
        print(f"right: {encoder_right}, left: {encoder_left}")

    if ser.in_waiting:
        continue
    client.publish("encoders", json.dumps([encoder_right, encoder_left]))

    # d = ser.readline()
    # print(d)
    client.loop()









