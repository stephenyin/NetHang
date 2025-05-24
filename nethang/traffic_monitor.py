"""
Traffic Monitor

This module provides a mechanism for monitoring network traffic.

Author: Hang Yin
Date: 2025-05-19
"""

import re
import subprocess
import time
import random
from . import app
from typing import Dict, List
from threading import Thread

class TrafficMonitor:
    # Ethernet Frame Header Size
    ETHERNET_HEADER_SIZE = 14
    def __init__(
            self, id_range: tuple,
            interval: float = 1,
            lan_iface: str = '', wan_iface: str = '',
            stats_callback=None):
        self.interval = interval
        self.lan_iface = lan_iface
        self.wan_iface = wan_iface
        self.ids = range(id_range[0], id_range[1]) # Total 32 marks are available. Seems it is not necessary to make it configurable
        self.running = False
        self.thread = None
        self.stats: Dict = {}
        self.data_to_emit: Dict = {
            'labels': [None for _ in range(100)],
            'data': {
                str(id): {
                    'uplink': {
                        'bitRateIn': [None for _ in range(100)],
                        'bitRateOut': [None for _ in range(100)],
                        'packetRateIn': [None for _ in range(100)],
                        'packetRateOut': [None for _ in range(100)],
                        'bytesIn': [None for _ in range(100)],
                        'bytesOut': [None for _ in range(100)],
                        'packetsIn': [None for _ in range(100)],
                        'packetsOut': [None for _ in range(100)],
                        'queuePackets': [None for _ in range(100)],
                        'queueDropPackets': [None for _ in range(100)],
                        'queueDropRate': [None for _ in range(100)],
                    },
                    'downlink': {
                        'bitRateIn': [None for _ in range(100)],
                        'bitRateOut': [None for _ in range(100)],
                        'packetRateIn': [None for _ in range(100)],
                        'packetRateOut': [None for _ in range(100)],
                        'bytesIn': [None for _ in range(100)],
                        'bytesOut': [None for _ in range(100)],
                        'packetsIn': [None for _ in range(100)],
                        'packetsOut': [None for _ in range(100)],
                        'queuePackets': [None for _ in range(100)],
                        'queueDropPackets': [None for _ in range(100)],
                        'queueDropRate': [None for _ in range(100)],
                    }
                } for id in self.ids
            }
        }
        self.previous_stats: Dict = {}
        self.start_time = None
        self.stats_callback = stats_callback

    def _run_command(self, cmd: List[str]) -> str:
        """Run shell command"""
        app.logger.debug(f"Run command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout

    def _extract_iptables_stats(self, iptables_output: str, in_iface: str, out_iface: str, id: int) -> Dict:
        for line in iptables_output.splitlines():
            parts = line.split()
            if f'MARK set {hex(int(id))}' in line and in_iface == parts[5] and out_iface == parts[6]:
                return {
                    # Calculate actual bytes, add ethernet header size
                    'bytes': int(parts[1]) + (int(parts[0]) * TrafficMonitor.ETHERNET_HEADER_SIZE),
                    'packets': int(parts[0])
                }
        return {'bytes': 0, 'packets': 0}

    def _extract_tc_stats(self, tc_output: str, id: int) -> Dict:
        stats = {}
        current_leaf_id = None

        for line in tc_output.split('\n'):
            if 'qdisc netem' in line:
                match = re.search(r'qdisc netem\s+(\d+)', line)
                if match:
                    if current_leaf_id == id:
                        break
                    current_leaf_id = int(match.group(1))

            if current_leaf_id != id:
                continue

            if 'Sent' in line:
                match = re.search(r'Sent\s+(\d+)\s+bytes\s+(\d+)\s+pkt', line)
                if match:
                    stats['bytes'] = int(match.group(1))
                    stats['packets'] = int(match.group(2))

            if 'backlog' in line:
                match = re.search(r'backlog\s+(\d+)b\s+(\d+)p', line)
                if match:
                    stats['backlog'] = int(match.group(1))
                    stats['backlog_packets'] = int(match.group(2))
                else:
                    match = re.search(r'backlog\s+(\d+)Kb\s+(\d+)p', line)
                    if match:
                        stats['backlog'] = int(match.group(1)) * 1024
                        stats['backlog_packets'] = int(match.group(2))

            if 'dropped' in line:
                match = re.search(r'dropped\s+(\d+)', line)
                if match:
                    stats['drops'] = int(match.group(1))

        return stats

    def _get_direction_stats(self, direction: str, iptables_stats: Dict, egress_tc: str, current_time: float, id: int) -> Dict:
        tc_stats_egress = self._extract_tc_stats(egress_tc, id)
        if tc_stats_egress == {}:
            return {}

        previous_time = self.stats.get(str(id), {}).get('timeStamp', current_time)
        elapsed_time = current_time - previous_time

        previous_ingress_bytes = self.stats.get(str(id), {}).get('trafficStats', {}).get(direction, {}).get('ingress', {}).get('bytes', 0)
        previous_ingress_packets = self.stats.get(str(id), {}).get('trafficStats', {}).get(direction, {}).get('ingress', {}).get('packets', 0)
        previous_q_drops = self.stats.get(str(id), {}).get('trafficStats', {}).get(direction, {}).get('queue', {}).get('dropPackets', 0)
        previous_egress_bytes = self.stats.get(str(id), {}).get('trafficStats', {}).get(direction, {}).get('egress', {}).get('bytes', 0)
        previous_egress_packets = self.stats.get(str(id), {}).get('trafficStats', {}).get(direction, {}).get('egress', {}).get('packets', 0)

        ingress_bytes_diff = iptables_stats['bytes'] - previous_ingress_bytes
        ingress_packets_diff = iptables_stats['packets'] - previous_ingress_packets
        q_drops_diff = tc_stats_egress.get('drops', 0) - previous_q_drops
        egress_bytes_diff = tc_stats_egress.get('bytes', 0) - previous_egress_bytes
        egress_packets_diff = tc_stats_egress.get('packets', 0) - previous_egress_packets

        return {
            "ingress": {
                "bytes": iptables_stats['bytes'],
                "packets": iptables_stats['packets'],
                "bitRate": int(ingress_bytes_diff * 8 / elapsed_time) if elapsed_time != 0 else 0,
                "packetRate": int(ingress_packets_diff / elapsed_time) if elapsed_time != 0 else 0,
            },
            "queue": {
                "bytes": tc_stats_egress.get('backlog', 0),
                "packets": tc_stats_egress.get('backlog_packets', 0),
                "dropPackets": tc_stats_egress.get('drops', 0),
                "dropRate": round(q_drops_diff / ingress_packets_diff if ingress_packets_diff != 0 else 0, 4)
            },
            "egress": {
                "bytes": tc_stats_egress.get('bytes', 0),
                "packets": tc_stats_egress.get('packets', 0),
                "bitRate": int(egress_bytes_diff * 8 / elapsed_time) if elapsed_time != 0 else 0,
                "packetRate": int(egress_packets_diff / elapsed_time) if elapsed_time != 0 else 0
            }
        }


    def _create_empty_direction_stats(self) -> Dict:
        return {
            'ingress': {'bytes': 0, 'packets': 0, 'bitRate': 0, 'packetRate': 0},
            'queue': {'bytes': 0, 'packets': 0, 'dropPackets': 0, 'dropRate': 0},
            'egress': {'bytes': 0, 'packets': 0, 'bitRate': 0, 'packetRate': 0}
        }

    def _create_base_stats(self, timestamp: float, id: int) -> Dict:
        return {
            'filter': {
                'lan': self.lan_iface,
                'wan': self.wan_iface,
                'mark_id': id,
            },
            'timeStamp': timestamp,
            'elapsedTime': int(timestamp - self.start_time),
            'trafficStats': {
                'uplink': self._create_empty_direction_stats(),
                'downlink': self._create_empty_direction_stats()
            }
        }

    def _process_stats(self, iptables_output: str, tc_lan_output: str, tc_wan_output: str, current_time: float) -> Dict:
        stats_ = {}

        # TODO: performance improvement needed
        for id in self.ids:
            iptables_uplink_stats = self._extract_iptables_stats(iptables_output, self.lan_iface, self.wan_iface, id)
            iptables_downlink_stats = self._extract_iptables_stats(iptables_output, self.wan_iface, self.lan_iface, id)
            stats_[str(id)] = self._create_base_stats(current_time, id)
            stats_[str(id)]['trafficStats']['uplink'] = self._get_direction_stats('uplink', iptables_uplink_stats, tc_wan_output, current_time, id)
            stats_[str(id)]['trafficStats']['downlink'] = self._get_direction_stats('downlink', iptables_downlink_stats, tc_lan_output, current_time, id)

            for direction in ['uplink', 'downlink']:
                if stats_[str(id)]['trafficStats'][direction] and stats_[str(id)]['trafficStats'][direction] != {}:
                    self.data_to_emit['data'][str(id)][direction]['bitRateIn'].append(round(stats_[str(id)]['trafficStats'][direction]['ingress']['bitRate'] / 1000, 2)) # To Kbps
                    self.data_to_emit['data'][str(id)][direction]['packetRateIn'].append(stats_[str(id)]['trafficStats'][direction]['ingress']['packetRate'])
                    self.data_to_emit['data'][str(id)][direction]['bytesIn'].append(stats_[str(id)]['trafficStats'][direction]['ingress']['bytes'])
                    self.data_to_emit['data'][str(id)][direction]['packetsIn'].append(stats_[str(id)]['trafficStats'][direction]['ingress']['packets'])
                    self.data_to_emit['data'][str(id)][direction]['queuePackets'].append(stats_[str(id)]['trafficStats'][direction]['queue']['packets'])
                    self.data_to_emit['data'][str(id)][direction]['queueDropPackets'].append(stats_[str(id)]['trafficStats'][direction]['queue']['dropPackets'])
                    self.data_to_emit['data'][str(id)][direction]['queueDropRate'].append(round(stats_[str(id)]['trafficStats'][direction]['queue']['dropRate'] * 100, 2)) # To Percentage
                    self.data_to_emit['data'][str(id)][direction]['bitRateOut'].append(round(stats_[str(id)]['trafficStats'][direction]['egress']['bitRate'] / 1000, 2)) # To Kbps
                    self.data_to_emit['data'][str(id)][direction]['packetRateOut'].append(stats_[str(id)]['trafficStats'][direction]['egress']['packetRate'])
                    self.data_to_emit['data'][str(id)][direction]['bytesOut'].append(stats_[str(id)]['trafficStats'][direction]['egress']['bytes'])
                    self.data_to_emit['data'][str(id)][direction]['packetsOut'].append(stats_[str(id)]['trafficStats'][direction]['egress']['packets'])

                    self.data_to_emit['data'][str(id)][direction]['bitRateIn'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['packetRateIn'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['bytesIn'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['packetsIn'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['queuePackets'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['queueDropPackets'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['queueDropRate'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['bitRateOut'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['packetRateOut'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['bytesOut'].pop(0)
                    self.data_to_emit['data'][str(id)][direction]['packetsOut'].pop(0)

        self.data_to_emit['labels'].append(time.strftime('%H:%M:%S', time.localtime(current_time)))
        self.data_to_emit['labels'].pop(0)

        return stats_

    def _get_current_stats(self) -> Dict:
        iptables_output = self._run_command(['iptables', '-nvxL', 'FORWARD', '-t', 'mangle'])
        tc_lan_output = self._run_command(['tc', '-s', 'qdisc', 'show', 'dev', self.lan_iface])
        tc_wan_output = self._run_command(['tc', '-s', 'qdisc', 'show', 'dev', self.wan_iface])

        return self._process_stats(iptables_output, tc_lan_output, tc_wan_output, time.time())

    def monitor_loop(self):
        """Main monitoring loop"""
        self.start_time = time.time()
        while self.running:
            self.stats = self._get_current_stats()

            # Call callback function if provided
            if self.stats_callback:
                self.stats_callback(self.data_to_emit)

            time.sleep(self.interval)  # Update every interval

    def restart(self):
        """Restart the monitor"""
        self.stop()
        self.start()

    def stop(self):
        """Stop the monitor"""
        self.running = False
        try:
            if self.thread and self.thread.is_alive():
                self.thread.join()
            self.thread = None
        except Exception as e:
            app.logger.warning(f"Warning in stop traffic monitor: {e}")
            self.restart()

    def start(self):
        """Start the monitor"""
        self.running = True

        try:
            if self.thread is None:
                self.thread = Thread(target=self.monitor_loop, daemon=True)
                self.thread.start()

        except Exception as e:
            app.logger.warning(f"Warning in start traffic monitor: {e}")
            self.restart()
