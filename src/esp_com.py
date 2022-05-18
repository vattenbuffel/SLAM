# Handles communication with esp and publishes received encoder values, also listens for velocities to write to the esp
import time
from paho.mqtt import client
from datetime import datetime
import config
import serial
import serial.tools.list_ports

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
        global n
        global time_start
        # print(f"Received `{msg.payload}` from `{msg.topic}` topic")

        n+=1
        if n%10 == 0:
            print(f"{datetime.now().strftime('%H:%M:%S')}: Map received frequency: {n/(time.time()-time_start)} hz")
            time_start = time.time()
            n = 0

        if msg.topic == "vel":
            vel_msg_received(msg)
        

    client.subscribe("vel")
    client.on_message = on_message


def open_serial():
    for p in [comport.device for comport in serial.tools.list_ports.comports()]:
        if '/dev/ttyUSB' not in p:
            continue

        ser = serial.Serial(p, 115200, timeout=10)
        ser.write(b'?')
        data = ser.read_until(b'esp')
        if not b'esp' in data:
            continue
        
        return ser


    raise Exception("No esp was found")

def vel_to_esp(vel_r, vel_l):
    ser.write(b'!')
    ser.write(vel_r)
    ser.write(vel_l)


n = 0
time_start = time.time()
ser = open_serial()

client = client.Client("esp_com")
client.on_connect = on_connect
client.connect(config.mqtt_broker)

subscribe(client)
print("Esp communicator started")

while True:
    d = ser.read(8) # Read two uint_32

    enc_r = 5
    client.publish("encoder", "hej")

# client.loop_forever()








