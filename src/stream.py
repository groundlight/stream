"""Captures frames from a video device, file or stream and sends frames as
image queries to a configured detector using the Groundlight API

usage: stream [options] -t TOKEN -d DETECTOR

options:
  -d, --detector=ID      detector id to which the image queries are sent
  -e, --endpoint=URL     api endpoint [default: https://api.groundlight.ai/device-api]
  -f, --fps=FPS          number of frames to capture per second. 0 to use maximum rate possible. [default: 5]
  -h, --help             show this message.
  -s, --stream=STREAM    id, filename or URL of a video stream (e.g. rtsp://host:port/script?params OR movie.mp4 OR *.jpg) [default: 0]
  -x, --streamtype=TYPE  type of stream. One of [infer, device, directory, rtsp, youtube, file, image_url] [default: infer]
  -t, --token=TOKEN      api token to authenticate with the groundlight api
  -v, --verbose          enable debug logs
  -w, --width=WIDTH      resize images to w pixels wide (and scale height proportionately if not set explicitly)
  -y, --height=HEIGHT    resize images to y pixels high (and scale width proportionately if not set explicitly)
  -c, --crop=[x,y,w,h]   crop image to box before resizing. x,y,w,h are fractions from 0-1.  [Default:"0,0,1,1"]
  -m, --motion                 enable motion detection with pixel change threshold percentage (disabled by default)
  -r, --threshold=THRESHOLD    detection threshold for motion detection - percent of changed pixels [default: 1]
  -p, --postmotion=POSTMOTION  minimum number of seconds to capture for every motion detection [default: 1]
  -i, --maxinterval=MAXINT     maximum number of seconds before sending frames even without motion [default: 1000]
"""

import io
import logging
import math
import os
import time
from logging.config import dictConfig
from queue import Empty, Queue
from threading import Thread
from typing import Tuple

import cv2
import docopt
import yaml
from groundlight import Groundlight

from grabber import FrameGrabber
from motion import MotionDetector

fname = os.path.join(os.path.dirname(__file__), "logging.yaml")
dictConfig(yaml.safe_load(open(fname, "r")))

logger = logging.getLogger(name="groundlight.stream")


class ThreadControl:
    def __init__(self):
        self.exit_all_threads = False

    def force_exit(self):
        logger.debug("Attempting force exit of all threads")
        self.exit_all_threads = True


def frame_processor(q: Queue, client: Groundlight, detector: str, control: ThreadControl):
    logger.debug(f"frame_processor({q=}, {client=}, {detector=})")
    global thread_control_request_exit
    while True:
        if control.exit_all_threads:
            logger.debug("exiting worker thread.")
            break
        try:
            frame = q.get(timeout=1)  # timeout avoids deadlocked orphan when main process dies
        except Empty:
            continue
        try:
            # prepare image
            start = time.time()
            is_success, buffer = cv2.imencode(".jpg", frame)
            io_buf = io.BytesIO(buffer)  # type: ignore
            end = time.time()
            logger.info(f"Prepared the image in {1000*(end-start):.1f}ms")
            # send image query
            image_query = client.ask_async(detector=detector, image=io_buf)
            logger.debug(f"{image_query=}")
            start = end
            end = time.time()
            logger.info(f"API time for image {1000*(end-start):.1f}ms")
        except Exception as e:
            logger.error(f"Exception while processing frame : {e}")


def resize_if_needed(frame, width: int, height: int):
    # scales cv2 image frame to widthxheight pixels
    # values of 0 for width or height will keep proportional.

    if (width == 0) & (height == 0):
        return

    image_height, image_width, _ = frame.shape
    if width > 0:
        target_width = width
    else:
        target_width = int(image_width * (height / image_height))
    if height > 0:
        target_height = height
    else:
        target_height = int(image_height * (width / image_width))

    logger.debug(f"resizing from {frame.shape=} to {target_width=}x{target_height=}")
    frame = cv2.resize(frame, (target_width, target_height))


def crop_frame(frame, crop_region: Tuple[float, float, float, float]):
    """Returns a cropped version of the frame."""
    (img_height, img_width, _) = frame.shape
    x1 = int(img_width * crop_region[0])
    y1 = int(img_height * crop_region[1])
    x2 = x1 + int(img_width * crop_region[2])
    y2 = y1 + int(img_height * crop_region[3])

    out = frame[y1:y2, x1:x2, :]
    return out


def parse_crop_string(crop_string: str) -> Tuple[float, float, float, float]:
    """Parses a string like "0.25,0.25,0.5,0.5" to a tuple like (0.25,0.25,0.5,0.5)
    Also validates that numbers are between 0-1, and that it doesn't go off the edge.
    """
    parts = crop_string.split(",")
    if len(parts) != 4:
        raise ValueError("Expected crop to be list of four floating point numbers.")
    numbers = tuple([float(n) for n in parts])

    for n in numbers:
        if (n < 0) or (n > 1):
            raise ValueError("All numbers must be between 0 and 1, showing relative position in image")

    if numbers[0] + numbers[2] > 1.0:
        raise ValueError("Invalid crop: x+w is greater than 1.")
    if numbers[1] + numbers[3] > 1.0:
        raise ValueError("Invalid crop: y+h is greater than 1.")

    if numbers[2] * numbers[3] == 0:
        raise ValueError("Width and Height must both be >0")

    return numbers


