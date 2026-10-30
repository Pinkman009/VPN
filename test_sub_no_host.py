from run_remote import run_script_on_vps

script = """
import subprocess

res = subprocess.run(['curl', '-k', '-v', 'https://127.0.0.1:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("STDOUT len:", len(res.stdout))
print("STDOUT snippet:", res.stdout[:100])
print("HTTP line:", [l for l in res.stderr.decode().splitlines() if '< HTTP' in l])
"""

run_script_on_vps(script)
