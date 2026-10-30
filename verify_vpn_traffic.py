import sys
import urllib.request
import json
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:10809', 'https': 'http://127.0.0.1:10809'})
opener = urllib.request.build_opener(proxy_handler)

targets = [
    "https://ipinfo.io/json",
    "https://www.youtube.com",
    "https://www.instagram.com",
    "https://chatgpt.com",
    "https://x.com"
]

print("=== ТЕСТИРОВАНИЕ ПОДКЛЮЧЕНИЯ ЧЕРЕЗ VLESS-REALITY ===")
for url in targets:
    t0 = time.time()
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with opener.open(req, timeout=12) as resp:
            dt = round((time.time() - t0) * 1000)
            status = resp.status
            content = resp.read()
            print(f"[OK] {url} -> Status: {status}, Time: {dt} ms, Bytes: {len(content)}")
            if "ipinfo" in url:
                data = json.loads(content.decode())
                print(f"     -> Real External IP: {data.get('ip')} ({data.get('city')}, {data.get('country')})")
    except Exception as e:
        print(f"[FAIL] {url} -> Error: {e}")
