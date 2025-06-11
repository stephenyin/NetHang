"""
Routes

This module provides the routes for the Flask application.

Author: Hang Yin
Date: 2025-05-19
"""

import os
import netifaces
import hashlib
import subprocess
import tomli
import yaml
import sys
import signal
from . import app, ID_LOCK_FILE, ADMIN_USERNAME, PATHS_FILE
from flask import render_template, request, jsonify, redirect, url_for, session, g
from functools import wraps
from nethang.proc_lock import ProcLock
from nethang.simu_path import SimuPathManager
from nethang.id_manager import IDManager
from nethang.extensions import socketio
from nethang.config_manager import ConfigManager
from nethang.version import __version__

app.config['SECRET_KEY'] = os.urandom(24)
socketio.init_app(app)

ConfigManager().ensure_models()

# Initialize SimuPathManager
SimuPathManager()

chart_data = {
    'labels': [None for _ in range(100)],
    'data': [None for _ in range(100)]
}

def cleanup(sig, frame):
    """Cleanup the application"""
    app.logger.info(f"Received signal {sig}, performing cleanup...")
    SimuPathManager().deactivate_all_paths()
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, cleanup)  # Handles Ctrl+C
signal.signal(signal.SIGTERM, cleanup)  # Handles kill/termination

def check_privileges():
    """Check if the application has sufficient privileges for tc and iptables"""
    tc_status = check_tc()
    iptables_status = check_iptables()

    return {
        'tc_access': tc_status.get('tc_access', False),
        'iptables_access': iptables_status.get('iptables_access', False),
        'tc_error': tc_status.get('error', ''),
        'iptables_error': iptables_status.get('error', '')
    }

@app.before_request
def before_request():
    """Check privileges before each request"""
    g.privileges = check_privileges()
    config = SimuPathManager().load_config()
    if 'lan_interface' not in config or 'wan_interface' not in config or config['lan_interface'] == '' or config['wan_interface'] == '':
        g.no_interface = True
    else:
        g.no_interface = False

