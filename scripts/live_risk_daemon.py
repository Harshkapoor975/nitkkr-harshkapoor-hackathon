"""
scripts/live_risk_daemon.py
---------------------------
CLI Runner forwarding to canonical implementation in src.crawlers.daemon.
"""
import os
import sys

# Ensure root import path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Forward to canonical daemon implementation in src/crawlers/daemon.py
from src.crawlers.daemon import GLOBAL_DAEMON

if __name__ == "__main__":
    print("🌐 Starting Live Risk Intelligence Daemon...")
    print("Press Ctrl+C to terminate.\n")
    try:
        GLOBAL_DAEMON.is_running = True
        GLOBAL_DAEMON._loop()
    except KeyboardInterrupt:
        GLOBAL_DAEMON.stop()
