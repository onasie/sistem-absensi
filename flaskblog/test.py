import cv2
import threading
import time
import logging
from mtcnn.mtcnn import MTCNN
from imutils.video import VideoStream
import threading

from flaskblog.models import Photo, User
from flaskblog.Model import *
from keras.preprocessing.image import img_to_array
import multiprocessing.dummy as mp
import math
import sys

logger = logging.getLogger(__name__)

thread = None

class Camera:
    def __init__(self,fps=20,video_source=0):
        logger.info(f"Initializing camera class with {fps} fps and video_source={video_source}")
        self.fps = fps
        self.video_source = video_source
        self.camera = VideoStream(src=0).start()
        # We want a max of 5s history to be stored, thats 5s*fps
        self.max_frames = 5
        self.frames = []
        self.isrunning = False
        self.detect_wajah = False
        self.counter=0
        self.database = {}

    def run(self):
        logging.debug("Perparing thread")
        global thread
        if thread is None:
            self.load_db()
            logging.debug("Creating thread")
            thread = threading.Thread(target=self._capture_loop,daemon=True)
            logger.debug("Starting thread")
            self.isrunning = True
            thread.start()
            logger.info("Thread started")
    
    def load_db(self):
        for x in Photo.query.all():
            user = User.query.get(x.user_id).username
            emb_value = np.load(x.emb_path)
            key = user +'#Id'+ str(x.user_id) + "_Face"+ str(x.id)
            list_value = []
            list_value.append(emb_value[0])
            list_value.append(x.img_path)
            self.database[key] = list_value
    
    def predict(self, model, images):
        embedding = []
        for i in range(0, images.shape[0]):
            img1 = np.expand_dims(images[i],axis=0)
            a = model.predict(img1)
            embedding.append(a)
        return np.array(embedding)

    def who_is_it(self, face_embed):
        self.threshold = 0.304
        self.min_dist = 100
        self.identity = "Unknown"
        self.path = "unknown.png"
        dist = []
        for (name, list_value) in self.database.items():
            dist = (self.euc_dist(list_value[0][0], face_embed[0]))

            print("dist ", dist)
            if (dist < self.min_dist):
                self.min_dist = dist
                self.identity = name
                self.path = list_value[1]
                print("self.identity1", self.identity)

        if self.min_dist > self.threshold:
            self.identity = "Unknown"
            self.path = "unknown.png"
            
        print("self.identity2", self.identity)
        return self.min_dist

    def euc_dist(self, vec1, vec2 ):
        sum_square = sum([(a - b) ** 2 for a, b in zip(vec1, vec2)])
        distance = math.sqrt(max(sum_square, sys.float_info.epsilon))

        return distance

    def _capture_loop(self):
        frame_count = 0
        model = get_model()
        self.detector= MTCNN()
        self.bounding_box = None

        self.detect_wajah = True

        dt = 1/self.fps

        while self.isrunning:
            frame_count += 1
            self.image = self.camera.read()
            if len(self.frames)==self.max_frames:
                self.frames = self.frames[1:]

            result = self.detector.detect_faces(self.image)

            if result != []:
                for person in result:
                    self.bounding_box = person['box']
                    keypoints = person['keypoints']
                    cv2.rectangle(self.image, (self.bounding_box[0], self.bounding_box[1]),
                        (self.bounding_box[0]+self.bounding_box[2], self.bounding_box[1] + self.bounding_box[3]),
                        (0,255,0),2)
                    
                    self.face = self.image[self.bounding_box[1]:self.bounding_box[1] + self.bounding_box[3],self.bounding_box[0]:self.bounding_box[0]+self.bounding_box[2]]
                        
            if self.face.size != 0:
                self.resized_face = cv2.resize(self.face, (96,96), interpolation = cv2.INTER_AREA)
                
                self.norm_img = np.zeros((96, 96))
                self.norm_img = self.resized_face
                self.gray_face = cv2.cvtColor(self.resized_face, cv2.COLOR_BGR2GRAY)
                self.disp_face = cv2.cvtColor(self.norm_img, cv2.COLOR_BGR2RGB)

                self.norm_face = img_to_array(self.gray_face).astype('float32') / 255

                self.norm_face = self.norm_face.reshape(1, self.gray_face.shape[0],
                                                        self.gray_face.shape[1], 1)

                face_embed = self.predict(model, self.norm_face)

                p = mp.Pool(8)
                p.map(self.who_is_it,face_embed)
                p.close()

            self.frames.append(self.image)
            time.sleep(dt)

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