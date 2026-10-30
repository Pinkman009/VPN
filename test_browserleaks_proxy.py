import urllib.request
import time

proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:10809', 'https': 'http://127.0.0.1:10809'})
opener = urllib.request.build_opener(proxy_handler)

req = urllib.request.Request("https://browserleaks.com/ip", headers={
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
})

t0 = time.time()
try:
    with opener.open(req, timeout=10) as resp:
        content = resp.read().decode('utf-8', errors='replace')
        print(f"Status: {resp.status}, Time: {round((time.time() - t0)*1000)}ms, Bytes: {len(content)}")
        # Search for IP in content
        import re
        m = re.search(r'193\.233\.138\.42', content)
        if m:
            print("SUCCESS! Found Finnish VPS IP 193.233.138.42 on browserleaks.com/ip!")
        else:
            # print first 500 chars
            print("Preview:", content[:400])
except Exception as e:
    print(f"Error: {e}")
