"""
Run

This module provides a mechanism for running the application.

Author: Hang Yin
Date: 2025-05-19
"""

from nethang import app

def main():
    app.run(host='0.0.0.0', port=9527, debug=False)

if __name__ == '__main__':
    main()