import argparse

import pytest

from stream.stream import parse_motion_args, parse_resize_args, parse_stream_args


def test_parse_resize_args():
    # Test no resize args
    args = argparse.Namespace(width=None, height=None)
    width, height = parse_resize_args(args)
    assert width == 0
    assert height == 0

    # Test valid width only
    args = argparse.Namespace(width="100", height=None)
    width, height = parse_resize_args(args)
    assert width == 100
    assert height == 0

    # Test valid height only
    args = argparse.Namespace(width=None, height="200")
    width, height = parse_resize_args(args)
    assert width == 0
    assert height == 200

    # Test both width and height
    args = argparse.Namespace(width="100", height="200")
    width, height = parse_resize_args(args)
    assert width == 100
    assert height == 200

    # Test invalid width
    args = argparse.Namespace(width="invalid", height=None)
    with pytest.raises(ValueError):
        parse_resize_args(args)

    # Test invalid height
    args = argparse.Namespace(width=None, height="invalid")
    with pytest.raises(ValueError):
        parse_resize_args(args)


def test_parse_stream_args():
    # Test device number with infer type
    args = argparse.Namespace(stream="0", streamtype="infer")
    stream, stream_type = parse_stream_args(args)
    assert stream == 0
    assert stream_type is None

    # Test explicit device type
    args = argparse.Namespace(stream="1", streamtype="device")
    stream, stream_type = parse_stream_args(args)
    assert stream == "1"
    assert stream_type == "device"

    # Test directory type
    args = argparse.Namespace(stream="*.jpg", streamtype="directory")
    stream, stream_type = parse_stream_args(args)
    assert stream == "*.jpg"
    assert stream_type == "directory"

    # Test RTSP stream
    args = argparse.Namespace(stream="rtsp://example.com/stream", streamtype="rtsp")
    stream, stream_type = parse_stream_args(args)
    assert stream == "rtsp://example.com/stream"
    assert stream_type == "rtsp"

    # Test YouTube URL
    args = argparse.Namespace(stream="https://youtube.com/watch?v=123", streamtype="youtube")
    stream, stream_type = parse_stream_args(args)
    assert stream == "https://youtube.com/watch?v=123"
    assert stream_type == "youtube"

    # Test invalid stream type
    args = argparse.Namespace(stream="0", streamtype="invalid")
    with pytest.raises(ValueError):
        parse_stream_args(args)


def test_parse_motion_args():
    # Test motion detection disabled
    args = argparse.Namespace(motion=None, threshold=None, postmotion=None, maxinterval=None)
    motion_on, threshold, post_motion, max_interval = parse_motion_args(args)
    assert not motion_on
    assert threshold == 0
    assert post_motion == 0
    assert max_interval == 0

    # Test motion detection enabled with defaults
    args = argparse.Namespace(motion=True, threshold="1", postmotion="1", maxinterval="1000")
    motion_on, threshold, post_motion, max_interval = parse_motion_args(args)
    assert motion_on
    assert threshold == 1.0
    assert post_motion == 1.0
    assert max_interval == 1000.0

    # Test custom values
    args = argparse.Namespace(motion=True, threshold="2.5", postmotion="0.5", maxinterval="100")
    motion_on, threshold, post_motion, max_interval = parse_motion_args(args)
    assert motion_on
    assert threshold == 2.5
    assert post_motion == 0.5
    assert max_interval == 100.0

    # Test invalid threshold
    args = argparse.Namespace(motion=True, threshold="invalid", postmotion="1", maxinterval="1000")
    with pytest.raises(SystemExit):
        parse_motion_args(args)

    # Test invalid post-motion time
    args = argparse.Namespace(motion=True, threshold="1", postmotion="invalid", maxinterval="1000")
    with pytest.raises(SystemExit):
        parse_motion_args(args)

    # Test invalid max interval
    args = argparse.Namespace(motion=True, threshold="1", postmotion="1", maxinterval="invalid")
    with pytest.raises(SystemExit):
        parse_motion_args(args)
