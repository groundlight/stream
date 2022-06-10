import logging

import cv2

logger = logging.getLogger('groundlight.stream')


class FrameGrabber:

    @staticmethod
    def create_grabber(stream=None):
        if type(stream) not in [str, int]:
            raise ValueError(f'invalid type for {stream=}')

        if type(stream) == int:
            return DeviceFrameGrabber(stream=stream)
        elif stream.start[:7] == 'rtsp://':
            logger.debug(f'found rtsp stream {stream=}')
            return RTSPFrameGrabber(stream=stream)
        else:
            logger.debug(f'trying to create a frame grabber from file {stream=}')
            return FileFrameGraber(stream=stream)


    @abstractmethod
    def grab():
        pass


class DeviceFrameGrabber():

    def __init__(self, stream=None, **kwargs):
        self.capture = cv2.VideoCapture(stream, cv2.CAP_ANY)
