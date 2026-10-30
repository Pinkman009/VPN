import socket
import ssl

# 1. Connect to local SOCKS5 proxy
s = socket.socket()
s.connect(('127.0.0.1', 10808))

# 2. SOCKS5 Handshake
s.sendall(b'\x05\x01\x00')
assert s.recv(2) == b'\x05\x00'

# 3. SOCKS5 Connect to chatgpt.com:443
domain = b'chatgpt.com'
port = 443
req = b'\x05\x01\x00\x03' + bytes([len(domain)]) + domain + port.to_bytes(2, 'big')
s.sendall(req)
resp = s.recv(10)
assert resp[1] == 0, f"SOCKS5 connect failed: {resp[1]}"
print("SOCKS5 tunnel established to chatgpt.com:443!")

# 4. Wrap with TLS
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
ss = ctx.wrap_socket(s, server_hostname='chatgpt.com')
print("TLS Handshake OK! Version:", ss.version(), "Cipher:", ss.cipher()[0])

# 5. Send HTTP GET
ss.sendall(b"GET / HTTP/1.1\r\nHost: chatgpt.com\r\nUser-Agent: Mozilla/5.0\r\nConnection: close\r\n\r\n")
resp = ss.recv(500)
print("HTTP Response Preview:\n", resp.decode('utf-8', errors='replace')[:200])
ss.close()
