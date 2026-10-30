"""
Generate final Android-optimized keys with fp=randomized and create QR codes.
Also generate Hiddify deep-link QR.
"""
import qrcode
import urllib.parse
import os

UUID = "04756662-2f98-44ad-a53a-369d29118670"
SERVER = "193.233.138.42"
PUBLIC_KEY = "t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE"
SHORT_ID = "dae45f"

output_dir = os.path.dirname(os.path.abspath(__file__))

def make_qr(data, filename):
    filepath = os.path.join(output_dir, filename)
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filepath)
    return filepath

# === MAIN KEY: Port 443, fp=randomized ===
params_443 = {
    "security": "reality",
    "encryption": "none",
    "pbk": PUBLIC_KEY,
    "headerType": "none",
    "fp": "randomized",
    "spx": "/",
    "type": "tcp",
    "flow": "xtls-rprx-vision",
    "sni": "speed.cloudflare.com",
    "sid": SHORT_ID
}
query_443 = urllib.parse.urlencode(params_443)
key_443 = f"vless://{UUID}@{SERVER}:443?{query_443}#VLESS-443-Finland"

# === BACKUP KEY: Port 2053, fp=randomized ===
params_2053 = {
    "security": "reality",
    "encryption": "none",
    "pbk": PUBLIC_KEY,
    "headerType": "none",
    "fp": "randomized",
    "spx": "/",
    "type": "tcp",
    "flow": "xtls-rprx-vision",
    "sni": "azure.microsoft.com",
    "sid": SHORT_ID
}
query_2053 = urllib.parse.urlencode(params_2053)
key_2053 = f"vless://{UUID}@{SERVER}:2053?{query_2053}#VLESS-2053-Finland"

# Generate QR codes
make_qr(key_443, "vpn_qr_android_main_443.png")
make_qr(key_2053, "vpn_qr_android_backup_2053.png")

# Hiddify deep links
hiddify_443 = f"hiddify://import/{key_443}"
hiddify_2053 = f"hiddify://import/{key_2053}"
make_qr(hiddify_443, "vpn_qr_hiddify_android_443.png")
make_qr(hiddify_2053, "vpn_qr_hiddify_android_2053.png")

# Happ one-click links
happ_443 = f"happ://add/{key_443}"
happ_2053 = f"happ://add/{key_2053}"
make_qr(happ_443, "vpn_qr_happ_android_443.png")
make_qr(happ_2053, "vpn_qr_happ_android_2053.png")

print("ANDROID KEYS (fp=randomized) GENERATED SUCCESSFULLY")
print()
print("=== PORT 443 (main) ===")
print(key_443)
print()
print("=== PORT 2053 (backup) ===")
print(key_2053)
print()
print("QR FILES:")
print("  vpn_qr_android_main_443.png    - direct VLESS key (scan in Happ/any app)")
print("  vpn_qr_android_backup_2053.png - backup VLESS key")
print("  vpn_qr_hiddify_android_443.png - Hiddify deep link")
print("  vpn_qr_happ_android_443.png    - Happ deep link")
