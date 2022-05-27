'''Captures frames from a real-time video stream and sends frames as
image queries to a configured detector using the Groundlight API

usage: streamlight [options] -t TOKEN -d DETECTOR -s STREAM

options:
  -d, --detector=ID      detector id to which the image queries are sent
  -e, --endpoint=URL     api endpoint [default: https://device.positronix.ai/device-api]
  -f, --framerate=FPS    number of frames to capture per second.
  -h, --help             show this message.
  -s, --stream=URL       URL of video stream (e.g. rtsp://host:port/script?params)
  -t, --token=TOKEN      api token to authenticate with the groundlight api
  -v, --verbose

'''
import io
import logging
from logging.config  import dictConfig
import os
import time

import cv2
import docopt
import yaml

from groundlight import Groundlight


fname = os.path.join(os.path.dirname(__file__), 'logging.yaml')
dictConfig(yaml.safe_load(open(fname, 'r')))
logger = logging.getLogger(name='groundlight.stream')

STREAM = "rtsp://admin:password@10.77.0.29:554/cam/realmonitor?channel=1&subtype=0"
DETECTOR = "772d549499394726b06fd6e36ec41153"
INTEG_ENDPOINT = "https://device.integ.positronix.ai/device-api"
TOKEN = 'api_29imQxusKndanuiigGzLqAoL3Zj_AD2VFYi191ghbUJeLHJ11GDfVCjfa55JCS'


def main():
    args = docopt.docopt(__doc__)
    if args.get('--verbose'):
        logger.level = logging.DEBUG
        logger.debug(f'{args=}')

    ENDPOINT=args['--endpoint']
    if ENDPOINT == 'integ':
        ENDPOINT = INTEG_ENDPOINT
    TOKEN=args['--token']
    DETECTOR=args['--detector']
    STREAM=args['--stream']

    logger.debug(f'creating groundlight client with {ENDPOINT=} and {TOKEN=}')
    gl = Groundlight(endpoint=ENDPOINT, api_token=TOKEN)

    logger.debug(f'initializing video capture: {STREAM=}')
    cap = cv2.VideoCapture(STREAM, cv2.CAP_FFMPEG)

    while True:
       start = time.time()
       if not cap.isOpened():
           logger.error(f'Cannot open stream {STREAM=}')
           # logger.debug(cv2.getBuildInformation())
           exit(-1)

       ret, frame = cap.read()
       logger.debug(f"Original {frame.shape=}")
       frame = cv2.resize(frame, (480,270))
       logger.debug(f"Resized {frame.shape=}")

       is_success, buffer = cv2.imencode(".jpg", frame)
       logger.debug(f"buffer size is {len(buffer)}")
       io_buf = io.BytesIO(buffer)
       #cv2.imwrite('temp.jpg', frame)
       end = time.time()
       logger.info(f"Time to prep image {1000*(end-start):.1f}ms")
       image_query = gl.submit_image_query(detector_id=DETECTOR, image=io_buf)
       start = end
       end = time.time()
       logger.info(f"API time for image {1000*(start-end):.1f}ms")

    cap.release()


if __name__ == '__main__':
    main()
