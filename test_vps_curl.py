import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')
from run_remote import run_script_on_vps

script = """
import subprocess

for cmd in [
    'curl -4 -s -o /dev/null -w "%{http_code} in %{time_total}s\\n" https://www.google.com',
    'curl -6 -s -o /dev/null -w "%{http_code} in %{time_total}s\\n" https://www.google.com',
    'curl -4 -s -o /dev/null -w "%{http_code} in %{time_total}s\\n" https://www.youtube.com',
    'curl -6 -s -o /dev/null -w "%{http_code} in %{time_total}s\\n" https://www.youtube.com'
]:
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
    print(cmd.split(' ')[1], cmd.split(' ')[-1], '->', r.stdout.strip() or r.stderr.strip())
"""

run_script_on_vps(script)
