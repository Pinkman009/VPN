import urllib.request, ssl, json

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://193.233.138.42:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m'
for ua in ['Happ', 'HiddifyNext/1.0', 'sing-box']:
    req = urllib.request.Request(url, headers={'User-Agent': ua})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=5) as r:
            body = r.read().decode('utf-8', errors='replace')
            print(f"\n=== UA={ua} Code={r.status} len={len(body)} ===")
            try:
                data = json.loads(body)
                print("VALID JSON SING-BOX DETECTED! Keys:", list(data.keys()))
                if 'dns' in data:
                    print("DNS servers:", json.dumps(data['dns'].get('servers'), indent=2))
                if 'route' in data:
                    print("Route rules count:", len(data['route'].get('rules', [])))
                if 'outbounds' in data:
                    print("Outbounds:", [o.get('tag') for o in data['outbounds']])
            except:
                print("Raw response (first 200 chars):", body[:200])
    except Exception as e:
        print(f"Error for UA={ua}: {e}")
