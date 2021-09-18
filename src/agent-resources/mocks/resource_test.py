import time
import paho.mqtt.client as mqtt

import time

CAMERA_DATA = '''{
    "id" : "cam5",
    "state": "OK",
    "ip": "localhost",
    "type": "VIDEO"
}'''

client = None
def on_connect(c, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        client.publish("passive_resources/building/block1/floor0/lobby/camera1", CAMERA_DATA)
        print("connected OK")
    else:
        print("Bad connection Returned code=",rc)




mqtt.Client.connected_flag=False
client = mqtt.Client()
client.on_connect = on_connect
client.loop_start()

client.connect("localhost", 1883, 60)
while not client.connected_flag: #wait in loop
    print("In wait loop")
    time.sleep(1)




