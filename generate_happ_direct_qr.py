import qrcode

# Основной проверенный VLESS Reality ключ (Порт 443, маскировка speed.cloudflare.com)
link_443 = "vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:443?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=chrome&spx=%2F&type=tcp&flow=xtls-rprx-vision&sni=speed.cloudflare.com&sid=dae45f#VLESS-443-Aeza-Finland"

# Резервный VLESS Reality ключ (Порт 2053, маскировка azure.microsoft.com)
link_2053 = "vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:2053?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=chrome&spx=%2F&type=tcp&flow=xtls-rprx-vision&sni=azure.microsoft.com&sid=dae45f#VLESS-2053-Aeza-Finland"

def make_qr(data, filename):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"Generated {filename}")

# 1. Главный QR-код для Happ (идеально читается камерой на iOS и Android)
make_qr(link_443, "vpn_qr_happ_main_443.png")

# 2. Резервный QR-код для Happ
make_qr(link_2053, "vpn_qr_happ_backup_2053.png")

# Обновляем и старые имена файлов для совместимости
make_qr(link_443, "vpn_qr_port443.png")
make_qr(link_2053, "vpn_qr_port2053.png")

print("All Happ direct QR codes generated successfully!")
