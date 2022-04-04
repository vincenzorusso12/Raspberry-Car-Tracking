import os
from typing import Sequence
from urllib.request import urlretrieve
import sys

import cv2
from motpy import Detection, MultiObjectTracker, NpImage
from motpy.core import setup_logger,Box
from motpy.detector import BaseObjectDetector
from motpy.testing_viz import draw_detection, draw_track
from motpy.utils import ensure_packages_installed

import argparse
import sys
import time

import numpy as np

import cv2
from object_detector import ObjectDetector
from object_detector import ObjectDetectorOptions
import utils

#from object_detector import Detection

from time import time
import argparse

from iou_tracker import track_iou
from util import load_mot, save_to_csv

ensure_packages_installed(['cv2'])


"""

    Example uses built-in camera (0) and baseline face detector from OpenCV (10 layer ResNet SSD)
    to present the library ability to track a face of the user

"""

logger = setup_logger(__name__, 'DEBUG', is_main=True)


WEIGHTS_URL = 'https://github.com/opencv/opencv_3rdparty/raw/dnn_samples_face_detector_20170830/res10_300x300_ssd_iter_140000.caffemodel'
WEIGHTS_PATH = '/tmp/opencv_face_detector.caffemodel'
CONFIG_URL = 'https://raw.githubusercontent.com/opencv/opencv/master/samples/dnn/face_detector/deploy.prototxt'
CONFIG_PATH = '/tmp/deploy.prototxt'


class FaceDetector(BaseObjectDetector):
    def __init__(self,
                 weights_url: str = WEIGHTS_URL,
                 weights_path: str = WEIGHTS_PATH,
                 config_url: str = CONFIG_URL,
                 config_path: str = CONFIG_PATH,
                 conf_threshold: float = 0.5) -> None:
        super(FaceDetector, self).__init__()

        if not os.path.isfile(weights_path) or not os.path.isfile(config_path):
            logger.debug('downloading model...')
            urlretrieve(weights_url, weights_path)
            urlretrieve(config_url, config_path)

        #self.net = cv2.dnn.readNetFromCaffe(config_path, weights_path)
        options = ObjectDetectorOptions(
            num_threads=4,
            score_threshold=0.3,
            max_results=3,
            label_allow_list=['car','truck','motorcycle'],
            enable_edgetpu=False)
        
         
        self.net = ObjectDetector(model_path='efficientdet_lite0.tflite', options=options)
        #print(self.net.__dict__)
        # specify detector hparams
        self.conf_threshold = conf_threshold

    def process_image(self, image: NpImage) -> Sequence[Detection]:
        blob = cv2.dnn.blobFromImage(image, 1.0, (300, 300), [104, 117, 123], False, False)
        #self.net.setInput(blob)
        #print(self.net.__dict__)
        detections = self.net.detect(image)
        
        
        #print(detections)
        #print(type(detections[0]))
        
        #print(detections[0].bounding_box.left)
        ##detections[0] è di classe Detection devo usare i suoi metodi per accedere

        # convert output from OpenCV detector to tracker expected format [xmin, ymin, xmax, ymax]
        out_detections = []
        for detection in detections:
            confidence = round(detection.categories[0].score, 2)
            #print(confidence)
            xmin=0
            ymin=0
            xmax=0
            ymax=0
            if confidence > self.conf_threshold:
                box=Box(4)
                #print(box)
                xmin = float(detection.bounding_box.left)
                #print(xmin)
                ymin = float(detection.bounding_box.bottom)
                xmax = float(detection.bounding_box.right)
                ymax = float(detection.bounding_box.top)
                box[0]=xmin
                box[1]=ymin
                box[2]=xmax
                box[3]=ymax
                #print(box)
                #box = np.array([0, 0, 10, 10])
                ##creare una nuova Box con i valori sopra e gliela devo passare
                #out_detections.append(Detection(box=box, score=confidence))
                
                det=np.array([0,0,xmin,ymin,xmax,ymax,confidence])
                print(det)
                #setattr(det,'box',[0,0,0,0])
                #setattr(det,'score',confidence)
                #print(det)
                out_detections.append(det)
                print(out_detections)
                #out_detections=det

        return out_detections##devo mettere le detctions nell oggetto Box


def run():
    # prepare multi object tracker
    model_spec = {'order_pos': 2, 'dim_pos': 2,
                  'order_size': 0, 'dim_size': 2,
                  'q_var_pos': 5000., 'r_var_pos': 0.1}


    dt = 1/5  # assume 15 fps
    tracker = MultiObjectTracker(dt=dt, model_spec=model_spec)
    print(tracker)

    # open camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 5)

    face_detector = FaceDetector()
    print(face_detector.__dict__)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.resize(frame, dsize=None, fx=0.5, fy=0.5)
        
        

        # run face detector on current frame
        detections = face_detector.process_image(frame)
        #logger.debug(f'detections: {detections}')
        print("detections di 0 ")
        print(np.array(detections))
        print(type(detections))
        print("fine detections")
        #numbers = np.array([10,20,30,40,50])
        mot_dets=load_mot(np.array(detections))
        print(mot_dets)
        
        #sys.exit()
       
        
        
        

        # preview the boxes on frame
        #for det in detections:
            #draw_detection(frame, det)

        #for track in tracks:
            #draw_track(frame, track)

        cv2.imshow('frame', frame)

        # stop demo by pressing 'q'
        if cv2.waitKey(int(1000 * dt)) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    run()
