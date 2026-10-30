from run_remote import run_script_on_vps

script = """
import subprocess
print(subprocess.getoutput('journalctl -u x-ui --since "5 minutes ago" --no-pager'))
"""

if __name__ == '__main__':
    run_script_on_vps(script)
