import subprocess, time, json, urllib.request

XRAY = r"C:\Users\MiPro\Desktop\VPN\v2rayN\v2rayN-windows-64\bin\Xray\xray.exe"
NODES = [(2053, "azure.microsoft.com"), (443, "speed.cloudflare.com")]
FPS = ["randomized", "chrome", "firefox", "safari", "ios", "edge", "android", "random"]

port_local = 14100
for vps_port, sni in NODES:
    for fp in FPS:
        port_local += 1
        cfg = {
            "log": {"loglevel": "none"},
            "inbounds": [{"listen": "127.0.0.1", "port": port_local, "protocol": "http"}],
            "outbounds": [{
                "protocol": "vless",
                "settings": {"vnext": [{"address": "193.233.138.42", "port": vps_port, "users": [{"id": "04756662-2f98-44ad-a53a-369d29118670", "encryption": "none", "flow": "xtls-rprx-vision"}]}]},
                "streamSettings": {"network": "tcp", "security": "reality", "realitySettings": {"serverName": sni, "fingerprint": fp, "publicKey": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE", "shortId": "dae45f", "spiderX": "/"}}
            }]
        }
        fn = f"scratch/fp_{vps_port}_{fp}.json"
        json.dump(cfg, open(fn, "w"))
        p = subprocess.Popen([XRAY, "run", "-c", fn], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        op = urllib.request.build_opener(urllib.request.ProxyHandler({"https": f"http://127.0.0.1:{port_local}"}))
        ok = 0
        times = []
        for _ in range(3):
            t0 = time.time()
            try:
                with op.open(urllib.request.Request("https://www.youtube.com/", headers={"User-Agent": "Mozilla/5.0"}), timeout=6) as r:
                    ok += 1
                    times.append(round((time.time() - t0) * 1000))
            except Exception:
                pass
        p.terminate()
        print(f"port {vps_port} fp={fp:<10} -> {ok}/3 OK {times}", flush=True)
