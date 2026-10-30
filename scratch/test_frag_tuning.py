import subprocess
import time
import json
import urllib.request

XRAY = r"C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\bin\Xray\xray.exe"

def test_frag(p_range, l_range, i_range):
    cfg = {
        "log": {"loglevel": "error"},
        "inbounds": [{"tag": "http-in", "listen": "127.0.0.1", "port": 13999, "protocol": "http"}],
        "outbounds": [
            {
                "tag": "proxy",
                "protocol": "vless",
                "settings": {"vnext": [{"address": "193.233.138.42", "port": 2053, "users": [{"id": "04756662-2f98-44ad-a53a-369d29118670", "encryption": "none", "flow": "xtls-rprx-vision"}]}]},
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {"serverName": "azure.microsoft.com", "fingerprint": "chrome", "publicKey": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE", "shortId": "dae45f", "spiderX": "/"},
                    "sockopt": {"dialerProxy": "fragment"}
                }
            },
            {
                "tag": "fragment",
                "protocol": "freedom",
                "settings": {"fragment": {"packets": p_range, "length": l_range, "interval": i_range}}
            }
        ]
    }
    with open("scratch/test_frag_tuning.json", "w") as f:
        json.dump(cfg, f)
    
    p = subprocess.Popen([XRAY, "run", "-c", "scratch/test_frag_tuning.json"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    
    h = urllib.request.ProxyHandler({"http": "http://127.0.0.1:13999", "https": "http://127.0.0.1:13999"})
    op = urllib.request.build_opener(h)
    
    t0 = time.time()
    res = ""
    try:
        req = urllib.request.Request("https://www.youtube.com/", headers={"User-Agent": "Mozilla/5.0 Chrome/130.0.0.0"})
        with op.open(req, timeout=5) as r:
            res = f"SUCCESS {r.status} in {round((time.time()-t0)*1000)}ms"
    except Exception as e:
        res = f"ERR: {e}"
    p.terminate()
    print(f"Frag[{p_range}, {l_range}, {i_range}]: {res}", flush=True)

test_frag("1-2", "10-20", "2-5")
test_frag("1-3", "20-50", "1-3")
test_frag("1-2", "50-100", "1-5")
test_frag("1-1", "10-30", "1-3")
test_frag("1-3", "10-20", "5-10")
