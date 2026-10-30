import json

path = r'v2rayN\v2rayN-windows-64\guiConfigs\guiNConfig.json'
with open(path, 'r', encoding='utf-8') as f:
    d = json.load(f)

# 1. Russian DNS
if 'SimpleDNSItem' in d and d['SimpleDNSItem']:
    d['SimpleDNSItem']['DirectDNS'] = '77.88.8.8'
    d['SimpleDNSItem']['BootstrapDNS'] = '77.88.8.8'
    d['SimpleDNSItem']['RemoteDNS'] = '8.8.8.8'

# 2. Block QUIC (UDP 443) for anti-throttling on YouTube
if 'Mux4RayItem' in d and d['Mux4RayItem']:
    d['Mux4RayItem']['XudpProxyUDP443'] = 'reject'

# 3. Russian UI language
if 'UiItem' in d and d['UiItem']:
    d['UiItem']['CurrentLanguage'] = 'ru'

# 4. TUN mode: stack system or mixed
if 'TunModeItem' in d and d['TunModeItem']:
    d['TunModeItem']['Stack'] = 'system'
    d['TunModeItem']['AutoRoute'] = True
    d['TunModeItem']['StrictRoute'] = True

# 5. Active server: Port 443
d['IndexId'] = '4850475246551215996'

with open(path, 'w', encoding='utf-8') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)

print("guiNConfig.json успешно оптимизирован для РФ (Yandex/Google DNS, блок QUIC, русский язык, стек system)!")
