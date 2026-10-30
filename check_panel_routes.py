import sys
from run_remote import run_script_on_vps

script = """
import subprocess

for path in ["/", "/pYjH5z6vA2oXm0Ytt9/", "/pYjH5z6vA2oXm0Ytt9", "/pYjH5z6vA2oXm0Ytt9/panel", "/pYjH5z6vA2oXm0Ytt9/xui"]:
    p = subprocess.run(["curl", "-k", "-s", "-I", f"https://127.0.0.1:8443{path}"], capture_output=True, text=True)
    first_line = p.stdout.splitlines()[0] if p.stdout else "EMPTY"
    location = [l for l in p.stdout.splitlines() if "Location" in l or "location" in l]
    print(f"Path: {path} -> {first_line}, Loc: {location}")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
