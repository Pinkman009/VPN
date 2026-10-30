from run_remote import run_script_on_vps

script = """
import subprocess
p = subprocess.run(["curl", "-I", "https://browserleaks.com/ip", "--connect-timeout", "10"], capture_output=True, text=True)
print("STDOUT:", p.stdout)
print("STDERR:", p.stderr)
"""

if __name__ == '__main__':
    run_script_on_vps(script)
