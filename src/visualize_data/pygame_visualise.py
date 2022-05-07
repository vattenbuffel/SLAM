# import pygame
from paho.mqtt import client
import json
import pygame
import math

WHITE =     (255, 255, 255)
BLACK =       (0,   0,   0)
(width, height) = (1920, 1080)

pygame.init()
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("TUFF")
screen.fill(BLACK)
pygame.display.update()

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)


def subscribe(client):
    def on_message(client, userdata, msg):
        # print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        payload = msg.payload.decode()
        data = json.loads(payload)

        screen.fill(BLACK)
        for i in range(360):
            alpha_rad = math.radians(i)
            d = data[i]

            x = d*math.cos(alpha_rad) + width/2
            y = d*math.sin(alpha_rad) + height/2

            pygame.draw.circle(screen, WHITE, (x, y), 1)

        pygame.display.update()




    client.subscribe("lidar_data")
    client.on_message = on_message


client = client.Client("Pygame")
client.on_connect = on_connect
client.connect("192.168.1.11")
subscribe(client)
# client.loop_forever()

while True:
    client.loop()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print("Goodbye")
            exit()