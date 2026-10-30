import subprocess
import json
import time
import urllib.request
import os
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

XRAY_BIN = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
if not os.path.exists(XRAY_BIN):
    XRAY_BIN = r'client_test\xray.exe'

TEST_TARGETS = [
    ("IP Verify (ipify.org)", "https://api.ipify.org?format=json"),
    ("IP Geolocation (ipinfo.io)", "https://ipinfo.io/json"),
    ("YouTube (проверка скорости и отсутствия замедления)", "https://www.youtube.com"),
    ("Instagram (заблокирован в РФ)", "https://www.instagram.com"),
    ("X / Twitter (заблокирован в РФ)", "https://x.com"),
    ("OpenAI / ChatGPT (через WARP)", "https://chatgpt.com")
]

def run_node_test(node_name, config_file, proxy_port=10899):
    print(f"\n=======================================================")
    print(f"ТЕСТИРОВАНИЕ КАНАЛА: {node_name}")
    print(f"Конфиг: {config_file}, Прокси: socks5h://127.0.0.1:{proxy_port}")
    print(f"=======================================================")
    
    proc = subprocess.Popen([XRAY_BIN, 'run', '-c', config_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1.5)
    
    proxy_handler = urllib.request.ProxyHandler({
        'http': f'socks5h://127.0.0.1:{proxy_port}',
        'https': f'socks5h://127.0.0.1:{proxy_port}'
    })
    opener = urllib.request.build_opener(proxy_handler)
    
    results = []
    for label, url in TEST_TARGETS:
        t0 = time.time()
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
            })
            with opener.open(req, timeout=10) as resp:
                elapsed = round((time.time() - t0) * 1000)
                data = resp.read()
                details = f"HTTP {resp.status}, {elapsed} ms"
                if "ipify" in url or "ipinfo" in url:
                    try:
                        j = json.loads(data.decode())
                        ip = j.get('ip')
                        country = j.get('country', '')
                        org = j.get('org', '')
                        details += f" -> IP: {ip} ({country}, {org})"
                    except:
                        pass
                print(f"  [PASSED] {label}: {details}")
                results.append((label, True, details))
        except Exception as e:
            elapsed = round((time.time() - t0) * 1000)
            err_msg = str(e)
            print(f"  [FAILED] {label}: {err_msg} ({elapsed} ms)")
            results.append((label, False, err_msg))
            
    proc.terminate()
    try:
        proc.wait(timeout=3)
    except:
        proc.kill()
        
    return results

if __name__ == '__main__':
    print(f"Используемый бинарник Xray: {XRAY_BIN}")
    res1 = run_node_test("ОСНОВНОЙ КАНАЛ (Порт 443, speed.cloudflare.com)", "test_exact_node1.json")
    res2 = run_node_test("РЕЗЕРВНЫЙ КАНАЛ (Порт 2053, azure.microsoft.com)", "test_exact_node2.json")
    
    print("\n=======================================================")
    print("ИТОГОВАЯ СВОДКА ТЕСТИРОВАНИЯ")
    print("=======================================================")
    passed1 = sum(1 for _, ok, _ in res1 if ok)
    passed2 = sum(1 for _, ok, _ in res2 if ok)
    print(f"Основной канал (443): {passed1}/{len(res1)} тестов пройдено")
    print(f"Резервный канал (2053): {passed2}/{len(res2)} тестов пройдено")
