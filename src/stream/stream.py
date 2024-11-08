"""Groundlight Stream Processor

A command-line tool that captures frames from a video source and sends them to a Groundlight detector for analysis.
Supports multiple input sources including:
- Video devices (webcams)
- Video files (mp4, etc)
- RTSP streams
- YouTube videos
- Image directories
- Image URLs

Usage:
    stream [options] -t TOKEN -d DETECTOR

Required Arguments:
    -t, --token=TOKEN      Groundlight API token for authentication
    -d, --detector=ID      Detector ID to send image queries to

Optional Arguments:
    -e, --endpoint=URL     API endpoint [default: https://api.groundlight.ai/device-api]
    -f, --fps=FPS          Frames per second to capture (0 for max rate) [default: 5]
    -s, --stream=STREAM    Video source - device ID, filename, or URL [default: 0]
    -x, --streamtype=TYPE  Source type: [infer, device, directory, rtsp, youtube, file, image_url] [default: infer]
    -v, --verbose          Enable debug logging

Image Processing:
    -w, --width=WIDTH      Resize width in pixels (height scaled proportionally if not set)
    -y, --height=HEIGHT    Resize height in pixels (width scaled proportionally if not set)
    -c, --crop=[x,y,w,h]   Crop region as fractions (0-1) before resize [default: "0,0,1,1"]

Motion Detection:
    -m, --motion           Enable motion detection
    -r, --threshold=PCT    Motion detection threshold - % pixels changed [default: 1]
    -p, --postmotion=SEC   Seconds to capture after motion detected [default: 1]
    -i, --maxinterval=SEC  Max seconds between frames even without motion [default: 1000]
"""

import io
import logging
import math
import os
import sys
import time
from functools import partial
from logging.config import dictConfig
from queue import Queue

import cv2
import docopt
import yaml
from framegrab import MotionDetector
from grabber import FrameGrabber
from groundlight import Groundlight
from image_processing import crop_frame, parse_crop_string, resize_if_needed
from threads import setup_workers

fname = os.path.join(os.path.dirname(__file__), "logging.yaml")
dictConfig(yaml.safe_load(open(fname)))
logger = logging.getLogger(name="groundlight.stream")


# TODO list:
# - Remove multithreading - not needed now that the Groundlight client supports ask_async
# - Use the FrameGrabber class from the framegrab library
# - Better argument parsing and validation


def process_single_frame(frame: cv2.Mat, client: Groundlight, detector: str) -> None:
    """Process a single frame and send it to Groundlight

    Args:
        frame: OpenCV image frame to process
        client: Groundlight client instance
        detector: ID of detector to query
    """
    try:
        # Prepare and send image
        start = time.time()
        is_success, buffer = cv2.imencode(".jpg", frame)
        io_buf = io.BytesIO(buffer)  # type: ignore
        end = time.time()
        logger.info(f"Prepared the image in {1000*(end-start):.1f}ms")

        start = time.time()
        image_query = client.ask_async(detector=detector, image=io_buf)
        end = time.time()
        logger.debug(f"{image_query=}")
        logger.info(f"API time for image {1000*(end-start):.1f}ms")
    except Exception as e:
        logger.error(f"Exception while processing frame : {e}", exc_info=True)


def parse_resize_args(args: dict) -> tuple[int, int]:
    """Parse and validate width/height resize arguments"""
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

    return resize_width, resize_height


def parse_stream_args(args: dict) -> tuple[str | int, str | None]:
    """Parse and validate stream source arguments"""
    stream = args["--stream"]
    stream_type = args["--streamtype"].lower()

    if stream_type not in [
        "infer",
        "device",
        "directory",
        "rtsp",
        "youtube",
        "file",
        "image_url",
    ]:
        raise ValueError(f"Invalid stream type {stream_type=}")

    if stream_type == "infer":
        try:
            stream = int(stream)
        except ValueError:
            logger.debug(f"{stream=} is not an int. Treating as a filename or url.")
        stream_type = None

    return stream, stream_type


def parse_motion_args(args: dict) -> tuple[bool, float, float, float]:
    """Parse and validate motion detection arguments"""
    if not args.get("--motion"):
        logger.info("Motion detection disabled.")
        return False, 0, 0, 0

    try:
        threshold = float(args["--threshold"])
        post_motion = float(args["--postmotion"])
        max_interval = float(args["--maxinterval"])
    except ValueError as e:
        logger.error(f"Invalid motion detection parameter: {e}")
        sys.exit(-1)

    logger.info(
        f"Motion detection enabled with threshold={threshold} and post-motion capture of {post_motion}s and max interval of {max_interval}s"
    )
    return True, threshold, post_motion, max_interval


