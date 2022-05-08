# from tkinter import N
import cv2
import numpy as np
import tcod
from paho.mqtt import client

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def map_msg_received(msg):
    # TODO: Make sure that the goal is still reachable from cur pos and with the new map
    global mapp
    payload = msg.payload
    byte_array = bytearray(payload)
    mapp = np.array(byte_array, dtype=np.int32).reshape(-1, int(len(payload)**0.5))
    assert mapp.shape[0] == mapp.shape[1]
    mapp[mapp<240] = 0
    mapp = np.flipud(mapp)
    mapp[mapp != 0] = np.iinfo(np.int32).max
    show_map(mapp)

def pos_msg_received(msg):
    global pos
    pos = msg.payload.decode()

def goal_msg_received(msg):
    global goal
    global mapp

    map_temp = mapp.copy()

    goal = msg.payload.decode()
    p = pf.get_path(60, 60, 65, 65)

    for x, y in p:
        map_temp[x, y] = 127

    # cv2.imwrite("astar.png", mapp)
    show_map(map_temp)

    client.publish("path", p)


def show_map(mapp):
    cv2.imshow("Path planner", mapp.astype(np.uint8))
    cv2.waitKey(1)


def subscribe(client):
    def on_message(client, userdata, msg):
        global pos
        global goal
        global path

        # print(f"Received `{msg.payload}` from `{msg.topic}` topic")

        if msg.topic == "map":
            map_msg_received(msg)
        elif msg.topic == "pos":
            pos_msg_received(msg)
        elif msg.topic == "goal":
            goal_msg_received(msg)
        else:
            raise Exception(f"Invalid topic: {msg.topic}")
        

    client.subscribe("map")
    client.subscribe("goal")
    client.subscribe("cur_pos")
    client.on_message = on_message


mapp = np.array([1], dtype=np.int32).reshape(1,1)
map_path = None
pos = None
path = None
goal = None

pf = tcod.path.AStar(mapp, 0)


client = client.Client("path_planner")
client.on_connect = on_connect
# client.connect("192.168.1.11")
client.connect("localhost")

subscribe(client)
print("path planner started")
client.loop_forever()
