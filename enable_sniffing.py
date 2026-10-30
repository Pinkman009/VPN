
import sys
from run_remote import run_script_on_vps

script = """
import sqlite3, json, subprocess

conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()

sniffing_config = {
    "enabled": True,
    "destOverride": ["http", "tls", "quic"],
    "metadataOnly": False,
    "routeOnly": False
}

c.execute("UPDATE inbounds SET sniffing=? WHERE id=1", (json.dumps(sniffing_config),))
c.execute("UPDATE inbounds SET sniffing=? WHERE id=2", (json.dumps(sniffing_config),))
conn.commit()

subprocess.run(["systemctl", "restart", "x-ui"])
print("Sniffing enabled successfully!")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
