"""
Network Simulation Path Management

This module provides a mechanism for managing network simulation paths.

Author: Hang Yin
Date: 2025-05-19
"""

import subprocess
import re
import yaml
import os
import time
from . import app, CONFIG_PATH, CONFIG_FILE, MODELS_FILE, PATHS_FILE, IPT_LOCK_FILE
from multiprocessing import Process
from dataclasses import dataclass
from typing import Optional, Dict, List
from nethang.proc_lock import ProcLock
from nethang.traffic_monitor import TrafficMonitor
from nethang.extensions import socketio

@dataclass
class SimuSettings:
    """Network simulation settings for a direction (uplink/downlink)"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        if hasattr(self, 'restrict_settings') and self.restrict_settings:
            try:
                for key, value in self.restrict_settings.items():
                    if value == None or value == '':
                        value = self.get_default_value(key)
                        self.restrict_settings[key] = value
            except Exception as e:
                app.logger.error(f"Error in SimuSettings: {e}")

    def get_default_value(self, key):
        if key == 'rate_limit':
            return 32000000
        elif key == 'qdepth':
            return 1000
        elif key == 'loss':
            return 0.0
        elif key == 'delay':
            return 0
        elif key == 'jitter':
            return 0
        else:
            app.logger.info(f"Not implemented key: {key}")

    def __eq__(self, other):
        return (
            self.mode == other.mode and \
            self.restrict_settings['rate_limit'] == other.restrict_settings['rate_limit'] and \
            self.restrict_settings['qdepth'] == other.restrict_settings['qdepth'] and \
            self.restrict_settings['loss'] == other.restrict_settings['loss'] and \
            self.restrict_settings['delay'] == other.restrict_settings['delay'] and \
            self.restrict_settings['jitter'] == other.restrict_settings['jitter'] and \
            self.restrict_settings['reorder_allowed'] == other.restrict_settings['reorder_allowed']
        )

    def to_dict(self):
        """Convert the SimuSettings object to a dictionary"""
        return self.restrict_settings

@dataclass
class FilterSettings:
    """Filter settings for a network path"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __eq__(self, other):
        return self.protocol == other.protocol and self.lan_ip == other.lan_ip and self.lan_port == other.lan_port and self.wan_ip == other.wan_ip and self.wan_port == other.wan_port and self.mark == other.mark

