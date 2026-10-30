import urllib.request
import urllib.parse
import json
import hashlib
import time
import sys

sys.stdout.reconfigure(encoding='utf-8')

API_URL = "http://193.233.138.42:2096"
SECRET = "m7l2Z5/tbSSOSEArC2P4gmOS"

opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

print("--- 1. Testing /api/subscription/status ---")
req = urllib.request.Request(f"{API_URL}/api/subscription/status?client_id=79500490409")
with opener.open(req, timeout=5) as resp:
    data = json.loads(resp.read().decode())
    print("Subscription data:\n", json.dumps(data, indent=2, ensure_ascii=False))

print("\n--- 2. Testing /api/payment/create (Plan 1m) ---")
payload = json.dumps({"client_id": "79500490409", "plan_id": "1m"}).encode()
req = urllib.request.Request(f"{API_URL}/api/payment/create", data=payload, headers={"Content-Type": "application/json"})
with opener.open(req, timeout=5) as resp:
    create_data = json.loads(resp.read().decode())
    print("Payment creation:\n", json.dumps(create_data, indent=2, ensure_ascii=False))

print("\n--- 3. Testing YooMoney Webhook SHA1 Verification ---")
# Simulate YooMoney webhook POST
label = create_data.get("order_id", "tt_1m_79500490409_12345")
params = {
    "notification_type": "p2p-incoming",
    "operation_id": f"test_op_{int(time.time())}",
    "amount": "149.00",
    "currency": "643",
    "datetime": "2026-10-27T03:10:00Z",
    "sender": "410019999999999",
    "codepro": "false",
    "label": label,
    "unaccepted": "false"
}
# Calculate signature
sig_str = f"{params['notification_type']}&{params['operation_id']}&{params['amount']}&{params['currency']}&{params['datetime']}&{params['sender']}&{params['codepro']}&{SECRET}&{params['label']}"
sha1_hash = hashlib.sha1(sig_str.encode('utf-8')).hexdigest()
params["sha1_hash"] = sha1_hash

webhook_body = urllib.parse.urlencode(params).encode('utf-8')
req = urllib.request.Request(
    f"{API_URL}/api/payment/yoomoney/webhook",
    data=webhook_body,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

try:
    with opener.open(req, timeout=5) as resp:
        res_text = resp.read().decode()
        print(f"Webhook Response HTTP {resp.status}: {res_text}")
except Exception as e:
    print(f"Webhook failed: {e}")

print("\n--- 4. Checking updated subscription status ---")
req = urllib.request.Request(f"{API_URL}/api/subscription/status?client_id=79500490409")
with opener.open(req, timeout=5) as resp:
    data = json.loads(resp.read().decode())
    print("Subscription data after payment:\n", json.dumps(data, indent=2, ensure_ascii=False))
