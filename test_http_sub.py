import urllib.request
import base64

url = 'http://193.233.138.42:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m'
req = urllib.request.Request(url, headers={'User-Agent': 'v2rayN'})
try:
    with urllib.request.urlopen(req, timeout=5) as resp:
        body = resp.read().decode('utf-8', errors='replace')
        print('HTTP Code:', resp.status)
        print('Headers:', dict(resp.headers))
        try:
            decoded = base64.b64decode(body).decode('utf-8', errors='replace')
            print('DECODED BODY:\n', decoded)
        except Exception:
            print('RAW BODY:\n', body[:500])
except Exception as e:
    print('Error:', e)
