import queue
import threading
import time
from unittest.mock import Mock

from stream.threads import ThreadControl, setup_workers, worker_loop


def test_thread_control():
    tc = ThreadControl()
    assert not tc.exit_all_threads
    tc.force_exit()
    assert tc.exit_all_threads


def test_worker_loop():
    q = queue.Queue()
    tc = ThreadControl()
    mock_fn = Mock()

    # Start worker thread
    thread = threading.Thread(target=worker_loop, kwargs=dict(q=q, control=tc, fn=mock_fn))
    thread.start()

    # Add work item and verify it gets processed
    test_data = "test"
    q.put(test_data)
    time.sleep(0.1)  # Give thread time to process
    mock_fn.assert_called_once_with(test_data)

    # Verify thread exits when control.exit_all_threads is set
    tc.force_exit()
    thread.join(timeout=2)
    assert not thread.is_alive()


def test_setup_workers():
    mock_fn = Mock()
    num_workers = 3

    q, tc, workers = setup_workers(fn=mock_fn, num_workers=num_workers)

    # Verify correct number of workers created
    assert len(workers) == num_workers
    assert all(isinstance(w, threading.Thread) for w in workers)
    assert all(w.is_alive() for w in workers)

    # Add work items and verify they get processed
    test_data = "test"
    for _ in range(num_workers):
        q.put(test_data)

    time.sleep(0.1)  # Give threads time to process
    assert mock_fn.call_count == num_workers

    # Clean up
    tc.force_exit()
    for worker in workers:
        worker.join(timeout=2)
        assert not worker.is_alive()
