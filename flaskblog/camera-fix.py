import cv2
import threading
import time
import logging
import numpy as np
from mtcnn.mtcnn import MTCNN
import imutils
from imutils.video import VideoStream, FPS, WebcamVideoStream
import threading
from threading import Thread
from keras.preprocessing.image import img_to_array

logger = logging.getLogger(__name__)

thread = None

class Camera:
    def __init__(self,fps=20,video_source=0):
        logger.info(f"Initializing camera class with {fps} fps and video_source={video_source}")
        self.fps = fps
        self.video_source = video_source
        # We want a max of 5s history to be stored, thats 5s*fps
        self.max_frames = 5
        self.frames = []
        self.isrunning = False
        self.counter=0

    def run(self):
        logging.debug("Perparing thread")
        global thread
        if thread is None:
            logging.debug("Creating thread")
            thread = threading.Thread(target=self._capture_loop,daemon=True)
            logger.debug("Starting thread")
            self.isrunning = True
            thread.start()
            logger.info("Thread started")
            self.camera = VideoStream(src=0).start()

    def _capture_loop(self):
        detector= MTCNN()
        self.bounding_box = None
        dt = 1/self.fps
        logger.debug("Observation started")
        while self.isrunning:
            self.image = self.camera.read()
            if len(self.frames)==self.max_frames:
                self.frames = self.frames[1:]
            result = detector.detect_faces(self.image)

            if result != []:
                for person in result:
                    self.bounding_box = person['box']
                    keypoints = person['keypoints']
                    cv2.rectangle(self.image, (self.bounding_box[0], self.bounding_box[1]),
                        (self.bounding_box[0]+self.bounding_box[2], self.bounding_box[1] + self.bounding_box[3]),
                        (0,155,255),2)

            self.frames.append(self.image)
            time.sleep(dt)
        logger.info("Thread stopped successfully")

    def stop(self):
        logger.debug("Stopping thread")
        self.isrunning = False
        
    def get_frame(self):
        if len(self.frames)>0:
            img = cv2.imencode('.png',self.frames[-1])[1].tobytes()
        else:
            with open("./images/not_found.jpeg","rb") as f:
                img = f.read()
        return img

    def capture_frame(self):
        img = self.image[self.bounding_box[1]:self.bounding_box[1] + self.bounding_box[3],
                self.bounding_box[0]:self.bounding_box[0] + self.bounding_box[2]]
        resized_face = cv2.resize(img, (96, 96), interpolation=cv2.INTER_AREA)
        gray_face = cv2.cvtColor(resized_face, cv2.COLOR_BGR2GRAY)
        gray_face = img_to_array(gray_face).astype('float32') / 255

        return resized_face, gray_face