class SimuPath:
    """Represents a network simulation path with filter and simulation settings"""
    def __init__(self, filter_settings: FilterSettings, mode: str, model: str, status: str,
                 uplink_settings: SimuSettings, downlink_settings: SimuSettings):
        self.filter = filter_settings
        self.mode = mode # 'model', 'custom'
        self.model = model # models.yaml
        self.status = status # "active" or "inactive"
        self.uplink_settings = uplink_settings
        self.downlink_settings = downlink_settings
        self.simu_proc = None
        self.__direction = {
            'uplink':{
                'from':SimuPathManager.lan_ifname,
                'to':SimuPathManager.wan_ifname,
                'dir':'s',
            },
            'downlink':{
                'from':SimuPathManager.wan_ifname,
                'to':SimuPathManager.lan_ifname,
                'dir':'d',
            }
        }

    def __eq__(self, other):
        return self.filter == other.filter

    def is_active(self):
        return self.status == "active"

    def _cleanup(self, direction_ : str):
        """Cleanup the path by removing traffic control"""
        app.logger.info(f"Cleaning up path {self.filter.mark} {direction_}")
        if hasattr(self, 'filter'):
            SimuPathManager.run_cmd('tc filter del dev {iface} parent {handle}: handle {host_num} protocol ip pref {prio} fw'.format(
                iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name, host_num = self.filter.mark, prio = SimuPathManager.PRIO ))
            SimuPathManager.run_cmd('tc class del dev {iface} classid {handle}:{host_num}'.format(
                iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name, host_num = self.filter.mark ))
            SimuPathManager.run_cmd('tc qdisc del dev {iface} parent {handle}:{host_num} handle {host_num}'.format(
                iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name, host_num = self.filter.mark ))
        else:
            app.logger.error(f'Cannot delete rules: filter not available')

        self.status = "inactive"

    def _init_tc(self, direction_ : str):
        """Initialize traffic control for a direction"""
        app.logger.info(f"Initializing traffic control for {direction_}")
        # SimuPathManager.run_cmd('tc qdisc add dev {iface} root handle {handle}: stab overhead {overhead} linklayer ethernet htb default 0xffff direct_qlen 1000'.format(
        #     iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name, overhead = SimuPathManager.OVERHEAD))
        SimuPathManager.run_cmd('tc qdisc add dev {iface} root handle {handle}: htb default 0xffff direct_qlen 1000'.format(
            iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name))
        SimuPathManager.run_cmd('tc class add dev {iface} parent {handle}: classid {handle}:ffff htb rate {rate}kbit quantum 60000'.format(
            iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name, rate = SimuPathManager.MAX_RATE))

    def _apply_tc(self, direction_ : str, opt : str = 'add',
            rate_limit : int = 32000000, rate_ceil : int = 32000000,
            rate_burst : int = 0, rate_cburst : int = 0,
            qdepth : int = 1000,
            loss : float = 0.0,
            delay : int = 0,
            jitter : int = 0,
            jitter_dist : str = 'normal',
            slot : list = [0, 0],
            reorder_allowed : bool = False
            ):

        class_str_ = ''
        # If rate_limit is greater than MAX_RATE, using MAX_RATE as rate
        # Otherwise, using rate_limit as rate
        if rate_limit > SimuPathManager.MAX_RATE:
            class_str_ += ' rate {}Gbit'.format(SimuPathManager.MAX_RATE / 1000000)
        else:
            class_str_ += ' rate {}Kbit'.format(rate_limit)

        # If rate_ceil is greater than or equal to MAX_RATE, using rate_limit as ceil
        # Otherwise, using rate_ceil as ceil
        if rate_ceil >= SimuPathManager.MAX_RATE:
            class_str_ += ' ceil {}Kbit'.format(rate_limit)
        else:
            class_str_ += ' ceil {}Kbit'.format(rate_ceil)

        # If rate_burst is less than or equal to 0, using rate_limit / 80 as burst
        # Otherwise, using rate_burst as burst
        if rate_burst <= 0:
            class_str_ += ' burst {}KB'.format(round(rate_limit / 80, 2))
        else:
            class_str_ += ' burst {}KB'.format(rate_burst)

        # If rate_cburst is less than or equal to 0, using rate_limit / 80 as cburst
        # Otherwise, using rate_cburst as cburst
        if rate_cburst <= 0:
            class_str_ += ' cburst {}KB'.format(round(rate_limit / 80, 2))
        else:
            class_str_ += ' cburst {}KB'.format(rate_cburst)

        netem_str_ = ''
        netem_str_ += f' limit {qdepth}'
        delay_, jitter_ = self.__get_delay_jitter_param(delay, jitter)
        if delay_ != 0 or jitter_ != 0:
            netem_str_ += ' delay'
            netem_str_ += f' {delay_}ms'
            if jitter_ != 0:
                netem_str_ += f' {jitter_}ms distribution {jitter_dist}'
        netem_str_ += f' loss {loss}%'
        netem_str_ += f' slot {slot[0]}ms {slot[1]}ms'

        SimuPathManager.run_cmd('tc class {opt} dev {iface} parent {handle}: classid {handle}:{host_num} htb {class_str} quantum 60000'.format(
            opt = opt, iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name, host_num = self.filter.mark, class_str = class_str_))
        SimuPathManager.run_cmd('tc qdisc {opt} dev {iface} parent {handle}:{host_num} handle {host_num}: netem {netem_str}'.format(
            opt = opt, iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name, host_num = self.filter.mark, netem_str = netem_str_))
        if opt == 'add':
            SimuPathManager.run_cmd('tc filter add dev {iface} parent {handle}: prio {prio} protocol ip handle {host_num} fw flowid {handle}:{host_num}'.format(
            iface = self.__direction[direction_]['to'], handle = SimuPathManager.handle_name, prio = SimuPathManager.PRIO, host_num = self.filter.mark))

    def _run_custom(self):
        """Run custom simulation"""

        app.logger.info(f"Running custom simulation for PATH {self.filter.mark}")

        for direction in ['uplink', 'downlink']:
            self._cleanup(direction)

        if self.uplink_settings.mode != 'bypass':
            self._set_rule('uplink', 'add', self.uplink_settings.to_dict())
        else:
            app.logger.info(f"Bypassing uplink for PATH {self.filter.mark}")
            self._cleanup('uplink')

        if self.downlink_settings.mode != 'bypass':
            self._set_rule('downlink', 'add', self.downlink_settings.to_dict())
        else:
            app.logger.info(f"Bypassing downlink for PATH {self.filter.mark}")
            self._cleanup('downlink')

    def _run_model(self):
        app.logger.info(f"Running model simulation for PATH {self.filter.mark}")
        try:
            if self.model not in SimuPathManager().models:
                raise ValueError(f'Case {self.model} not found, please check available models, exit ...')
            model_ = SimuPathManager().get_model_settings(self.model)
        except Exception as e:
            raise e

        # At first cleanup
        for direction in ['uplink', 'downlink']:
            self._cleanup(direction)

        model_global = model_.get('global', {})
        model_timeline = model_.get('timeline', [])

        if not model_timeline:
            # Static model
            for direction in ['uplink', 'downlink']:
                self._set_rule(direction, 'add', model_global[direction])
        else:
            # Dynamic model
            is_first_timeslot : bool = True
            while True:
                for model_timeslot in model_timeline:

                    merged_model = SimuPathManager.merge_dicts(model_global, model_timeslot)

                    if is_first_timeslot:
                        opt_ = 'add'
                        is_first_timeslot = False
                    else:
                        opt_ = 'change'

                    for direction in ['uplink', 'downlink']:
                        self._set_rule(direction, opt_, merged_model[direction])

                    if 'duration' in model_timeslot:
                        # Maybe need high precision sleep
                        time.sleep(model_timeslot['duration'])

    def _set_rule(self, direction : str, opt : str, config : dict):
        """Set traffic control rules using provided parameters"""

        app.logger.info(f"set_rule: {direction} {opt} {config}")

        if opt == 'add':
            self._init_tc(direction)
            self._cleanup(direction)

        self._apply_tc(
            direction,
            opt,
            rate_limit = config.get('rate_limit', SimuPathManager.MAX_RATE),
            qdepth = config.get('qdepth', 1000),
            loss = config.get('loss', 0.0),
            delay = config.get('delay', 0),
            jitter = config.get('jitter', 0),
            jitter_dist = config.get('jitter_dist', 'normal'),
            slot = config.get('slot', [0, 0]),
            reorder_allowed = config.get('reorder_allowed', False),
        )

    def _simu_path_worker(self):
        """Run tc command for path activation"""
        app.logger.info(f"Running simulation for PATH {self.filter.mark}")

        try:
            if self.mode == 'custom':
                self._run_custom()
            elif self.mode == 'model':
                self._run_model()
            else:
                raise ValueError(f"Invalid mode: {self.mode}")

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to set up traffic control: {e}")

    def activate(self):
        """Activate the path by setting up traffic control"""
        app.logger.info(f"Activating path {self.filter.mark}")
        try:
            # Create the path in system by creating a new iptables rule
            self.create()

            # Set up traffic control for both directions
            self.simu_proc = Process(target=self._simu_path_worker, args=(), daemon=True)
            self.simu_proc.start()
            self.status = "active"
        except Exception as e:
            raise RuntimeError(f"Failed to activate path: {e}")

    def deactivate(self):
        """Deactivate the path by removing traffic control"""
        app.logger.info(f"Deactivating path {self.filter.mark}")
        try:
            if self.simu_proc:
                self.simu_proc.terminate()

            # Delete the path in system by deleting the iptables rule
            self.delete()
        finally:
            for direction in ['uplink', 'downlink']:
                self._cleanup(direction)
            self.status = "inactive"

    def create(self):
        """ Create the path in system by creating a new iptables rule """

        def create_iptables_rule(direction_ : str):
            iptables_str_ = ''

            if self.filter.lan_ip:
                if direction_ == 'uplink':
                    iptables_str_ += ' -s {}'.format(self.filter.lan_ip)
                else:
                    iptables_str_ += ' -d {}'.format(self.filter.lan_ip)

            if self.filter.wan_ip:
                if direction_ == 'uplink':
                    iptables_str_ += ' -d {}'.format(self.filter.wan_ip)
                else:
                    iptables_str_ += ' -s {}'.format(self.filter.wan_ip)

            if self.filter.protocol in ['udp', 'tcp']:
                iptables_str_ += ' -p {}'.format(self.filter.protocol)
                if self.filter.lan_port and self.filter.lan_port != 'Any' and int(self.filter.lan_port) > 0 and int(self.filter.lan_port) < 65536:
                    if direction_ == 'uplink':
                        iptables_str_ += ' --sport {}'.format(self.filter.lan_port)
                    else:
                        iptables_str_ += ' --dport {}'.format(self.filter.lan_port)

                if self.filter.wan_port and self.filter.wan_port != 'Any' and int(self.filter.wan_port) > 0 and int(self.filter.wan_port) < 65536:
                    if direction_ == 'uplink':
                        iptables_str_ += ' --dport {}'.format(self.filter.wan_port)
                    else:
                        iptables_str_ += ' --sport {}'.format(self.filter.wan_port)

            with ProcLock(IPT_LOCK_FILE):
                SimuPathManager.run_cmd('iptables -t mangle -A FORWARD -i {form_iface} -o {to_iface} {iptables_str} -j MARK --set-mark {host_num} > /dev/null 2>&1'.format(
                    form_iface = self.__direction[direction_]['from'], to_iface = self.__direction[direction_]['to'], iptables_str=iptables_str_, host_num = self.filter.mark))

        create_iptables_rule('uplink')
        create_iptables_rule('downlink')

    def delete(self):
        """Delete the path in system by deleting the iptables rule"""
        def delete_iptables_rule(direction_ : str):
            iptables_str_ = ''

            if self.filter.lan_ip:
                if direction_ == 'uplink':
                    iptables_str_ += ' -s {}'.format(self.filter.lan_ip)
                else:
                    iptables_str_ += ' -d {}'.format(self.filter.lan_ip)

            if self.filter.wan_ip:
                if direction_ == 'uplink':
                    iptables_str_ += ' -d {}'.format(self.filter.wan_ip)
                else:
                    iptables_str_ += ' -s {}'.format(self.filter.wan_ip)

            if self.filter.protocol in ['udp', 'tcp']:
                iptables_str_ += ' -p {}'.format(self.filter.protocol)
                if self.filter.lan_port and self.filter.lan_port != 'Any' and int(self.filter.lan_port) > 0 and int(self.filter.lan_port) < 65536:
                    if direction_ == 'uplink':
                        iptables_str_ += ' --sport {}'.format(self.filter.lan_port)
                    else:
                        iptables_str_ += ' --dport {}'.format(self.filter.lan_port)

                if self.filter.wan_port and self.filter.wan_port != 'Any' and int(self.filter.wan_port) > 0 and int(self.filter.wan_port) < 65536:
                    if direction_ == 'uplink':
                        iptables_str_ += ' --dport {}'.format(self.filter.wan_port)
                    else:
                        iptables_str_ += ' --sport {}'.format(self.filter.wan_port)

            with ProcLock(IPT_LOCK_FILE):
                SimuPathManager.run_cmd('iptables -t mangle -D FORWARD -i {form_iface} -o {to_iface} {iptables_str} -j MARK --set-mark {host_num} > /dev/null 2>&1'.format(
                    form_iface = self.__direction[direction_]['from'], to_iface = self.__direction[direction_]['to'], iptables_str=iptables_str_, host_num = self.filter.mark))

        delete_iptables_rule('uplink')
        delete_iptables_rule('downlink')

    def __del__(self):
        """Delete the path by removing traffic control"""
        self.deactivate()

    def __get_delay_jitter_param(self, input_delay, input_jitter):
        delay_ = input_delay if input_delay != None else 0
        jitter_ = input_jitter if input_jitter != None else 0

        if jitter_ == 0:
            return delay_, jitter_

        # Delay must be greater than 0, otherwise jitter will not work in netem
        delay_ = delay_ if delay_ != 0 else 1

        # Make the jitter's literal value closer to the observed value in statistics
        return delay_, int(jitter_ / 2)

    @classmethod
    def from_dict(cls, data: Dict) -> 'SimuPath':
        """Create a SimuPath instance from a dictionary"""
        return cls(
            filter_settings=FilterSettings(**data['filter_settings']),
            mode=data['simu_settings']['mode'],
            model=data['simu_settings']['model'],
            status=data['status'],
            uplink_settings=SimuSettings(**data['simu_settings']['uplink']),
            downlink_settings=SimuSettings(**data['simu_settings']['downlink'])
        )

