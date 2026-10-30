import sys, json, urllib.request, time

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Update local test config to use spiderX /ec2973b76d0d4ce
with open('client_test/config.json') as f:
    cfg = json.load(f)

cfg["outbounds"][0]["streamSettings"]["realitySettings"]["spiderX"] = "/ec2973b76d0d4ce"
with open('client_test/config.json', 'w') as f:
    json.dump(cfg, f, indent=2)

print("Updated client config with spiderX /ec2973b76d0d4ce")
