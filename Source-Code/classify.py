# Copyright 2021 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Main script to run image classification."""

import argparse
import pandas as pd
import sys
import time
import cv2
import paho.mqtt.publish as publish
from image_classifier import ImageClassifier
from image_classifier import ImageClassifierOptions
from datetime import datetime
from threading import Thread
from twilio.rest import Client
import requests
import json
import logging

# Visualization parameters
_ROW_SIZE = 20  # pixels
_LEFT_MARGIN = 24  # pixels
_TEXT_COLOR = (0, 0, 255)  # red
_FONT_SIZE = 1
_FONT_THICKNESS = 1

# MQTT services
MQTT_SERVER = "192.168.1.253"
MQTT_CAT   = "classify/cat"
MQTT_MOUSE   = "classify/mouse"
MQTT_ALL   = "classify/all"
MQTT_CAT_N_MOUSE = "classify/catnmouse"
MQTT_STATS   = "classify/stats"
MQTT_HIST   = "classify/hist"
MQTT_HIST_DAY   = "classify/hist_day"
MQTT_ALL_IMAGE= "classify/aImage"
MQTT_CAT_IMAGE= "classify/cImage"
MQTT_MOUSE_IMAGE= "classify/mImage"
MQTT_CATNMOUSE_IMAGE= "classify/cnmImage"
NGROK_PATH = "http://38c3-84-74-194-47.ngrok.io/"
CATLOG_PATH = '/home/pi/Downloads/examples-master/lite/examples/image_classification/raspberry_pi/logs/cat.log'
MQTT_ALL_LOG = "classify/allLog"
MQTT_CAT_LOG = "classify/catLog"
MQTT_MOUSE_LOG = "classify/mouseLog"
MQTT_CATNMOUSE_LOG = "classify/cnmLog"
dictionary = {}

def create_snapshot(frame, _SPOTTED, objects):
    """
      Method to create a snapshot
      
      frame: the image (the actual image of the snapshot)
      _SPOTTED: the number (for incrementing images)
      objects: the object which has been spotted
    """
    cv2.imwrite(f'./logs/{objects}/{_SPOTTED}_{objects}.png', frame)
    

def write_log(loggy, obje, snaps=0, image=None):
  """
      Method to write the actual log message into the specific files
      At the end, messages will be published onto the specific mqtt publisher
      
      loggy: the specific logger
      obje: the spotted object (CAT, MOUSE, CAT AND MOUSE)
      snaps: the number of images on which we currently are (for image naming -> required for the "all" log)
      image: image is required for the all log (with this the snapshot will be made
  """
  start_time = datetime.now()
  organizer = obje.split(';')
  if obje == "CAT_AND_MOUSE":
    loggy.critical(f'{obje} spotted')
    publish.single(MQTT_CATNMOUSE_LOG, f'{start_time} - {obje} spotted', hostname=MQTT_SERVER)
    publish.single(MQTT_CAT_N_MOUSE, 1, hostname=MQTT_SERVER)
  elif obje.__contains__("CAT") or obje.__contains__("MOUSE"):
    loggy.warning(f'{obje} spotted')
    if obje.__contains__("CAT"):
        publish.single(MQTT_CAT_LOG, f'{start_time} - {obje} spotted', hostname=MQTT_SERVER)
        publish.single(MQTT_CAT, 1, hostname=MQTT_SERVER)
    else:
        publish.single(MQTT_MOUSE_LOG, f'{start_time} - {obje} spotted', hostname=MQTT_SERVER)
    publish.single(MQTT_MOUSE, 1, hostname=MQTT_SERVER)
  else:
    loggy.warning(f'{obje} spotted')
    mqtt_sender_string = '{"' + organizer[0] + '":' + organizer[1] + ',"' + organizer[2] + '":' + organizer[3] + ',"' + organizer[4] + '":' + organizer[5] + '}'
    publish.single(MQTT_ALL, mqtt_sender_string, hostname=MQTT_SERVER)
    publish.single(MQTT_ALL_IMAGE, f'{NGROK_PATH}ALL/{snaps}_ALL.png', hostname=MQTT_SERVER)
    publish.single(MQTT_ALL_LOG, f'{start_time} - {obje} spotted', hostname=MQTT_SERVER)
    Thread(target=create_snapshot, args=(image, snaps, "ALL")).start()
  
  
def got_spotted(start_time, message_time, spot_object, image, stringSpot, loggy):
    """
        This method is called when the cat (with or without mouse) is spotted.
        There will be an entry in the specific log file and a snapshot will be made.
        
        start_time: the start time of the tool, basically a spam prevention as well
        message_time: the last time a message was sent via whatsapp (to prevent spamming)
        spot_object: the object which was seen: CAT, MOUSE, CAT AND MOUSE
        image: the image which currently is seen by the camera, will be used to create a snapshot
        stringSpot: the message which will be written in the log
        loggy: the logger object which will be used to write the log in
    """
    Thread(target=write_log, args=(loggy, stringSpot)).start()
    time_delta = datetime.now() - start_time
    if time_delta.total_seconds() >= 1:
        spot_object += 1
        # create thread for snapshot recording
        Thread(target=create_snapshot, args=(image, spot_object, stringSpot)).start()
        start_time = datetime.now()
    if (datetime.now() - message_time).total_seconds() >= 60:
        send_message("INFO: " + stringSpot + " spotted", spot_object, stringSpot)
        message_time = datetime.now()
        generate_graph_data_for_histogram()
    return start_time, spot_object, message_time


formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
def setup_logger(name, log_file, level=logging.WARNING):
    """
        We have several loggers, all logging into different files, hence it makes sense
        to create a method for the logger creation
    """    
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    return logger

def send_message(msg, number, spot_obj):
    """
        Sending message via twilio.
    """
    account_sid = 'XXXXXXXXXXXXXXXXXXXX' 
    auth_token = 'XXXXXXXXXXXXXXXXXXXX' 
    phone_number = '+XXXXXXXXXX'
    client = Client(account_sid, auth_token)
    
    # create an online file service whith the log files to send them as whatsapp message
    # ./ngrok http "file:/home/pi/Downloads/examples-master/lite/examples/image_classification/raspberry_pi/logs/"
    message = client.messages.create( 
                                  from_='whatsapp:+14155238886',  
                                  body=msg,
                                  media_url=f'{NGROK_PATH}{spot_obj}/{number}_{spot_obj}.png',
                                  to='whatsapp:'+phone_number 
                              ) 

def publish_object_statistics(stats_time, labels, cat=False):
    """
        Function to create a barchart for node-red ui, this function relies on the
        history data (from the log files) and will be called every 15 seconds after writing
        the log. This function adds values to the object in the barchart. 
    """
    if (datetime.now() - stats_time).total_seconds() > 5:
      for label in labels:
          if label in dictionary:
            dictionary[label] = dictionary[label] + 1
          else:
            dictionary[label] = 1
            
      publish.single(MQTT_STATS, json.dumps(dictionary), hostname=MQTT_SERVER)
      stats_time = datetime.now()
    return stats_time


def generate_graph_data_for_histogram():
    """
        Function to create a hourly histogram for node-red ui, this function relies on the
        history data (from the log files) and will be called each time the cat is seen,
        but only in a 1min interval (to prevent spamming)
    """
    colspecs = [(0, 19), (24, 43)]
    df = pd.read_fwf(CATLOG_PATH, colspecs=colspecs, names=['date', 'spot'])
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d %H:%M:%S")
    df.set_index('date', inplace=True)
    df['spotted'] = 1
    a = df.groupby(df.index.hour)['spotted'].sum()
    #send that to node red
    publish.single(MQTT_HIST, a.to_json(), hostname=MQTT_SERVER)


def generate_graph_data_for_histogram_daily():
    """
        Function to create a daily histogram for node-red ui, this function relies on the
        history data (from the log files) and will be called once on midnight.
    """
    colspecs = [(0, 19), (24, 43)]
    df = pd.read_fwf(CATLOG_PATH, colspecs=colspecs, names=['date', 'spot'])
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d %H:%M:%S")
    df.set_index('date', inplace=True)
    df['spotted'] = 1
    a = df.groupby(df.index.day)['spotted'].sum()
    #send that to node red
    publish.single(MQTT_HIST_DAY, a.to_json(), hostname=MQTT_SERVER)


