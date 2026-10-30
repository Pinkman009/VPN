from run_remote import run_script_on_vps

script = """
import subprocess

for ua in ['curl/7.81.0', 'HiddifyNext', 'v2rayN', 'Mozilla/5.0']:
    res = subprocess.run(['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-H', f'User-Agent: {ua}', 'https://127.0.0.1:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m'], stdout=subprocess.PIPE)
    code = res.stdout.decode()
    print(f"UA: {ua} -> Code: {code}")
"""

run_script_on_vps(script)
