"""
Process Lock

This module provides a process lock mechanism using file locking.
It allows multiple processes to coordinate access to a shared resource
by locking a file.

The lock is acquired by calling the `acquire` method, and released by
calling the `release` method.

The lock is automatically released when the `ProcLock` object is deleted.

The lock is also automatically released when the `ProcLock` object is used
in a with statement.

Author: Hang Yin
Date: 2025-05-19
"""

import fcntl

class ProcLock:
    def __init__(self, filename):
        self.filename = filename
        self.handle = open(filename, 'wb')

    def acquire(self):
        """Acquire file lock"""
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX)

    def release(self):
        """Release file lock"""
        fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)

    def __del__(self):
        self.handle.close()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
