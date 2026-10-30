import socket
import ssl

TARGET_IP = "193.233.138.42"
TARGET_PORT = 2087

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5.0)
s.connect((TARGET_IP, TARGET_PORT))
print("TCP Connected to port 2087")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
try:
    # server_hostname=None means no SNI extension
    ss = ctx.wrap_socket(s, server_hostname=None)
    print("Handshake without SNI succeeded! Cipher:", ss.cipher())
    ss.close()
except Exception as e:
    print("Without SNI failed:", type(e).__name__, e)
    s.close()
