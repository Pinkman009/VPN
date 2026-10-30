import sys, base64
from run_remote import run_script_on_vps

script = """
import sqlite3, json

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

inbounds = c.execute("SELECT id, port, protocol, remark, settings, stream_settings FROM inbounds WHERE enable=1").fetchall()
for ib in inbounds:
    ib_id, port, proto, remark, settings_str, stream_str = ib
    settings = json.loads(settings_str)
    stream = json.loads(stream_str)
    
    client = settings["clients"][0]
    uuid = client["id"]
    flow = client.get("flow", "")
    
    reality = stream.get("realitySettings", {})
    pbk = reality.get("settings", {}).get("publicKey", "")
    sni = reality.get("serverNames", [""])[0]
    sid = reality.get("shortIds", [""])[0]
    spx = reality.get("settings", {}).get("spiderX", "")
    fp = reality.get("settings", {}).get("fingerprint", "chrome")
    
    link = f"vless://{uuid}@193.233.138.42:{port}?security=reality&encryption=none&pbk={pbk}&headerType=none&fp={fp}&spx={spx}&type=tcp&flow={flow}&sni={sni}&sid={sid}#{remark}"
    print("=== " + remark + " ===")
    print(link)
    print()
"""

if __name__ == '__main__':
    run_script_on_vps(script)
