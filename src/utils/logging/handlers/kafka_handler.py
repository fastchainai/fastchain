"""
File: src/utils/logging/handlers/kafka_handler.py
Description: Kafka logging handler implementation
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any
from kafka import KafkaProducer

class KafkaHandler(logging.Handler):
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Kafka handler.
        
        Args:
            config (dict): Configuration containing Kafka connection details
                and topic settings.
        """
        super().__init__()
        
        self.bootstrap_servers = config.get('bootstrap_servers', ['localhost:9092'])
        self.topic = config.get('topic', 'logs')
        self.extra_fields = config.get('extra_fields', {})
        
        # Initialize Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            retries=5
        )

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record to Kafka.
        
        Args:
            record: The log record to emit
        """
        try:
            # Extract extra fields from record if they exist
            extra = {
                key: value for key, value in record.__dict__.items()
                if not key.startswith('_') and 
                key not in logging.LogRecord.__dict__
            }
            
            # Build the message
            message = {
                'timestamp': datetime.utcnow().isoformat(),
                'logger': record.name,
                'level': record.levelname,
                'message': self.format(record),
                'source': {
                    'file': record.filename,
                    'line': record.lineno,
                    'function': record.funcName,
                },
                'extra': {**extra, **self.extra_fields}
            }
            
            # Add exception info if present
            if record.exc_info:
                message['exception'] = {
                    'type': str(record.exc_info[0].__name__),
                    'message': str(record.exc_info[1]),
                    'traceback': self.formatter.formatException(record.exc_info)
                }
            
            # Send to Kafka
            self.producer.send(self.topic, message)
            self.producer.flush()
            
        except Exception as e:
            # Fall back to console logging if Kafka emission fails
            print(f"Failed to send log to Kafka: {e}")
            print(f"Original log message: {record.getMessage()}")
            
    def close(self) -> None:
        """Close the Kafka producer when the handler is closed."""
        if self.producer:
            self.producer.close()
        super().close()
