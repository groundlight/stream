import logging
from enum import StrEnum
from pathlib import Path
from typing import Any

from framegrab import FrameGrabber

logger = logging.getLogger("groundlight.stream")


class StreamType(StrEnum):
    GENERIC_USB = "generic_usb"
    RTSP = "rtsp"
    HLS = "hls"
    YOUTUBE_LIVE = "youtube_live"
    DIRECTORY = "directory"  # Not implemented yet
    FILE = "file"  # Not implemented yet
    IMAGE_URL = "image_url"  # Not implemented yet


def _infer_stream_type(stream: str | int) -> StreamType:
    """Infer the stream type from the stream source."""
    if isinstance(stream, int):
        return StreamType.GENERIC_USB

    if not isinstance(stream, str):
        raise TypeError(f"Stream must be a string or int, got {type(stream)}")

    logger.debug(f"Stream {stream} is not an int, inferring type from string")

    # Check URL patterns
    if stream.startswith("rtsp://"):
        return StreamType.RTSP
    if stream.startswith("http"):
        if stream.endswith(".m3u8"):
            return StreamType.HLS
        if stream.startswith("https://www.youtube.com"):
            return StreamType.YOUTUBE_LIVE
        raise NotImplementedError("Image URL stream type is not supported yet")

    # Check file patterns
    if "*" in stream:
        raise NotImplementedError("Directory stream type is not supported yet")
    if Path(stream).is_file():
        raise NotImplementedError("File stream type is not supported yet")

    raise ValueError(f"Could not infer stream type from: {stream}")


def _stream_to_id(stream: str | int, stream_type: StreamType) -> dict[str, str | int] | None:
    if stream_type == StreamType.YOUTUBE_LIVE:
        return {"youtube_url": stream}
    elif stream_type == StreamType.RTSP:
        return {"rtsp_url": stream}
    elif stream_type == StreamType.HLS:
        return {"hls_url": stream}
    elif stream_type == StreamType.GENERIC_USB:
        return {"serial_number": stream}
    return None


def _configure_options(
    stream_type: StreamType,
    height: int | None = None,
    width: int | None = None,
    max_fps: int | None = None,
    keep_connection_open: bool | None = None,
) -> dict:
    options = {}

    if height is not None:
        options["resolution.height"] = height
    if width is not None:
        options["resolution.width"] = width

    if max_fps is not None:
        if stream_type == StreamType.RTSP:
            options["max_fps"] = max_fps
        else:
            logger.warning(f"max_fps is not supported for stream type {stream_type}")

    if keep_connection_open is not None:
        if stream_type in [StreamType.RTSP, StreamType.YOUTUBE_LIVE, StreamType.HLS]:
            options["keep_connection_open"] = keep_connection_open
            logger.info(f"keep_connection_open set to {keep_connection_open}")
        else:
            logger.debug(f"keep_connection_open is not supported for stream type {stream_type}")

    return options


def framegrabber_factory(  # noqa: PLR0913
    stream: str | int,
    stream_type: StreamType | None = None,
    height: int | None = None,
    width: int | None = None,
    max_fps: int | None = None,
    keep_connection_open: bool | None = None,
) -> FrameGrabber:
    if stream_type is None:
        stream_type = _infer_stream_type(stream)

    grabber_config: dict[str, Any] = {"input_type": stream_type}
    stream_id = _stream_to_id(stream, stream_type)
    if stream_id is not None:
        grabber_config["id"] = stream_id

    grabber_options = _configure_options(stream_type, height, width, max_fps, keep_connection_open)
    if len(grabber_options) > 0:
        grabber_config["options"] = grabber_options

    grabber = FrameGrabber.create_grabber(config=grabber_config)
    return grabber
