import socket
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

base = "193.233.138."
found = []

for i in range(1, 60):
    ip = f"{base}{i}"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.6)
        s.connect((ip, 443))
        ss = ctx.wrap_socket(s)
        cert = ss.getpeercert(binary_form=True)
        # Parse common name / SAN if possible or print that it responded
        ss.close()
        print(f"IP {ip} has valid TLS on 443!")
        found.append(ip)
    except Exception:
        pass

print("Found responsive IPs:", found)
