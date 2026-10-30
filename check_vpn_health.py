import sys
import json
import socket
import ssl
import paramiko
import urllib.request
import time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

VPS_IP = '193.233.138.42'
SSH_USER = 'root'
SSH_PASS = 'xXM3yS7biwUj'

def check_remote_vps():
    print("==================================================")
    print("1. ПРОВЕРКА СТАТУСА СЕРВЕРА И СЛУЖБ (VPS)")
    print("==================================================")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(VPS_IP, username=SSH_USER, password=SSH_PASS, timeout=10)
        print("[OK] SSH подключение к VPS успешно установлено")
    except Exception as e:
        print(f"[FAIL] Не удалось подключиться по SSH: {e}")
        return None

    # Check services
    cmd = "systemctl is-active x-ui; systemctl is-active warp-svc"
    _, stdout, _ = client.exec_command(cmd)
    res = stdout.read().decode().strip().split('\n')
    print(f"  - Статус 3X-UI: {res[0] if len(res) > 0 else 'unknown'}")
    print(f"  - Статус Cloudflare WARP: {res[1] if len(res) > 1 else 'unknown'}")

    # Check listening ports
    _, stdout, _ = client.exec_command("ss -tulpn | grep -E ':(443|2053|2096|8443|40000)'")
    print("\nСлушающие порты на VPS:")
    print(stdout.read().decode().strip())

    # Check UFW status
    _, stdout, _ = client.exec_command("ufw status")
    print("\nСтатус UFW (Firewall):")
    print(stdout.read().decode().strip())

    remote_script = """import sqlite3, json
conn = sqlite3.connect('/etc/x-ui/x-ui.db')
c = conn.cursor()
inbounds = []
for row in c.execute("SELECT id, port, protocol, remark, enable, stream_settings, settings FROM inbounds").fetchall():
    inbounds.append({
        'id': row[0],
        'port': row[1],
        'proto': row[2],
        'remark': row[3],
        'enable': row[4],
        'stream': json.loads(row[5]) if row[5] else {},
        'settings': json.loads(row[6]) if row[6] else {}
    })
print(json.dumps(inbounds))
"""
    sftp = client.open_sftp()
    with sftp.file('/tmp/check_inb.py', 'w') as f:
        f.write(remote_script)
    sftp.close()
    stdin, stdout, stderr = client.exec_command("python3 /tmp/check_inb.py")
    raw_out = stdout.read().decode().strip()
    err_out = stderr.read().decode().strip()
    if err_out:
        print(f"STDERR: {err_out}")
    inbounds_data = json.loads(raw_out)
    print("\nКонфигурация Inbounds в 3X-UI:")
    for inb in inbounds_data:
        reality = inb['stream'].get('realitySettings', {})
        settings_reality = reality.get('settings', {})
        print(f"  - ID: {inb['id']}, Port: {inb['port']}, Remark: {inb['remark']}, Enable: {inb['enable']}")
        print(f"    ServerNames: {reality.get('serverNames', [])}")
        print(f"    Dest: {reality.get('dest')}")
        print(f"    ShortIds: {reality.get('shortIds', [])}")
        clients = inb['settings'].get('clients', [])
        print(f"    Clients count: {len(clients)}")
        for cl in clients:
            print(f"      Client: {cl.get('email')} (UUID: {cl.get('id')})")

    # Check WARP connectivity on VPS
    _, stdout, _ = client.exec_command("curl -s -x socks5://127.0.0.1:40000 https://cloudflare.com/cdn-cgi/trace | grep -E 'warp=|ip='")
    print("\nWARP SOCKS5 (локально на VPS):")
    print(stdout.read().decode().strip())

    client.close()
    return inbounds_data

def test_reality_handshake(port, sni):
    print(f"\nТестирование TLS Reality Handshake на {VPS_IP}:{port} с SNI '{sni}'...")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(6.0)
    try:
        t0 = time.time()
        s.connect((VPS_IP, port))
        tcp_time = round((time.time() - t0) * 1000)
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        t1 = time.time()
        ss = ctx.wrap_socket(s, server_hostname=sni)
        tls_time = round((time.time() - t1) * 1000)
        
        cipher = ss.cipher()
        version = ss.version()
        cert = ss.getpeercert(binary_form=True)
        ss.close()
        print(f"[OK] Handshake успешен! TCP: {tcp_time}ms, TLS: {tls_time}ms, {version}, Cipher: {cipher[0]}, Cert: {len(cert)} байт")
        return True
    except Exception as e:
        print(f"[FAIL] Ошибка рукопожатия: {e}")
        s.close()
        return False

def test_subscription_endpoint():
    print("\n==================================================")
    print("3. ПРОВЕРКА ЭНДПОИНТА ПОДПИСКИ (PORT 2096)")
    print("==================================================")
    url = "https://193.233.138.42:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m"
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request(url, headers={'User-Agent': 'Happ/3.0.0'})
        with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
            data = resp.read()
            print(f"[OK] Подписка отвечает со статусом {resp.status}, получено {len(data)} байт")
            # Try to decode base64
            import base64
            try:
                decoded = base64.b64decode(data).decode('utf-8', errors='replace')
                print(f"Содержимое подписки (декодировано, первые 200 символов):\n{decoded[:200]}...")
            except:
                print(f"Содержимое в открытом виде:\n{data.decode('utf-8', errors='replace')[:200]}...")
    except Exception as e:
        print(f"[FAIL] Ошибка при запросе подписки: {e}")

if __name__ == '__main__':
    inbounds = check_remote_vps()
    print("\n==================================================")
    print("2. ПРОВЕРКА РЕАЛЬНОГО РУКОПОЖАТИЯ REALITY")
    print("==================================================")
    test_reality_handshake(443, "speed.cloudflare.com")
    test_reality_handshake(2053, "azure.microsoft.com")
    test_subscription_endpoint()
