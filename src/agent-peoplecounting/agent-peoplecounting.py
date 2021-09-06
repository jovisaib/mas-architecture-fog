from libs.centroidtracker import CentroidTracker
from libs.trackableobject import TrackableObject
from imutils.video import VideoStream
from imutils.video import FPS
from libs import config
import time, csv
import numpy as np
import imutils
import time, dlib, cv2, datetime
from itertools import zip_longest

import time
import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour



t0 = time.time()



class MainAgent(Agent):
	class PeopleCounterAgent(CyclicBehaviour):
		async def on_start(self):
			print("Starting behaviour . . .")

			self.BASE_CONFIDENCE = 0.4
			self.SKIP_FRAMES = 30
			self.CLASSES = ["background", "aeroplane", "bicycle", "bird", "boat",
				"bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
				"dog", "horse", "motorbike", "person", "pottedplant", "sheep",
				"sofa", "train", "tvmonitor"]

			self.net = cv2.dnn.readNetFromCaffe("mobilenet_ssd/MobileNetSSD_deploy.prototxt", "mobilenet_ssd/MobileNetSSD_deploy.caffemodel")

			self.vs = VideoStream(config.url).start()
			time.sleep(2.0)


			self.writer = None
			self.W = None
			self.H = None

			self.ct = CentroidTracker(maxDisappeared=40, maxDistance=50)
			self.trackers = []
			self.trackableObjects = {}

			self.totalFrames = 0
			self.totalDown = 0
			self.totalUp = 0
			self.x = []
			self.empty=[]
			self.empty1=[]

			self.fps = FPS().start()



		async def run(self):
			self.frame = self.vs.read()
			self.frame = imutils.resize(self.frame, width = 500)
			rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)

			if self.W is None or self.H is None:
				(self.H, self.W) = self.frame.shape[:2]

			status = "Waiting"
			rects = []

			if self.totalFrames % self.SKIP_FRAMES == 0:
				status = "Detecting"
				self.trackers = []

				blob = cv2.dnn.blobFromImage(self.frame, 0.007843, (self.W, self.H), 127.5)
				self.net.setInput(blob)
				detections = self.net.forward()

				for i in np.arange(0, detections.shape[2]):
					confidence = detections[0, 0, i, 2]


					if confidence > self.BASE_CONFIDENCE:
						idx = int(detections[0, 0, i, 1])

						if self.CLASSES[idx] != "person":
							continue

						box = detections[0, 0, i, 3:7] * np.array([self.W, self.H, self.W, self.H])
						(startX, startY, endX, endY) = box.astype("int")


						tracker = dlib.correlation_tracker()
						rect = dlib.rectangle(startX, startY, endX, endY)
						tracker.start_track(rgb, rect)

						self.trackers.append(tracker)
			else:
				for tracker in self.trackers:
					status = "Tracking"

					tracker.update(rgb)
					pos = tracker.get_position()

					startX = int(pos.left())
					startY = int(pos.top())
					endX = int(pos.right())
					endY = int(pos.bottom())

					rects.append((startX, startY, endX, endY))

			cv2.line(self.frame, (0, self.H // 2), (self.W, self.H // 2), (0, 0, 0), 3)


			objects = self.ct.update(rects)

			for (objectID, centroid) in objects.items():
				to = self.trackableObjects.get(objectID, None)

				# if there is no existing trackable object, create one
				if to is None:
					to = TrackableObject(objectID, centroid)

				else:
					y = [c[1] for c in to.centroids]
					direction = centroid[1] - np.mean(y)
					to.centroids.append(centroid)

					# check to see if the object has been counted or not
					if not to.counted:
						if direction < 0 and centroid[1] < self.H // 2:
							self.totalUp += 1
							self.empty.append(self.totalUp)
							to.counted = True

						elif direction > 0 and centroid[1] > self.H // 2:
							self.totalDown += 1
							self.empty1.append(self.totalDown)
							if sum(self.x) >= config.Threshold:
								cv2.putText(self.frame, "-ALERT: People limit exceeded-", (10, frame.shape[0] - 80),
									cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 2)

							to.counted = True
							
						self.x = []
						self.x.append(len(self.empty1)-len(self.empty))


				self.trackableObjects[objectID] = to

				text = "ID {}".format(objectID)
				cv2.putText(self.frame, text, (centroid[0] - 10, centroid[1] - 10),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
				cv2.circle(self.frame, (centroid[0], centroid[1]), 4, (255, 255, 255), -1)

			info = [
			("Exit", self.totalUp),
			("Enter", self.totalDown),
			("Status", status),
			]

			info2 = [
			("Total people inside", self.x),
			]

			for (i, (k, v)) in enumerate(info):
				text = "{}: {}".format(k, v)
				cv2.putText(self.frame, text, (10, self.H - ((i * 20) + 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)

			for (i, (k, v)) in enumerate(info2):
				text = "{}: {}".format(k, v)
				cv2.putText(self.frame, text, (265, self.H - ((i * 20) + 60)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

			datetimee = [datetime.datetime.now()]
			d = [datetimee, self.empty1, self.empty, self.x]
			export_data = zip_longest(*d, fillvalue = '')

			with open('registry.csv', 'w', newline='') as myfile:
				wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
				wr.writerow(("End Time", "In", "Out", "Total Inside"))
				wr.writerows(export_data)
					
			if self.writer is not None:
				self.writer.write(self.frame)

			self.totalFrames += 1
			self.fps.update()
			

		async def on_end(self):
			self.fps.stop()
			print("[INFO] elapsed time: {:.2f}".format(self.fps.elapsed()))
			print("[INFO] approx. FPS: {:.2f}".format(self.fps.fps()))

	async def setup(self):
		print("Agent starting . . .")
		self.peoplecounter_agent = self.PeopleCounterAgent()
		self.add_behaviour(self.peoplecounter_agent)

if __name__ == "__main__":
	mainAgent = MainAgent("test@localhost", "test")
	future = mainAgent.start()
	future.result()
	mainAgent.web.start(hostname="127.0.0.1", port="10000")
	
	while not mainAgent.peoplecounter_agent.is_killed():
		try:
			time.sleep(1)
		except KeyboardInterrupt:
			break

	mainAgent.stop()