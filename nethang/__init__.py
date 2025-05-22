"""
NetHang

This is a Flask application for managing network quality simulation.

Author: Hang Yin
Date: 2025-05-19
"""

import os
from flask import Flask
import logging
from logging.handlers import RotatingFileHandler

# Admin username
ADMIN_USERNAME = 'admin'

# Lock files
IPT_LOCK_FILE : str = '/tmp/nethang_iptables_modi.lock'
ID_LOCK_FILE : str = '/tmp/nethang_id.lock'

# Config files
CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.nethang')
CONFIG_FILE = os.path.join(CONFIG_PATH, 'config.yaml')
MODELS_FILE = os.path.join(CONFIG_PATH, 'models.yaml')
PATHS_FILE = os.path.join(CONFIG_PATH, 'paths.yaml')

# Log file
LOG_FILE = os.path.join(CONFIG_PATH, 'nethang.log')

# Configure logging
logging.basicConfig(level=logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# File handler with rotation
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10000000, backupCount=5)
file_handler.setFormatter(formatter)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# Create Flask app
app = Flask(__name__)
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
app.logger.setLevel(logging.INFO)

# Import routes after app creation to avoid circular imports
from . import routes