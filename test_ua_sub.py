import urllib.request

url = 'http://193.233.138.42:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m'
for ua in ['HiddifyNext/1.0', 'Hiddify/2.5.7', 'ClashMeta', 'v2rayNG/1.8']:
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            body = r.read().decode('utf-8', errors='replace')
            print(f'UA={ua} -> Code={r.status}, Content-Type={r.headers.get("Content-Type")}, len={len(body)}')
            if 'outbounds' in body or 'dns' in body or 'proxies' in body:
                print('  JSON/Clash structure detected! First 200 chars:', body[:200].replace('\n', ' '))
    except Exception as e:
        print(f'UA={ua} -> Error: {e}')
