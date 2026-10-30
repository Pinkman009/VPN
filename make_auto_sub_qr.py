import qrcode

sub_url = "https://193.233.138.42:2096/dlngedpbfjlw072y/83sm0dymf1qn5w9m"
happ_url = f"happ://add/{sub_url}"

# 1. Main Subscription QR Code (scannable by Happ, Hiddify, v2rayNG, Streisand, etc.)
qr_sub = qrcode.QRCode(box_size=10, border=4)
qr_sub.add_data(sub_url)
qr_sub.make(fit=True)
img_sub = qr_sub.make_image(fill_color="black", back_color="white")
img_sub.save("vpn_qr_auto_subscription.png")
print("Saved vpn_qr_auto_subscription.png with HTTPS (Verified Let's Encrypt)")

# 2. Happ 1-click QR code
qr_happ = qrcode.QRCode(box_size=10, border=4)
qr_happ.add_data(happ_url)
qr_happ.make(fit=True)
img_happ = qr_happ.make_image(fill_color="black", back_color="white")
img_happ.save("vpn_qr_happ_one_click.png")
print("Saved vpn_qr_happ_one_click.png with HTTPS")
