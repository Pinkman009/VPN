import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from vpn_core import VpnEngine

engine = VpnEngine()
print("Starting connection...", flush=True)
engine.connect()
print("VPN CONNECTED AND SYSTEM PROXY ACTIVE!", flush=True)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    engine.disconnect()
    print("Disconnected cleanly.")
