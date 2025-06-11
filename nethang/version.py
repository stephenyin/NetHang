"""
nethang/version.py

This module provides a mechanism for getting the version of the application.

Author: Hang Yin
Date: 2025-06-11
"""

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8 的兼容性
    from importlib_metadata import version, PackageNotFoundError

def get_version():
    """Get the version of the application"""
    try:
        return version('nethang')
    except PackageNotFoundError:
        # In development environment, the package may not be installed
        return "dev"

def get_package_info():
    """Get the complete package information"""
    try:
        from importlib.metadata import metadata
        meta = metadata('nethang')
        return {
            'name': meta['Name'],
            'version': meta['Version'],
            'summary': meta.get('Summary', ''),
            'author': meta.get('Author', ''),
            'homepage': meta.get('Home-page', ''),
        }
    except (PackageNotFoundError, ImportError):
        return {
            'name': 'nethang',
            'version': 'dev',
            'summary': 'Development version',
            'author': 'Unknown',
            'homepage': '',
        }

# Export the version information
__version__ = get_version()