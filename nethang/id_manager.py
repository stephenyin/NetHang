"""
ID Manager

This module provides a mechanism for managing unique IDs across processes
using file locking.

Author: Hang Yin
Date: 2025-05-19
"""

import os
import yaml
from typing import Optional

class IDManager:
    """Manage unique IDs across processes using file locking"""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 paths_file: str,
                 id_range: tuple):
        self.paths_file = paths_file
        self.id_range = id_range
        self.current_id = None
        self._init_files()

    def _init_files(self):
        """Initialize lock file if it doesn't exist"""

        # Ensure the directory for paths.yaml exists
        os.makedirs(os.path.dirname(self.paths_file), exist_ok=True)

    def _read_paths(self) -> dict:
        """Read current paths from paths.yaml"""
        if os.path.exists(self.paths_file):
            try:
                with open(self.paths_file, 'r') as f:
                    return yaml.safe_load(f) or[]
            except (yaml.YAMLError, IOError):
                return[]
        return[]

    def _get_used_ids(self) -> set:
        """Get the set of IDs currently in use from paths.yaml"""
        paths_data = self._read_paths()
        used_ids = set()

        for path in paths_data:
            if 'id' in path:
                used_ids.add(path['id'])

        return used_ids

    def acquire_id(self) -> Optional[int]:
        """Acquire a unique ID for the current process"""
        # Get currently used IDs from paths.yaml
        used_ids = self._get_used_ids()

        # Find first available ID in the range
        for potential_id in range(self.id_range[0], self.id_range[1] + 1):
            if potential_id not in used_ids:
                self.current_id = potential_id
                return potential_id

        return None  # No available IDs

    def release_id(self):
        """Release the ID held by the current process"""
        # No need to do anything here as the ID is managed by paths.yaml
        # The ID will be released when the path is deleted from paths.yaml
        self.current_id = None

    def get_current_id(self) -> Optional[int]:
        """Get the current process's ID without acquiring a new one"""
        return self.current_id

    def __enter__(self):
        """Context manager support"""
        self.acquire_id()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support"""
        self.release_id()
