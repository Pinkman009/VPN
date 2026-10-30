import subprocess, time, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

xray = r'v2rayN\v2rayN-windows-64\bin\Xray\xray.exe'
print("Запуск локального Xray ядра...")
p = subprocess.Popen([xray, 'run', '-c', 'test_desktop_vless.json'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(2)

try:
    print("Проверка HTTP прокси (127.0.0.1:10898)...")
    cmd = ['curl', '-v', '-s', '-x', 'http://127.0.0.1:10898', '--max-time', '5', 'https://api.ipify.org?format=json']
    r = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:", r.stdout.strip())
    print("STDERR (first 500 chars):", r.stderr[:500].strip())
finally:
    p.kill()
    print("Xray остановлен.")
