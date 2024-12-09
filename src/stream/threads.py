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
    """Gracefully shutdown all worker threads

    Args:
        timeout: Maximum time to wait for threads to finish
    Returns:
        bool: True if all threads completed, False if timeout occurred
    """

    def __init__(self):
        self.exit_all_threads = False

    def shutdown(self) -> bool:
        logger.debug("Attempting force exit of all threads")
        self.exit_all_threads = True
        return True


def setup_workers(
    fn: Callable, num_workers: int = 10, daemon: bool = True
) -> tuple[Queue, ThreadControl, list[Thread]]:
    """Setup worker threads and queues

    Args:
        fn: Function to process work items
        num_workers: Number of worker threads
        daemon: If True, threads will be daemon threads that exit when main thread exits
    """

    q = Queue()
    tc = ThreadControl()
    workers = []

    for _ in range(num_workers):
        thread = Thread(target=worker_loop, kwargs=dict(q=q, control=tc, fn=fn), daemon=daemon)
        workers.append(thread)
        thread.start()

    return q, tc, workers


def worker_loop(q: Queue, control: ThreadControl, fn: Callable):
    """Worker thread that takes work (frames) from the queue and uses the provided function to process them

    Args:
        q: Queue containing work to do
        fn: Function to do the work
        control: ThreadControl instance for coordinated shutdown
    """
    while not control.exit_all_threads:
        try:
            work = q.get(timeout=1)  # Timeout prevents orphaned threads

            try:
                fn(work)
            except Exception as e:
                logger.error(f"Error processing work item: {e}", exc_info=True)
            finally:
                q.task_done()  # Signal completion even if there was an error

        except Empty:
            continue
        except Exception as e:
            logger.error(f"Critical error in worker thread: {e}", exc_info=True)
            break

    logger.debug("exiting worker thread.")
