from run_remote import run_script_on_vps

script = """
import os
for path in ['/var/log/xray/access.log', '/var/log/xray/error.log']:
    if os.path.exists(path):
        print(f"=== {path} ===")
        with open(path) as f:
            lines = f.readlines()
            for l in lines[-25:]:
                print(l.strip())
"""

if __name__ == '__main__':
    run_script_on_vps(script)
