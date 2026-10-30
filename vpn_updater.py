"""
vpn_updater.py - Automatic Updater for Unblocknet Desktop Client.
Checks GitHub Releases for Pinkman009/VPN, downloads new release binary,
and performs atomic in-place update and app restart.
"""

import os
import sys
import json
import time
import shutil
import urllib.request
import subprocess
import threading

CURRENT_VERSION = "2.6.0"
GITHUB_REPO = "Pinkman009/VPN"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

USER_DATA_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "Unblocknet")
os.makedirs(USER_DATA_DIR, exist_ok=True)
LOG_FILE = os.path.join(USER_DATA_DIR, "updater.log")


def log_updater(msg):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        pass
    print(f"[Updater] {msg}")


def parse_version(v_str):
    """Converts version string like 'v2.6.1' or '2.6.1' to a comparable tuple of ints."""
    clean = v_str.strip().lstrip("vV")
    parts = []
    for p in clean.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def check_for_updates(timeout=5):
    """
    Queries GitHub API to determine if a newer version of Unblocknet is released.
    Returns:
        dict: {
            "has_update": bool,
            "current_version": str,
            "latest_version": str,
            "download_url": str,
            "asset_name": str,
            "asset_size": int,
            "release_notes": str,
            "published_at": str,
            "html_url": str,
            "error": str or None
        }
    """
    res = {
        "has_update": False,
        "current_version": CURRENT_VERSION,
        "latest_version": CURRENT_VERSION,
        "download_url": "",
        "asset_name": "",
        "asset_size": 0,
        "release_notes": "",
        "published_at": "",
        "html_url": f"https://github.com/{GITHUB_REPO}/releases",
        "error": None
    }

    try:
        headers = {
            "User-Agent": f"Unblocknet-Updater/{CURRENT_VERSION}",
            "Accept": "application/vnd.github+json"
        }
        req = urllib.request.Request(RELEASES_API, headers=headers)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))

        tag = data.get("tag_name", "").strip()
        if not tag:
            res["error"] = "no_tag"
            return res

        res["latest_version"] = tag.lstrip("vV")
        res["release_notes"] = data.get("body", "").strip()
        res["published_at"] = data.get("published_at", "")
        res["html_url"] = data.get("html_url", res["html_url"])

        # Compare versions
        current_v = parse_version(CURRENT_VERSION)
        remote_v = parse_version(tag)

        if remote_v > current_v:
            # Locate Windows .exe asset
            assets = data.get("assets", [])
            chosen_asset = None
            for asset in assets:
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    chosen_asset = asset
                    if "unblocknet" in name.lower():
                        break

            if chosen_asset:
                res["has_update"] = True
                res["download_url"] = chosen_asset.get("browser_download_url", "")
                res["asset_name"] = chosen_asset.get("name", "Unblocknet.exe")
                res["asset_size"] = chosen_asset.get("size", 0)
                log_updater(f"New update found: {res['latest_version']} (current: {CURRENT_VERSION})")
            else:
                res["error"] = "no_exe_asset"
        else:
            log_updater(f"Client is up to date ({CURRENT_VERSION}).")

    except urllib.error.HTTPError as e:
        if e.code == 404:
            # No releases published yet on GitHub -> current version is latest
            res["error"] = None
            log_updater("No releases published yet on GitHub. Current version is up to date.")
        else:
            res["error"] = f"HTTP {e.code}"
            log_updater(f"Update check HTTP error: {e}")
    except Exception as e:
        res["error"] = str(e)
        log_updater(f"Update check failed: {e}")

    return res


def download_update(download_url, progress_callback=None, cancel_event=None):
    """
    Downloads the update file with progress tracking.
    progress_callback: fn(downloaded_bytes, total_bytes, percent)
    Returns: (bool success, str path_or_error)
    """
    if not download_url:
        return False, "Empty download URL"

    temp_path = os.path.join(USER_DATA_DIR, "Unblocknet_update.tmp")
    dest_path = os.path.join(USER_DATA_DIR, "Unblocknet_update.exe")

    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception:
        pass

    try:
        log_updater(f"Starting download from: {download_url}")
        headers = {"User-Agent": f"Unblocknet-Updater/{CURRENT_VERSION}"}
        req = urllib.request.Request(download_url, headers=headers)
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

        with opener.open(req, timeout=30) as resp:
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 65536

            with open(temp_path, "wb") as out_file:
                while True:
                    if cancel_event and cancel_event.is_set():
                        log_updater("Download cancelled by user.")
                        return False, "Download cancelled"

                    chunk = resp.read(block_size)
                    if not chunk:
                        break

                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback:
                        pct = int((downloaded / total_size) * 100) if total_size > 0 else 0
                        progress_callback(downloaded, total_size, pct)

        # Validate downloaded executable
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) < 1024 * 100:
            return False, "Downloaded file is corrupted or too small."

        with open(temp_path, "rb") as f:
            header = f.read(2)
            if header != b'MZ':
                return False, "Downloaded file is not a valid Windows executable (PE header missing)."

        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except Exception:
                pass

        shutil.move(temp_path, dest_path)
        log_updater(f"Download complete: {dest_path} ({os.path.getsize(dest_path)} bytes)")
        return True, dest_path

    except Exception as e:
        log_updater(f"Download failed: {e}")
        return False, str(e)


def install_update_and_restart(new_exe_path):
    """
    Spawns detached Windows batch script to replace running executable and relaunch it.
    """
    if getattr(sys, 'frozen', False):
        running_exe = sys.executable
    else:
        # Development mode: replace Unblocknet.exe in workspace or notify
        workspace_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Unblocknet.exe")
        running_exe = workspace_exe

    pid = os.getpid()
    updater_bat = os.path.join(USER_DATA_DIR, "unblocknet_apply_update.bat")

    bat_content = f"""@echo off
chcp 65001 >nul
title Обновление Unblocknet...
echo ===================================================
echo     Обновление Unblocknet до новой версии...
echo ===================================================
echo.
echo Ожидание завершения предыдущего процесса (PID {pid})...
timeout /t 2 /nobreak >nul

taskkill /F /PID {pid} >nul 2>&1
timeout /t 1 /nobreak >nul

echo Замена исполняемого файла...
set RETRY=0
:RETRY_COPY
copy /Y "{new_exe_path}" "{running_exe}" >nul
if errorlevel 1 (
    set /a RETRY+=1
    if %RETRY% leq 6 (
        echo Файл занят, повторная попытка через 1 сек...
        timeout /t 1 /nobreak >nul
        goto RETRY_COPY
    ) else (
        echo Ошибка: не удалось обновить файл {running_exe}.
        pause
        exit /b 1
    )
)

echo Обновление успешно установлено!
echo Запуск новой версии Unblocknet...
start "" "{running_exe}"

timeout /t 2 /nobreak >nul
del "{new_exe_path}" >nul 2>&1
(goto) 2>nul & del "%~f0"
"""

    with open(updater_bat, "w", encoding="utf-8") as f:
        f.write(bat_content)

    log_updater(f"Spawning update batch script: {updater_bat}")
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NEW_CONSOLE | subprocess.CREATE_NO_WINDOW

    subprocess.Popen(["cmd.exe", "/c", updater_bat], creationflags=flags)
    return True
