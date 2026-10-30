import urllib.request
import urllib.parse
import http.cookiejar
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx), urllib.request.HTTPCookieProcessor(cj))

base_url = "https://193.233.138.42:8443/pYjH5z6vA2oXm0Ytt9"

# 1. Fetch CSRF token
req = urllib.request.Request(f"{base_url}/")
with opener.open(req) as resp:
    html = resp.read().decode('utf-8')

csrf_match = re.search(r'csrf-token" content="([^"]+)', html)
csrf = csrf_match.group(1) if csrf_match else ""

# 2. Login
login_data = json.dumps({"username": "igorsvincov@yandex.ru", "password": "IgoR@090362"}).encode('utf-8')
req = urllib.request.Request(f"{base_url}/login", data=login_data, headers={
    "X-CSRF-Token": csrf,
    "Content-Type": "application/json"
})
with opener.open(req) as resp:
    pass

# 3. Get inbound 1
req = urllib.request.Request(f"{base_url}/panel/api/inbounds/get/1", headers={"X-CSRF-Token": csrf})
with opener.open(req) as resp:
    inbound1 = json.loads(resp.read().decode('utf-8'))["obj"]

# Modify realitySettings for inbound 1
stream = inbound1["streamSettings"]
if isinstance(stream, str):
    stream = json.loads(stream)

reality = stream.get("realitySettings", {})
reality["serverNames"] = ["193-233-138-42.sslip.io"]
reality["target"] = "cspeak.193-233-138-20.sslip.io:443"
if "settings" in reality:
    reality["settings"]["serverName"] = "193-233-138-42.sslip.io"

inbound1["streamSettings"] = stream
inbound1["remark"] = "VLESS-Reality-8880-sslip"

# 4. Update inbound 1
update_data = json.dumps(inbound1).encode('utf-8')
req = urllib.request.Request(f"{base_url}/panel/api/inbounds/update/1", data=update_data, headers={
    "X-CSRF-Token": csrf,
    "Content-Type": "application/json"
})
with opener.open(req) as resp:
    print("Update Inbound 1:", resp.read().decode('utf-8'))
