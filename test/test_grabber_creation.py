import pytest
from framegrab import FrameGrabber

from stream.grabber2 import StreamType, _configure_options, _infer_stream_type, _stream_to_id, framegrabber_factory


def test_infer_stream_type():
    # Test integer input
    assert _infer_stream_type(0) == StreamType.GENERIC_USB
    assert _infer_stream_type(1) == StreamType.GENERIC_USB
    assert _infer_stream_type(2) == StreamType.GENERIC_USB

    # Test RTSP URLs
    assert _infer_stream_type("rtsp://example.com/stream") == StreamType.RTSP

    # Test HLS URLs
    assert _infer_stream_type("http://example.com/stream.m3u8") == StreamType.HLS
    assert _infer_stream_type("https://example.com/stream.m3u8") == StreamType.HLS

    # Test YouTube URLs
    assert _infer_stream_type("https://www.youtube.com/watch?v=123") == StreamType.YOUTUBE_LIVE

    # Test invalid inputs
    with pytest.raises(TypeError):
        _infer_stream_type(None)
    with pytest.raises(TypeError):
        _infer_stream_type(1.0)
    with pytest.raises(ValueError):
        _infer_stream_type("invalid://stream")

    # Test unimplemented types
    with pytest.raises(NotImplementedError):
        _infer_stream_type("http://example.com/image.jpg")
    with pytest.raises(NotImplementedError):
        _infer_stream_type("*.jpg")


def test_stream_to_id():
    # Test YouTube stream
    assert _stream_to_id("https://youtube.com/123", StreamType.YOUTUBE_LIVE) == {
        "youtube_url": "https://youtube.com/123"
    }

    # Test RTSP stream
    assert _stream_to_id("rtsp://example.com", StreamType.RTSP) == {"rtsp_url": "rtsp://example.com"}

    # Test HLS stream
    assert _stream_to_id("http://example.com/stream.m3u8", StreamType.HLS) == {
        "hls_url": "http://example.com/stream.m3u8"
    }

    # Test USB device
    assert _stream_to_id(0, StreamType.GENERIC_USB) == {"serial_number": 0}

    # Test unimplemented types
    assert _stream_to_id("test.jpg", StreamType.FILE) is None
    assert _stream_to_id("*.jpg", StreamType.DIRECTORY) is None
    assert _stream_to_id("http://example.com/img.jpg", StreamType.IMAGE_URL) is None


def test_configure_options():
    # Test resolution options
    opts = _configure_options(StreamType.RTSP, height=480, width=640)
    assert opts["resolution.height"] == 480
    assert opts["resolution.width"] == 640

    # Test max_fps option
    opts = _configure_options(StreamType.RTSP, max_fps=30)
    assert opts["max_fps"] == 30

    # Test max_fps warning for unsupported types
    opts = _configure_options(StreamType.GENERIC_USB, max_fps=30)
    assert "max_fps" not in opts

    # Test keep_connection_open for supported types
    opts = _configure_options(StreamType.RTSP, keep_connection_open=True)
    assert opts["keep_connection_open"] is True

    opts = _configure_options(StreamType.YOUTUBE_LIVE, keep_connection_open=True)
    assert opts["keep_connection_open"] is True

    opts = _configure_options(StreamType.HLS, keep_connection_open=True)
    assert opts["keep_connection_open"] is True

    # Test keep_connection_open for unsupported types
    opts = _configure_options(StreamType.GENERIC_USB, keep_connection_open=True)
    assert "keep_connection_open" not in opts


def test_framegrabber_factory():
    # Test USB camera creation
    grabber = framegrabber_factory(0)
    assert isinstance(grabber, FrameGrabber)

    # Test RTSP stream creation with options
    grabber = framegrabber_factory(
        "rtsp://example.com", stream_type=StreamType.RTSP, height=480, width=640, max_fps=30, keep_connection_open=True
    )
    assert isinstance(grabber, FrameGrabber)

    # Test stream type inference
    grabber = framegrabber_factory("rtsp://example.com")
    assert isinstance(grabber, FrameGrabber)

    # Test invalid stream
    with pytest.raises(ValueError):
        framegrabber_factory("invalid://stream")
