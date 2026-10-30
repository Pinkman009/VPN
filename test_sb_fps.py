import subprocess, json

fps = ["safari", "firefox", "edge", "360", "qq", "android", "random", "randomized"]

for fp in fps:
    cfg = {
      "log": { "level": "warn" },
      "inbounds": [{ "type": "mixed", "tag": "mixed-in", "listen": "127.0.0.1", "listen_port": 20880 }],
      "outbounds": [{
        "type": "vless",
        "tag": "proxy",
        "server": "193.233.138.42",
        "server_port": 443,
        "uuid": "04756662-2f98-44ad-a53a-369d29118670",
        "flow": "xtls-rprx-vision",
        "tls": {
          "enabled": True,
          "server_name": "speed.cloudflare.com",
          "utls": { "enabled": True, "fingerprint": fp },
          "reality": {
            "enabled": True,
            "public_key": "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE",
            "short_id": "dae45f"
          }
        }
      }]
    }
    with open('test_sb_tmp.json', 'w') as f:
        json.dump(cfg, f)
    
    sb = r'v2rayN\v2rayN-windows-64\bin\sing_box\sing-box.exe'
    p = subprocess.Popen([sb, 'run', '-c', 'test_sb_tmp.json'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    import time
    time.sleep(1)
    
    r = subprocess.run(['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-x', 'http://127.0.0.1:20880', '--max-time', '3', 'https://www.google.com'], capture_output=True, text=True)
    p.kill()
    out, _ = p.communicate()
    print(f"FP '{fp}': HTTP {r.stdout.strip()} | Log: {out.decode('utf-8', errors='replace').strip()[-150:]}")
