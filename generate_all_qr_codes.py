import qrcode

# 1. Ссылка авто-подписки (Порт 80 HTTP - мгновенная загрузка, без блокировок портов и SSL)
sub_url = "http://193.233.138.42/dlngedpbfjlw072y/83sm0dymf1qn5w9m"
sub_clash_url = "http://193.233.138.42/j982a1z7s8tn85o4/83sm0dymf1qn5w9m"

# 2. Ссылка для Happ в 1 клик
happ_url = f"happ://add/{sub_url}"

# 3. Ссылка для Hiddify в 1 клик (с зашитыми правилами Block QUIC и DNS)
hiddify_url = f"clash://install-config?url={sub_clash_url}&name=VPN-Aeza-Finland"

# 4. Прямые ключи VLESS Reality
link_443 = "vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:443?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=chrome&spx=%2Fbc4490fea17e685&type=tcp&flow=xtls-rprx-vision&sni=speed.cloudflare.com&sid=dae45f#VLESS-Reality-443"
link_2053 = "vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:2053?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=chrome&spx=%2Fbc4490fea17e685&type=tcp&flow=xtls-rprx-vision&sni=azure.microsoft.com&sid=be146e24233aec#VLESS-Reality-2053"

def save_qr(data, filename):
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"Saved {filename}")

save_qr(sub_url, "vpn_qr_auto_subscription.png")
save_qr(happ_url, "vpn_qr_happ_one_click.png")
save_qr(hiddify_url, "vpn_qr_hiddify_one_click.png")
save_qr(link_443, "vpn_qr_port443.png")
save_qr(link_2053, "vpn_qr_port2053.png")

print("All QR codes generated successfully!")
