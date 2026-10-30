from run_remote import run_script_on_vps

script = """
import subprocess

p = subprocess.run(["strings", "/usr/local/x-ui/x-ui"], capture_output=True, text=True)
for line in p.stdout.splitlines():
    if "xraytemplateconfig" in line.lower() or "xraytemplate" in line.lower():
        print(line)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
