"""
Фоновый сервис запуска и поддержания Teletok VPN.
Подключает ядро Xray, балансировщик каналов и включает системный прокси Windows.
"""
import sys
import time
import os

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import vpn_core

print("Starting Teletok VPN Engine...")
engine = vpn_core.VpnEngine()
try:
    engine.connect()
    print("STATUS: CONNECTED_SUCCESSFULLY")
    print("Proxy listening on 127.0.0.1:10897 (HTTP) and 127.0.0.1:10898 (SOCKS5)")
    sys.stdout.flush()
    while True:
        time.sleep(2)
except Exception as e:
    print(f"ERROR: {e}")
    sys.stdout.flush()
finally:
    print("Shutting down VPN Engine...")
    engine.disconnect()
