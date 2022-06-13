from abc import ABCMeta, abstractmethod
import logging

import cv2

logger = logging.getLogger('groundlight.stream')


class FrameGrabber(metaclass=ABCMeta):

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
        ret, frame = self.capture.read()
        if not ret:
            logger.warning('could not read frame from {self.capture=}')
        logger.info(f'grabbed {frame=}')
        return frame


class RTSPFrameGrabber(FrameGrabber):
    '''grabs frames from an rtsp stream. It attempts to return the latest
    frame in the stream by opening the stream right before capturing;
    otherwise each call to read would fetch the next frame in line rather
    than the latest.'''

    def __init__(self, stream=None):
        self.stream = stream


    def grab(self):
        capture = VideoCapture(self.stream, cv2.CAP_ANY)
        if not capture.isOpened():
            logger.error(f'could not open {stream=}')
            return None
        else:
            ret, frame = capture.read()
            if not ret:
                logger.warning(f'could not read frame from {capture=}')
            capture.release()
            logger.info(f'grabbed {frame=}')
            return frame
