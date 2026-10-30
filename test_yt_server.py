import sys
from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["curl", "-s", "-I", "https://www.youtube.com"], capture_output=True, text=True)
print("YOUTUBE CURL:", p.stdout.splitlines()[:5])
"""

if __name__ == '__main__':
    run_script_on_vps(script)
