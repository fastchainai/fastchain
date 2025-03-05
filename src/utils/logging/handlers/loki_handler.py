"""
File: src/utils/logging/handlers/loki_handler.py
Description: Implements a custom logging handler that sends logs to Loki via HTTP API.
Date: 24/02/2025
Version: 1.0.0
Repository: [repo]
"""

import json
import logging
import threading
import time

import requests

class LokiHandler(logging.Handler):
    """
    A logging handler that sends log records to Loki via its HTTP API.
    """

    def __init__(self, config):
        """
        Initialize the LokiHandler.

        Args:
            config (dict): Configuration for the Loki handler.
                Expected keys:
                    - url: The Loki push API endpoint URL.
                    - batch_size: (Optional) Number of logs to batch before sending.
                    - flush_interval: (Optional) Time interval in seconds to flush logs.
                    - labels: (Optional) A dict of static labels to attach to every log.
        """
        super().__init__()
        self.url = config.get("url")
        if not self.url:
            raise ValueError("LokiHandler requires a 'url' in the configuration.")
        
        self.batch_size = config.get("batch_size", 10)
        self.flush_interval = config.get("flush_interval", 5)
        self.static_labels = config.get("labels", {})

        self.log_batch = []
        self.lock = threading.RLock()  # changed from Lock() to RLock()
        self.last_flush_time = time.time()

        # Start background flush thread if flush_interval is set.
        self._stop_event = threading.Event()
        self.flush_thread = threading.Thread(target=self._periodic_flush, daemon=True)
        self.flush_thread.start()

    def emit(self, record):
        """
        Emit a log record to Loki. Formats the record as a JSON payload and adds it
        to the batch. Flushes the batch if the batch size is reached.
        """
        try:
            # Format the log record into a string.
            msg = self.format(record)
            timestamp_ns = int(record.created * 1e9)
            stream = {
                "stream": self.static_labels,
                "values": [[str(timestamp_ns), msg]]
            }
            with self.lock:
                self.log_batch.append(stream)
                # Check if batch size is reached.
                if len(self.log_batch) >= self.batch_size:
                    self.flush()
        except Exception:
            self.handleError(record)

    def flush(self):
        """
        Flush the batched log records to Loki.
        """
        with self.lock:
            if not self.log_batch:
                return
            payload = {"streams": self.log_batch}
            try:
                headers = {"Content-Type": "application/json"}
                response = requests.post(self.url, headers=headers,
                                         data=json.dumps(payload))
                response.raise_for_status()
            except Exception as e:
                # Log error to stderr since logging might be in a bad state.
                print(f"Error sending logs to Loki: {e}")
            finally:
                self.log_batch.clear()
                self.last_flush_time = time.time()

    def _periodic_flush(self):
        """
        Background thread that periodically flushes logs based on the flush_interval.
        """
        while not self._stop_event.is_set():
            time.sleep(self.flush_interval)
            with self.lock:
                if self.log_batch and (time.time() - self.last_flush_time) >= self.flush_interval:
                    self.flush()

    def close(self):
        """
        Ensure all logs are flushed and background thread is stopped.
        """
        self._stop_event.set()
        self.flush_thread.join(timeout=2)
        self.flush()
        super().close()
