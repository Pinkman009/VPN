import socket
import ssl

TARGET_IP = "193.233.138.42"
TARGET_PORT = 2087
SNI = "193-233-138-42.sslip.io"

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5.0)
try:
    s.connect((TARGET_IP, TARGET_PORT))
    print("TCP Connected to port 2087")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ss = ctx.wrap_socket(s, server_hostname=SNI)
    print("HANDSHAKE WITH sslip.io SUCCEEDED! Cipher:", ss.cipher())
    ss.close()
except Exception as e:
    print("Failed with sslip.io:", type(e).__name__, e)
    s.close()
