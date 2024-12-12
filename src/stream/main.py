import argparse
import io
import logging
import math
import os
import time
from functools import partial
from logging.config import dictConfig
from queue import Queue

import cv2
import yaml
from framegrab import FrameGrabber, GrabError, MotionDetector
from groundlight import Groundlight

from stream.grabber import StreamType, framegrabber_factory
from stream.image_processing import crop_frame, parse_crop_string
from stream.threads import setup_workers

fname = os.path.join(os.path.dirname(__file__), "logging.yaml")
dictConfig(yaml.safe_load(open(fname)))
logger = logging.getLogger(name="groundlight.stream")


HELP_TEXT = """Groundlight Stream Processor

A command-line tool that captures frames from a video source and sends them to a Groundlight detector for analysis.

Supports a variety of input sources including:
- Video devices (usb cameras, webcams, etc)
- RTSP streams
- YouTube Live streams
- HLS streams
- Image directories
- Video files (mp4, etc)
- Image URLs
"""

# TODO list:
# - Reintroduce support for image URLs in upstream framegrab lib
# - Reintroduce support for image directories in upstream framegrab lib
# - Reintroduce support for video files in upstream framegrab lib


def process_single_frame(frame: cv2.Mat, gl: Groundlight, detector: str) -> None:
    """Process a single frame and send it to Groundlight.

    Args:
        frame: OpenCV image frame to process
        gl: Groundlight client instance
        detector: ID of detector to query
    """
    try:
        # Encode image to JPEG
        start = time.time()
        _, buffer = cv2.imencode(".jpg", frame)
        io_buf = io.BytesIO(buffer)
        encode_time = time.time() - start
        logger.debug(f"Encoded image to JPEG in {encode_time*1000:.1f}ms")

        # Submit to Groundlight
        start = time.time()
        image_query = gl.ask_async(detector=detector, image=io_buf)
        api_time = time.time() - start
        logger.debug(f"Submitted image query via gl.ask_async() in {api_time*1000:.1f}ms")
        logger.debug(f"Image query response:\n{image_query.model_dump_json(indent=2)}")

    except Exception as e:
        logger.error(f"Failed to process frame: {e}", exc_info=True)


def validate_stream_args(args: argparse.Namespace) -> tuple[str | int, StreamType | None]:
    """Parse and validate stream source arguments"""
    stream = args.stream
    stream_type = args.streamtype.lower()

    if stream_type == "infer":
        try:
            stream = int(stream)
        except ValueError:
            logger.debug(f"{stream=} is not an int. Treating as a filename or url.")
        stream_type = None
    else:
        stream_type = StreamType(stream_type)

    return stream, stream_type


def parse_motion_args(args: argparse.Namespace) -> tuple[bool, float, int, float, float]:
    """Parse and validate motion detection arguments"""
    if not args.motion:
        logger.info("Motion detection disabled.")
        return False, 0, 0, 0, 0

    logger.info(
        f"Motion detection enabled with pixel_threshold={args.motion_pixel_threshold}, value_threshold={args.motion_val_threshold} post-motion capture of {args.postmotion}s "
        f"and max interval of {args.maxinterval}s"
    )
    return True, args.motion_pixel_threshold, args.motion_val_threshold, args.postmotion, args.maxinterval


