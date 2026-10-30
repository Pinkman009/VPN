import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

targets = [
    ('IP & Country Check', ['curl', '-s', '-x', 'socks5h://127.0.0.1:10808', 'https://ipinfo.io/json']),
    ('OpenAI API (ChatGPT)', ['curl', '-s', '-x', 'socks5h://127.0.0.1:10808', 'https://api.openai.com/v1/models']),
    ('Anthropic API (Claude)', ['curl', '-s', '-x', 'socks5h://127.0.0.1:10808', 'https://api.anthropic.com/v1/models']),
    ('Spotify', ['curl', '-s', '-I', '-x', 'socks5h://127.0.0.1:10808', 'https://www.spotify.com/']),
    ('Notion', ['curl', '-s', '-I', '-x', 'socks5h://127.0.0.1:10808', 'https://www.notion.so/']),
    ('Docker Hub', ['curl', '-s', '-I', '-x', 'socks5h://127.0.0.1:10808', 'https://hub.docker.com/']),
    ('Microsoft Copilot', ['curl', '-s', '-I', '-x', 'socks5h://127.0.0.1:10808', 'https://copilot.microsoft.com/'])
]

print("=== ПРОВЕРКА ДОСТУПА К СЕРВИСАМ С ГЕО-БЛОКИРОВКОЙ ЧЕРЕЗ ВПН ===")
for name, cmd in targets:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
        out = p.stdout.strip()
        if 'ipinfo' in cmd[-1]:
            d = json.loads(out)
            print(f"[OK] {name}: IP={d.get('ip')} ({d.get('country')}, {d.get('city')})")
        elif 'openai' in cmd[-1]:
            if "You didn't provide an API key" in out or "invalid_api_key" in out:
                print(f"[OK] {name}: Гео-блок ОТСУТСТВУЕТ (Запрос принят, сервер OpenAI ожидает ключ)")
            elif "Country, region, or territory not supported" in out or "unsupported_country" in out:
                print(f"[BLOCKED] {name}: Гео-блок активен!")
            else:
                print(f"[STATUS] {name}: {out[:120]}")
        elif 'anthropic' in cmd[-1]:
            if "x-api-key" in out or "authentication_error" in out:
                print(f"[OK] {name}: Гео-блок ОТСУТСТВУЕТ (Запрос принят, сервер Anthropic ожидает ключ)")
            elif "unavailable_region" in out:
                print(f"[BLOCKED] {name}: Гео-блок активен!")
            else:
                print(f"[STATUS] {name}: {out[:120]}")
        else:
            first_line = out.splitlines()[0] if out else "No HTTP header response"
            print(f"[OK] {name}: {first_line}")
    except Exception as e:
        print(f"[ERROR] {name}: {e}")
