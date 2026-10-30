import sys
from run_remote import run_script_on_vps

script = """
import socket, ssl

targets = [
    ("dl.google.com", 443),
    ("gateway.icloud.com", 443),
    ("swdist.apple.com", 443),
    ("www.microsoft.com", 443),
    ("speedtest.net", 443),
    ("www.google.com", 443),
    ("www.samsung.com", 443)
]

context = ssl.create_default_context()
context.set_alpn_protocols(["h2", "http/1.1"])

for host, port in targets:
    try:
        with socket.create_connection((host, port), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                ver = ssock.version()
                alpn = ssock.selected_alpn_protocol()
                print(f"{host}:{port} -> TLS: {ver}, ALPN: {alpn} [OK]")
    except Exception as e:
        print(f"{host}:{port} -> ERROR: {e}")
"""

if __name__ == '__main__':
    run_script_on_vps(script)