def run_capture_loop(  # noqa: PLR0912 PLR0913
    grabber: FrameGrabber,
    queue: Queue,
    fps: float,
    motion_detector: MotionDetector | None,
    post_motion_time: float,
    max_frame_interval: float,
    resize_width: int,
    resize_height: int,
    crop_region: tuple[float, float, float, float] | None,
) -> None:
    """Main capture loop implementation"""
    # Handle fps=0 case for maximum frame rate
    desired_delay = 1 / fps if fps > 0 else 0
    if fps == 0:
        logger.warning("FPS set to 0. Using maximum stream rate")

    last_frame_time = time.time()
    motion_start = 0

    while True:
        start = time.time()
        frame = grabber.grab()
        if frame is None:
            logger.warning("No frame captured!")
            time.sleep(0.1)  # Brief pause before retrying
            continue

        now = time.time()
        logger.debug(f"Captured frame in {now-start:.3f}s, size {frame.shape}")

        # Apply cropping if configured
        if crop_region:
            frame = crop_frame(frame, crop_region)
            logger.debug(f"Cropped to {frame.shape}")

        # Determine if we should process this frame
        add_frame_to_queue = True
        if motion_detector:
            time_since_motion = time.time() - motion_start
            time_since_last_frame = time.time() - last_frame_time

            if motion_detector.motion_detected(frame):
                logger.info("Motion detected")
                motion_start = time.time()
            elif time_since_motion < post_motion_time:
                logger.debug(f"Adding post-motion frame ({time_since_motion:.3f}s / {post_motion_time}s)")
            elif time_since_last_frame > max_frame_interval:
                logger.debug(f"Adding periodic frame ({time_since_last_frame:.3f}s / {max_frame_interval}s)")
            else:
                logger.debug("Skipping frame - no motion detected")
                add_frame_to_queue = False

        # Process frame if needed
        if add_frame_to_queue:
            frame = resize_if_needed(frame, resize_width, resize_height)
            queue.put(frame)
            last_frame_time = time.time()

        # Handle frame timing
        if desired_delay > 0:
            elapsed_time = time.time() - start
            actual_delay = desired_delay - elapsed_time
            if actual_delay < 0:
                logger.warning(
                    f"Cannot maintain {fps} FPS - processing taking {now-start:.3f}s (queue size: {queue.qsize()})"
                )
            else:
                logger.debug(f"Waiting {actual_delay:.3f}s until next frame")
                time.sleep(actual_delay)


def main():
    """Main entry point - parse args and run frame capture loop"""
    args = docopt.docopt(__doc__)
    if args.get("--verbose"):
        logger.level = logging.DEBUG
        logger.debug(f"{args=}")

    # Parse arguments
    resize_width, resize_height = parse_resize_args(args)
    crop_region = parse_crop_string(args["--crop"]) if args.get("--crop") else None
    stream, stream_type = parse_stream_args(args)
    motion_detect, motion_threshold, post_motion_time, max_frame_interval = parse_motion_args(args)

    # Setup Groundlight client
    gl = Groundlight(endpoint=args["--endpoint"], api_token=args["--token"])
    logger.debug(f"groundlight client created, whoami={gl.whoami()}")

    # Setup frame grabber
    grabber_config = dict(stream=stream, stream_type=stream_type, fps_target=float(args["--fps"]))
    grabber = FrameGrabber.create_grabber(**grabber_config)

    # Setup workers
    fps = float(args["--fps"])
    worker_count = 10 if fps == 0 else math.ceil(fps)
    _process_single_frame = partial(process_single_frame, client=gl, detector=args["--detector"])
    q, tc, workers = setup_workers(fn=_process_single_frame, num_workers=worker_count)

    # Setup motion detection if enabled
    motion_detector = MotionDetector(pct_threshold=motion_threshold) if motion_detect else None

    # Main capture loop
    try:
        run_capture_loop(
            grabber=grabber,
            queue=q,
            fps=float(args["--fps"]),
            motion_detector=motion_detector,
            post_motion_time=post_motion_time,
            max_frame_interval=max_frame_interval,
            resize_width=resize_width,
            resize_height=resize_height,
            crop_region=crop_region,
        )
    except KeyboardInterrupt:
        logger.info("exiting with KeyboardInterrupt.")
        tc.force_exit()
        sys.exit(-1)


if __name__ == "__main__":
    main()
