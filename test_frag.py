import socket
import ssl
import time

TARGET_IP = "193.233.138.42"
TARGET_PORT = 2087
SNI = "gateway.icloud.com"

def test_raw_tls_handshake(fragment=False, frag_size=30, delay_ms=10):
    print(f"\n--- Testing with fragment={fragment} (size={frag_size}, delay={delay_ms}ms) ---")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5.0)
    try:
        s.connect((TARGET_IP, TARGET_PORT))
        print("TCP Connected!")
        
        # Craft a basic TLS 1.3/1.2 ClientHello
        # We can use ssl.create_default_context to generate client_hello or use scapy/raw bytes
        # Alternatively, use standard socket with SSLContext wrapping
        if not fragment:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ss = ctx.wrap_socket(s, server_hostname=SNI)
            print("TLS Handshake SUCCEEDED! Cipher:", ss.cipher())
            ss.close()
            return True
        else:
            # For fragmented test, let's create raw ClientHello bytes
            # We can capture client_hello from a memory BIO
            incoming = ssl.MemoryBIO()
            outgoing = ssl.MemoryBIO()
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ssl_obj = ctx.wrap_bio(incoming, outgoing, server_hostname=SNI)
            try:
                ssl_obj.do_handshake()
            except ssl.SSLWantReadError:
                pass
            client_hello = outgoing.read()
            print(f"Generated ClientHello: {len(client_hello)} bytes")
            
            # Send fragmented
            part1 = client_hello[:frag_size]
            part2 = client_hello[frag_size:]
            s.sendall(part1)
            time.sleep(delay_ms / 1000.0)
            s.sendall(part2)
            
            # Wait for ServerHello response
            resp = s.recv(4096)
            print(f"Received from server: {len(resp)} bytes (first byte={hex(resp[0]) if resp else 'None'})")
            s.close()
            return len(resp) > 0
    except Exception as e:
        print("FAILED:", type(e).__name__, e)
        s.close()
        return False

test_raw_tls_handshake(fragment=False)
test_raw_tls_handshake(fragment=True, frag_size=20, delay_ms=20)
test_raw_tls_handshake(fragment=True, frag_size=40, delay_ms=50)
test_raw_tls_handshake(fragment=True, frag_size=1, delay_ms=20)
