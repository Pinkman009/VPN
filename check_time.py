import time, subprocess
from run_remote import run_script_on_vps

print("Local PC time:", time.time())

script = """
import time, subprocess
print("VPS UTC epoch:", time.time())
print("VPS date:", subprocess.getoutput("date -u"))
"""

if __name__ == '__main__':
    run_script_on_vps(script)

# Also check phone time via adb
p = subprocess.run([r'.\platform-tools\adb.exe', '-s', '19ac4fde', 'shell', 'date +%s; date -u'], capture_output=True, text=True)
print("Phone time:", p.stdout)