def run(model: str, max_results: int, num_threads: int, enable_edgetpu: bool,
        camera_id: int, width: int, height: int) -> None:
  """Continuously run inference on images acquired from the camera.

  Args:
      model: Name of the TFLite image classification model.
      max_results: Max of classification results.
      num_threads: Number of CPU threads to run the model.
      enable_edgetpu: Whether to run the model on EdgeTPU.
      camera_id: The camera id to be passed to OpenCV.
      width: The width of the frame captured from the camera.
      height: The height of the frame captured from the camera.
  """
  # todo: create static vars / set them to zero or so, or add datetime to filename
  _CAT_SPOTTED = 1137
  _MOUSE_SPOTTED = 50
  _CAT_AND_MOUSE_SPOTTED = 40
  _LIVE_SNAP = 22384
  generate_graph_data_for_histogram_daily()
  generate_graph_data_for_histogram()
  send_message("INFO: spotted", _LIVE_SNAP, 'ALL')
  # Initialize the image classification model
  options = ImageClassifierOptions(
      num_threads=num_threads,
      max_results=max_results,
      enable_edgetpu=enable_edgetpu)
  classifier = ImageClassifier(model, options)

  # Start capturing video input from the camera
  cap = cv2.VideoCapture(camera_id) #camera on 0 is raspicam
  cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
  cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
  
  #setup logging basic configuration for logging to a file
  general_logger = setup_logger('general', './logs/all.log')
  mouse_logger = setup_logger('mouse', './logs/mouse.log')
  cat_logger = setup_logger('cat', './logs/cat.log')
  cat_and_mouse_logger = setup_logger('cat_and_mouse', './logs/cat_and_mouse.log')

  # set up start time for tool
  start_time = datetime.now()
  message_time = datetime.now()
  log_time = datetime.now()
  stats_time = datetime.now()
  
  # Continuously capture images from the camera and run inference
  while cap.isOpened():
    
    success, image = cap.read()
    if not success:
      sys.exit(
          'ERROR: Unable to read from webcam. Please verify your webcam settings.'
      )

    image = cv2.flip(image, 1)
        
    # List classification results
    categories = classifier.classify(image)
    c = [cat.label for cat in categories]
    
    # if cat & mouse spotted, record
    # if cat only spotted, log
    # if mouse only spotted, log
    # log what is spotted all 15 seconds
    # check if the labels which got detected contain something with cat / dog
    # as cat sometimes gets detected but wrongly identified as a dog.. since there is no dog
    # running around, this should not be an issue
    cats = [x for x in c if x.lower().__contains__('tabby') or x.lower().__contains__('cat') or x.lower().__contains__('shepherd') or x.lower().__contains__('terrier')
         or x.lower().__contains__('husky')
         or x.lower().__contains__('pembroke')
         or x.lower().__contains__('pomeranian')
         or x.lower().__contains__('lynx')
         or x.lower().__contains__('chihuahua')
         or x.lower().__contains__('dog')
         ]
    prey = [x for x in c if x.lower().__contains__('hamster')
         or x.lower().__contains__('mouse')
         or x.lower().__contains__('bird')
         or x.lower().__contains__('rat')
         or x.lower().__contains__('weasel')] 
    # if y contains > 0 elements, we have spotted something and need to log this
    if len(cats) > 0 and len(prey) > 0:
        start_time, _CAT_AND_MOUSE_SPOTTED, message_time = got_spotted(start_time, message_time, _CAT_AND_MOUSE_SPOTTED, image, 'CAT_AND_MOUSE', cat_and_mouse_logger)
        publish.single(MQTT_CATNMOUSE_IMAGE, f'{NGROK_PATH}CAT_AND_MOUSE/{_CAT_AND_MOUSE_SPOTTED}_CAT_AND_MOUSE.png', hostname=MQTT_SERVER)
    elif len(cats) > 0:
        print(cats)
        start_time, _CAT_SPOTTED, message_time = got_spotted(start_time, message_time, _CAT_SPOTTED, image, 'CAT', cat_logger)
        publish.single(MQTT_CAT_IMAGE, f'{NGROK_PATH}CAT/{_CAT_SPOTTED}_CAT.png', hostname=MQTT_SERVER)
    elif len(prey) > 0:
        start_time, _MOUSE_SPOTTED, message_time = got_spotted(start_time, message_time, _MOUSE_SPOTTED, image, 'MOUSE', mouse_logger)
        publish.single(MQTT_MOUSE_IMAGE, f'{NGROK_PATH}MOUSE/{_MOUSE_SPOTTED}_MOUSE.png', hostname=MQTT_SERVER)
            
    allC = []
    allCategories = []
    # Show classification results on the image
    for idx, category in enumerate(categories):      
      class_name = category.label
      allC.append(category.label)
      allCategories.append(category.label)
      score = round(category.score, 2)
      allC.append(str(score))
      result_text = class_name + ' (' + str(score) + ')'
      text_location = (_LEFT_MARGIN, (idx + 2) * _ROW_SIZE)
      cv2.putText(image, result_text, text_location, cv2.FONT_HERSHEY_PLAIN,
                  _FONT_SIZE, _TEXT_COLOR, _FONT_THICKNESS)
      
    stats_time = publish_object_statistics(stats_time, allCategories)
    if (datetime.now() - log_time).total_seconds() > 15:
        _LIVE_SNAP = _LIVE_SNAP+1
        Thread(target=write_log, args=(general_logger, '; '.join(allC), _LIVE_SNAP, image)).start()
        log_time = datetime.now()
        
    if (datetime.now() - datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds() == 0:
        generate_graph_data_for_histogram_daily()
    # Stop the program if the ESC key is pressed.
    if cv2.waitKey(1) == 27:
      break
    cv2.imshow('image_classification', image)
    
    
  cap.release()
  cv2.destroyAllWindows()


def main():
  parser = argparse.ArgumentParser(
      formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      '--model',
      help='Name of image classification model.',
      required=False,
      default='efficientnet_lite0.tflite')
  parser.add_argument(
      '--maxResults',
      help='Max of classification results.',
      required=False,
      default=5)
  parser.add_argument(
      '--numThreads',
      help='Number of CPU threads to run the model.',
      required=False,
      default=4)
  parser.add_argument(
      '--enableEdgeTPU',
      help='Whether to run the model on EdgeTPU.',
      action='store_true',
      required=False,
      default=False)
  parser.add_argument(
      '--cameraId', help='Id of camera.', required=False, default=1)
  parser.add_argument(
      '--frameWidth',
      help='Width of frame to capture from camera.',
      required=False,
      default=640)
  parser.add_argument(
      '--frameHeight',
      help='Height of frame to capture from camera.',
      required=False,
      default=480)
  args = parser.parse_args()

  run(args.model, int(args.maxResults), int(args.numThreads),
      bool(args.enableEdgeTPU), int(args.cameraId), args.frameWidth,
      args.frameHeight)

if __name__ == '__main__':
  main()
