import io
import logging
from logging.config  import dictConfig
import os
import time

import cv2
import yaml

from groundlight import Groundlight


fname = os.path.join(os.path.dirname(__file__), 'logging.yaml')
dictConfig(yaml.safe_load(open(fname, 'r')))

logger = logging.getLogger(name='groundlight.stream')

#rtsp_url = "rtsp://admin:password@10.77.0.29:554/cam/realmonitor?channel=1&subtype=0"

det_id = "det_29R4pwUkfuJNpjmXUWev8fjQUVg"

logger.info(f"configured to read camera at {rtsp_url}")
logger.info(f"using detector ID {det_id}")

gl = Groundlight(endpoint="https://device.integ.positronix.ai/device-api")

logger.info(f"available detectors:")
logger.info(gl.list_detectors())

cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)

while True:
   start_time = time.time()
   #cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
   if not cap.isOpened():
       logger.error('Cannot open RTSP stream')
       #print(cv2.getBuildInformation())
       exit(-1)

   ret, frame = cap.read()

   logger.debug(f"Original {frame.shape=}")
   frame = cv2.resize(frame, (480,270))
   logger.debug(f"Resized {frame.shape=}")
   is_success, buffer = cv2.imencode(".jpg", frame)
   logger.debug(f"buffer size is {len(buffer)=}")
   io_buf = io.BytesIO(buffer)
   #cv2.imwrite('temp.jpg', frame)
   #cap.release()
   #break
   time2 = time.time()
   logger.info(f"Time to prep image {1000*(time2-start_time):.1f}ms")
   image_query = gl.submit_image_query(detector_id=det_id, image=io_buf)
   time3 = time.time()
   logger.info(f"API time for image {1000*(time3-time2):.1f}ms")

cap.release()
