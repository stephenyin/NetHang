"""
NetHang

This is a Flask application for managing network quality simulation.

Author: Hang Yin
Date: 2025-05-19
"""

import os
import logging
from flask import Flask
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

# Create config directory if it doesn't exist
os.makedirs(CONFIG_PATH, exist_ok=True)

# Create Flask app
app = Flask(__name__)

# Configure logging
try:
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10000000, backupCount=5)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
except (IOError, PermissionError) as e:
    # If we can't create the log file, just log to stderr
    app.logger.warning(f"Could not create log file: {e}")
    app.logger.warning("Logging to stderr instead")

app.logger.setLevel(logging.INFO)
app.logger.info('NetHang startup')

# Import routes after app creation to avoid circular imports
from . import routes