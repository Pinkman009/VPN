from run_remote import run_script_on_vps

script = """
import subprocess

for path in ['/', '/dlngedpbfjlw072y', '/dlngedpbfjlw072y/', '/dlngedpbfjlw072y/83sm0dymf1qn5w9m', '/sub', '/sub/']:
    res = subprocess.run(['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', f'https://127.0.0.1:2096{path}'], stdout=subprocess.PIPE)
    print(f"Path: {path} -> Code: {res.stdout.decode()}")
"""

run_script_on_vps(script)
