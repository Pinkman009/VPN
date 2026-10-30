import urllib.request
import base64

urls = [
    ("Standard Sub", "http://193.233.138.42:80/dlngedpbfjlw072y/83sm0dymf1qn5w9m", {}),
    ("Happ User-Agent Sub", "http://193.233.138.42:80/dlngedpbfjlw072y/83sm0dymf1qn5w9m", {"User-Agent": "Happ/3.2.0"}),
    ("Sing-box Sub", "http://193.233.138.42:80/dlngedpbfjlw072y/83sm0dymf1qn5w9m", {"User-Agent": "sing-box/1.9.0"}),
    ("Json Sub", "http://193.233.138.42:80/w53zt74m07v76phv/83sm0dymf1qn5w9m", {}),
    ("Json Sub Happ", "http://193.233.138.42:80/w53zt74m07v76phv/83sm0dymf1qn5w9m", {"User-Agent": "Happ/3.2.0"}),
]

for name, url, headers in urls:
    print(f"=== {name} ===")
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            print("Status:", resp.status)
            print("Headers:", dict(resp.headers))
            # try base64 decode if applicable
            try:
                decoded = base64.b64decode(content).decode('utf-8', errors='ignore')
                print("Decoded base64:\n", decoded[:1000])
            except Exception:
                print("Raw content:\n", content[:1000].decode('utf-8', errors='ignore'))
    except Exception as e:
        print("Error:", e)
    print()
