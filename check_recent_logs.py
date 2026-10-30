import sys
from run_remote import run_script_on_vps

script = """
import os

for logfile in ["/tmp/xray_access.log", "/tmp/xray_error.log"]:
    if os.path.exists(logfile):
        print(f"=== {logfile} ===")
        with open(logfile) as f:
            lines = f.readlines()
            for l in lines[-30:]:
                print(l.strip())
"""

if __name__ == '__main__':
    run_script_on_vps(script)
