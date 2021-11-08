import cv2
import threading
import time
import logging
from mtcnn.mtcnn import MTCNN
import imutils
from imutils.video import VideoStream, FPS, WebcamVideoStream
import threading
from threading import Thread

from queue import Queue
from flaskblog.Model import *
from flaskblog.Model import get_model as model
import math
import sys
import multiprocessing.dummy as mp
from flaskblog.models import Photo

logger = logging.getLogger(__name__)

thread = None

class recogCamera:
  def __init__(self,fps=20,video_source=0):
    logger.info(f"Initializing camera class with {fps} fps and video_source={video_source}")
    self.fps = fps
    self.video_source = video_source
    self.camera = VideoStream(src=0).start()
    # We want a max of 5s history to be stored, thats 5s*fps
    self.max_frames = 5
    self.frames = []
    self.isrunning = False
    self.counter=0

  def run(self):
    logging.debug("Perparing thread")
    self.load_db()
    global thread
    if thread is None:
      logging.debug("Creating thread")
      thread = threading.Thread(target=self._capture_loop,daemon=True)
      logger.debug("Starting thread")
      self.isrunning = True
      thread.start()
      logger.info("Thread started")
  
  def load_db(self):
    for x in Photo.query.all():
      print("Photo ", x)
  
  def euc_dist(self, vec1, vec2):
    sum_square = sum([(a - b) ** 2 for a, b in zip(vec1, vec2)])
    distance = math.sqrt(max(sum_square, sys.float_info.epsilon))
    return distance

  def who_is_it(self, face_embed):
    self.threshold = 0.304
    self.min_dist = 100
    self.identity = "Unknown"
    self.path ="unknown.png"
    dist=[]
    for (name, list_value) in self.database.items():
      dist = (self.euc_dist(list_value[0][0], face_embed[0]))
      if(dist<self.min_dist):
        self.min_dist = dist
        self.identity = name
        self.path = list_value[1]
        # print("PATH : ", self.path)

    if self.min_dist > self.threshold:
      self.identity = "Unknown"
      self.path ="unknown.png"

    return self.min_dist

  def predict(self, model, images):
    embedding = []
  
    for i in range(0, images.shape[0]):
      img1 = np.expand_dims(images[i],axis=0)
      a = model.predict(img1)
      embedding.append(a)
    return np.array(embedding)
  
  def worker(self, input_q, output_q):
    while self.isrunning:
      frame = input_q.get()
      result = self.detector.detect_faces(frame)
      output_q.put(result)

  def _capture_loop(self):
    self.detector = MTCNN()
    input_queue = Queue(5)
    output_queue = Queue()

    for i in range(4):
      self.t = Thread(target=self.worker, args=(input_queue, output_queue))
      self.t.start()

    self.font_scale = 0.4
    self.font = cv2.FONT_HERSHEY_SIMPLEX
    frame_count = 0
    time.sleep(2.0)

    self.bounding_box = None
    dt = 1/self.fps
    
    while self.isrunning:
      frame_count+=1
      self.frame = self.camera.read()
      if len(self.frames)==self.max_frames:
        self.frames = self.frames[1:]

      if frame_count%10 == 0:
        input_queue.put(self.frame)
        
      if output_queue.empty():
        continue
      else:
        result = output_queue.get()

        if result != []:
          for person in result:
            self.bounding_box = person['box']
            keypoints = person['keypoints']
            #menambah rectangle pada frame
            cv2.rectangle(self.frame, (self.bounding_box[0], self.bounding_box[1]),
                    (self.bounding_box[0]+self.bounding_box[2], self.bounding_box[1] + self.bounding_box[3]),
                    (0,255,0),2)

            #mengambil potongan wajah dari rectangle
            self.face = self.frame[self.bounding_box[1]:self.bounding_box[1] + self.bounding_box[3],self.bounding_box[0]:self.bounding_box[0]+self.bounding_box[2]]
            
            if self.face.size != 0:
              #mengecilkan size untuk masuk ke model
              self.resized_face = cv2.resize(self.face, (96,96), interpolation = cv2.INTER_AREA)
              #masuk ke model
              face_embed = self.predict(model, self.resized_face)

              #mencari hasil predict dengan database
              p = mp.Pool(8)
              p.map(self.who_is_it,face_embed)
              p.close()         

              #memberi nama pada rectangle
              text = self.identity+ "(D = %.4f)" % self.min_dist
              self.prediction = text
              (text_width, text_height) = cv2.getTextSize(text, self.font,fontScale = self.font_scale, thickness = 1 )[0]
              text_offset_y = self.bounding_box[1] 
              text_offset_x = self.bounding_box[0] 

              box_coords = ((text_offset_x, text_offset_y), (text_offset_x + text_width - 2, text_offset_y - text_height - 2))
              cv2.rectangle(self.frame, box_coords[0], box_coords[1], (0,0,0), cv2.FILLED)
              cv2.putText(self.frame, text, (text_offset_x,text_offset_y), self.font,self.font_scale, (255,255,255),1)

              self.frames.append(self.frame)

  def stop(self):
    logger.debug("Stopping thread")
    self.isrunning = False
    
  def get_frame(self, _bytes=True):
    if len(self.frames)>0:
      if _bytes:
        img = cv2.imencode('.png',self.frames[-1])[1].tobytes()
      else:
        #kalau ditekan tombol capture
        self.counter += 1
        # img = self.frames[self.bounding_box[1]:self.bounding_box[1] + self.bounding_box[3],
        #             self.bounding_box[0]:self.bounding_box[0] + self.bounding_box[2]]
    else:
      with open("./images/not_found.jpeg","rb") as f:
        img = f.read()
    return img