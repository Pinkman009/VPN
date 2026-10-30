import sys
from run_remote import run_script_on_vps

script = """
with open('/usr/local/x-ui/bin/config.json') as f:
    print(f.read())
"""

if __name__ == '__main__':
    run_script_on_vps(script)
