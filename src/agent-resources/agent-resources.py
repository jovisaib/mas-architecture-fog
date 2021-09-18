import time, csv
import paho.mqtt.client as mqtt
import json

import time
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message



class ResourcesAgent(Agent):
    class MainBehaviour(CyclicBehaviour):

        async def on_start(self):
            self.resources = {}
            self.lastRes = None

            print("Agent connecting to MQTT...")
            def on_connect(client, userdata, flags, rc):
                if rc==0:
                    client.connected_flag = True
                    print("connected OK")
                    client.subscribe("passive_resources/building/block1/floor0/lobby/#")
                else:
                    print("Bad connection Returned code=",rc)


            def on_message(client, userdata, msg):
                data = json.loads(msg.payload)
                self.resources[data["id"]] = data
                self.lastRes = json.dumps(data)

                with open('registry.csv', 'w', newline='') as myfile:
                    dict_writer = csv.DictWriter(myfile, fieldnames=["id", "type", "state", "ip"])
                    dict_writer.writeheader()
                    for k, v in self.resources.items():
                        print(v)
                        dict_writer.writerow(v)


            mqtt.Client.connected_flag = False
            self.client = mqtt.Client()
            self.client.on_connect = on_connect
            self.client.on_message = on_message
            self.client.loop_start()

            self.client.connect("localhost", 1883, 60)
            while not self.client.connected_flag: #wait in loop
                print("In wait loop")
                time.sleep(1)


        async def run(self):
            if self.lastRes != None:
                msg = Message(to="peoplecounting@localhost")
                msg.set_metadata("performative", "inform")
                msg.set_metadata("ontology", "default_ontology")
                msg.body = json.dumps(self.lastRes)           
                await self.send(msg)
                self.lastRes = None

        async def on_end(self):
            self.client.disconnect()

    async def setup(self):
	    print("Agent starting . . .")
	    self.resourcesBeh = self.MainBehaviour()
	    self.add_behaviour(self.resourcesBeh)

if __name__ == "__main__":
    resourcesAgent = ResourcesAgent("resources@localhost", "resources")
    future = resourcesAgent.start()
    future.result()

    while not resourcesAgent.resourcesBeh.is_killed():
	    try:
		    time.sleep(1)
	    except KeyboardInterrupt:
		    break 
        
    resourcesAgent.stop()
    print("Resource agent stopped")