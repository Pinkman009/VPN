import os, sys, winreg, subprocess, hashlib

def get_hw_fingerprint():
    hw = {"mg": "", "bios": "", "disk": "", "cpu": ""}
    # 1. MachineGuid
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
            mg, _ = winreg.QueryValueEx(k, "MachineGuid")
            if mg: hw["mg"] = hashlib.sha256(mg.strip().lower().encode()).hexdigest()
    except Exception as e:
        pass

    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    # 2. BIOS UUID
    try:
        out = subprocess.run(["wmic", "csproduct", "get", "uuid"], capture_output=True, text=True, creationflags=flags).stdout
        lines = [l.strip() for l in out.splitlines() if l.strip() and "UUID" not in l]
        if lines: hw["bios"] = hashlib.sha256(lines[0].lower().encode()).hexdigest()
    except Exception:
        pass

    # 3. Disk serial
    try:
        out = subprocess.run(["wmic", "diskdrive", "get", "serialnumber"], capture_output=True, text=True, creationflags=flags).stdout
        lines = [l.strip() for l in out.splitlines() if l.strip() and "SerialNumber" not in l]
        if lines: hw["disk"] = hashlib.sha256(lines[0].lower().encode()).hexdigest()
    except Exception:
        pass

    # 4. CPU
    try:
        out = subprocess.run(["wmic", "cpu", "get", "processorid"], capture_output=True, text=True, creationflags=flags).stdout
        lines = [l.strip() for l in out.splitlines() if l.strip() and "ProcessorId" not in l]
        if lines: hw["cpu"] = hashlib.sha256(lines[0].lower().encode()).hexdigest()
    except Exception:
        pass

    return hw

res = get_hw_fingerprint()
print("HWID result:")
for k, v in res.items():
    print(f"  {k}: {v[:16]}... (valid 64: {len(v)==64})")
