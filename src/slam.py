LIDAR_DEVICE            = '/dev/ttyUSB0'

# Ideally we could use all 250 or so samples that the RPLidar delivers in one 
# scan, but on slower computers you'll get an empty map and unchanging position
# at that rate.
MIN_SAMPLES   = 150

from breezyslam.algorithms import RMHC_SLAM
from breezyslam.sensors import RPLidarA1 as LaserModel
from adafruit_rplidar import RPLidar as Lidar
import os
from paho.mqtt import client
import json
import config
import time

if __name__ == '__main__':
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    client = client.Client("slam")
    client.on_connect = on_connect
    client.connect(config.mqtt_broker)

    def publish_data(map, pos):
        client.publish("map", map)
        client.publish("pos", json.dumps(pos))


    # Create an RMHC SLAM object with a laser model and optional robot model
    slam = RMHC_SLAM(LaserModel(), config.map_size_pixels, config.map_size_m)

    # Initialize an empty trajectory
    trajectory = []

    # Initialize empty map
    mapbytes = bytearray(config.map_size_pixels * config.map_size_pixels)

    n = 0
    time_start = time.time()

    print("slam started")
    while True:
        try:
            os.system(f"sudo chmod 666 {LIDAR_DEVICE}")
            lidar = Lidar(None, LIDAR_DEVICE, timeout=3)
            # Create an iterator to collect scan data from the RPLidar
            iterator = lidar.iter_scans()

            # We will use these to store previous scan in case current scan is inadequate
            previous_distances = None
            previous_angles    = None

            # First scan is crap, so ignore it
            next(iterator)
            break

        except Exception as e:
            print(f"exception {e} happend")

    while True:
        n += 1
        if n%25 == 0:
            print(f"slam frequency: {n/(time.time()-time_start)} hz")
            time_start = time.time()
            n = 0


        # Extract (quality, angle, distance) triples from current scan
        items = [item for item in next(iterator)]

        # Extract distances and angles from triples
        distances = [item[2] for item in items]
        angles    = [360-item[1] for item in items]
        if n % 10 == 0:
            print(f"Got: {len(angles)} lidar measurements samples")

        # Update SLAM with current Lidar scan and scan angles if adequate
        if len(distances) > MIN_SAMPLES:
            slam.update(distances, scan_angles_degrees=angles)
            previous_distances = distances.copy()
            previous_angles    = angles.copy()

        # If not adequate, use previous
        elif previous_distances is not None:
            slam.update(previous_distances, scan_angles_degrees=previous_angles)

        # Get current robot position
        x, y, theta = slam.getpos()

        # Get current map bytes as grayscale
        slam.getmap(mapbytes)
        publish_data(mapbytes, (x,y,theta, slam.sigma_xy_mm, slam.sigma_theta_degrees))

    # Shut down the lidar connection
    lidar.stop()
    lidar.disconnect()
