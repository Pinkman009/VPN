"""
vpn_speedtest.py - Diagnostics, latency check, IP info and speed test for Teletok VPN.
Uses standard urllib to avoid hard external dependencies.
"""

import os
import time
import socket
import json
import urllib.request
import urllib.error

VPS_HOST = "node.teletok.space"
DEFAULT_PROXY = "http://127.0.0.1:10897"

def measure_ping(host=VPS_HOST, port=443, timeout=3.0):
    """Measures TCP handshake latency in milliseconds."""
    t0 = time.perf_counter()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        latency = (time.perf_counter() - t0) * 1000
        return round(latency, 1)
    except Exception:
        return -1

def get_ip_info(proxy=DEFAULT_PROXY, timeout=5.0):
    """
    Fetches external IP and geolocation.
    Returns dict: {ip, country, city, isp} or fallback info.
    """
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}))
    else:
        handlers.append(urllib.request.ProxyHandler({}))
    
    opener = urllib.request.build_opener(*handlers)
    
    # Try ip-api.com
    try:
        req = urllib.request.Request("http://ip-api.com/json/?fields=status,query,country,countryCode,city,isp",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if data.get('status') == 'success':
                return {
                    'ip': data.get('query', 'Unknown'),
                    'country': data.get('country', ''),
                    'country_code': data.get('countryCode', ''),
                    'city': data.get('city', ''),
                    'isp': data.get('isp', '')
                }
    except Exception:
        pass

    # Fallback to ipify
    try:
        req = urllib.request.Request("https://api.ipify.org?format=json",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return {
                'ip': data.get('ip', 'Unknown'),
                'country': 'Unknown',
                'country_code': '',
                'city': '',
                'isp': ''
            }
    except Exception as e:
        return {'ip': 'Offline / Недоступен', 'country': '', 'country_code': '', 'city': '', 'isp': str(e)}

def check_service_status(proxy=DEFAULT_PROXY, timeout=4.0):
    """
    Checks accessibility of popular blocked/geoblocked services.
    Handles HTTPError properly (e.g. 401 on OpenAI API / 403 on Cloudflare).
    Returns dict: {service_name: bool}
    """
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}))
    else:
        handlers.append(urllib.request.ProxyHandler({}))
    opener = urllib.request.build_opener(*handlers)

    services = {
        'YouTube': ('https://www.youtube.com/generate_204', (200, 204, 301, 302)),
        'Google': ('https://www.google.com/generate_204', (200, 204, 301, 302)),
        'ChatGPT': ('https://api.openai.com/v1/models', (200, 401, 403)),
        'Claude': ('https://api.anthropic.com/v1/messages', (200, 400, 401, 403)),
    }

    results = {}
    for name, (url, valid_codes) in services.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with opener.open(req, timeout=timeout) as resp:
                results[name] = resp.status in valid_codes
        except urllib.error.HTTPError as e:
            results[name] = e.code in valid_codes
        except Exception:
            results[name] = False
    return results

def update_geodata_files(target_dirs):
    """
    Downloads latest geosite.dat and geoip.dat from Loyalsoldier GitHub release
    and updates them in target directories.
    Returns (success: bool, message: str)
    """
    sources = {
        'geosite.dat': 'https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat',
        'geoip.dat': 'https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat'
    }
    updated = []
    for filename, url in sources.items():
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                if len(data) < 100000:
                    return False, f"Ошибка загрузки {filename}: файл слишком мал"
                for d in target_dirs:
                    if os.path.exists(d):
                        dest = os.path.join(d, filename)
                        with open(dest, "wb") as f:
                            f.write(data)
                updated.append(f"{filename} ({round(len(data)/1024/1024, 1)} МБ)")
        except Exception as e:
            return False, f"Ошибка скачивания {filename}: {e}"

    return True, f"Базы успешно обновлены: {', '.join(updated)}"

def measure_download_speed(proxy=DEFAULT_PROXY, bytes_count=10000000, max_seconds=5.0):
    """
    Measures download speed in Mbps using a chunk from Cloudflare speed test.
    Returns Mbps as float.
    """
    handlers = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({'http': proxy, 'https': proxy}))
    else:
        handlers.append(urllib.request.ProxyHandler({}))
    opener = urllib.request.build_opener(*handlers)

    url = f"https://speed.cloudflare.com/__down?bytes={bytes_count}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        t0 = time.perf_counter()
        total_bytes = 0
        with opener.open(req, timeout=max_seconds + 3.0) as resp:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if time.perf_counter() - t0 >= max_seconds:
                    break
        elapsed = time.perf_counter() - t0
        if elapsed > 0:
            speed_mbps = (total_bytes * 8) / (elapsed * 1_000_000)
            return round(speed_mbps, 2)
    except Exception:
        pass
    return 0.0

if __name__ == '__main__':
    print("Testing ping to VPS:", measure_ping(), "ms")
    print("Fetching direct IP info:", get_ip_info(proxy=None))
