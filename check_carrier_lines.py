from run_remote import run_script_on_vps

script = """
with open('/var/log/x-ui/access.log') as f:
    for line in f:
        if '91.79' in line or '178.157' in line:
            print(line.strip())
"""

run_script_on_vps(script)
