import sys
sys.path.insert(0, r"c:\Users\MiPro\Desktop\VPN")
from run_remote import run_script_on_vps

# 1. Получаем код владельца с сервера
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('193.233.138.42', username='root', password='xXM3yS7biwUj', timeout=10)
stdin, stdout, stderr = client.exec_command('unblocknet-admin code --owner')
out = stdout.read().decode('utf-8', 'replace').strip()
client.close()

print("SERVER CODE:", out)
code = out.split(":")[1].split("(")[0].strip()

# 2. Активируем код локально в клиенте
import vpn_core
ok, msg, res = vpn_core.activate_code(code)
print("ACTIVATE RESULT:", ok, msg)
print("IS OWNER:", res.get("is_owner"))
print("SUB:", res.get("subscription"))
print("NODE UUID:", res.get("node", {}).get("uuid"))

# 3. Проверяем повторный sync_identity
st = vpn_core.sync_identity()
print("FINAL SYNC is_owner:", st.get("is_owner"), "expiry:", st.get("subscription", {}).get("expiry_date"))