def run_capture_loop(  # noqa: PLR0912 PLR0913
    grabber: FrameGrabber,
    queue: Queue,
    fps: float,
    motion_detector: MotionDetector | None,
    post_motion_time: float,
    max_frame_interval: float,
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
        try:
            frame = grabber.grab()
        except GrabError:
            logger.exception("Error grabbing frame")
            frame = None

        if frame is None:  # No frame captured, or exception occurred
            logger.warning("No frame captured!")
            time.sleep(0.1)  # Brief pause before retrying
            continue

        now = time.time()
        logger.debug(f"Grabbed frame in {now-start:.3f}s, size {frame.shape}")

        # Apply cropping if configured, needs to happen before motion detection
        if crop_region:
            original_shape = frame.shape
            frame = crop_frame(frame, crop_region)  # type: ignore
            logger.debug(f"Cropped frame from {original_shape} to {frame.shape}")

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

        # Add frame to work queue
        if add_frame_to_queue:
            queue.put(frame)
            last_frame_time = time.time()

        # Handle frame timing
        if desired_delay > 0:
            elapsed_time = time.time() - start
            actual_delay = desired_delay - elapsed_time
            if actual_delay < 0:
                logger.warning(
                    f"Cannot maintain {fps} FPS. Processing took {now-start:.3f}s (queue size: {queue.qsize()})"
                )
            else:
                logger.debug(f"Waiting {actual_delay:.3f}s until next frame")
                time.sleep(actual_delay)


def print_banner(gl: Groundlight, args: argparse.Namespace) -> None:
    detector = gl.get_detector(id=args.detector)
    motdet = "enabled" if args.motion else "disabled"
    print("==================================================")
    print("Groundlight Stream Processor")
    print(f"  Target Detector: {detector}")
    print(f"  Groundlight Endpoint: {gl.endpoint}")
    print(f"  Whoami: {gl.whoami()}")
    print(f"  Frames/sec: {args.fps}    (Seconds/frame: {1/args.fps:.3f})")
    print(f"  Motion Detection: {motdet}")
    print("==================================================")


def main():
    """Main entry point - parse args and run frame capture loop"""
    parser = argparse.ArgumentParser(
        description=HELP_TEXT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage="python -m stream -t TOKEN -d DETECTOR [options]",
    )

    # Required arguments
    parser.add_argument("-t", "--token", required=True, help="Groundlight API token for authentication.")
    parser.add_argument("-d", "--detector", required=True, help="Detector ID to send ImageQueries to.")

    # Optional arguments
    parser.add_argument(
        "-e",
        "--endpoint",
        default="https://api.groundlight.ai/device-api",
        help="API endpoint to target. For example, could be pointed at an edge-endpoint proxy server (https://github.com/groundlight/edge-endpoint).",
    )
    parser.add_argument(
        "-s", "--stream", default="0", help="Video source. A device ID, filename, or URL. Defaults to device ID '0'."
    )
    parser.add_argument(
        "-x",
        "--streamtype",
        default="infer",
        choices=["infer", "device", "directory", "rtsp", "youtube", "file", "image_url"],
        help="Source type. Defaults to 'infer' which will attempt to set this value based on --stream.",
    )
    parser.add_argument(
        "-f", "--fps", type=float, default=1, help="Frames per second to capture (0 for max rate). Defaults to 1 FPS."
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")

    # Motion detection
    parser.add_argument(
        "-m", "--motion", action="store_true", help="Enables motion detection, which is disabled by default."
    )
    parser.add_argument(
        "-r",
        "--motion_pixel_threshold",
        type=float,
        default=1,
        help="Motion detection pixel threshold (%% pixels changed). Defaults to 1%%.",
    )
    parser.add_argument(
        "-b",
        "--motion_val_threshold",
        type=int,
        default=20,
        help="Motion detection value threshold (degree of change). Defaults to 20.",
    )
    parser.add_argument(
        "-p",
        "--postmotion",
        type=float,
        default=1,
        help="Seconds to capture after motion detected. Defaults to 1 second.",
    )
    parser.add_argument(
        "-i",
        "--maxinterval",
        type=float,
        default=1000,
        help="Max seconds between frames even without motion. Defaults to 1000 seconds.",
    )

    # Stream options
    parser.add_argument(
        "-k",
        "--keep-connection-open",
        action="store_true",
        default=False,
        help="Keep connection open for low-latency frame grabbing (uses more CPU and network bandwidth). Defaults to false.",
    )

    # Image pre-processing
    parser.add_argument("-w", "--width", dest="resize_width", type=int, default=0, help="Resize width in pixels.")
    parser.add_argument("-y", "--height", dest="resize_height", type=int, default=0, help="Resize height in pixels.")
    parser.add_argument(
        "-c",
        "--crop",
        default=None,
        help="Crop region, specified as fractions (0-1) of each dimension (e.g. '0.25,0.2,0.8,0.9').",
    )

    # Parse and validate arguments
    args = parser.parse_args()

    if args.verbose:
        logger.level = logging.DEBUG
        logger.debug(f"{args=}")

    crop_region = parse_crop_string(args.crop) if args.crop else None
    stream, stream_type = validate_stream_args(args)
    motion_detect, motion_pixel_threshold, motion_val_threshold, post_motion_time, max_frame_interval = (
        parse_motion_args(args)
    )

    # Setup Groundlight client
    gl = Groundlight(endpoint=args.endpoint, api_token=args.token)
    logger.debug(f"Groundlight client created, whoami={gl.whoami()}")

    # Setup frame grabber
    grabber = framegrabber_factory(
        stream=stream,
        stream_type=stream_type,
        height=args.resize_height,
        width=args.resize_width,
        max_fps=args.fps,
        keep_connection_open=args.keep_connection_open,
    )

    # Setup workers
    worker_count = 10 if args.fps == 0 else math.ceil(args.fps)
    _process_single_frame = partial(process_single_frame, gl=gl, detector=args.detector)
    queue, tc, workers = setup_workers(fn=_process_single_frame, num_workers=worker_count)

    # Setup motion detection if enabled
    motion_detector = (
        MotionDetector(pct_threshold=motion_pixel_threshold, val_threshold=motion_val_threshold)
        if motion_detect
        else None
    )

    print_banner(gl=gl, args=args)

    # Main capture loop
    try:
        run_capture_loop(
            grabber=grabber,
            queue=queue,
            fps=args.fps,
            motion_detector=motion_detector,
            post_motion_time=post_motion_time,
            max_frame_interval=max_frame_interval,
            crop_region=crop_region,
        )
    except KeyboardInterrupt:
        logger.info("Exiting with KeyboardInterrupt.")
    except Exception as e:
        logger.error(f"Exiting with exception: {e}", exc_info=True)
    finally:
        # Clean up threads
        tc.shutdown()
        for worker in workers:
            worker.join(timeout=5.0)


if __name__ == "__main__":
    main()
