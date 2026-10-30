from run_remote import run_script_on_vps

script = """
import subprocess

res = subprocess.run(['curl', '-k', '-v', '-H', 'Host: 193.233.138.42', 'https://127.0.0.1:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("STDOUT len:", len(res.stdout))
print("STDOUT sample:", res.stdout[:200])
print("STDERR sample:", res.stderr.decode(errors='replace')[:400])
"""

run_script_on_vps(script)
