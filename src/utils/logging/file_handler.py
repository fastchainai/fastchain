"""
File: src/utils/logging/file_handler.py
Description: Provides a FileHandler class for file-based logging.
Date: 24/02/2025
Version: 1.0.0
Repository: https://github.com/
"""

import logging

class FileHandler(logging.FileHandler):
    def __init__(self, filename: str):
        # Opens the file in append mode by default.
        super().__init__(filename, mode='a')
