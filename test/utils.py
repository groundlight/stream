import contextlib
import logging


@contextlib.contextmanager
def thread_logging():
    """Context manager to handle logging in threads."""
    try:
        yield
    finally:
        # Ensure all logging handlers are closed properly
        logging.shutdown()
