from abc import ABCMeta, abstractmethod
import logging
import time

import cv2

logger = logging.getLogger('groundlight.stream')


class FrameGrabber(metaclass=ABCMeta):

    @staticmethod
    def create_grabber(stream=None):
        if type(stream) not in [str, int]:
            raise ValueError(f'invalid type for {stream=}')

        if type(stream) == int:
            return DeviceFrameGrabber(stream=stream)
        elif stream[:7] == 'rtsp://':
            logger.debug(f'found rtsp stream {stream=}')
            return RTSPFrameGrabber(stream=stream)
        else:
            raise ValueError(f'cannot create a frame grabber from {stream=}')


    @abstractmethod
    def grab():
        pass


class DeviceFrameGrabber(FrameGrabber):
    '''Grabs frames directly from a device via a VideoCapture object that
    is kept open for the lifetime of this instance.

    importantly, this grabber does not buffer frames on behalf of the
    caller, so each call to grab will directly read a frame from the
    device
    '''


    def __init__(self, stream=None):
        '''stream must be an int representing a device id'''
        try:
            self.capture = cv2.VideoCapture(int(stream), cv2.CAP_ANY)
        except Exception as e:
            logging.error(f'could not initialize DeviceFrameGrabber: {stream=} must be an int corresponding to a valid device id.')
            raise e


    def grab(self):
        '''consistent with existing behavior based on VideoCapture.read()
        which may return None when it cannot read a frame.

        TODO: consider raising to avoid silently failing since this
        grabber cannot recover
        '''
        start = time.time()
        ret, frame = self.capture.read()
        if not ret:
            logger.warning('could not read frame from {self.capture=}')
        now = time.time()
        logger.debug(f'grabbed {frame=}')
        logger.info(f'grabbed frame in {now-start}s.')
        return frame


class RTSPFrameGrabber(FrameGrabber):
    '''grabs frames from an rtsp stream. It attempts to return the latest
    frame in the stream by opening the stream right before capturing;
    otherwise each call to read would fetch the next frame in line rather
    than the latest.'''

    def __init__(self, stream=None):
        for x in cv2.videoio_registry.getBackends():
            print(x,cv2.videoio_registry.getBackendName(x))

        self.stream = stream
        self.capture = cv2.VideoCapture(self.stream, cv2.CAP_FFMPEG)
        logger.debug(f'initialized video capture with backend={self.capture.getBackendName()}')
        if not self.capture.isOpened():
            raise ValueError(f'could not open {self.stream=}')
        logger.debug(f'before updating buffer={self.capture.get(cv2.CAP_PROP_BUFFERSIZE)}')
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1.0)
        logger.debug(f'initialized capture with buffer={self.capture.get(cv2.CAP_PROP_BUFFERSIZE)}')


    def grab(self):
        start = time.time()
        ret = self.capture.grab()
        logger.debug(f'grabbed a frame to empty buffer before reading new frame.')
        ret, frame = self.capture.read()
        if not ret:
            logger.warning(f'could not read frame from {capture=}')
        now = time.time()
        logger.debug(f'grabbed {frame=}')
        logger.info(f'grabbed frame in {now-start}s.')
        return frame
