import sys
from run_remote import run_script_on_vps

script = """
import urllib.request, urllib.parse, json, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://127.0.0.1:8443/pYjH5z6vA2oXm0Ytt9/login"
data = urllib.parse.urlencode({"username": "igorsvincov@yandex.ru", "password": "IgoR@090362"}).encode()
req = urllib.request.Request(url, data=data, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, context=ctx) as resp:
        print("Status:", resp.status)
        print("Body:", resp.read().decode())
        print("Cookies:", resp.headers.get_all('Set-Cookie'))
except urllib.error.HTTPError as e:
    print("HTTPError:", e.code, e.read().decode())
"""

if __name__ == '__main__':
    run_script_on_vps(script)
