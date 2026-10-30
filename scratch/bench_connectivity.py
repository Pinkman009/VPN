import subprocess
import time
import json
import urllib.request

XRAY = r"C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\bin\Xray\xray.exe"

def test_config(name, sockopt_frag, port, sni):
    cfg = {
        "log": {"loglevel": "error"},
        "inbounds": [{"tag": "http-in", "listen": "127.0.0.1", "port": 12345, "protocol": "http"}],
        "outbounds": [
            {
                "tag": "proxy",
                "protocol": "vless",
                "settings": {
                    "vnext": [{
                        "address": "193.233.138.42",
                        "port": port,
                        "users": [{"id": "04756662-2f98-44ad-a53a-369d29118670", "encryption": "none", "flow": "xtls-rprx-vision"}]
                    }]
                },
                "streamSettings": {
                    "network": "tcp",
                    "security": "reality",
                    "realitySettings": {
                        "serverName": sni,
                        "fingerprint": "chrome",
                        "publicKey": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
                        "shortId": "dae45f",
                        "spiderX": "/"
                    }
                }
            }
        ]
    }
    if sockopt_frag:
        cfg["outbounds"][0]["streamSettings"]["sockopt"] = {"dialerProxy": "fragment"}
        cfg["outbounds"].append({
            "tag": "fragment",
            "protocol": "freedom",
            "settings": {"fragment": {"packets": "1-3", "length": "10-20", "interval": "10-20"}}
        })
    with open("scratch/test_tmp.json", "w") as f:
        json.dump(cfg, f)
    
    p = subprocess.Popen([XRAY, "run", "-c", "scratch/test_tmp.json"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.2)
    
    h = urllib.request.ProxyHandler({"http": "http://127.0.0.1:12345", "https": "http://127.0.0.1:12345"})
    op = urllib.request.build_opener(h)
    
    res_str = []
    for u in ["https://aistudio.google.com/", "https://www.youtube.com/", "https://api.ipify.org"]:
        host = u.split("/")[2]
        t0 = time.time()
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0 Chrome/130.0.0.0"})
            with op.open(req, timeout=10) as r:
                res_str.append(f"{host}: OK {round((time.time()-t0)*1000)}ms")
        except Exception as e:
            res_str.append(f"{host}: ERR({type(e).__name__}) {round((time.time()-t0)*1000)}ms")
    p.terminate()
    try:
        p.wait(timeout=2)
    except Exception:
        pass
    print(f"[{name}] " + " | ".join(res_str), flush=True)

test_config("Port 443 + Fragment", True, 443, "speed.cloudflare.com")
test_config("Port 443 NO Fragment", False, 443, "speed.cloudflare.com")
test_config("Port 2053 + Fragment", True, 2053, "azure.microsoft.com")
test_config("Port 2053 NO Fragment", False, 2053, "azure.microsoft.com")
