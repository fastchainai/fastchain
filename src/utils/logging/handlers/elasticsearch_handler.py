"""
File: src/utils/logging/handlers/elasticsearch_handler.py
Description: Elasticsearch logging handler implementation
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any
from elasticsearch import Elasticsearch

class ElasticsearchHandler(logging.Handler):
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Elasticsearch handler.
        
        Args:
            config (dict): Configuration containing Elasticsearch connection details
                and index settings.
        """
        super().__init__()
        
        self.es_hosts = config.get('hosts', ['http://localhost:9200'])
        self.index_prefix = config.get('index_prefix', 'logs')
        self.extra_fields = config.get('extra_fields', {})
        
        # Initialize Elasticsearch client
        self.client = Elasticsearch(
            self.es_hosts,
            retry_on_timeout=True,
            max_retries=3
        )

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record to Elasticsearch.
        
        Args:
            record: The log record to emit
        """
        try:
            # Create the log document
            timestamp = datetime.utcnow().isoformat()
            index_name = f"{self.index_prefix}-{datetime.utcnow():%Y.%m.%d}"
            
            # Extract extra fields from record if they exist
            extra = {
                key: value for key, value in record.__dict__.items()
                if not key.startswith('_') and 
                key not in logging.LogRecord.__dict__
            }
            
            # Build the document
            doc = {
                'timestamp': timestamp,
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
                doc['exception'] = {
                    'type': str(record.exc_info[0].__name__),
                    'message': str(record.exc_info[1]),
                    'traceback': self.formatter.formatException(record.exc_info)
                }
            
            # Send to Elasticsearch
            self.client.index(
                index=index_name,
                document=doc
            )
            
        except Exception as e:
            # Fall back to console logging if Elasticsearch emission fails
            print(f"Failed to send log to Elasticsearch: {e}")
            print(f"Original log message: {record.getMessage()}")
