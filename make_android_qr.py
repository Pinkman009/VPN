import qrcode

# Рабочие проверенные ссылки с обходом ТСПУ (DPI)
link_443 = "vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:443?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=chrome&spx=%2Fbc4490fea17e685&type=tcp&flow=xtls-rprx-vision&sni=speed.cloudflare.com&sid=dae45f#VLESS-Reality-443"
link_2053 = "vless://04756662-2f98-44ad-a53a-369d29118670@193.233.138.42:2053?security=reality&encryption=none&pbk=t0hTDOJOklZjxWHR_hJo2gg6nWUmSNA-gxFdERpTWRE&headerType=none&fp=chrome&spx=%2Fbc4490fea17e685&type=tcp&flow=xtls-rprx-vision&sni=azure.microsoft.com&sid=be146e24233aec&type=tcp#VLESS-Reality-2053"

qr1 = qrcode.QRCode(box_size=10, border=4)
qr1.add_data(link_443)
qr1.make(fit=True)
img1 = qr1.make_image(fill_color="black", back_color="white")
img1.save("vpn_qr_port443.png")
print("Saved vpn_qr_port443.png (speed.cloudflare.com)")

qr2 = qrcode.QRCode(box_size=10, border=4)
qr2.add_data(link_2053)
qr2.make(fit=True)
img2 = qr2.make_image(fill_color="black", back_color="white")
img2.save("vpn_qr_port2053.png")
print("Saved vpn_qr_port2053.png (azure.microsoft.com)")

