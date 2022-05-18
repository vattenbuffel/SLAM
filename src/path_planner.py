import cv2
import numpy as np
import tcod
from paho.mqtt import client
import json
import config
import time

# This should broadcast it's calculatd path on mqtt


def mm_to_pixel(x, y):
    convesion_factor = config.map_size_m*1000 / config.map_size_pixels
    x = x/convesion_factor
    y = y/convesion_factor
    return int(x), int(y)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def prepare_mapp_for_pathplan(mapp):
    # Changes values/weights in mapp to be 0 for blocked area and very very big for other areas, to indicate cost
    mapp[mapp<240] = 0
    mapp[mapp != 0] = np.iinfo(np.int32).max

def map_msg_received(msg):
    global mapp
    global path
    global n
    global time_start


    if n%25 == 0:
        print(f"Map received frequency: {n/(time.time()-time_start)} hz")
        time_start = time.time()
        n = 0

    payload = msg.payload
    byte_array = bytearray(payload)
    mapp = np.array(byte_array, dtype=np.int32).reshape(-1, int(len(payload)**0.5))
    assert mapp.shape[0] == mapp.shape[1]
    mapp = np.flipud(mapp)
    prepare_mapp_for_pathplan(mapp)
    
    if show_img:
        cv2.imshow("Path planner", mapp.astype(np.uint8))
        cv2.waitKey(1)

    # TODO: Make sure that the goal is still reachable from cur pos and with the new map
    # if(len(path) > 0):
    #     # TODO CHECK IF ANY OF THE PATH IS 0. this means it's unavailable now
    #     p, _, _ = path_plan()
    #     if(len(p) < 0):
    #         path = []
    #         publish_path()



def publish_path():
    client.publish("path", json.dumps(path))

def pos_msg_received(msg):
    global pos
    pos = json.loads(msg.payload.decode())

def goal_msg_received(msg):
    global goal
    global mapp
    global path

    goal = json.loads(msg.payload.decode())
    path, pos_cur, pos_goal = path_plan()

    if(len(path) == 0):
        print(f"path_planner: Failed to find a path from: {pos_cur} to {pos_goal}")
        return

    for x, y in path:
        mapp[x, y] = 127

    if show_img:
        cv2.imshow("Path planner with path", mapp.astype(np.uint8))
        cv2.waitKey(1)

    publish_path()

def path_plan():
    x_cur, y_cur = mm_to_pixel(pos[0], pos[1])
    x_goal, y_goal = mm_to_pixel(goal[0], goal[1])

    pf = tcod.path.AStar(mapp, 0)
    p = pf.get_path(y_cur, x_cur, y_goal, x_goal)# x and y are in this order because rows are first in matrices

    return p, (x_cur, y_cur), (x_goal, y_goal)

def subscribe(client):
    def on_message(client, userdata, msg):
        # print(f"Received `{msg.payload}` from `{msg.topic}` topic")

        if msg.topic == "map":
            map_msg_received(msg)
        elif msg.topic == "pos":
            pos_msg_received(msg)
        elif msg.topic == "goal":
            goal_msg_received(msg)
        

    client.subscribe("map")
    client.subscribe("goal")
    client.subscribe("pos")
    client.on_message = on_message


mapp = np.array([1], dtype=np.int32).reshape(1,1)
pos = None
path = []
goal = None

n = 0
time_start = time.time()

# Figure out if images can be shown or not
show_img = False
try:
    img = cv2.imread("imgs/pp_start.png")
    cv2.imshow("Start image", img)
    cv2.waitKey(1000)
    print(f"Can show images. Starting in head mode")

except Exception as e:
    print(f"Can't show images. Starting in headless mode")

client = client.Client("path_planner")
client.on_connect = on_connect
client.connect(config.mqtt_broker)

subscribe(client)
print("path planner started")
client.loop_forever()
