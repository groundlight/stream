import logging
import os
from collections.abc import Callable
from logging.config import dictConfig
from queue import Empty, Queue
from threading import Thread

import yaml

fname = os.path.join(os.path.dirname(__file__), "logging.yaml")
dictConfig(yaml.safe_load(open(fname)))
logger = logging.getLogger(name="groundlight.stream")


class ThreadControl:
    """Controls graceful shutdown of worker threads"""

    def __init__(self):
        self.exit_all_threads = False

    def force_exit(self):
        logger.debug("Attempting force exit of all threads")
        self.exit_all_threads = True


def setup_workers(fn: Callable, num_workers: int = 10) -> tuple[Queue, ThreadControl, list[Thread]]:
    """Setup worker threads and queues"""

    q = Queue()
    tc = ThreadControl()
    workers = []

    for _ in range(num_workers):
        thread = Thread(target=worker_loop, kwargs=dict(q=q, control=tc, fn=fn))
        workers.append(thread)
        thread.start()

    return q, tc, workers


def worker_loop(q: Queue, control: ThreadControl, fn: Callable):
    """Worker thread that processes frames from the queue and sends them to Groundlight

    Args:
        q: Queue containing work to do
        fn: Function to do the work
        control: ThreadControl instance for coordinated shutdown
    """
    while not control.exit_all_threads:
        try:
            work = q.get(timeout=1)  # Timeout prevents orphaned threads
            fn(work)
        except Empty:
            continue

    logger.debug("exiting worker thread.")
