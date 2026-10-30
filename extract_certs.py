import socket
import ssl
from cryptography import x509
from cryptography.hazmat.backends import default_backend

ips = ['193.233.138.3', '193.233.138.4', '193.233.138.6', '193.233.138.7', '193.233.138.15', '193.233.138.16', '193.233.138.20', '193.233.138.21', '193.233.138.22', '193.233.138.33', '193.233.138.34', '193.233.138.47']

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

for ip in ips:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect((ip, 443))
        ss = ctx.wrap_socket(s)
        der_cert = ss.getpeercert(binary_form=True)
        cert = x509.load_der_x509_certificate(der_cert, default_backend())
        ss.close()
        
        # Extract CN and SAN
        subject = cert.subject
        names = []
        for attr in subject:
            if attr.oid == x509.NameOID.COMMON_NAME:
                names.append(f"CN={attr.value}")
        try:
            san = cert.extensions.get_extension_for_oid(x509.ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
            for name in san.value:
                names.append(f"SAN={name.value}")
        except Exception:
            pass
        print(f"IP {ip}: {', '.join(names)}")
    except Exception as e:
        print(f"IP {ip} error: {e}")
