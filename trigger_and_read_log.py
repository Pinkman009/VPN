import subprocess
import time
from run_remote import run_script_on_vps

adb = r'.\platform-tools\adb.exe'

# Tap check latency button at (959, 2015)
print('Tapping check latency...')
subprocess.run([adb, '-s', '19ac4fde', 'shell', 'input', 'tap', '959', '2015'])

time.sleep(3)

# Read journalctl from VPS
read_script = """
import subprocess
print(subprocess.getoutput('journalctl -u x-ui -n 40 --no-pager'))
"""
run_script_on_vps(read_script)
