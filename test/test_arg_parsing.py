import argparse

import pytest

from stream.stream import parse_motion_args, validate_stream_args


def test_parse_stream_args():
    # Test device number with infer type
    args = argparse.Namespace(stream="0", streamtype="infer")
    stream, stream_type = validate_stream_args(args)
    assert stream == 0
    assert stream_type is None

    # Test non-numeric string with infer type
    args = argparse.Namespace(stream="test.mp4", streamtype="infer")
    stream, stream_type = validate_stream_args(args)
    assert stream == "test.mp4"
    assert stream_type is None

    # Test explicit device type
    args = argparse.Namespace(stream="1", streamtype="device")
    stream, stream_type = validate_stream_args(args)
    assert stream == "1"
    assert stream_type == "device"

    # Test directory type
    args = argparse.Namespace(stream="*.jpg", streamtype="directory")
    stream, stream_type = validate_stream_args(args)
    assert stream == "*.jpg"
    assert stream_type == "directory"

    # Test RTSP stream
    args = argparse.Namespace(stream="rtsp://example.com/stream", streamtype="rtsp")
    stream, stream_type = validate_stream_args(args)
    assert stream == "rtsp://example.com/stream"
    assert stream_type == "rtsp"

    # Test YouTube URL
    args = argparse.Namespace(stream="https://youtube.com/watch?v=123", streamtype="youtube")
    stream, stream_type = validate_stream_args(args)
    assert stream == "https://youtube.com/watch?v=123"
    assert stream_type == "youtube"


def test_parse_motion_args():
    # Test motion detection disabled
    args = argparse.Namespace(motion=False)
    motion_on, threshold, post_motion, max_interval = parse_motion_args(args)
    assert not motion_on
    assert threshold == 0
    assert post_motion == 0
    assert max_interval == 0

    # Test motion detection enabled with defaults
    args = argparse.Namespace(motion=True, threshold=1.0, postmotion=1.0, maxinterval=1000.0)
    motion_on, threshold, post_motion, max_interval = parse_motion_args(args)
    assert motion_on
    assert threshold == 1.0
    assert post_motion == 1.0
    assert max_interval == 1000.0

    # Test custom values
    args = argparse.Namespace(motion=True, threshold=2.5, postmotion=0.5, maxinterval=100.0)
    motion_on, threshold, post_motion, max_interval = parse_motion_args(args)
    assert motion_on
    assert threshold == 2.5
    assert post_motion == 0.5
    assert max_interval == 100.0
