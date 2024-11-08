import io
import threading
import time
from functools import partial
from queue import Queue
from unittest.mock import MagicMock, Mock

import numpy as np
import pytest
from framegrab import MotionDetector
from groundlight import Groundlight

from stream import process_single_frame, run_capture_loop
from test.utils import thread_logging


@pytest.fixture
def mock_client():
    client = MagicMock(spec=Groundlight)
    client.ask_async = MagicMock(return_value={"id": "test_query"})
    return client


@pytest.fixture
def test_frame():
    # Create a simple test frame
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame[:, :] = [255, 128, 0]  # BGR color
    return frame


def test_process_single_frame_success(mock_client, test_frame):
    """Test that process_single_frame correctly processes a frame and submits it to the client."""
    detector = Mock()
    process_single_frame(test_frame, mock_client, detector)

    # Verify client was called correctly
    mock_client.ask_async.assert_called_once()
    call_args = mock_client.ask_async.call_args
    assert call_args[1]["detector"] == detector
    assert isinstance(call_args[1]["image"], io.BytesIO)


def test_run_capture_loop_basic(test_frame):
    """Test the basic functionality of run_capture_loop without motion detection."""
    with thread_logging():
        # Mock frame grabber
        mock_grabber = MagicMock()
        mock_grabber.grab.return_value = test_frame

        # Setup test queue
        test_queue = Queue()

        run_loop = partial(
            run_capture_loop,
            grabber=mock_grabber,
            queue=test_queue,
            fps=10.0,
            motion_detector=None,
            post_motion_time=0,
            max_frame_interval=0,
            resize_width=0,
            resize_height=0,
            crop_region=None,
        )

        thread = threading.Thread(target=run_loop)
        thread.daemon = True
        thread.start()

        # Let it run for a bit
        time.sleep(0.3)

        # Verify frames were grabbed and queued
        assert mock_grabber.grab.called
        assert not test_queue.empty()
        assert test_queue.qsize() > 1


def test_run_capture_loop_motion_detection(test_frame):
    """Test run_capture_loop with motion detection enabled."""
    with thread_logging():
        # Mock frame grabber
        mock_grabber = MagicMock()
        mock_grabber.grab.return_value = test_frame

        # Setup motion detector that always detects motion
        motion_detector = MagicMock(spec=MotionDetector)
        motion_detector.motion_detected.return_value = True

        test_queue = Queue()

        run_loop = partial(
            run_capture_loop,
            grabber=mock_grabber,
            queue=test_queue,
            fps=10.0,
            motion_detector=motion_detector,
            post_motion_time=1.0,
            max_frame_interval=5.0,
            resize_width=0,
            resize_height=0,
            crop_region=None,
        )

        thread = threading.Thread(target=run_loop)
        thread.daemon = True
        thread.start()

        time.sleep(0.3)

        # Verify motion detection was used and frames were queued
        assert motion_detector.motion_detected.called
        assert not test_queue.empty()


def test_run_capture_loop_fps_zero(test_frame):
    """Test run_capture_loop behavior when FPS is set to zero."""
    with thread_logging():
        mock_grabber = MagicMock()
        mock_grabber.grab.return_value = test_frame
        test_queue = Queue()

        run_loop = partial(
            run_capture_loop,
            grabber=mock_grabber,
            queue=test_queue,
            fps=0,  # Test fps=0 case
            motion_detector=None,
            post_motion_time=0,
            max_frame_interval=0,
            resize_width=0,
            resize_height=0,
            crop_region=None,
        )

        thread = threading.Thread(target=run_loop)
        thread.daemon = True
        thread.start()

        time.sleep(0.3)

        # Verify frames were grabbed and queued
        assert not test_queue.empty()


def test_run_capture_loop_no_frame():
    """Test run_capture_loop behavior when no frames are available."""
    with thread_logging():
        # Mock grabber that returns no frame
        mock_grabber = MagicMock()
        mock_grabber.grab.return_value = None
        test_queue = Queue()

        run_loop = partial(
            run_capture_loop,
            grabber=mock_grabber,
            queue=test_queue,
            fps=10.0,
            motion_detector=None,
            post_motion_time=0,
            max_frame_interval=0,
            resize_width=0,
            resize_height=0,
            crop_region=None,
        )

        thread = threading.Thread(target=run_loop)
        thread.daemon = True
        thread.start()

        time.sleep(0.3)

        # Verify no frames were queued
        assert test_queue.empty()
