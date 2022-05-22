# Ideally we could use all 250 or so samples that the RPLidar delivers in one 
# scan, but on slower computers you'll get an empty map and unchanging position
# at that rate.
MIN_SAMPLES   = 150

import config
from breezyslam.algorithms import RMHC_SLAM
from breezyslam.sensors import RPLidarA1 as LaserModel
if config.lidar_sim:
    from simulator.lidar_simulator import Lidar as Lidar
else:
    from adafruit_rplidar import RPLidar as Lidar
import os
from paho.mqtt import client
import json
import time
from datetime import datetime
from Pelle import Pelle
import json

headless = False
try:
    from roboviz import MapVisualizer
    print(f"Starting in not headless mode")
except Exception as e:
    headless = True
    print(f"Starting in headless mode")


def create_lidar():
    while True:
        for i in range(5):
            for _ in range(3):
                try:
                    # device_path = f"/dev/ttyUSB{i}"
                    device_path = f"/dev/ttyUSB1"
                    os.system(f"sudo chmod 666 {device_path}")
                    lidar = Lidar(None, device_path, timeout=3)
                    # Create an iterator to collect scan data from the RPLidar
                    iterator = lidar.iter_scans()


                    # First scan is crap, so ignore it
                    next(iterator)
                    return lidar, iterator

                except Exception as e:
                    print(f"exception {e} happend")

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)

def publish_data(map, pos):
    client.publish("map", map)
    client.publish("pos", json.dumps(pos))

def subscribe(client):
    def on_message(client, userdata, msg):
        global enc_left
        global enc_right
        # print(f"Received `{msg.payload}` from `{msg.topic}` topic")

        if msg.topic == "encoders":
            data = json.loads(msg.payload)
            enc_right = data[0]
            enc_left = data[1]
        

    client.subscribe("encoders")
    client.on_message = on_message


if __name__ == '__main__':
    enc_left, enc_right = 0,0
    client = client.Client("slam")
    client.on_connect = on_connect
    client.connect(config.mqtt_broker)
    subscribe(client)
    client.loop_start()

    # Create an RMHC SLAM object with a laser model and optional robot model
    slam = RMHC_SLAM(LaserModel(), config.map_size_pixels, config.map_size_m, map_quality=5, max_search_iter=10000)
    if not headless:
        viz = MapVisualizer(config.map_size_pixels, config.map_size_m, 'SLAM')

    # Initialize an empty trajectory
    trajectory = []

    # Initialize empty map
    mapbytes = bytearray(config.map_size_pixels * config.map_size_pixels)

    n = 0
    time_start = time.time()
    last_pub_t_s = time.time()
    # We will use these to store previous scan in case current scan is inadequate
    previous_distances = None
    previous_angles    = None

    lidar, iterator = create_lidar()
    pelle = Pelle()

    print("slam started")
    while True:
        n += 1
        if n%25 == 0:
            print(f"{datetime.now().strftime('%H:%M:%S')}: Slam frequency: {n/(time.time()-time_start)} hz")
            time_start = time.time()
            n = 0

        # Extract (quality, angle, distance) triples from current scan
        items = [item for item in next(iterator)]

        # Extract distances and angles from triples
        distances = [item[2] for item in items]
        # angles    = [360-item[1] for item in items]
        angles    = [item[1] for item in items]

        # Publish lidar data
        if config.slam_pub_lidar:
            client.publish("lidar_data", json.dumps((distances, angles)))

        # Compute pose change
        pose_change = pelle.computePoseChange(enc_left, enc_right)
        # print(f"Pose change: {pose_change}")

        # Update SLAM with current Lidar scan and scan angles if adequate
        if len(distances) > MIN_SAMPLES:
            slam.update(distances, scan_angles_degrees=angles, pose_change=pose_change)
            previous_distances = distances.copy()
            previous_angles    = angles.copy()
            print(f"Good amount of lidar samples: {len(angles)}")

        # If not adequate, use previous
        elif previous_distances is not None:
            print(f"Warning too few lidar samples: {len(angles)}")
            slam.update(previous_distances, scan_angles_degrees=previous_angles, pose_change=pose_change)

        # Publish
        if time.time() - last_pub_t_s > 1/config.map_pub_freq_hz:
            # Get current robot position
            x, y, theta = slam.getpos()

            # Get current map bytes as grayscale
            slam.getmap(mapbytes)
            publish_data(mapbytes, (x,y,theta, slam.sigma_xy_mm, slam.sigma_theta_degrees))

            last_pub_t_s = time.time()

        # Display map and robot pose, exiting gracefully if user closes it
        if not headless:
            if not viz.display(x/1000., y/1000., theta, mapbytes):
                exit(0)



    # Shut down the lidar connection
    lidar.stop()
    lidar.disconnect()