def main():
    args = docopt.docopt(__doc__)
    if args.get("--verbose"):
        logger.level = logging.DEBUG
        logger.debug(f"{args=}")

    resize_width = 0
    if args.get("--width"):
        try:
            resize_width = int(args["--width"])
        except ValueError:
            raise ValueError(f"invalid width parameter: {args['--width']}")

    resize_height = 0
    if args.get("--height"):
        try:
            resize_height = int(args["--height"])
        except ValueError:
            raise ValueError(f"invalid height parameter: {args['--height']}")

    if args.get("--crop"):
        crop_region = parse_crop_string(args["--crop"])
    else:
        crop_region = None

    ENDPOINT = args["--endpoint"]
    TOKEN = args["--token"]
    DETECTOR = args["--detector"]

    STREAM = args["--stream"]
    STREAM_TYPE = args["--streamtype"]
    STREAM_TYPE = STREAM_TYPE.lower()
    if STREAM_TYPE not in [
        "infer",
        "device",
        "directory",
        "rtsp",
        "youtube",
        "file",
        "image_url",
    ]:
        raise ValueError(f"Invalid stream type {STREAM_TYPE=}")
    logger.debug(f"{STREAM_TYPE=}")
    if STREAM_TYPE == "infer":
        try:
            STREAM = int(STREAM)
        except ValueError:
            logger.debug(f"{STREAM=} is not an int.  Treating as a filename or url.")
        STREAM_TYPE = None

    FPS = args["--fps"]
    try:
        FPS = float(FPS)
        logger.debug(f"frames_per_second: {FPS}, seconds_per_frame: {1/FPS}")
    except ValueError:
        logger.error(f"Invalid argument {FPS=}. Must be a number.")
        exit(-1)
    if FPS == 0:
        worker_thread_count = 10
    else:
        worker_thread_count = math.ceil(FPS)

    if args.get("--motion"):
        motion_detect = True
        motion_threshold = args["--threshold"]
        post_motion_time = args["--postmotion"]
        max_frame_interval = args["--maxinterval"]
        try:
            motion_threshold = float(motion_threshold)
        except ValueError:
            logger.error(f"Invalid arguement threshold={motion_threshold} must be a number")
            exit(-1)
        try:
            post_motion_time = float(post_motion_time)
        except ValueError:
            logger.error(f"Invalid arguement postmotion={post_motion_time} must be a number")
            exit(-1)
        try:
            max_frame_interval = float(max_frame_interval)
        except ValueError:
            logger.error(f"Invalid arguement maxinterval={max_frame_interval} must be a number")
            exit(-1)
        logger.info(
            f"Motion detection enabled with {motion_threshold=} and post-motion capture of {post_motion_time=} and max interval of {max_frame_interval=}"
        )
    else:
        motion_detect = False
        motion_threshold = 0  # appease the type checker
        post_motion_time = 0
        max_frame_interval = 0
        logger.info("Motion detection disabled.")

    logger.debug(f"creating groundlight client with {ENDPOINT=} and {TOKEN=}")
    gl = Groundlight(endpoint=ENDPOINT, api_token=TOKEN)
    logger.debug(f"groundlight client created, whoami={gl.whoami()}")
    grabber = FrameGrabber.create_grabber(stream=STREAM, stream_type=STREAM_TYPE, fps_target=FPS)
    q = Queue()
    tc = ThreadControl()
    if motion_detect:
        m = MotionDetector(pct_threshold=motion_threshold)
    workers = []

    for i in range(worker_thread_count):
        thread = Thread(
            target=frame_processor,
            kwargs=dict(q=q, client=gl, detector=DETECTOR, control=tc),
        )
        workers.append(thread)
        thread.start()

    try:
        desired_delay = 1 / FPS
    except ZeroDivisionError:
        desired_delay = 1
        logger.warning("FPS set to 0.  Using maximum stream rate")
    start = time.time()

    last_frame_time = time.time()
    try:
        while True:
            start = time.time()
            frame = grabber.grab()
            if frame is None:
                logger.warning(f"No frame captured! {frame=}")
                continue

            now = time.time()
            logger.debug(f"captured a new frame after {now-start:.3f}s of size {frame.shape=} ")

            if crop_region:
                frame = crop_frame(frame, crop_region)
                logger.debug(f"Cropped to {frame.shape=}")

            if motion_detect:
                if m.motion_detected(frame):
                    logger.info(f"Motion detected")
                    motion_start = time.time()
                    add_frame_to_queue = True
                elif time.time() - motion_start < post_motion_time:
                    logger.debug(
                        f"adding post motion frame after {(time.time() - motion_start):.3} with {post_motion_time=}"
                    )
                    add_frame_to_queue = True
                elif time.time() - last_frame_time > max_frame_interval:
                    logger.debug(
                        f"adding frame after {(time.time()-last_frame_time):.3}s because {max_frame_interval=}s"
                    )
                    add_frame_to_queue = True
                else:
                    logger.debug("skipping frame per motion detection settings")
                    add_frame_to_queue = False
            else:
                add_frame_to_queue = True

            if add_frame_to_queue:
                resize_if_needed(frame, resize_width, resize_height)
                q.put(frame)
                last_frame_time = time.time()

            now = time.time()
            if desired_delay > 0:
                actual_delay = desired_delay - (now - start)
                if actual_delay < 0:
                    logger.warning(
                        f"Falling behind the desired {FPS=}.  Either grabbing frames or putting them into output queue (length={q.qsize()}) is taking too long."
                    )
                else:
                    logger.debug(f"waiting for {actual_delay=:.3}s to capture the next frame.")
                    time.sleep(actual_delay)

    except KeyboardInterrupt:
        logger.info("exiting with KeyboardInterrupt.")
        tc.force_exit()
        exit(-1)


if __name__ == "__main__":
    main()
