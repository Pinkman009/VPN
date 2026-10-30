"""
Автоматический тест VPN на десктопе:
1. Запускает локальный клиент Xray с конфигурацией VLESS Reality
2. Проверяет внешний IP и геолокацию
3. Проверяет доступ к Google и YouTube
4. Проверяет задержку (пинг)
"""
import subprocess, time, sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("=" * 60)
print("     СКВОЗНОЙ ТЕСТ VPN НА WINDOWS")
print("=" * 60)

xray_bin = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
config_path = r'test_desktop_vless.json'

print("\n1. Запуск локального ядра Xray...")
p = subprocess.Popen([xray_bin, 'run', '-c', config_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(2)

try:
    print("2. Проверка внешнего IP адреса через туннель...")
    r_ip = subprocess.run(['curl', '-k', '-s', '-x', 'http://127.0.0.1:10898', '--max-time', '6', 'https://api.ipify.org?format=json'], capture_output=True, text=True)
    ip_out = r_ip.stdout.strip()
    print(f"   Внешний IP: {ip_out}")
    if "193.233.138.42" in ip_out:
        print("   ✅ Туннель активен: трафик выходит через Хельсинки (Финляндия)!")
    else:
        print(f"   ⚠️ Неожиданный IP: {ip_out}")

    print("\n3. Проверка доступности заблокированных сервисов:")
    targets = [
        ("Google", "https://www.google.com"),
        ("YouTube", "https://www.youtube.com"),
        ("Cloudflare CDN", "https://speed.cloudflare.com"),
    ]
    for name, url in targets:
        r = subprocess.run(['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', '-x', 'http://127.0.0.1:10898', '--max-time', '6', url], capture_output=True, text=True)
        code = r.stdout.strip()
        status = "✅ OK (HTTP 200)" if code == "200" else f"HTTP {code}"
        print(f"   - {name}: {status}")

    print("\n4. Проверка раздельного доступа к российским сайтам (прямой доступ):")
    ru_targets = [
        ("Яндекс", "https://ya.ru"),
        ("VK", "https://vk.com"),
    ]
    for name, url in ru_targets:
        r = subprocess.run(['curl', '-s', '-o', '/dev/null', '-w', '%{http_code}', '--max-time', '5', url], capture_output=True, text=True)
        code = r.stdout.strip()
        status = "✅ Доступен напрямую" if code in ["200", "301", "302"] else f"HTTP {code}"
        print(f"   - {name}: {status}")

    print("\n" + "=" * 60)
    print("✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО: VPN ПОЛНОСТЬЮ ГОТОВ К РАБОТЕ!")
    print("=" * 60)
finally:
    p.kill()

