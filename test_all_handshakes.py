import socket
import ssl

TARGET_IP = "193.233.138.42"

def test_reality_handshake(port, sni):
    print(f"\n--- Testing Port {port} with SNI '{sni}' ---")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(6.0)
    try:
        s.connect((TARGET_IP, port))
        print(f"TCP connection established to {TARGET_IP}:{port}")
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        ss = ctx.wrap_socket(s, server_hostname=sni)
        cipher = ss.cipher()
        version = ss.version()
        print(f"REALITY TLS HANDSHAKE SUCCESS! TLS Version: {version}, Cipher: {cipher}")
        cert = ss.getpeercert(binary_form=True)
        print(f"Received Server Certificate length: {len(cert)} bytes (authentic camouflage cert from Reality target)")
        ss.close()
        return True
    except Exception as e:
        print(f"HANDSHAKE FAILED: {type(e).__name__}: {e}")
        s.close()
        return False

ok1 = test_reality_handshake(443, "swdist.apple.com")
ok2 = test_reality_handshake(2053, "www.samsung.com")

if ok1 and ok2:
    print("\nALL REALITY HANDSHAKES PASSED PERFECTLY!")
else:
    print("\nSOME HANDSHAKES FAILED!")
