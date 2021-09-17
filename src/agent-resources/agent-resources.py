import time, csv
import paho.mqtt.client as mqtt

import time
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour



class ResourcesAgent(Agent):
    class MainBehaviour(CyclicBehaviour):


        async def on_start(self):
            print("Agent connecting to MQTT...")
            def on_connect(client, userdata, flags, rc):
                if rc==0:
                    self.client.connected_flag=True #set flag
                    print("connected OK")
                else:
                    print("Bad connection Returned code=",rc)

                client.subscribe("passive_resources/building/block1/floor0/lobby/#")

            def on_message(client, userdata, msg):
                print(msg.topic+" "+str(msg.payload))


            mqtt.Client.connected_flag=False
            self.client = mqtt.Client()
            self.client.on_connect = on_connect
            self.client.on_message = on_message
            self.client.loop_start()

            self.client.connect("localhost", 1883, 60)
            while not self.client.connected_flag: #wait in loop
                print("In wait loop")
                time.sleep(1)


        async def run(self):
            pass

        async def on_end(self):
            self.client.disconnect()

    async def setup(self):
	    print("Agent starting . . .")
	    self.resourcesBeh = self.MainBehaviour()
	    self.add_behaviour(self.resourcesBeh)

if __name__ == "__main__":
    resourcesAgent = ResourcesAgent("test@localhost", "test")
    future = resourcesAgent.start()
    future.result()

    while not resourcesAgent.resourcesBeh.is_killed():
	    try:
		    time.sleep(1)
	    except KeyboardInterrupt:
		    break 
        
    resourcesAgent.stop()
    print("Resource agent stopped")