class SimuPathManager:
    """Manages network simulation paths"""
    _instance = None

    PRIO = 2
    OVERHEAD = 0
    MAX_RATE = 32000000 # 32Gbps
    handle_name = '9527'
    lan_ifname = None
    wan_ifname = None
    mark_range = (9527, 9559)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimuPathManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.load_config()

        self.paths: Dict[int, SimuPath] = {}
        self.refresh_paths()
        self.reset_all_paths()

        self.models = self.load_models()['models']
        self.traffic_monitor = TrafficMonitor(
            interval=1, # Seems it is not necessary to make it configurable
            lan_iface=SimuPathManager.lan_ifname,
            wan_iface=SimuPathManager.wan_ifname,
            id_range=SimuPathManager.mark_range,
            stats_callback=SimuPathManager.emit_chart_data
        )

        self._initialized = True

    def refresh_paths(self):
        """Refresh paths by loading from paths.yaml"""
        self.paths.clear()
        for path in self.load_paths():
            self.paths[path['id']] = SimuPath.from_dict(path)

    def load_models(self):
        try:
            if os.path.exists(MODELS_FILE):
                with open(MODELS_FILE, 'r') as f:
                    models = yaml.safe_load(f)
                    if 'models' in models:
                        return models
                    else:
                        return {'models': {}}
            else:
                return {'models': {}}
        except Exception as e:
            app.logger.error(f"Error loading models: {e}")
            return {'models': {}}

    def load_config(self):
        """Load configuration from config.yaml"""
        if os.path.exists(CONFIG_FILE):
            config = {}
            with open(CONFIG_FILE, 'r') as f:
                config = yaml.safe_load(f)
                if config:
                    SimuPathManager.lan_ifname = config.get('lan_interface', '') if 'lan_interface' in config else ''
                    SimuPathManager.wan_ifname = config.get('wan_interface', '') if 'wan_interface' in config else ''
                    return config
                else:
                    SimuPathManager.lan_ifname = ''
                    SimuPathManager.wan_ifname = ''
                    return {
                        'lan_interface': '',
                        'wan_interface': '',
                    }
        else:
            SimuPathManager.lan_ifname = ''
            SimuPathManager.wan_ifname = ''
            return {
                'lan_interface': '',
                'wan_interface': '',
            }

    def save_config(self, config):
        """Save configuration to config.yaml"""
        os.makedirs(CONFIG_PATH, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            yaml.dump(config, f)
        self.emit_config_update()  # Emit config update event

    def load_paths(self) -> List:
        """Load paths from paths.yaml"""
        if os.path.exists(PATHS_FILE):
            try:
                with open(PATHS_FILE, 'r') as f:
                    paths_data = yaml.safe_load(f)
                    if paths_data is None:
                        paths_data = []
                    return paths_data
            except yaml.YAMLError as e:
                app.logger.error(f"Error parsing paths.yaml: {e}")
                # If the file is corrupted, create a new one with empty paths
                paths = []
                self.save_paths(paths)
                return paths
        return []

    def save_paths(self, paths):
        """Save paths to paths.yaml"""
        os.makedirs(CONFIG_PATH, exist_ok=True)
        with open(PATHS_FILE, 'w') as f:
            yaml.dump(paths, f)
        self.emit_config_update()  # Emit config update event

    def deactivate_all_paths(self):
        """Deactivate all paths"""
        for path in self.paths.values():
            path.deactivate()

    def reset_all_paths(self):
        """Reset all paths according to the config"""

        # Deactivate all paths
        self.deactivate_all_paths()

        # Update paths.yaml
        paths_data = self.load_paths()
        for p in paths_data:
            p['status'] = 'inactive'

        self.save_paths(paths_data)

    def add_to_path_config(self, path: SimuPath):
        """Add a path to paths.yaml"""
        paths_data = self.load_paths()
        paths_data.append(path)
        self.save_paths(paths_data)

    def update_path_config(self, id: int, path):
        """Update a path in paths.yaml"""
        paths_data = self.load_paths()
        for i, p in enumerate(paths_data):
            if int(p['id']) == id:
                paths_data[i] = path
                break
        self.save_paths(paths_data)
        self.refresh_paths()

    def delete_from_path_config(self, id: int):
        """Delete a path from paths.yaml"""
        paths_data = self.load_paths()
        for p in paths_data:
            if int(p['id']) == id:
                paths_data.remove(p)
                break
        self.save_paths(paths_data)

    def get_path_config(self, id: int) -> SimuPath:
        """Get a path from paths.yaml"""
        paths_data = self.load_paths()
        for p in paths_data:
            if int(p['id']) == id:
                return p
        return None

    def add_path(self, path):
        """Add a path in system by creating a new iptables rule and save it to paths.yaml"""
        self.paths[path['id']] = SimuPath.from_dict(path)
        self.add_to_path_config(path)

    def delete_path(self, id: int):
        """Delete a path in system by deleting the iptables rule and save it to paths.yaml"""
        if id not in self.paths:
            raise ValueError(f"Path with id {id} not found")

        del self.paths[id]
        self.delete_from_path_config(id)

    def activate_path(self, id: int):
        """Activate a path by id"""
        if id not in self.paths:
            raise ValueError(f"Path with id {id} not found")

        self.paths[id].activate()

        # Update paths.yaml
        paths_data = self.load_paths()
        for p in paths_data:
            if int(p['id']) == id:
                p['status'] = 'active'
                break
        self.save_paths(paths_data)
        self.traffic_monitor.start()

    def deactivate_path(self, id: int):
        """Deactivate a path by id"""
        if id not in self.paths:
            raise ValueError(f"Path with id {id} not found")

        self.paths[id].deactivate()

        # Update paths.yaml
        paths_data = self.load_paths()
        for p in paths_data:
            if int(p['id']) == id:
                p['status'] = 'inactive'
                break
        self.save_paths(paths_data)

        if len(self.get_active_paths()) == 0:
            self.traffic_monitor.stop()

    def get_active_paths(self) -> List[SimuPath]:
        """Get all active paths"""
        return [path for path in self.paths.values() if path.status == 'active']

    def is_path_active(self, id: int) -> bool:
        """Check if a path is active by id"""
        pass

    def get_paths(self) -> List[SimuPath]:
        """Get all paths"""
        return list(self.paths.values())

    def get_model_settings(self, model_name: str) -> Optional[Dict]:
        """Get settings for a specific model"""
        return self.models.get(model_name)

    @staticmethod
    def emit_chart_data(chart_data_callback):
        """Send chart data to all connected clients."""
        socketio.emit('update_chart', {
            'labels': chart_data_callback['labels'],
            'data': chart_data_callback['data']
        })

    @staticmethod
    def emit_config_update():
        """Emit configuration update event to all connected clients."""
        socketio.emit('config_updated')

    @staticmethod
    def run_cmd(cmd : str = '', mute : bool = True) -> str:
        app.logger.debug(f"Run command: {cmd}")
        if mute:
            cmd += ' > /dev/null 2>&1'

        ret = os.popen(cmd).read()
        return ret

    @staticmethod
    def merge_dicts(base: dict, update: dict) -> dict:
        """
        Recursively merge two dictionaries, with values from update taking precedence
        """
        merged = base.copy()
        for key, value in update.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                merged[key] = SimuPathManager.merge_dicts(merged[key], value)
            elif value is not None:  # Only update if value is not None
                merged[key] = value
        return merged