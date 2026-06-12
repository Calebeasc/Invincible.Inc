import logging
import requests
import traceback
import threading
import queue

# Create a thread-safe queue for logs
log_queue = queue.Queue()

# Background worker to process logs without blocking FastAPI
def _sentinel_worker():
    while True:
        log_entry = log_queue.get()
        if log_entry is None:
            break
        try:
            requests.post("http://localhost:9999/log", json=log_entry, timeout=1.0)
        except Exception:
            pass # Fail silently if Sentinel is offline
        finally:
            log_queue.task_done()

# Start the daemon thread
threading.Thread(target=_sentinel_worker, daemon=True).start()

class SentinelHandler(logging.Handler):
    def emit(self, record):
        try:
            log_entry = {
                "source": "BACKEND",
                "level": record.levelname,
                "message": record.getMessage(),
                "traceback": traceback.format_exc() if record.exc_info else None
            }
            # Put the log in the queue; do not wait for the network request
            log_queue.put_nowait(log_entry)
        except Exception:
            pass

def setup_sentinel_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(SentinelHandler())
