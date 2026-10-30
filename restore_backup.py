"""
Скрипт быстрого отката/восстановления рабочей конфигурации на VPS.
Копирует сохраненные файлы из папки backup/ на сервер и перезапускает службы.
"""
import paramiko, os, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

VPS_IP = '193.233.138.42'
VPS_USER = 'root'
VPS_PASS = 'xXM3yS7biwUj'

def restore():
    print(f"Подключение к VPS {VPS_IP}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(VPS_IP, username=VPS_USER, password=VPS_PASS, timeout=10)
    
    sftp = client.open_sftp()
    
    # 1. Остановка x-ui перед заменой базы и конфига
    print("1. Остановка службы x-ui...")
    client.exec_command("systemctl stop x-ui")
    
    # 2. Загрузка базы данных и конфига
    if os.path.exists('backup/x-ui.db'):
        print("2. Восстановление /etc/x-ui/x-ui.db...")
        sftp.put('backup/x-ui.db', '/etc/x-ui/x-ui.db')
    
    if os.path.exists('backup/config.json'):
        print("3. Восстановление /usr/local/x-ui/bin/config.json...")
        sftp.put('backup/config.json', '/usr/local/x-ui/bin/config.json')
    
    if os.path.exists('backup/99-vpn-optimize.conf'):
        print("4. Восстановление /etc/sysctl.d/99-vpn-optimize.conf...")
        sftp.put('backup/99-vpn-optimize.conf', '/etc/sysctl.d/99-vpn-optimize.conf')
        client.exec_command("sysctl --system")
        
    if os.path.exists('backup/ufw_user.rules'):
        print("5. Восстановление /etc/ufw/user.rules...")
        sftp.put('backup/ufw_user.rules', '/etc/ufw/user.rules')
        client.exec_command("ufw reload")
        
    sftp.close()
    
    # 3. Запуск x-ui и warp
    print("6. Запуск и проверка служб x-ui и warp-svc...")
    client.exec_command("systemctl restart warp-svc && systemctl start x-ui")
    
    stdin, stdout, stderr = client.exec_command("systemctl is-active x-ui warp-svc")
    status = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"Статус служб:\n{status}")
    
    client.close()
    print("\n✅ Восстановление завершено! Сервер возвращен к эталонному рабочему состоянию.")

if __name__ == '__main__':
    restore()