def hash_password(password):
    """Hash a password using MD5"""
    return hashlib.md5(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify a password against its hash"""
    return hash_password(password) == hashed_password

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_network_interfaces():
    interfaces = []
    for iface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(iface)
        if netifaces.AF_INET in addrs:
            ip = addrs[netifaces.AF_INET][0]['addr']
            interfaces.append({'name': iface, 'ip': ip})
    return interfaces

def check_iptables():
    try:
        # First check if iptables command exists
        which_result = subprocess.run(
            ['which', 'iptables'],
            capture_output=True, text=True, check=True)

        if not which_result.stdout.strip():
            return {
                'iptables_access': False,
                'error': 'iptables command not found in system'
            }

        # Run a harmless iptables command (e.g., list rules)
        result = subprocess.run(['iptables', '-L', '-n'], capture_output=True, text=True, check=True)
        return {
            'iptables_access': True,
            'output': result.stdout,
            'message': 'iptables command executed successfully'
        }
    except subprocess.CalledProcessError as e:
        return {
            'iptables_access': False,
            'error': f'iptables command failed: {str(e)}'
        }
    except PermissionError:
        return {
            'iptables_access': False,
            'error': 'Permission denied: Insufficient privileges for iptables'
        }
    except FileNotFoundError:
        return {
            'iptables_access': False,
            'error': 'iptables command not found in system'
        }

def check_tc():
    try:
        # First check if tc command exists
        which_result = subprocess.run(
            ['which', 'tc'],
            capture_output=True, text=True, check=True)

        if not which_result.stdout.strip():
            return {
                'tc_access': False,
                'error': 'tc command not found in system'
            }

        # Run a harmless tc command
        result = subprocess.run(
            ['tc', 'qdisc', 'add', 'dev', 'lo', 'handle', '0', 'netem', 'delay', '0ms'],
            capture_output=True, text=True, check=True)
        return {
            'tc_access': True,
            'output': result.stdout,
            'message': 'tc command executed successfully'
        }
    except subprocess.CalledProcessError as e:
        return {
            'tc_access': True,
            'error': f'tc command failed: {str(e)}'
        }
    except PermissionError:
        return {
            'tc_access': False,
            'error': 'Permission denied: Insufficient privileges for tc'
        }
    except FileNotFoundError:
        return {
            'tc_access': False,
            'error': 'tc command not found in system'
        }

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Get admin password from config
        config = SimuPathManager().load_config()
        admin_password = config.get('admin_password', hash_password('admin'))  # Default to hashed 'admin' if not set

        if username != ADMIN_USERNAME:
            app.logger.error(f"Invalid username: {username}")
            return render_template('login.html', error='Invalid username')

        if not verify_password(password, admin_password):
            app.logger.error(f"Invalid password: {password}")
            return render_template('login.html', error='Invalid password')

        session['logged_in'] = True
        app.logger.info(f"Login successful for username: {username}")
        return redirect(url_for('index'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    app.logger.info("Logout successful")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    """Render the main dashboard page"""
    try:
        # Load configuration
        config = SimuPathManager().load_config()

        # Load paths
        paths = SimuPathManager().load_paths()

        # Load models
        models = SimuPathManager().load_models()

        return render_template('index.html', paths=paths, config=config, models=models)
    except Exception as e:
        app.logger.error(f"Error rendering index page: {e}")
        return render_template('error.html', error=str(e))

@app.route('/api/paths', methods=['GET', 'POST', 'PUT', 'DELETE'])
@login_required
def manage_paths():
    # Get paths
    if request.method == 'GET':
        app.logger.info("Getting paths")
        return jsonify(SimuPathManager().load_paths())

    # Add path
    if request.method == 'POST':
        new_path = request.json

        # Get a new path ID from IDManager
        id_manager = IDManager(paths_file=PATHS_FILE, id_range=SimuPathManager.mark_range)
        with ProcLock(ID_LOCK_FILE):
            path_id = id_manager.acquire_id()
            if path_id is None:
                return jsonify({'status': 'error', 'message': 'Failed to acquire path ID'}), 500

            new_path['id'] = path_id
            new_path['filter_settings']['mark'] = path_id
            SimuPathManager().add_path(new_path)

        app.logger.info(f"Adding path {new_path}")
        return jsonify({'status': 'success', 'message': 'Path added successfully', 'id': path_id})

    # Update path
    if request.method == 'PUT':
        app.logger.info(f"Updating path {request.json.get('id')}")
        SimuPathManager().update_path_config(request.json.get('id'), request.json)
        return jsonify({'status': 'success', 'message': 'Path updated successfully'})

    # Delete path
    if request.method == 'DELETE':
        path_id = request.args.get('id')
        app.logger.info(f"Deleting path {path_id}")
        # Find the path to be deleted
        path_to_delete = SimuPathManager().get_path_config(int(path_id))

        if path_to_delete:
            # Delete the path in system
            with ProcLock(ID_LOCK_FILE):
                SimuPathManager().delete_path(int(path_id))
            return jsonify({'status': 'success', 'message': 'Path deleted successfully'})
        else:
            return jsonify({'status': 'error', 'message': 'Path not found'}), 404

@app.route('/api/paths/<path_id>/activate', methods=['POST'])
@login_required
def activate_path(path_id):
    app.logger.info(f"Activating path {path_id}")
    try:
        SimuPathManager().activate_path(int(path_id))
        return jsonify({'status': 'success', 'message': 'Path activated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/paths/<path_id>/deactivate', methods=['POST'])
@login_required
def deactivate_path(path_id):
    app.logger.info(f"Deactivating path {path_id}")
    try:
        SimuPathManager().deactivate_path(int(path_id))
        return jsonify({'status': 'success', 'message': 'Path deactivated successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@socketio.on('connect')
def handle_connect():
    """Send initial chart data to new clients."""
    app.logger.info("Sending initial chart data to new clients")
    socketio.emit('update_chart', {
        'labels': chart_data['labels'],
        'data': chart_data['data']
    })

def emit_config_update():
    """Emit configuration update event to all connected clients."""
    app.logger.info("Emitting configuration update event to all connected clients")
    socketio.emit('config_updated')

@app.route('/config', methods=['GET', 'POST'])
@login_required
def config():
    if request.method == 'POST':
        config_data = SimuPathManager().load_config()
        config_data.update({
            'lan_interface': request.form.get('lan_interface', ''),
            'wan_interface': request.form.get('wan_interface', ''),
        })
        app.logger.info(f"Saving configuration: {config_data}")
        SimuPathManager().save_config(config_data)
        emit_config_update()  # Emit config update event
        return redirect(url_for('index'))

    current_config = SimuPathManager().load_config()
    interfaces = get_network_interfaces()
    return render_template('config.html', config=current_config, interfaces=interfaces)

def get_version():
    """Read version from pyproject.toml"""
    try:
        with open("pyproject.toml", "rb") as f:
            pyproject = tomli.load(f)
            return pyproject["project"]["version"]
    except Exception as e:
        app.logger.error(f"Error reading version from pyproject.toml: {e}")
        return "unknown"

def get_models_version():
    """Read models version from models.yaml"""
    try:
        models_file = os.path.expanduser("~/.nethang/models.yaml")
        if os.path.exists(models_file):
            with open(models_file, 'r') as f:
                models_data = yaml.safe_load(f)
                if models_data and isinstance(models_data, dict) and 'version' in models_data:
                    return models_data['version']
        return "unknown"
    except Exception as e:
        app.logger.error(f"Error reading models version: {e}")
        return "unknown"

@app.route('/about')
@login_required
def about():
    return render_template('about.html', version=__version__, models_version=get_models_version())

@app.route('/api/settings', methods=['GET', 'POST'])
def settings_api():
    app.logger.info("Getting settings")
    if request.method == 'GET':
        # Get current settings
        config = SimuPathManager().load_config()
        settings = {
            'lan_interface': config.get('lan_interface', ''),
            'wan_interface': config.get('wan_interface', ''),
        }
        return jsonify(settings)
    elif request.method == 'POST':
        app.logger.info("Updating settings")
        # Update settings
        data = request.json

        # Load current config
        config = SimuPathManager().load_config()

        # Update config with new values
        config['lan_interface'] = data.get('lan_interface', '')
        config['wan_interface'] = data.get('wan_interface', '')

        # Only update password if a new one is provided
        if data.get('password'):
            config['admin_password'] = hash_password(data.get('password'))

        # Save config to file
        try:
            SimuPathManager().save_config(config)
            return jsonify({'status': 'success'})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)})