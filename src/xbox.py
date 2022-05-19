from evdev import InputDevice, categorize, ecodes
import config
from paho.mqtt import client

class Motor:
    def __init__(self):
        self.throttle_val = 0
        self.steering_val = 0


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
    else:
        print("Failed to connect, return code %d\n", rc)


def read_inputs():
    for event in gamepad.read_loop():
        if event.type == ecodes.EV_ABS:
            if event.code == GAS_BUTTON:
                return (GAS_BUTTON, event.value/1024)
            elif event.code == BREAK_BUTTON:
                return(BREAK_BUTTON, event.value/1024)
            elif event.code == LEFT_X:
                return(LEFT_X, event.value/32768 - 1)

def output(inputs):
    input_event, input_value = inputs

    if input_event == GAS_BUTTON :
        right_motor.throttle_val = input_value 
        left_motor.throttle_val = input_value
    elif input_event == BREAK_BUTTON:
        right_motor.throttle_val = -input_value 
        left_motor.throttle_val = -input_value

    if input_event == LEFT_X:
        right_motor.steering_val = -input_value
        left_motor.steering_val = input_value

    # Remap velocites to what esp expects
    right_vel = 100*(right_motor.throttle_val-right_motor.steering_val)
    right_vel = min(right_vel, 100)
    right_vel = max(right_vel, -100)
    right_vel = int(right_vel)
    right_vel = right_vel + 100 if right_vel > 0 else abs(right_vel)
    
    left_vel = 100*(left_motor.throttle_val-left_motor.steering_val)
    left_vel = min(left_vel, 100)
    left_vel = max(left_vel, -100)
    left_vel = int(left_vel)
    left_vel = left_vel + 100 if left_vel > 0 else abs(left_vel)

    client.publish("vel", bytearray([right_vel, left_vel]))


gamepad = InputDevice('/dev/input/event1')
print(gamepad)
LEFT_X = 0
GAS_BUTTON = 9
BREAK_BUTTON = 10

right_motor = Motor()
left_motor = Motor()


client = client.Client("xbox")
client.on_connect = on_connect
client.connect(config.mqtt_broker)

print("Xbox input started")

# This is the main loop
while True:
    inputs = read_inputs()
    if inputs is not None:
        output(inputs)

    client.loop()