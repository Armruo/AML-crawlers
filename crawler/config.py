"""Configuration settings for the crawler application."""

import os
from typing import Dict, Any

# Base URLs
MISTTRACK_BASE_URL = "https://misttrack.io/aml_risks"

# HTTP Settings
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json"
}

# Scraper Settings
SCRAPER_CONFIG: Dict[str, Any] = {
    'browser': {
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    },
    'timeout': 30,  # seconds
    'max_retries': 3
}

# File Upload Settings
UPLOAD_DIR = 'uploads'
ALLOWED_FILE_TYPES = ('.csv', '.xls', '.xlsx')
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# WebSocket Settings
WS_GROUP_PREFIX = "task_"

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'crawler.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'crawler': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
