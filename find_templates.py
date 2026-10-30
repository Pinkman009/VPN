import sys
from run_remote import run_script_on_vps

script = """
import os

for root, dirs, files in os.walk("/usr/local/x-ui"):
    for f in files:
        if f.endswith(".json") or f.endswith(".yaml") or f.endswith(".tmpl") or "sub" in f:
            print(os.path.join(root, f))
"""

if __name__ == '__main__':
    run_script_on_vps(script)
