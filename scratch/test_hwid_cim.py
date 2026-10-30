import os, sys, winreg, subprocess, hashlib

def get_hw_fingerprint():
    hw = {"mg": "", "bios": "", "disk": "", "cpu": ""}
    # 1. MachineGuid (из реестра - мгновенно)
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as k:
            mg, _ = winreg.QueryValueEx(k, "MachineGuid")
            if mg: hw["mg"] = hashlib.sha256(mg.strip().lower().encode()).hexdigest()
    except Exception:
        pass

    flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0

    # 2. PowerShell CIM одним запросом
    ps_cmd = (
        "$b = (Get-CimInstance Win32_ComputerSystemProduct -ErrorAction SilentlyContinue).UUID; "
        "$d = (Get-CimInstance Win32_DiskDrive -ErrorAction SilentlyContinue | Select-Object -First 1).SerialNumber; "
        "$c = (Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1).ProcessorId; "
        "\"$b`n$d`n$c\""
    )
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                             capture_output=True, text=True, creationflags=flags).stdout
        parts = [l.strip() for l in out.splitlines() if l.strip()]
        if len(parts) >= 1 and parts[0]:
            hw["bios"] = hashlib.sha256(parts[0].lower().encode()).hexdigest()
        if len(parts) >= 2 and parts[1]:
            hw["disk"] = hashlib.sha256(parts[1].lower().encode()).hexdigest()
        if len(parts) >= 3 and parts[2]:
            hw["cpu"] = hashlib.sha256(parts[2].lower().encode()).hexdigest()
    except Exception:
        pass

    return hw

res = get_hw_fingerprint()
print("CIM HWID result:")
for k, v in res.items():
    print(f"  {k}: {v[:16]}... (valid 64: {len(v)==64})")
