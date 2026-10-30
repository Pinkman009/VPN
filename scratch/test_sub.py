import urllib.request
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

sub_url = "http://193.233.138.42:80/sub/83sm0dymf1qn5w9m"
req = urllib.request.Request(sub_url, headers={"User-Agent": "Happ/1.0.0"})

try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        raw = resp.read()
        print('HTTP Status:', resp.status)
        print('Headers:', resp.headers)
        try:
            decoded = base64.b64decode(raw).decode('utf-8')
            print('=== DECODED SUBSCRIPTION ===')
            for line in decoded.strip().splitlines():
                print(line)
        except Exception:
            print('=== RAW (not base64) ===')
            print(raw.decode('utf-8', errors='ignore'))
except Exception as e:
    print('Error fetching sub:', e)
