import time
from PIL import ImageGrab

time.sleep(2)
im = ImageGrab.grab()
im.save("c:/Users/MiPro/Desktop/VPN/screen_proof.png")
print("Saved screen_proof.png with resolution:", im.size)
